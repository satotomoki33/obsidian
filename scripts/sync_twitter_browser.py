#!/usr/bin/env python3
"""Sync an X profile to Obsidian through a dedicated local Chrome profile."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


OWN_STATUS_RE_TEMPLATE = r"^/{username}/status/(?P<id>\d+)$"


class LoginRequiredError(RuntimeError):
    pass


def load_log_modules(script_dir: Path):
    sys.path.insert(0, str(script_dir))
    import sort_twitter_log  # type: ignore
    import sync_twitter  # type: ignore

    return sync_twitter, sort_twitter_log


def own_status_id(href: str | None, username: str) -> str | None:
    if not href:
        return None
    match = re.match(
        OWN_STATUS_RE_TEMPLATE.format(username=re.escape(username)), href, re.I
    )
    return match.group("id") if match else None


def article_post(article, username: str, post_type):
    post_id = None
    for link in article.locator('a[href*="/status/"]').all():
        post_id = own_status_id(link.get_attribute("href"), username)
        if post_id:
            break
    if not post_id:
        return None

    time_locator = article.locator("time").first
    created_raw = time_locator.get_attribute("datetime")
    if not created_raw:
        return None
    created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    text_locator = article.locator('[data-testid="tweetText"]').first
    text = text_locator.inner_text().strip() if text_locator.count() else ""
    return post_type(
        post_id=post_id,
        created_at=created_at.astimezone(timezone.utc),
        text=text or "（画像・動画のみの投稿）",
        url=f"https://x.com/{username}/status/{post_id}",
    )


def collect_timeline(page, url: str, username: str, known_ids: set[str], post_type):
    page.goto(url, wait_until="domcontentloaded", timeout=45_000)
    page.wait_for_timeout(4_000)

    posts = {}
    reached_known_post = False
    for _ in range(30):
        articles = page.locator("article")
        for index in range(articles.count()):
            article = articles.nth(index)
            post = article_post(article, username, post_type)
            if not post:
                continue
            posts[post.post_id] = post
            is_pinned = "固定" in article.inner_text().splitlines()[:2]
            if post.post_id in known_ids and not is_pinned:
                reached_known_post = True

        if reached_known_post:
            break
        page.mouse.wheel(0, 1_400)
        page.wait_for_timeout(1_200)

    if not posts:
        login_visible = page.get_by_role("link", name="ログイン").count() > 0
        if login_visible or "/login" in page.url:
            raise LoginRequiredError(
                "Xへのログインが必要です。--login を付けて初期設定してください"
            )
        raise RuntimeError(f"タイムラインを読み取れませんでした: {url}")
    return list(posts.values())


def update_log(log_path: Path, posts: list, sync_twitter, sort_twitter_log) -> int:
    original = log_path.read_text(encoding="utf-8")
    known_ids = sync_twitter.existing_ids(original)
    new_posts = [post for post in posts if post.post_id not in known_ids]
    if not new_posts:
        print(f"取得成功: {len(posts)}件を確認。新規投稿はありません。")
        return 0

    updated = sync_twitter.update_markdown(original, new_posts)
    updated = sort_twitter_log.sort_log(updated)
    log_path.write_text(updated, encoding="utf-8")
    print(f"取得成功: {len(posts)}件を確認し、{len(new_posts)}件を追記しました。")
    return len(new_posts)


def login(profile: Path, chrome: str, username: str) -> int:
    from playwright.sync_api import sync_playwright

    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), executable_path=chrome, headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(f"https://x.com/{username}", wait_until="domcontentloaded")
        input(
            "専用ChromeでXにログインし、プロフィールが表示されたら"
            "このターミナルでEnterを押してください: "
        )
        context.close()
    print("同期専用のXログインを保存しました。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--username", default="sato_mega33")
    parser.add_argument("--log", default="Twitterログ.md")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--chrome", default="/usr/bin/google-chrome")
    parser.add_argument("--login", action="store_true")
    args = parser.parse_args()

    if args.login:
        return login(args.profile, args.chrome, args.username)

    from playwright.sync_api import sync_playwright

    script_dir = Path(__file__).resolve().parent
    sync_twitter, sort_twitter_log = load_log_modules(script_dir)
    log_path = args.vault / args.log
    if not log_path.exists():
        raise RuntimeError(f"保存先が存在しません: {log_path}")

    original = log_path.read_text(encoding="utf-8")
    known_ids = sync_twitter.existing_ids(original)
    args.profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(args.profile),
            executable_path=args.chrome,
            headless=True,
            args=["--disable-dev-shm-usage"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        posts = {}
        for suffix in ("", "/with_replies"):
            for post in collect_timeline(
                page,
                f"https://x.com/{args.username}{suffix}",
                args.username,
                known_ids,
                sync_twitter.Post,
            ):
                posts[post.post_id] = post
        context.close()

    return 0 if update_log(log_path, list(posts.values()), sync_twitter, sort_twitter_log) >= 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
