#!/usr/bin/env python3
"""Sort Twitterログ.md in reverse chronological order.

Date sections are ordered newest first, and posts inside each date section are
also ordered newest first. Text outside dated sections is preserved at the top.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

DATE_HEADING_RE = re.compile(r"(?m)^## (?P<date>\d{4}-\d{2}-\d{2})\s*$")
POST_HEADING_RE = re.compile(r"(?m)^### (?P<time>\d{2}:\d{2})\s*$")


@dataclass(frozen=True)
class DateSection:
    date: str
    body: str


def sort_posts(body: str) -> str:
    matches = list(POST_HEADING_RE.finditer(body))
    if not matches:
        return body.strip()

    prefix = body[: matches[0].start()].strip()
    posts: list[tuple[str, str]] = []

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        posts.append((match.group("time"), body[match.start() : end].strip()))

    posts.sort(key=lambda item: item[0], reverse=True)
    parts = [prefix] if prefix else []
    parts.extend(post for _, post in posts)
    return "\n\n".join(parts)


def sort_log(markdown: str) -> str:
    matches = list(DATE_HEADING_RE.finditer(markdown))
    if not matches:
        return markdown

    preamble = markdown[: matches[0].start()].strip()
    sections: list[DateSection] = []

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[match.end() : end].strip()
        sections.append(DateSection(match.group("date"), sort_posts(body)))

    sections.sort(key=lambda section: section.date, reverse=True)

    rendered_sections = [
        f"## {section.date}\n\n{section.body}" if section.body else f"## {section.date}"
        for section in sections
    ]
    parts = [preamble] if preamble else []
    parts.extend(rendered_sections)
    return "\n\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="Twitterログ.md")
    args = parser.parse_args()

    path = Path(args.log)
    if not path.exists():
        raise RuntimeError(f"保存先が存在しません: {path}")

    original = path.read_text(encoding="utf-8")
    sorted_markdown = sort_log(original)

    if sorted_markdown == original:
        print("Twitterログは既に新しい順です。")
        return 0

    path.write_text(sorted_markdown, encoding="utf-8")
    print("Twitterログを日付・時刻ともに新しい順へ並べ替えました。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
