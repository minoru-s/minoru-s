#!/usr/bin/env python3
"""Refresh the public-repository activity block in the profile README."""

from __future__ import annotations

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "minoru-s"
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- recent:start -->"
END = "<!-- recent:end -->"

# Verified icons from the deployed applications themselves. Immutable commit URLs
# keep the profile stable even if a favicon is replaced later.
DEPLOYED_APPS = {
    "pdf-injection-detector": {
        "url": "https://minoru-s.github.io/pdf-injection-detector/",
        "icon": "https://raw.githubusercontent.com/minoru-s/pdf-injection-detector/8bcc734609b0b5f2994f3b6bec9e4f7bc9392e88/public/apple-touch-icon.png",
        "label": "PDFender",
    },
    "portfolio": {
        "url": "https://minoru-s.github.io/portfolio/en/",
        "icon": "https://raw.githubusercontent.com/minoru-s/portfolio/f53efcdd7689cc64a44bfe802b5bffcedc596c5c/portfolio-src/public/favicon.svg",
        "label": "portfolio",
    },
    "mapping-plus": {
        "url": "https://minoru-s.github.io/mapping-plus/",
        "icon": "https://raw.githubusercontent.com/minoru-s/mapping-plus/6aadb5e0671f8060e4f0d73613f972c8bddcd61d/favicon.svg",
        "label": "Mapping Plus",
    },
    "pdf-raster-exporter": {
        "url": "https://minoru-s.github.io/pdf-raster-exporter/",
        "icon": "https://raw.githubusercontent.com/minoru-s/pdf-raster-exporter/f979de41eaba53a4e78ba3af6ed8546a948a13d9/public/apple-touch-icon.png",
        "label": "PDF Raster Exporter",
    },
}


def fetch_repositories() -> list[dict]:
    request = Request(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USERNAME}-profile-readme",
            **(
                {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
                if os.environ.get("GITHUB_TOKEN")
                else {}
            ),
        },
    )
    with urlopen(request, timeout=20) as response:
        repositories = json.load(response)

    return [
        repo
        for repo in repositories
        if not repo["fork"]
        and not repo["archived"]
        and repo["name"] != USERNAME
    ][:4]


def clean(value: str | None) -> str:
    return escape((value or "Public project").replace("\n", " ").strip())


def render(repositories: list[dict]) -> str:
    rows = ["<table>"]

    for repo in repositories:
        updated = datetime.fromisoformat(
            repo["updated_at"].replace("Z", "+00:00")
        ).strftime("%Y-%m-%d")
        name = escape(repo["name"])
        repo_url = escape(repo["html_url"], quote=True)
        description = clean(repo.get("description"))
        app = DEPLOYED_APPS.get(repo["name"])

        if app:
            app_url = escape(app["url"], quote=True)
            icon_url = escape(app["icon"], quote=True)
            label = escape(app["label"], quote=True)
            icon = (
                f'<a href="{app_url}"><img src="{icon_url}" width="48" '
                f'height="48" alt="Open {label}"></a>'
            )
            action = f'<br><a href="{app_url}"><code>OPEN APP ↗</code></a>'
        else:
            icon = "<sub>REPO</sub>"
            action = ""

        rows.extend(
            [
                "<tr>",
                f'<td width="72" align="center">{icon}</td>',
                f'<td><strong><a href="{repo_url}">{name}</a></strong><br>'
                f"<sub>{description}</sub>{action}</td>",
                f'<td width="105" align="right"><sub>UPDATED</sub><br>'
                f"<code>{updated}</code></td>",
                "</tr>",
            ]
        )

    rows.append("</table>")
    return "\n".join(rows)


def main() -> None:
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise RuntimeError("README activity markers are missing")

    before, remainder = readme.split(START, 1)
    _, after = remainder.split(END, 1)
    block = f"{START}\n{render(fetch_repositories())}\n{END}"
    README.write_text(f"{before}{block}{after}", encoding="utf-8")


if __name__ == "__main__":
    main()
