import argparse
from pathlib import Path
from subprocess import check_output

import tomllib
from nbconvert import MarkdownExporter
from nbconvert.filters.strings import get_lines


def generate_frontmatter(notebook):
    last_commit_date = (
        check_output(f'git log -1 --pretty=format:"%cs" {notebook["file"]}'.split())
        .decode()
        .strip()
    )
    first_commit_date = (
        check_output(
            f'git log --reverse --pretty=format:"%cs" {notebook["file"]}'.split()
        )
        .decode()
        .strip()
        .splitlines()[0]
    )

    frontmatter = f"""---
layout: cookbook
featured_image: /images/tutorial_walkthrough_thumbnail.png
images: ["/images/tutorial_walkthrough_thumbnail.png"]
sitemap_exclude: False
colab: {notebook.get("colab")}
toc: True
title: "{notebook["title"]}"
lastmod: {last_commit_date}
created_at: {first_commit_date}
download: /downloads/{notebook["file"].name}
featured: {notebook.get("featured", False)}
experimental: {notebook.get("experimental", False)}
discuss: {notebook.get("discuss", False)}
hidden: {notebook.get("hidden", False)}
new: {notebook.get("new", False)}
topics: {notebook.get("topics", False)}
---
    """
    return frontmatter


def generate_markdown_from_notebook(notebook, output_path):
    frontmatter = generate_frontmatter(notebook)
    md_exporter = MarkdownExporter(exclude_output=True)
    body, _ = md_exporter.from_filename(f"{notebook['file']}")
    body = get_lines(body, start=1)
    print(f"Processing {notebook['file']}")
    filename = notebook["file"].stem
    with open(f"{output_path}/{filename}.md", "w", encoding="utf-8") as f:
        try:
            f.write(frontmatter + "\n\n")
        except IndexError as e:
            raise IndexError(
                "Can't find the header for this tutorial. Have you added it in 'scripts/generate_markdowns.py'?"
            ) from e
        f.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", dest="output", default="markdowns")
    args = parser.parse_args()
    root_path = Path(__file__).parent.parent

    readme_file = root_path / "README.md"
    readme_content = readme_file.read_text()

    index_file = root_path / "index.toml"
    index_data = tomllib.loads(index_file.read_text())

    if not Path(args.output).exists():
        Path(args.output).mkdir(parents=True, exist_ok=True)

    for cookbook_data in index_data["cookbook"]:
        data = {
            "file": root_path / "notebooks" / cookbook_data["notebook"],
            "title": cookbook_data["title"],
            "colab": f"{index_data["config"]["colab"]}/{cookbook_data['notebook']}",
            "featured": cookbook_data.get("featured", False),
            "experimental": cookbook_data.get("experimental", False),
            "discuss": cookbook_data.get("discuss", False),
            "hidden": cookbook_data.get("hidden", False),
            "new": cookbook_data.get("new", False),
            "topics": cookbook_data.get("topics", False),
        }
        generate_markdown_from_notebook(data, args.output)
