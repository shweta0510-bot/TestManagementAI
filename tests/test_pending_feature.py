import json
import tempfile
import unittest
from pathlib import Path

from zara_platform.pending_feature import run_feature_file
from zara_platform.pipeline_repository import (
    JsonZaraPipelineRepository,
    Pipeline,
    PipelineStatus,
    ZaraPipelineRepository,
)

ROOT = Path(__file__).resolve().parent.parent
FEATURE = ROOT / "features" / "pending_pipeline.feature"


class PendingFeatureTests(unittest.TestCase):
    def test_pending_pipeline_skips_end_to_end_creation(self) -> None:
        repository = ZaraPipelineRepository(
            [
                Pipeline("pipeline-pending-1", "Checkout pipeline", PipelineStatus.PENDING_SETUP),
                Pipeline("pipeline-ready-1", "Search pipeline", PipelineStatus.READY),
            ]
        )

        report = run_feature_file(FEATURE, repository)

        self.assertFalse(report.ran_end_to_end)
        statuses = {result.name: result.status for result in report.results}
        self.assertEqual(statuses["Reuse a pipeline that is already pending setup"], "passed")
        self.assertEqual(statuses["Create a pipeline when none are pending setup"], "skipped")
        self.assertEqual(len(repository.all()), 2)
        skipped = next(result for result in report.results if result.status == "skipped")
        self.assertEqual(skipped.steps_run, [])

    def test_empty_repository_runs_creation_once(self) -> None:
        repository = ZaraPipelineRepository()

        report = run_feature_file(FEATURE, repository)

        self.assertTrue(report.ran_end_to_end)
        created = repository.find_pending_setup()
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].status, PipelineStatus.PENDING_SETUP)
        statuses = {result.name: result.status for result in report.results}
        self.assertEqual(statuses["Create a pipeline when none are pending setup"], "passed")
        self.assertEqual(statuses["Reuse a pipeline that is already pending setup"], "skipped")

    def test_second_run_reuses_the_pipeline_created_by_the_first(self) -> None:
        repository = ZaraPipelineRepository()

        first = run_feature_file(FEATURE, repository)
        second = run_feature_file(FEATURE, repository)

        self.assertTrue(first.ran_end_to_end)
        self.assertFalse(second.ran_end_to_end)
        self.assertEqual(len(repository.find_pending_setup()), 1)

    def test_checked_in_repository_skips_end_to_end(self) -> None:
        repository = JsonZaraPipelineRepository(ROOT / "data" / "zara_pipelines.json")

        report = run_feature_file(FEATURE, repository)

        self.assertTrue(repository.has_pending_setup())
        self.assertFalse(report.ran_end_to_end)

    def test_json_repository_persists_a_created_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "zara_pipelines.json"
            path.write_text(json.dumps({"pipelines": []}), encoding="utf-8")
            repository = JsonZaraPipelineRepository(path)

            report = run_feature_file(FEATURE, repository)
            reloaded = JsonZaraPipelineRepository(path)

        self.assertTrue(report.ran_end_to_end)
        self.assertEqual(len(reloaded.find_pending_setup()), 1)


if __name__ == "__main__":
    unittest.main()
