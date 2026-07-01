import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"


def request_json(url, token=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Equ-Blog-Issue-Exporter",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {url}\n{detail}") from exc


def collect_paginated(url, token=None):
    page = 1
    items = []
    separator = "&" if "?" in url else "?"
    while True:
        batch = request_json(f"{url}{separator}per_page=100&page={page}", token=token)
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def toml_string(value):
    return json.dumps(value or "", ensure_ascii=False)


def toml_array(values):
    return "[" + ", ".join(toml_string(value) for value in values) + "]"


def issue_html_url(owner, repo, number):
    return f"https://github.com/{owner}/{repo}/issues/{number}"


def format_date(value):
    return (value or time.strftime("%Y-%m-%d"))[:10]


def floor_label(label, user, created_at):
    author = user.get("login", "unknown") if user else "unknown"
    date = format_date(created_at)
    return f'<p class="issue-floor-label">{label} · @{author} · {date}</p>'


def normalize_markdown(body):
    body = (body or "").strip()
    return body if body else "_这一层暂时没有正文。_"


def render_issue(owner, repo, issue, comments):
    number = issue["number"]
    labels = [label["name"] for label in issue.get("labels", [])]
    frontmatter = [
        "+++",
        f"title = {toml_string(issue.get('title'))}",
        f"date = {format_date(issue.get('created_at'))}",
        "[taxonomies]",
        f"tags = {toml_array(labels)}",
        "[extra]",
        f"issue_url = {toml_string(issue_html_url(owner, repo, number))}",
        f"issue_number = {number}",
        f"comment_count = {len(comments)}",
        "+++",
        "",
    ]

    body_parts = [
        floor_label("主楼", issue.get("user"), issue.get("created_at")),
        "",
        normalize_markdown(issue.get("body")),
    ]

    for index, comment in enumerate(comments, start=1):
        body_parts.extend(
            [
                "",
                "---",
                "",
                floor_label(f"第 {index} 楼", comment.get("user"), comment.get("created_at")),
                "",
                normalize_markdown(comment.get("body")),
            ]
        )

    return "\n".join(frontmatter + body_parts).rstrip() + "\n"


def write_issue_pages(owner, repo, output_dir, token=None, state="open"):
    issues_url = f"{API_ROOT}/repos/{owner}/{repo}/issues?state={state}"
    issues = collect_paginated(issues_url, token=token)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    written = 0
    for issue in issues:
        if "pull_request" in issue:
            continue
        number = issue["number"]
        comments_url = f"{API_ROOT}/repos/{owner}/{repo}/issues/{number}/comments"
        comments = collect_paginated(comments_url, token=token)
        markdown = render_issue(owner, repo, issue, comments)
        (output_path / f"issue-{number}.md").write_text(markdown, encoding="utf-8")
        written += 1

    return written


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate full Zola issue pages, including issue comments."
    )
    parser.add_argument("--user", required=True, help="GitHub owner")
    parser.add_argument("--repo", required=True, help="GitHub repository")
    parser.add_argument("--output", default="output/content", help="Zola content directory")
    parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    return parser.parse_args()


def main():
    args = parse_args()
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    owner = args.user
    repo = args.repo

    if "/" in repo:
        parsed = repo.split("/", 1)
        owner, repo = parsed[0], parsed[1]

    written = write_issue_pages(owner, repo, args.output, token=token, state=args.state)
    print(f"Generated {written} full issue page(s) in {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
