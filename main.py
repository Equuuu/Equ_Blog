# -*- coding: utf-8 -*-
import argparse
import os
import re

import markdown
from feedgen.feed import FeedGenerator
from github import Github
from lxml.etree import CDATA
from marko.ext.gfm import gfm as marko

DEFAULT_BRANCH = "main"
BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5
RECENT_ISSUE_LIMIT = 2

TOP_ISSUES_LABELS = ["Top"]
TODO_ISSUES_LABELS = ["TODO"]
FRIENDS_LABELS = ["Friends"]
ABOUT_LABELS = ["About"]
IGNORE_LABELS = FRIENDS_LABELS + TOP_ISSUES_LABELS + TODO_ISSUES_LABELS + ABOUT_LABELS

README_HEADER = """<div align="center">

# Equ's Blog

<p align="center">彷佛像水面泡沫的短暂光亮。</p>

[最近更新](#最近更新) · [RSS Feed](https://raw.githubusercontent.com/{repo_name}/{branch}/feed.xml) · [GitHub](https://github.com/{repo_name})

</div>

---

<p align="center">这里记录阅读、生活、技术、我们曾种植的蜀葵，以及一些短暂但明亮的东西。</p>
"""

FRIENDS_TABLE_HEAD = "| Name | Link | Desc |\n| ---- | ---- | ---- |\n"
FRIENDS_TABLE_TEMPLATE = "| {name} | {link} | {desc} |\n"
FRIENDS_INFO_DICT = {
    "名字": "",
    "链接": "",
    "描述": "",
}


def get_me(user):
    return user.get_user().login


def is_me(issue, me):
    return issue.user.login == me


def is_hearted_by_me(comment, me):
    for reaction in comment.get_reactions():
        if reaction.content == "heart" and reaction.user.login == me:
            return True
    return False


def _make_friend_table_string(body):
    info_dict = FRIENDS_INFO_DICT.copy()
    try:
        lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
        for line in lines:
            parts = re.split(r"[：:]", line, maxsplit=1)
            if len(parts) != 2:
                continue
            key, value = parts[0].strip(), parts[1].strip()
            if key in info_dict:
                info_dict[key] = value
        return FRIENDS_TABLE_TEMPLATE.format(
            name=info_dict["名字"],
            link=info_dict["链接"],
            desc=info_dict["描述"],
        )
    except Exception as exc:
        print(str(exc))
        return ""


def _valid_xml_char_ordinal(char):
    codepoint = ord(char)
    return (
        0x20 <= codepoint <= 0xD7FF
        or codepoint in (0x9, 0xA, 0xD)
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def format_time(value):
    return str(value)[:10]


def get_issue_page_url(issue):
    match = re.match(r"https://github.com/([^/]+)/([^/]+)/issues/(\d+)", issue.html_url)
    if not match:
        return issue.html_url
    owner, repo, number = match.groups()
    return f"https://{owner}.github.io/{repo}/issues/issue-{number}/"


def login(token):
    return Github(token) if token else Github()


def get_repo(user: Github, repo: str):
    return user.get_repo(repo)


def parse_todo(issue):
    body = (issue.body or "").splitlines()
    todo_undone = [line for line in body if line.startswith("- [ ] ")]
    todo_done = [line for line in body if line.startswith("- [x] ")]
    if not todo_undone:
        return f"[{issue.title}]({issue.html_url}) all done", []
    return (
        f"[{issue.title}]({issue.html_url})--{len(todo_undone)} jobs to do--{len(todo_done)} jobs done",
        todo_done + todo_undone,
    )


def get_top_issues(repo):
    return repo.get_issues(labels=TOP_ISSUES_LABELS)


def get_todo_issues(repo):
    return repo.get_issues(labels=TODO_ISSUES_LABELS)


def get_repo_labels(repo):
    return [label for label in repo.get_labels()]


def get_issues_from_label(repo, label):
    return repo.get_issues(labels=(label,))


def add_issue_info(issue, handle):
    handle.write(f"- [{issue.title}]({get_issue_page_url(issue)}) · {format_time(issue.created_at)}\n")


def add_md_todo(repo, md_path, me):
    todo_issues = list(get_todo_issues(repo))
    if not TODO_ISSUES_LABELS or not todo_issues:
        return
    with open(md_path, "a+", encoding="utf-8") as handle:
        handle.write("\n## TODO\n\n")
        for issue in todo_issues:
            if is_me(issue, me):
                todo_title, todo_list = parse_todo(issue)
                handle.write("TODO list from " + todo_title + "\n")
                for todo in todo_list:
                    handle.write(todo + "\n")
                handle.write("\n")


def add_md_top(repo, md_path, me):
    top_issues = list(get_top_issues(repo))
    if not TOP_ISSUES_LABELS or not top_issues:
        return
    with open(md_path, "a+", encoding="utf-8") as handle:
        handle.write("\n## 置顶文章\n\n")
        for issue in top_issues:
            if is_me(issue, me):
                add_issue_info(issue, handle)
        handle.write("\n")


def add_md_friends(repo, md_path, me):
    friends_issues = list(repo.get_issues(labels=FRIENDS_LABELS))
    if not FRIENDS_LABELS or not friends_issues:
        return

    table_markdown = FRIENDS_TABLE_HEAD
    friends_issue_url = friends_issues[0].html_url
    for issue in friends_issues:
        for comment in issue.get_comments():
            if is_hearted_by_me(comment, me):
                table_markdown += _make_friend_table_string(comment.body or "")

    table_html = markdown.markdown(table_markdown, output_format="html", extensions=["extra"])
    with open(md_path, "a+", encoding="utf-8") as handle:
        handle.write(f"\n## [友情链接]({friends_issue_url})\n\n")
        handle.write("<details><summary>显示</summary>\n")
        handle.write(table_html)
        handle.write("</details>\n\n")


def add_md_recent(repo, md_path, me, limit=RECENT_ISSUE_LIMIT):
    count = 0
    with open(md_path, "a+", encoding="utf-8") as handle:
        try:
            handle.write("\n## 最近更新\n\n")
            for issue in repo.get_issues():
                if is_me(issue, me):
                    add_issue_info(issue, handle)
                    count += 1
                    if count >= limit:
                        break
            handle.write("\n")
        except Exception as exc:
            print(str(exc))


def add_md_header(md_path, repo_name):
    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(README_HEADER.format(repo_name=repo_name, branch=DEFAULT_BRANCH))
        handle.write("\n")


def add_md_label(repo, md_path, me):
    labels = sorted(
        get_repo_labels(repo),
        key=lambda label: (
            label.description is None,
            label.description == "",
            label.description,
            label.name,
        ),
    )

    with open(md_path, "a+", encoding="utf-8") as handle:
        for label in labels:
            if label.name in IGNORE_LABELS:
                continue

            issues = get_issues_from_label(repo, label)
            if not issues.totalCount:
                continue

            handle.write("\n## " + label.name + "\n\n")
            visible_issues = sorted(issues, key=lambda item: item.created_at, reverse=True)
            count = 0
            for issue in visible_issues:
                if not issue or not is_me(issue, me):
                    continue
                if count == ANCHOR_NUMBER:
                    handle.write("<details><summary>显示更多</summary>\n\n")
                add_issue_info(issue, handle)
                count += 1
            if count > ANCHOR_NUMBER:
                handle.write("</details>\n\n")


def get_to_generate_issues(repo, dir_name, issue_number=None):
    md_files = os.listdir(dir_name)
    generated_issue_numbers = [int(name.split("_")[0]) for name in md_files if name.split("_")[0].isdigit()]
    to_generate_issues = [
        issue
        for issue in list(repo.get_issues())
        if int(issue.number) not in generated_issue_numbers
    ]
    if issue_number:
        try:
            to_generate_issues.append(repo.get_issue(int(issue_number)))
        except Exception:
            pass
    return to_generate_issues


def generate_rss_feed(repo, filename, me):
    generator = FeedGenerator()
    generator.id(repo.html_url)
    generator.title(f"RSS feed of {repo.owner.login}'s {repo.name}")
    generator.author({"name": os.getenv("GITHUB_NAME"), "email": os.getenv("GITHUB_EMAIL")})
    generator.link(href=repo.html_url)
    generator.link(
        href=f"https://raw.githubusercontent.com/{repo.full_name}/{DEFAULT_BRANCH}/{filename}",
        rel="self",
    )
    for issue in repo.get_issues():
        if not issue.body or not is_me(issue, me) or issue.pull_request:
            continue
        item = generator.add_entry(order="append")
        item.id(issue.html_url)
        item.link(href=get_issue_page_url(issue))
        item.title(issue.title)
        item.published(issue.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
        for label in issue.labels:
            item.category({"term": label.name})
        body = "".join(char for char in issue.body if _valid_xml_char_ordinal(char))
        item.content(CDATA(marko.convert(body)), type="html")
    generator.atom_file(filename)


def save_issue(issue, me, dir_name=BACKUP_DIR):
    md_name = os.path.join(
        dir_name, f"{issue.number}_{issue.title.replace('/', '-').replace(' ', '.')}.md"
    )
    with open(md_name, "w", encoding="utf-8") as handle:
        handle.write(f"# [{issue.title}]({issue.html_url})\n\n")
        handle.write(issue.body or "")
        if issue.comments:
            for comment in issue.get_comments():
                if is_me(comment, me):
                    handle.write("\n\n---\n\n")
                    handle.write(comment.body or "")


def main(token, repo_name, issue_number=None, dir_name=BACKUP_DIR):
    user = login(token)
    me = get_me(user)
    repo = get_repo(user, repo_name)

    add_md_header("README.md", repo_name)
    for writer in [add_md_friends, add_md_top, add_md_recent, add_md_label, add_md_todo]:
        writer(repo, "README.md", me)

    generate_rss_feed(repo, "feed.xml", me)
    for issue in get_to_generate_issues(repo, dir_name, issue_number):
        save_issue(issue, me, dir_name)


if __name__ == "__main__":
    if not os.path.exists(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)

    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument("--issue_number", help="issue_number", default=None, required=False)
    options = parser.parse_args()
    main(options.github_token, options.repo_name, options.issue_number)
