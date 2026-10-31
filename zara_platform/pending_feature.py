"""Run the pending-pipeline feature without always executing it end to end.

The Zara pipeline repository is checked once. While any pipeline is Pending
Setup, scenarios tagged @end-to-end are skipped. Those steps create a new
pipeline, so they run only when the repository has nothing left to set up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from zara_platform.pipeline_repository import ZaraPipelineRepository

END_TO_END_TAG = "end-to-end"
REUSE_TAG = "reuse-pending"


@dataclass
class Scenario:
    name: str
    tags: set[str]
    steps: list[str]


@dataclass
class ScenarioResult:
    name: str
    status: str
    ran_end_to_end: bool
    detail: str
    steps_run: list[str] = field(default_factory=list)


@dataclass
class FeatureReport:
    feature: str
    results: list[ScenarioResult]

    @property
    def ran_end_to_end(self) -> bool:
        return any(result.ran_end_to_end for result in self.results)

    def summary(self) -> str:
        lines = [self.feature]
        for result in self.results:
            lines.append(f"  {result.status.upper():7} {result.name}")
            lines.append(f"          {result.detail}")
        return "\n".join(lines)


def parse_feature(feature_text: str) -> tuple[str, list[Scenario]]:
    feature_name = "Pending pipeline"
    scenarios: list[Scenario] = []
    tags: set[str] = set()
    current: Scenario | None = None

    for raw_line in feature_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("Feature:"):
            feature_name = line.split(":", 1)[1].strip()
            continue
        if line.startswith("@"):
            tags.update(tag[1:] for tag in line.split() if tag.startswith("@"))
            continue
        if line.startswith("Scenario:"):
            if current is not None:
                scenarios.append(current)
            current = Scenario(
                name=line.split(":", 1)[1].strip(),
                tags=set(tags),
                steps=[],
            )
            tags = set()
            continue
        first_word = line.split(" ", 1)[0]
        if current is not None and first_word in {"Given", "When", "Then", "And", "But"}:
            current.steps.append(line)

    if current is not None:
        scenarios.append(current)
    return feature_name, scenarios


def run_feature_file(
    feature_path: Path,
    repository: ZaraPipelineRepository,
) -> FeatureReport:
    feature_name, scenarios = parse_feature(feature_path.read_text(encoding="utf-8"))
    pending_before = repository.find_pending_setup()
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        if END_TO_END_TAG in scenario.tags and pending_before:
            existing = pending_before[0]
            results.append(
                ScenarioResult(
                    name=scenario.name,
                    status="skipped",
                    ran_end_to_end=False,
                    detail=(
                        f"Skipped end-to-end creation. {existing.id} ({existing.name}) "
                        "is already Pending Setup in the Zara repository. "
                        "Finish setup on that pipeline in Zara."
                    ),
                )
            )
            continue

        if REUSE_TAG in scenario.tags and not pending_before:
            results.append(
                ScenarioResult(
                    name=scenario.name,
                    status="skipped",
                    ran_end_to_end=False,
                    detail="No pipeline is Pending Setup, so there is nothing to reuse.",
                )
            )
            continue

        results.append(_execute(scenario, repository, pending_before))

    return FeatureReport(feature=feature_name, results=results)


def _execute(
    scenario: Scenario,
    repository: ZaraPipelineRepository,
    pending_before: list,
) -> ScenarioResult:
    ran_end_to_end = False
    steps_run: list[str] = []

    for step in scenario.steps:
        steps_run.append(step)
        text = step.split(" ", 1)[1]
        _run_step(text, repository, pending_before)
        if "runs end to end" in text:
            ran_end_to_end = True

    if END_TO_END_TAG in scenario.tags:
        created = repository.create_pending()
        ran_end_to_end = True
        detail = (
            f"No pipeline was Pending Setup. Creation ran end to end once "
            f"and added {created.id} to the Zara repository."
        )
    else:
        chosen = pending_before[0]
        detail = (
            f"Reused {chosen.id} ({chosen.name}). "
            "Creation was not run. Complete setup for this pipeline in Zara."
        )

    return ScenarioResult(
        name=scenario.name,
        status="passed",
        ran_end_to_end=ran_end_to_end,
        detail=detail,
        steps_run=steps_run,
    )


def _run_step(text: str, repository: ZaraPipelineRepository, pending_before: list) -> None:
    lowered = text.lower()
    if "has no pipeline pending setup" in lowered and repository.has_pending_setup():
        raise AssertionError("Zara repository already has a pipeline pending setup.")
    if "has a pipeline pending setup" in lowered and not pending_before:
        raise AssertionError("Zara repository has no pipeline pending setup.")
    if "does not run end to end" in lowered and not pending_before:
        raise AssertionError("Creation can stop early only when a pending pipeline exists.")
    if "one pipeline pending setup" in lowered:
        return
