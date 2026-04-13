from __future__ import annotations

import json
from pathlib import Path

from src.analyzers import AnalyzerContext
from src.results import CaseOutput


def write_case_outputs(output_dir: Path | str, case_output: CaseOutput, context: AnalyzerContext) -> None:
    base_dir = Path(output_dir) / case_output.spot_id / case_output.case_id
    base_dir.mkdir(parents=True, exist_ok=True)

    (base_dir / "result.json").write_text(
        json.dumps(case_output.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (base_dir / "report.md").write_text(_build_markdown_report(case_output), encoding="utf-8")
    (base_dir / "prompt_system.txt").write_text(context.system_prompt, encoding="utf-8")
    (base_dir / "prompt_user.txt").write_text(context.user_prompt, encoding="utf-8")


def write_run_summary(output_dir: Path | str, case_outputs: list[CaseOutput]) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    summary = {
        "case_count": len(case_outputs),
        "status_counts": _count_by_key(case_outputs, "status"),
        "abnormal_type_counts": _count_by_key(case_outputs, "abnormal_type"),
    }
    (root / "run_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_markdown_report(case_output: CaseOutput) -> str:
    analysis_lines = "\n".join(f"- {line}" for line in case_output.analysis_log)
    decision_lines = "\n".join(f"- {line}" for line in case_output.decision_basis) or "- 없음"
    ignored_lines = "\n".join(f"- {line}" for line in case_output.ignored_factors) or "- 없음"

    return f"""# Case Report: {case_output.case_id}

## Summary

- Spot: `{case_output.spot_id}`
- Status: `{case_output.status}`
- Input scheme: `{case_output.input_scheme}`
- Abnormal detected: `{case_output.abnormal_detected}`
- Primary category: `{case_output.primary_category}`
- Abnormal type: `{case_output.abnormal_type}`
- Prompt version: `{case_output.prompt_version}`
- Model info: `{case_output.model_info}`

## Input Paths

- Reference: `{case_output.input_paths['reference_image_path']}`
- Current: `{case_output.input_paths['current_image_path']}`
- Diff: `{case_output.input_paths['diff_visualization_path']}`

## Preprocess Summary

```json
{json.dumps(case_output.preprocess_summary, indent=2, ensure_ascii=False)}
```

## Analysis Log

{analysis_lines}

## Report

{case_output.abnormal_report}

## Action Guide

{case_output.action_guide}

## Decision Basis

{decision_lines}

## Ignored Factors

{ignored_lines}
"""


def _count_by_key(case_outputs: list[CaseOutput], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case_output in case_outputs:
        value = str(getattr(case_output, key))
        counts[value] = counts.get(value, 0) + 1
    return counts
