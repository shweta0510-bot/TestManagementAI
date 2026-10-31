"""Run the pending-pipeline feature against the Zara pipeline repository."""

from __future__ import annotations

import argparse
from pathlib import Path

from zara_platform.pending_feature import run_feature_file
from zara_platform.pipeline_repository import JsonZaraPipelineRepository

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FEATURE = ROOT / "features" / "pending_pipeline.feature"
DEFAULT_REPOSITORY = ROOT / "data" / "zara_pipelines.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Zara pending-pipeline feature. End-to-end creation is skipped while a pipeline is Pending Setup."
    )
    parser.add_argument("--feature", type=Path, default=DEFAULT_FEATURE)
    parser.add_argument("--repository", type=Path, default=DEFAULT_REPOSITORY)
    args = parser.parse_args()

    repository = JsonZaraPipelineRepository(args.repository)
    report = run_feature_file(args.feature, repository)
    print(report.summary())


if __name__ == "__main__":
    main()
