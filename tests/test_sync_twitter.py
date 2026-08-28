import importlib.util
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
