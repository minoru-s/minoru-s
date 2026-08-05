#!/usr/bin/env python3
"""Refresh the public-repository activity block in the profile README."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "minoru-s"
README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- recent:start -->"
END = "<!-- recent:end -->"


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
    return (value or "Public project").replace("|", "\\|").replace("\n", " ").strip()


def render(repositories: list[dict]) -> str:
    rows = [
        "| Recently updated | What it is | Last change |",
        "|---|---|---|",
    ]

    for repo in repositories:
        updated = datetime.fromisoformat(
            repo["updated_at"].replace("Z", "+00:00")
        ).strftime("%Y-%m-%d")
        name = f"[{repo['name']}]({repo['html_url']})"
        description = clean(repo.get("description"))
        rows.append(f"| **{name}** | {description} | {updated} |")

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
