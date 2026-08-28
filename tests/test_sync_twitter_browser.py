import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "sync_twitter_browser.py"
SPEC = importlib.util.spec_from_file_location("sync_twitter_browser", SCRIPT_PATH)
assert SPEC and SPEC.loader
sync_browser = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sync_browser
SPEC.loader.exec_module(sync_browser)


class StatusIdTests(unittest.TestCase):
    def test_accepts_only_the_post_permalink_for_the_target_user(self) -> None:
        self.assertEqual(
            sync_browser.own_status_id(
                "/sato_mega33/status/2092765914110517399", "sato_mega33"
            ),
            "2092765914110517399",
        )

    def test_rejects_analytics_media_and_other_users(self) -> None:
        self.assertIsNone(
            sync_browser.own_status_id(
                "/sato_mega33/status/2092765914110517399/analytics", "sato_mega33"
            )
        )
        self.assertIsNone(
            sync_browser.own_status_id(
                "/someone/status/2092765914110517399", "sato_mega33"
            )
        )


if __name__ == "__main__":
    unittest.main()
