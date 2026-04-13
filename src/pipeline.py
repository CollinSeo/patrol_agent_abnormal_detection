from __future__ import annotations

from pathlib import Path

from src.analyzers import AnalyzerContext, BaseAnalyzer
from src.loaders import discover_cases
from src.preprocess import align_case_images
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
        alignment = align_case_images(case, output_dir)
        prepared_case = alignment.case
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
