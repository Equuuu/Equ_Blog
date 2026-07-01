import argparse
import html
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"
HOME_ABOUT_TEXT = (
    "这个博客由 GitHub Issues 自动整理。在这里我想留下这段话，宇宙如果放任不管，就会朝着散乱的方向发展，"
    "而我们却通过修复身体、整理信息来对抗这个宇宙的法则，正是这种对抗让我们活了下来，而对抗的痕迹则以记忆、"
    "文化和语言的形式残留在宇宙中，一切都朝着易碎而短暂的方向前进，然而人类却试图保存文化，留下爱与记忆。"
    "你说生命是一场苦行，人类需要脱离自己的劣根性，潜在的欲望，自我隐约的虚荣，自以为是的高尚和成功，"
    "探索内在的精神。去达到“神”的境界，选择和创造自己在乎的世界，并为这个“执念”而活，不需要过分地努力，"
    "只需要融化进自己的身体中。一个无关欲望，无关时代，无关他人的“心愿 执念 风格”。你觉得人是为了一个执念活着的，"
    "并因此经历生命的一切。至于它像什么，它像刺入灵魂的长长的柔软的钢筋，无意识地存在着，当不经意忘记和改变时，"
    "会感到心碎和疼痛，于是它变成了神性。于是，我爱你。"
)


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


def render_issue_body(issue, comments):
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

    return "\n".join(body_parts).rstrip() + "\n"


def render_zola_issue(owner, repo, issue, comments):
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

    return "\n".join(frontmatter) + render_issue_body(issue, comments)


def render_static_issue(owner, repo, issue, comments):
    import markdown

    number = issue["number"]
    title = issue.get("title") or f"Issue {number}"
    date = format_date(issue.get("created_at"))
    comment_count = len(comments)
    labels = [label["name"] for label in issue.get("labels", [])]
    labels_html = "".join(f"<span>#{html.escape(label)}</span>" for label in labels)
    article_html = markdown.markdown(
        render_issue_body(issue, comments),
        output_format="html5",
        extensions=["extra", "sane_lists"],
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} · Equ's Blog</title>
  <meta name="description" content="由 GitHub Issues 自动同步生成的阅读页">
  <link rel="stylesheet" href="../assets/css/home.css">
  <link rel="alternate" type="application/atom+xml" title="Equ's Blog" href="../feed.xml">
  <script defer src="../assets/js/home.js"></script>
</head>
<body>
  <div class="reading-progress" aria-hidden="true"></div>
  <header class="site-header">
    <a class="brand" href="../">Equ</a>
    <nav class="nav" aria-label="Primary navigation">
      <a href="../">首页</a>
      <a href="../#latest">最近更新</a>
      <a href="../feed.xml">RSS</a>
      <a href="https://github.com/{html.escape(owner)}/{html.escape(repo)}">GitHub</a>
    </nav>
    <button class="music-toggle" type="button" aria-label="播放巴赫音乐" aria-pressed="false" data-music-src="https://upload.wikimedia.org/wikipedia/commons/transcoded/4/4b/Bach_-_Cello_Suite_no._1_in_G_major%2C_BWV_1007_-_IV._Sarabande.ogg/Bach_-_Cello_Suite_no._1_in_G_major%2C_BWV_1007_-_IV._Sarabande.ogg.mp3">
      <span class="music-toggle-dot" aria-hidden="true"></span>
      <span class="music-toggle-label">Bach</span>
    </button>
    <button class="theme-toggle" type="button" aria-label="切换深浅主题" aria-pressed="false">
      <span class="theme-toggle-mark" aria-hidden="true">夜</span>
      <span class="theme-toggle-label">夜间</span>
    </button>
  </header>

  <main>
    <article class="article reading-article">
      <header class="article-header">
        <div class="article-kicker">
          <a class="back-link" href="../">← 返回首页</a>
          <span>Issue archive</span>
        </div>
        <h1>{html.escape(title)}</h1>
        <div class="article-meta">
          <time datetime="{date}">{date}</time>
          <span>·</span>
          <span>{comment_count} 个评论楼层</span>
          {f'<span>·</span><div class="article-tags">{labels_html}</div>' if labels_html else ''}
        </div>
      </header>

      <div class="article-content">
{article_html}
      </div>

      <footer class="article-footer">
        <a class="button" href="../">回到首页</a>
        <a class="issue-link" href="{issue_html_url(owner, repo, number)}">在 GitHub Issue 中查看原文</a>
      </footer>
    </article>
  </main>

  <footer class="site-footer">
    <span>Equ's Blog</span>
    <span>Notes from GitHub Issues.</span>
  </footer>
</body>
</html>
"""


def issue_labels(issue):
    labels = [
        label.get("name", "").strip()
        for label in issue.get("labels", [])
        if label.get("name", "").strip()
    ]
    return labels or ["未分类"]


def render_static_home(owner, repo, issues):
    visible_issues = [
        issue for issue in issues
        if "pull_request" not in issue
    ]
    visible_issues.sort(key=lambda item: item.get("created_at") or "", reverse=True)

    grouped = {}
    for issue in visible_issues:
        for label in issue_labels(issue):
            grouped.setdefault(label, []).append(issue)

    group_parts = []
    for label, group_issues in grouped.items():
        cards = []
        for issue in group_issues:
            labels = issue_labels(issue)
            title = issue.get("title") or f"Issue {issue['number']}"
            date = format_date(issue.get("created_at"))
            search_text = " ".join([title, *labels])
            cards.append(
                f"""            <article class="post-card" data-search="{html.escape(search_text)}">
              <div>
                <a class="post-title" href="issue-{issue['number']}/">{html.escape(title)}</a>
              </div>
              <time datetime="{date}">{date}</time>
            </article>"""
            )

        group_parts.append(
            f"""        <details class="post-group" data-group-search="{html.escape(label)}">
          <summary class="post-group-summary">
            <span class="post-group-title">{html.escape(label)}</span>
            <span class="post-group-count">{len(group_issues)} 篇</span>
          </summary>
          <div class="post-list post-list-nested">
{chr(10).join(cards)}
          </div>
        </details>"""
        )

    groups_html = "\n".join(group_parts) if group_parts else '        <p class="empty">还没有文章。</p>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Equ's Blog</title>
  <meta name="description" content="阅读、生活、技术与一些短暂但明亮的记录">
  <link rel="stylesheet" href="assets/css/home.css">
  <link rel="alternate" type="application/atom+xml" title="Equ's Blog" href="feed.xml">
  <script defer src="assets/js/home.js"></script>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="./">Equ</a>
    <nav class="nav" aria-label="Primary navigation">
      <a href="#latest">最近更新</a>
      <a href="#about">关于</a>
      <a href="feed.xml">RSS</a>
      <a href="https://github.com/{html.escape(owner)}/{html.escape(repo)}">GitHub</a>
    </nav>
    <button class="music-toggle" type="button" aria-label="播放巴赫音乐" aria-pressed="false" data-music-src="https://upload.wikimedia.org/wikipedia/commons/transcoded/4/4b/Bach_-_Cello_Suite_no._1_in_G_major%2C_BWV_1007_-_IV._Sarabande.ogg/Bach_-_Cello_Suite_no._1_in_G_major%2C_BWV_1007_-_IV._Sarabande.ogg.mp3">
      <span class="music-toggle-dot" aria-hidden="true"></span>
      <span class="music-toggle-label">Bach</span>
    </button>
    <button class="theme-toggle" type="button" aria-label="切换深浅主题" aria-pressed="false">
      <span class="theme-toggle-mark" aria-hidden="true">夜</span>
      <span class="theme-toggle-label">夜间</span>
    </button>
  </header>

  <main>
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Digital garden / notes / essays</p>
        <h1>彷佛像水面泡沫的短暂光亮</h1>
        <p class="hero-text">这里有小马的阅读、生活、技术和日常观察，以及曾经我们种植的蜀葵。</p>
        <div class="hero-actions">
          <a class="button button-primary" href="#latest">阅读最近更新</a>
          <a class="button" href="https://github.com/{html.escape(owner)}/{html.escape(repo)}/issues">浏览 Issues</a>
        </div>
      </div>
      <aside class="hero-panel" aria-label="Blog summary">
        <span class="panel-kicker">Archive</span>
        <strong>{len(visible_issues)}</strong>
        <span>篇公开记录</span>
        <div class="theme-list">
          <span>阅读</span>
          <span>生活</span>
          <span>技术</span>
          <span>花园</span>
        </div>
      </aside>
    </section>

    <section class="section-block" id="latest">
      <div class="section-heading">
        <p>Latest</p>
      </div>
      <div class="post-tools" aria-label="文章搜索">
        <label class="search-field">
          <span class="sr-only">搜索文章</span>
          <input class="blog-search-input" type="search" placeholder="搜索文章、标签或关键词" autocomplete="off">
        </label>
        <button class="search-clear" type="button" hidden>清除</button>
      </div>
      <div class="post-groups">
{groups_html}
      </div>
      <p class="search-empty" hidden>没有找到匹配的文章。</p>
    </section>

    <section class="section-block about-block" id="about">
      <div class="section-heading">
        <p>About</p>
      </div>
      <p>{html.escape(HOME_ABOUT_TEXT)}</p>
    </section>
  </main>

  <footer class="site-footer">
    <span>Equ's Blog</span>
    <span>Notes from GitHub Issues.</span>
  </footer>
</body>
</html>
"""


def write_issue_pages(owner, repo, output_dir, token=None, state="open", static_output_dir=None):
    issues_url = f"{API_ROOT}/repos/{owner}/{repo}/issues?state={state}"
    issues = collect_paginated(issues_url, token=token)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    static_output_path = Path(static_output_dir) if static_output_dir else None

    written = 0
    for issue in issues:
        if "pull_request" in issue:
            continue
        number = issue["number"]
        comments_url = f"{API_ROOT}/repos/{owner}/{repo}/issues/{number}/comments"
        comments = collect_paginated(comments_url, token=token)
        markdown = render_zola_issue(owner, repo, issue, comments)
        (output_path / f"issue-{number}.md").write_text(markdown, encoding="utf-8")
        if static_output_path:
            issue_dir = static_output_path / f"issue-{number}"
            issue_dir.mkdir(parents=True, exist_ok=True)
            (issue_dir / "index.html").write_text(
                render_static_issue(owner, repo, issue, comments),
                encoding="utf-8",
            )
        written += 1

    if static_output_path:
        (static_output_path / "index.html").write_text(
            render_static_home(owner, repo, issues),
            encoding="utf-8",
        )

    return written


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate full Zola issue pages, including issue comments."
    )
    parser.add_argument("--user", required=True, help="GitHub owner")
    parser.add_argument("--repo", required=True, help="GitHub repository")
    parser.add_argument("--output", default="output/content", help="Zola content directory")
    parser.add_argument("--static-output", help="Optional static site root for issue-N/index.html")
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

    written = write_issue_pages(
        owner,
        repo,
        args.output,
        token=token,
        state=args.state,
        static_output_dir=args.static_output,
    )
    print(f"Generated {written} full issue page(s) in {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
