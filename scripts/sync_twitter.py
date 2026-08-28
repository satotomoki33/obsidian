#!/usr/bin/env python3
"""Save recent posts from a public X profile into an Obsidian Markdown log.

The script intentionally avoids the paid X API. It uses X's official embedded
profile timeline first, then tries public Nitter instances and RSSHub as
fallbacks. Public mirrors can disappear, so the Nitter source list is
configurable with the NITTER_INSTANCES environment variable.
"""

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
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
TWITTER_EPOCH_MS = 1288834974657
SYNDICATION_URL = "https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"

DEFAULT_NITTER_INSTANCES = (
    "https://xcancel.com",
    "https://nitter.poast.org",
    "https://nitter.privacyredirect.com",
    "https://lightbrd.com",
    "https://nitter.space",
    "https://nitter.tiekoetter.com",
    "https://nitter.net",
)
DEFAULT_RSSHUB_FEEDS = (
    "https://rsshub.app/twitter/user/{username}",
)

STATUS_ID_RE = re.compile(r"(?:x|twitter)\.com/[^/\s)]+/status/(\d+)", re.I)
ANY_STATUS_RE = re.compile(
    r"https?://[^/]+/([^/#?\s]+)/status/(\d+)",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"[ \t\f\v]+")
NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class Post:
    post_id: str
    created_at: datetime
    text: str
    url: str


class SourceUnavailableError(RuntimeError):
    """Raised when every configured post source is unavailable."""


def retry_delay(headers: Any, attempt: int, max_delay: int) -> int:
    retry_after = headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        delay = int(retry_after)
    else:
        reset_at = headers.get("x-rate-limit-reset")
        if reset_at and reset_at.isdigit():
            delay = max(int(reset_at) - int(time.time()) + 2, 1)
        else:
            delay = 4 * attempt
    return min(delay, max_delay)


def request_text(url: str, attempts: int = 2, max_retry_delay: int = 20) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
            "Gecko/20100101 Firefox/128.0"
        ),
        "Accept": (
            "application/rss+xml, application/atom+xml, application/xml;q=0.9, "
            "text/xml;q=0.8, text/html;q=0.7, */*;q=0.5"
        ),
        "Accept-Language": "ja,en-US;q=0.8,en;q=0.6",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read().decode("utf-8", errors="replace")
                if not body.strip():
                    raise RuntimeError("empty response")
                return body
        except urllib.error.HTTPError as exc:
            last_error = RuntimeError(f"HTTP {exc.code} {exc.reason}")
            if attempt < attempts and exc.code in {408, 425, 429, 500, 502, 503, 504}:
                time.sleep(retry_delay(exc.headers, attempt, max_retry_delay))
            else:
                break
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(4 * attempt)

    raise RuntimeError(f"{url}: {last_error}")


def snowflake_datetime(post_id: str) -> datetime:
    timestamp_ms = (int(post_id) >> 22) + TWITTER_EPOCH_MS
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def get_path(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def recursive_tweet_candidates(value: Any) -> Iterable[dict[str, Any]]:
    """Find tweet-shaped objects if X changes the direct timeline path."""
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


def syndication_datetime(raw: str) -> datetime:
    formats = (
        "%a %b %d %H:%M:%S %z %Y",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
    )
    normalized = raw.strip().replace("Z", "+00:00")
    for date_format in formats:
        try:
            return datetime.strptime(normalized, date_format).astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(normalized).astimezone(timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Unsupported created_at value: {raw}") from exc


def tweet_screen_name(tweet: dict[str, Any]) -> str:
    possibilities = (
        get_path(tweet, "user", "screen_name"),
        get_path(tweet, "user", "legacy", "screen_name"),
        get_path(tweet, "core", "user_results", "result", "legacy", "screen_name"),
        get_path(tweet, "author", "screen_name"),
        get_path(tweet, "author", "userName"),
    )
    return next((str(item) for item in possibilities if item), "")


def normalize_syndication_tweet(
    tweet: dict[str, Any], username: str
) -> Post | None:
    legacy = tweet.get("legacy") if isinstance(tweet.get("legacy"), dict) else tweet
    author = tweet_screen_name(tweet)
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
    if not isinstance(text, str) or not text.strip() or text.lstrip().startswith("RT @"):
        return None

    post_id = tweet.get("id_str") or legacy.get("id_str") or tweet.get("id") or legacy.get("id")
    created_raw = legacy.get("created_at") or tweet.get("created_at")
    if post_id is None or not isinstance(created_raw, str):
        return None

    post_id = str(post_id)
    return Post(
        post_id=post_id,
        created_at=syndication_datetime(created_raw),
        text=html.unescape(text).replace("\r\n", "\n").replace("\r", "\n").strip(),
        url=f"https://x.com/{username}/status/{post_id}",
    )


def parse_syndication_html(document: str, username: str) -> list[Post]:
    match = NEXT_DATA_RE.search(document)
    if not match:
        raise RuntimeError("X embed response did not contain __NEXT_DATA__")
    try:
        data = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"X embed timeline JSON parse error: {exc}") from exc

    entries = get_path(data, "props", "pageProps", "timeline", "entries")
    tweets = []
    if isinstance(entries, list):
        tweets = [
            tweet
            for entry in entries
            if isinstance(entry, dict)
            and isinstance((tweet := get_path(entry, "content", "tweet")), dict)
        ]
    if not tweets:
        tweets = list(recursive_tweet_candidates(data))

    posts: dict[str, Post] = {}
    for tweet in tweets:
        try:
            post = normalize_syndication_tweet(tweet, username)
        except ValueError as exc:
            print(f"warning: skipped a post with an unknown timestamp: {exc}", file=sys.stderr)
            continue
        if post:
            posts[post.post_id] = post
    if not posts:
        raise RuntimeError("X embed timeline contained no matching posts")
    return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


def fetch_syndication_posts(username: str) -> tuple[list[Post], list[str]]:
    url = SYNDICATION_URL.format(username=username)
    try:
        # X publishes a rate-limit reset timestamp. Waiting for that reset is
        # more reliable on shared GitHub runner IPs than retrying after seconds.
        document = request_text(url, attempts=2, max_retry_delay=300)
        posts = parse_syndication_html(document, username)
        print(f"取得元: X公式埋め込みタイムライン ({len(posts)}件)")
        return posts, []
    except RuntimeError as exc:
        return [], [f"{url}: {exc}"]


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in list(element):
        if local_name(child.tag) in wanted:
            return "".join(child.itertext()).strip()
    return ""


def entry_link(element: ET.Element) -> str:
    for child in list(element):
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href", "").strip()
        if href:
            rel = child.attrib.get("rel", "alternate")
            if rel in {"alternate", ""}:
                return href
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def parse_datetime(raw: str, post_id: str) -> datetime:
    if raw.strip():
        try:
            value = parsedate_to_datetime(raw.strip())
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            try:
                value = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                return value.astimezone(timezone.utc)
            except ValueError:
                pass
    return snowflake_datetime(post_id)


class FragmentTextParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "li", "blockquote", "br", "hr"}
    SKIP_TAGS = {"script", "style", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if not self.skip_depth and tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(raw: str) -> str:
    parser = FragmentTextParser()
    try:
        parser.feed(raw)
        text = "".join(parser.parts)
    except Exception:
        text = TAG_RE.sub(" ", raw)
    text = html.unescape(text).replace("\r", "")
    lines = [SPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"(?:pic\.twitter\.com|https?://t\.co)/\S+", "", text)
    return text.strip()


def status_from_url(url: str) -> tuple[str, str] | None:
    match = ANY_STATUS_RE.search(html.unescape(url))
    if not match:
        return None
    return match.group(1), match.group(2)


def parse_feed(document: str, username: str) -> list[Post]:
    try:
        root = ET.fromstring(document.lstrip("\ufeff \t\r\n"))
    except ET.ParseError as exc:
        raise RuntimeError(f"feed XML parse error: {exc}") from exc

    entries = [element for element in root.iter() if local_name(element.tag) in {"item", "entry"}]
    if not entries:
        raise RuntimeError("feed contained no entries")

    posts: dict[str, Post] = {}
    for entry in entries:
        title = child_text(entry, "title")
        if title.casefold().startswith("rt by @"):
            continue

        link = entry_link(entry)
        guid = child_text(entry, "guid", "id")
        status = status_from_url(link) or status_from_url(guid)
        if not status:
            continue
        owner, post_id = status
        if owner.casefold() != username.casefold():
            continue

        description = child_text(entry, "description", "content", "summary")
        text = html_to_text(description) or html_to_text(title)
        if not text:
            text = "（画像・動画のみの投稿）"

        created_raw = child_text(entry, "pubdate", "published", "updated")
        posts[post_id] = Post(
            post_id=post_id,
            created_at=parse_datetime(created_raw, post_id),
            text=text,
            url=f"https://x.com/{username}/status/{post_id}",
        )

    if not posts:
        raise RuntimeError("feed entries were present, but no matching posts were parsed")
    return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


class NitterTimelineParser(HTMLParser):
    def __init__(self, username: str) -> None:
        super().__init__(convert_charrefs=True)
        self.username = username
        self.posts: dict[str, Post] = {}
        self.depth = 0
        self.current: dict[str, object] | None = None
        self.capture_depth: int | None = None

    @staticmethod
    def attr_map(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self.attr_map(attrs)
        classes = set(values.get("class", "").split())

        if tag == "div" and "timeline-item" in classes and self.current is None:
            self.current = {"owner": "", "post_id": "", "parts": [], "retweet": False}
            self.depth = 1
            return

        if self.current is None:
            return

        if tag == "div":
            self.depth += 1
            if "retweet-header" in classes:
                self.current["retweet"] = True
            if "tweet-content" in classes and self.capture_depth is None:
                self.capture_depth = self.depth

        if tag == "a" and "tweet-link" in classes and not self.current["post_id"]:
            href = values.get("href", "")
            status = status_from_url(f"https://nitter.invalid{href}" if href.startswith("/") else href)
            if status:
                self.current["owner"], self.current["post_id"] = status

        if tag == "br" and self.capture_depth is not None:
            parts = self.current["parts"]
            assert isinstance(parts, list)
            parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.current is not None and self.capture_depth is not None:
            parts = self.current["parts"]
            assert isinstance(parts, list)
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current is None or tag != "div":
            return

        if self.capture_depth == self.depth:
            self.capture_depth = None

        self.depth -= 1
        if self.depth != 0:
            return

        owner = str(self.current["owner"])
        post_id = str(self.current["post_id"])
        retweet = bool(self.current["retweet"])
        parts = self.current["parts"]
        assert isinstance(parts, list)
        text = html_to_text("".join(str(part) for part in parts))

        if not retweet and owner.casefold() == self.username.casefold() and post_id:
            self.posts[post_id] = Post(
                post_id=post_id,
                created_at=snowflake_datetime(post_id),
                text=text or "（画像・動画のみの投稿）",
                url=f"https://x.com/{self.username}/status/{post_id}",
            )

        self.current = None
        self.capture_depth = None


def parse_nitter_html(document: str, username: str) -> list[Post]:
    parser = NitterTimelineParser(username)
    parser.feed(document)
    if not parser.posts:
        raise RuntimeError("Nitter HTML contained no matching posts")
    return sorted(parser.posts.values(), key=lambda post: (post.created_at, int(post.post_id)))


def configured_instances() -> tuple[str, ...]:
    raw = os.environ.get("NITTER_INSTANCES", "").strip()
    if not raw:
        return DEFAULT_NITTER_INSTANCES
    values = tuple(value.strip().rstrip("/") for value in raw.split(",") if value.strip())
    return values or DEFAULT_NITTER_INSTANCES


def fetch_nitter_posts(username: str) -> tuple[list[Post], list[str]]:
    errors: list[str] = []
    instances = configured_instances()

    for index, base in enumerate(instances):
        base = base.rstrip("/")
        posts: dict[str, Post] = {}
        base_succeeded = False

        for suffix in ("", "/with_replies"):
            rss_url = f"{base}/{username}{suffix}/rss"
            try:
                for post in parse_feed(request_text(rss_url), username):
                    posts[post.post_id] = post
                base_succeeded = True
                continue
            except RuntimeError as exc:
                errors.append(f"{rss_url}: {exc}")

            html_url = f"{base}/{username}{suffix}"
            try:
                for post in parse_nitter_html(request_text(html_url), username):
                    posts[post.post_id] = post
                base_succeeded = True
            except RuntimeError as exc:
                errors.append(f"{html_url}: {exc}")

        if base_succeeded and posts:
            print(f"取得元: {base} ({len(posts)}件)")
            return sorted(posts.values(), key=lambda post: (post.created_at, int(post.post_id))), errors

        if index + 1 < len(instances):
            time.sleep(1)

    return [], errors


def fetch_rsshub_posts(username: str) -> tuple[list[Post], list[str]]:
    errors: list[str] = []
    templates_raw = os.environ.get("RSSHUB_FEEDS", "").strip()
    templates = (
        tuple(value.strip() for value in templates_raw.split(",") if value.strip())
        if templates_raw
        else DEFAULT_RSSHUB_FEEDS
    )

    for template in templates:
        url = template.format(username=username)
        try:
            posts = parse_feed(request_text(url), username)
            print(f"取得元: {url} ({len(posts)}件)")
            return posts, errors
        except RuntimeError as exc:
            errors.append(f"{url}: {exc}")
    return [], errors


def fetch_posts(username: str) -> list[Post]:
    posts, syndication_errors = fetch_syndication_posts(username)
    if posts:
        return posts

    posts, nitter_errors = fetch_nitter_posts(username)
    if posts:
        return posts

    posts, rsshub_errors = fetch_rsshub_posts(username)
    if posts:
        return posts

    errors = nitter_errors + rsshub_errors
    concise_parts = syndication_errors + errors[-7:]
    concise = "; ".join(concise_parts)
    raise SourceUnavailableError(
        f"すべての取得元から投稿を取得できませんでした: {concise}"
    )


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


def report_source_outage(exc: SourceUnavailableError) -> None:
    detail = str(exc).replace("\r", " ").replace("\n", " ")
    print(f"::warning title=Xログ同期をスキップ::{detail}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(
                "### ⚠️ Xログ同期をスキップ\n\n"
                "設定された取得元がすべて利用できなかったため、"
                "Twitterログ.md は変更していません。\n\n"
                f"`{detail.replace('`', "'")}`\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.environ.get("X_USERNAME", "sato_mega33"))
    parser.add_argument("--log", default=os.environ.get("X_LOG_PATH", "Twitterログ.md"))
    parser.add_argument(
        "--start-at",
        default=os.environ.get("START_AT", "2026-07-28T21:43:00+09:00"),
    )
    parser.add_argument(
        "--allow-source-outage",
        action="store_true",
        help="取得元が全滅した場合に警告を出し、ログを変更せず正常終了する",
    )
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise RuntimeError(f"保存先が存在しません: {log_path}")

    try:
        posts = fetch_posts(args.username)
    except SourceUnavailableError as exc:
        if not args.allow_source_outage:
            raise
        report_source_outage(exc)
        return 0
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
