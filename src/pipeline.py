from __future__ import annotations

from pathlib import Path

from src.analyzers import AnalyzerContext, AnalyzerResult, BaseAnalyzer
from src.loaders import discover_cases
from src.preprocess import AlignmentError, align_case_images
from src.prompts import load_prompt_bundle
from src.reporting import write_case_outputs, write_run_summary
from src.results import CaseOutput


def run_pipeline(
    input_dir: Path | str,
    output_dir: Path | str,
    analyzer: BaseAnalyzer,
    *,
    prompt_template_path: Path | str = Path("docs/prompt-template.md"),
) -> list[CaseOutput]:
    prompt_bundle = load_prompt_bundle(prompt_template_path)
    cases = discover_cases(input_dir)

    outputs: list[CaseOutput] = []
    for case in cases:
        try:
            alignment = align_case_images(case, output_dir)
            prepared_case = alignment.case
        except AlignmentError as error:
            case_output = CaseOutput.from_analysis(
                case,
                _build_angle_change_result(error),
                prompt_version=prompt_bundle.prompt_version,
                model_info="alignment_guard",
                preprocess_summary=error.metrics,
            )
            write_case_outputs(output_dir, case_output, _build_fallback_context(case, prompt_bundle))
            outputs.append(case_output)
            continue

        context = AnalyzerContext(
            case=prepared_case,
            prompt_version=prompt_bundle.prompt_version,
            system_prompt=prompt_bundle.system_prompt,
            user_prompt=prompt_bundle.render_user_prompt(prepared_case),
        )
        analyzer_result = analyzer.analyze(context)
        case_output = CaseOutput.from_analysis(
            prepared_case,
            analyzer_result,
            prompt_version=context.prompt_version,
            model_info=analyzer.name,
            preprocess_summary=alignment.preprocess_summary,
        )
        write_case_outputs(output_dir, case_output, context)
        outputs.append(case_output)

    write_run_summary(output_dir, outputs)
    return outputs


def _build_angle_change_result(error: AlignmentError) -> AnalyzerResult:
    reason = error.metrics.get("failure_reason", error.reason)
    metrics_summary = []
    for key in ("match_count", "inlier_count", "inlier_ratio", "mean_corner_shift_ratio", "area_ratio", "overlap_ratio"):
        if key in error.metrics:
            metrics_summary.append(f"{key}={error.metrics[key]}")

    return AnalyzerResult(
        abnormal_detected=False,
        primary_category="구조적 입력/판단 상태",
        abnormal_type="앵글 변경",
        analysis_log=[
            "raw images loaded",
            "sift alignment attempted",
            f"alignment rejected: {reason}",
        ],
        abnormal_report=(
            "입력 이미지 간 시점 차이가 동일 위치 촬영의 허용 범위를 벗어나 정렬 품질을 확보하지 못했다. "
            f"정렬 실패 사유: {reason}."
        ),
        action_guide="동일 위치와 유사한 카메라 각도에서 다시 촬영한 후 재분석한다.",
        decision_basis=metrics_summary,
        ignored_factors=["alignment rejected before abnormal analysis"],
        status="angle_changed",
    )


def _build_fallback_context(case, prompt_bundle) -> AnalyzerContext:
    return AnalyzerContext(
        case=case,
        prompt_version=prompt_bundle.prompt_version,
        system_prompt=prompt_bundle.system_prompt,
        user_prompt=prompt_bundle.render_user_prompt(case),
    )
