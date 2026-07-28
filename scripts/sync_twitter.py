#!/usr/bin/env python3
"""Append new posts from a public X profile to an Obsidian Markdown log."""

from __future__ import annotations

import argparse
import html
import json
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
from typing import Any, Iterable
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)
STATUS_ID_RE = re.compile(r"(?:x|twitter)\.com/[^/\s]+/status/(\d+)")


@dataclass(frozen=True)
class Post:
    post_id: str
    created_at: datetime
    text: str
    url: str


def fetch_timeline_html(username: str, cookie: str = "", attempts: int = 3) -> str:
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/138.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
        "Cache-Control": "no-cache",
    }
    if cookie.strip():
        headers["Cookie"] = cookie.strip()

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status != 200:
                    raise RuntimeError(f"X syndication endpoint returned HTTP {response.status}")
                if not body.strip():
                    raise RuntimeError("X syndication endpoint returned an empty response")
                return body
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))

    raise RuntimeError(f"Failed to fetch X timeline after {attempts} attempts: {last_error}")


def extract_next_data(document: str) -> dict[str, Any]:
    match = NEXT_DATA_RE.search(document)
    if not match:
        raise RuntimeError("X response did not contain the __NEXT_DATA__ timeline payload")
    try:
        return json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Could not decode X timeline JSON: {exc}") from exc


def get_path(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def direct_timeline_tweets(data: dict[str, Any]) -> list[dict[str, Any]]:
    entries = get_path(data, "props", "pageProps", "timeline", "entries")
    if not isinstance(entries, list):
        return []

    tweets: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        tweet = get_path(entry, "content", "tweet")
        if isinstance(tweet, dict):
            tweets.append(tweet)
    return tweets


def recursive_tweet_candidates(value: Any) -> Iterable[dict[str, Any]]:
    """Schema-change fallback; direct timeline entries are preferred."""
    if isinstance(value, dict):
        has_id = isinstance(value.get("id_str") or value.get("id"), (str, int))
        legacy = value.get("legacy") if isinstance(value.get("legacy"), dict) else value
        has_text = isinstance(legacy.get("full_text") or legacy.get("text"), str)
        has_time = isinstance(legacy.get("created_at") or value.get("created_at"), str)
        if has_id and has_text and has_time:
            yield value
        for child in value.values():
            yield from recursive_tweet_candidates(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_tweet_candidates(child)


def parse_datetime(raw: str) -> datetime:
    formats = (
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
    )
    normalized = raw.strip().replace("Z", "+00:00")
    for fmt in formats:
        try:
            return datetime.strptime(normalized, fmt).astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(normalized).astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Unsupported created_at value: {raw}") from exc


def screen_name(tweet: dict[str, Any]) -> str:
    possibilities = (
        get_path(tweet, "user", "screen_name"),
        get_path(tweet, "user", "legacy", "screen_name"),
        get_path(tweet, "core", "user_results", "result", "legacy", "screen_name"),
        get_path(tweet, "author", "screen_name"),
        get_path(tweet, "author", "userName"),
    )
    return next((str(item) for item in possibilities if item), "")


def normalize_tweet(tweet: dict[str, Any], username: str) -> Post | None:
    legacy = tweet.get("legacy") if isinstance(tweet.get("legacy"), dict) else tweet
    author = screen_name(tweet)
    if author and author.casefold() != username.casefold():
        return None

    if "retweeted_status" in tweet or "retweeted_status" in legacy:
        return None

    text = (
        get_path(tweet, "note_tweet", "note_tweet_results", "result", "text")
        or legacy.get("full_text")
        or legacy.get("text")
        or tweet.get("full_text")
        or tweet.get("text")
    )
    if not isinstance(text, str) or not text.strip():
        return None
    if text.lstrip().startswith("RT @"):
        return None

    post_id = tweet.get("id_str") or legacy.get("id_str") or tweet.get("id") or legacy.get("id")
    created_raw = legacy.get("created_at") or tweet.get("created_at")
    if post_id is None or not isinstance(created_raw, str):
        return None

    created_at = parse_datetime(created_raw)
    post_id = str(post_id)
    clean_text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n").strip()
    return Post(
        post_id=post_id,
        created_at=created_at,
        text=clean_text,
        url=f"https://x.com/{username}/status/{post_id}",
    )


def parse_posts(data: dict[str, Any], username: str) -> list[Post]:
    raw_tweets = direct_timeline_tweets(data)
    if not raw_tweets:
        raw_tweets = list(recursive_tweet_candidates(data))

    posts: dict[str, Post] = {}
    for raw in raw_tweets:
        try:
            post = normalize_tweet(raw, username)
        except ValueError as exc:
            print(f"warning: skipped a post with an unknown timestamp: {exc}", file=sys.stderr)
            continue
        if post:
            posts[post.post_id] = post
    return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


def existing_ids(markdown: str) -> set[str]:
    return set(STATUS_ID_RE.findall(markdown))


def render_post(post: Post) -> str:
    local = post.created_at.astimezone(JST)
    return f"### {local:%H:%M}\n\n{post.text}\n\n[元の投稿]({post.url})"


def insert_date_section(markdown: str, date_label: str, rendered_posts: list[str]) -> str:
    entries = "\n\n".join(rendered_posts).strip()
    heading_pattern = re.compile(rf"^## {re.escape(date_label)}\s*$", re.MULTILINE)
    match = heading_pattern.search(markdown)

    if not match:
        prefix = markdown.rstrip()
        block = f"## {date_label}\n\n{entries}\n"
        return f"{prefix}\n\n{block}" if prefix else block

    following_heading = re.compile(r"^##\s+", re.MULTILINE).search(markdown, match.end())
    insert_at = following_heading.start() if following_heading else len(markdown)
    before = markdown[:insert_at].rstrip()
    after = markdown[insert_at:].lstrip("\n")
    combined = f"{before}\n\n{entries}\n"
    if after:
        combined += f"\n{after}"
    return combined


def update_markdown(markdown: str, posts: list[Post]) -> str:
    grouped: dict[str, list[Post]] = defaultdict(list)
    for post in posts:
        grouped[post.created_at.astimezone(JST).strftime("%Y-%m-%d")].append(post)

    updated = markdown
    for date_label in sorted(grouped):
        rendered = [render_post(post) for post in sorted(grouped[date_label], key=lambda p: p.created_at)]
        updated = insert_date_section(updated, date_label, rendered)
    return updated


def parse_start_at(raw: str) -> datetime:
    normalized = raw.strip().replace("Z", "+00:00")
    value = datetime.fromisoformat(normalized)
    if value.tzinfo is None:
        raise ValueError("START_AT must include a timezone offset")
    return value.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.environ.get("X_USERNAME", "sato_mega33"))
    parser.add_argument("--log", default=os.environ.get("X_LOG_PATH", "Twitterログ.md"))
    parser.add_argument(
        "--start-at",
        default=os.environ.get("START_AT", "2026-07-28T21:43:00+09:00"),
    )
    parser.add_argument("--input-html", help="Read saved syndication HTML instead of making a network request")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise RuntimeError(f"Log file does not exist: {log_path}")

    document = (
        Path(args.input_html).read_text(encoding="utf-8")
        if args.input_html
        else fetch_timeline_html(args.username, os.environ.get("X_COOKIE", ""))
    )
    data = extract_next_data(document)
    posts = parse_posts(data, args.username)
    if not posts:
        raise RuntimeError("X timeline was fetched, but no posts could be parsed")

    start_at = parse_start_at(args.start_at)
    original = log_path.read_text(encoding="utf-8")
    known_ids = existing_ids(original)
    new_posts = [
        post for post in posts
        if post.created_at >= start_at and post.post_id not in known_ids
    ]

    if not new_posts:
        print("No new posts.")
        return 0

    updated = update_markdown(original, new_posts)
    log_path.write_text(updated, encoding="utf-8")
    print(f"Added {len(new_posts)} post(s) to {log_path}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
