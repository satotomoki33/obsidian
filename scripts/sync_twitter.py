#!/usr/bin/env python3
"""Save recent posts from a public X profile into an Obsidian Markdown log."""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
TWITTER_EPOCH_MS = 1288834974657

STATUS_ID_RE = re.compile(r"(?:x|twitter)\.com/[^/\s)]+/status/(\d+)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*]\([^)]*\)")
EMPTY_LINK_RE = re.compile(r"\[\]\([^)]*\)")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)]\((https?://[^)]*)\)")


@dataclass(frozen=True)
class Post:
    post_id: str
    created_at: datetime
    text: str
    url: str


def request_text(url: str, attempts: int = 3) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        ),
        "Accept": "text/plain",
        "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
        "X-No-Cache": "true",
        "X-Respond-With": "markdown",
    }
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response:
                body = response.read().decode("utf-8", errors="replace")
                if not body.strip():
                    raise RuntimeError("empty response")
                return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if attempt < attempts:
                retry_after = exc.headers.get("Retry-After")
                delay = (
                    int(retry_after)
                    if retry_after and retry_after.isdigit()
                    else 5 * attempt
                )
                time.sleep(min(delay, 30))
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(5 * attempt)

    raise RuntimeError(f"取得に失敗しました: {url}: {last_error}")


def fetch_profile(username: str, suffix: str = "") -> str:
    target = f"https://x.com/{username}{suffix}"
    return request_text(f"https://r.jina.ai/{target}")


def snowflake_datetime(post_id: str) -> datetime:
    """Restore the post creation time from its X Snowflake ID."""
    timestamp_ms = (int(post_id) >> 22) + TWITTER_EPOCH_MS
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def clean_post_text(raw: str, username: str, post_id: str) -> str:
    text = html.unescape(raw)

    # Remove the engagement-count tail belonging to this post.
    quotes_link = re.search(
        rf"\[\]\(https://x\.com/{re.escape(username)}/status/{post_id}/quotes\)",
        text,
        flags=re.IGNORECASE,
    )
    if quotes_link:
        text = text[: quotes_link.start()]

    text = MARKDOWN_IMAGE_RE.sub("", text)
    text = EMPTY_LINK_RE.sub("", text)
    text = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    text = re.sub(r"\b(?:Video|Image)\s+\d+\b", "", text)
    text = text.replace("Show more", "")
    text = re.sub(r"\s+", " ", text).strip(" -*\n\t")

    return text or "（画像・動画のみの投稿）"


def parse_profile(markdown: str, username: str) -> list[Post]:
    own_status_link = re.compile(
        rf"\[[^\]]*]\(https://x\.com/{re.escape(username)}/status/(\d+)\)",
        flags=re.IGNORECASE,
    )
    posts: dict[str, Post] = {}

    # Jina Reader renders each timeline item as a Markdown bullet.
    for block in re.split(r"(?m)^\*\s+", markdown):
        match = own_status_link.search(block)
        if not match:
            # Pure reposts use the original author's status URL, so they are
            # naturally excluded here.
            continue

        post_id = match.group(1)
        posts[post_id] = Post(
            post_id=post_id,
            created_at=snowflake_datetime(post_id),
            text=clean_post_text(block[match.end() :], username, post_id),
            url=f"https://x.com/{username}/status/{post_id}",
        )

    return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


def fetch_posts(username: str) -> list[Post]:
    posts: dict[str, Post] = {}
    errors: list[str] = []

    # These views can expose different recent items. Combining them captures
    # normal posts, replies and quote posts, while IDs remove duplicates.
    for suffix in ("", "/with_replies"):
        try:
            for post in parse_profile(fetch_profile(username, suffix), username):
                posts[post.post_id] = post
        except RuntimeError as exc:
            errors.append(str(exc))

    if not posts:
        detail = "; ".join(errors) if errors else "投稿を解析できませんでした"
        raise RuntimeError(f"Jina Readerから投稿を取得できませんでした: {detail}")

    return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


def existing_ids(markdown: str) -> set[str]:
    return set(STATUS_ID_RE.findall(markdown))


def render_post(post: Post) -> str:
    local = post.created_at.astimezone(JST)
    return f"### {local:%H:%M}\n\n{post.text}\n\n[元の投稿]({post.url})"


def insert_date_section(markdown: str, date_label: str, entries: list[str]) -> str:
    rendered = "\n\n".join(entries).strip()
    heading = re.compile(rf"^## {re.escape(date_label)}\s*$", re.MULTILINE)
    match = heading.search(markdown)

    if not match:
        prefix = markdown.rstrip()
        block = f"## {date_label}\n\n{rendered}\n"
        return f"{prefix}\n\n{block}" if prefix else block

    next_heading = re.compile(r"^##\s+", re.MULTILINE).search(markdown, match.end())
    insert_at = next_heading.start() if next_heading else len(markdown)
    before = markdown[:insert_at].rstrip()
    after = markdown[insert_at:].lstrip("\n")
    result = f"{before}\n\n{rendered}\n"
    return f"{result}\n{after}" if after else result


def update_markdown(markdown: str, posts: list[Post]) -> str:
    grouped: dict[str, list[Post]] = defaultdict(list)
    for post in posts:
        date_label = post.created_at.astimezone(JST).strftime("%Y-%m-%d")
        grouped[date_label].append(post)

    updated = markdown
    for date_label in sorted(grouped):
        entries = [
            render_post(post)
            for post in sorted(grouped[date_label], key=lambda item: item.created_at)
        ]
        updated = insert_date_section(updated, date_label, entries)
    return updated


def parse_start_at(raw: str) -> datetime:
    value = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("START_ATにはタイムゾーンが必要です")
    return value.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.environ.get("X_USERNAME", "sato_mega33"))
    parser.add_argument("--log", default=os.environ.get("X_LOG_PATH", "Twitterログ.md"))
    parser.add_argument(
        "--start-at",
        default=os.environ.get("START_AT", "2026-07-28T21:43:00+09:00"),
    )
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise RuntimeError(f"保存先が存在しません: {log_path}")

    posts = fetch_posts(args.username)
    start_at = parse_start_at(args.start_at)
    original = log_path.read_text(encoding="utf-8")
    known_ids = existing_ids(original)

    new_posts = [
        post
        for post in posts
        if post.created_at >= start_at and post.post_id not in known_ids
    ]
    if not new_posts:
        print(f"取得成功: {len(posts)}件を確認。新規投稿はありません。")
        return 0

    log_path.write_text(update_markdown(original, new_posts), encoding="utf-8")
    print(f"取得成功: {len(posts)}件を確認し、{len(new_posts)}件を追記しました。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
