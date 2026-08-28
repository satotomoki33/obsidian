import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "sync_twitter.py"
SPEC = importlib.util.spec_from_file_location("sync_twitter", SCRIPT_PATH)
assert SPEC and SPEC.loader
sync_twitter = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync_twitter
SPEC.loader.exec_module(sync_twitter)


def embedded_timeline(*tweets: dict) -> str:
    entries = [{"content": {"tweet": tweet}} for tweet in tweets]
    data = {"props": {"pageProps": {"timeline": {"entries": entries}}}}
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'


class SyndicationTests(unittest.TestCase):
    def test_parses_own_posts_and_excludes_retweets(self) -> None:
        own_post = {
            "id_str": "2089709440719376598",
            "created_at": "Tue Aug 18 13:42:00 +0000 2026",
            "text": "新しい投稿 &amp; テスト",
            "user": {"screen_name": "sato_mega33"},
        }
        retweet = {
            "id_str": "2089709440719376599",
            "created_at": "Tue Aug 18 13:43:00 +0000 2026",
            "text": "RT @someone: repost",
            "user": {"screen_name": "sato_mega33"},
            "retweeted_status": {},
        }

        posts = sync_twitter.parse_syndication_html(
            embedded_timeline(own_post, retweet), "sato_mega33"
        )

        self.assertEqual([post.post_id for post in posts], ["2089709440719376598"])
        self.assertEqual(posts[0].text, "新しい投稿 & テスト")

    def test_official_embed_is_preferred(self) -> None:
        post = sync_twitter.Post(
            post_id="2089709440719376598",
            created_at=sync_twitter.snowflake_datetime("2089709440719376598"),
            text="test",
            url="https://x.com/sato_mega33/status/2089709440719376598",
        )
        with mock.patch.object(
            sync_twitter, "fetch_syndication_posts", return_value=([post], [])
        ), mock.patch.object(sync_twitter, "fetch_nitter_posts") as nitter:
            posts = sync_twitter.fetch_posts("sato_mega33")

        self.assertEqual(posts, [post])
        nitter.assert_not_called()

    def test_public_mirror_is_used_when_embed_fails(self) -> None:
        post = sync_twitter.Post(
            post_id="2089709440719376598",
            created_at=sync_twitter.snowflake_datetime("2089709440719376598"),
            text="test",
            url="https://x.com/sato_mega33/status/2089709440719376598",
        )
        with mock.patch.object(
            sync_twitter,
            "fetch_syndication_posts",
            return_value=([], ["HTTP 429"]),
        ), mock.patch.object(
            sync_twitter, "fetch_nitter_posts", return_value=([post], [])
        ):
            posts = sync_twitter.fetch_posts("sato_mega33")

        self.assertEqual(posts, [post])


class MainTests(unittest.TestCase):
    def run_main(self, *extra_args: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "Twitterログ.md"
            summary_path = Path(directory) / "summary.md"
            log_path.write_text("# Xログ\n", encoding="utf-8")
            argv = ["sync_twitter.py", "--log", str(log_path), *extra_args]
            with mock.patch.object(sys, "argv", argv), mock.patch.dict(
                os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}
            ):
                result = sync_twitter.main()
            return result, summary_path.read_text(encoding="utf-8")

    def test_source_outage_can_be_downgraded_to_warning(self) -> None:
        error = sync_twitter.SourceUnavailableError("all sources unavailable")
        with mock.patch.object(sync_twitter, "fetch_posts", side_effect=error):
            result, summary = self.run_main("--allow-source-outage")

        self.assertEqual(result, 0)
        self.assertIn("Xログ同期をスキップ", summary)
        self.assertIn("all sources unavailable", summary)

    def test_source_outage_is_fatal_by_default(self) -> None:
        error = sync_twitter.SourceUnavailableError("all sources unavailable")
        with mock.patch.object(sync_twitter, "fetch_posts", side_effect=error):
            with self.assertRaises(sync_twitter.SourceUnavailableError):
                self.run_main()

    def test_unexpected_errors_are_not_downgraded(self) -> None:
        with mock.patch.object(
            sync_twitter, "fetch_posts", side_effect=ValueError("parser bug")
        ):
            with self.assertRaisesRegex(ValueError, "parser bug"):
                self.run_main("--allow-source-outage")


if __name__ == "__main__":
    unittest.main()
