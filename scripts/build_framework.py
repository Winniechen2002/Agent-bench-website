"""Render the two discussion outlines. Does not generate or update a PDF."""
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    {
        "source": "docs/website-outline.md", "output": "outline.html",
        "title": "网站框架", "label": "WEBSITE OUTLINE",
        "anchors": ["structure", "overview", "motivation", "tasks", "evaluation",
                    "results", "resources", "team", "options", "decisions"],
    },
    {
        "source": "docs/technical-report.md", "output": "report.html",
        "title": "Tech Report 框架", "label": "REPORT OUTLINE",
        "anchors": ["structure", "abstract", "introduction", "related-work",
                    "benchmark-design", "evaluation-protocol", "implementation",
                    "experiments", "limitations", "conclusion", "appendix", "website"],
    },
]


def render_page(page):
    raw = (ROOT / page["source"]).read_text(encoding="utf-8")
    soup = BeautifulSoup(MarkdownIt("default", {"html": False}).render(raw), "html.parser")
    headings = soup.find_all("h2")
    if len(headings) != len(page["anchors"]):
        raise ValueError(f'Update heading anchors for {page["source"]}')
    toc = []
    for heading, anchor in zip(headings, page["anchors"]):
        section = soup.new_tag("section", attrs={"class": "outline-section", "id": anchor})
        heading.insert_before(section)
        node = heading
        while node is not None and (node is heading or getattr(node, "name", None) != "h2"):
            following = node.next_sibling
            section.append(node.extract())
            node = following
        toc.append(f'<a href="#{anchor}">{escape(heading.get_text())}</a>')
    for table in soup.find_all("table"):
        label = table.find_previous("h2").get_text()
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll", "tabindex": "0",
                                              "role": "region", "aria-label": label})
        table.wrap(wrapper)
        for th in table.find_all("th"):
            th["scope"] = "col"
    title = soup.find("h1")
    title["id"] = "page-title"
    status = title.find_next_sibling("p")
    status["class"] = "draft-note"
    nav = "".join(
        f'<a href="{p["output"]}"' + (' aria-current="page"' if p is page else '') + f'>{p["title"]}</a>'
        for p in PAGES
    )
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Agent Bench {page['title']}：讨论章节、内容取舍与建议篇幅。">
  <meta name="theme-color" content="#f7f6f2">
  <title>Agent Bench · {page['title']}</title>
  <link rel="icon" href="assets/favicon.svg">
  <link rel="stylesheet" href="framework.css">
</head>
<body>
  <a class="skip-link" href="#content">跳到框架正文</a>
  <header class="site-header">
    <a class="brand" href="index.html">Agent Bench <span>／内容规划</span></a>
    <nav class="page-tabs" aria-label="两份框架">{nav}</nav>
  </header>
  <div class="layout">
    <aside class="sidebar">
      <p class="eyebrow">{page['label']}</p>
      <nav class="toc" aria-label="本页目录">{''.join(toc)}</nav>
      <a class="source-link" href="{page['source']}" download>下载可编辑 Markdown <span aria-hidden="true">↓</span></a>
      <p class="sidebar-note">可以逐项批注：<br>保留 · 合并 · 删除 · 调整篇幅</p>
    </aside>
    <main id="content" aria-labelledby="page-title">
      <div class="status"><span aria-hidden="true"></span> STRUCTURE FIRST <span class="status-version">V0.2</span></div>
      {soup}
      <footer class="page-footer">
        <span>结构确定后，再写英文正文与选择图表。</span>
        <a href="archive/README.md">上一版归档说明 ↗</a>
      </footer>
    </main>
  </div>
</body>
</html>
'''


def build():
    for page in PAGES:
        (ROOT / page["output"]).write_text(render_page(page), encoding="utf-8")
        print(f'{page["source"]} → {page["output"]}')


if __name__ == "__main__":
    build()
