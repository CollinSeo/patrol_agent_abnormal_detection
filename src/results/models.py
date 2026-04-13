from __future__ import annotations

from dataclasses import asdict, dataclass, field

from src.analyzers import AnalyzerResult
from src.loaders import AnalysisCase


@dataclass(frozen=True)
class CaseOutput:
    case_id: str
    spot_id: str
    status: str
    input_scheme: str
    abnormal_detected: bool
    primary_category: str
    abnormal_type: str
    analysis_log: list[str]
    abnormal_report: str
    action_guide: str
    decision_basis: list[str] = field(default_factory=list)
    ignored_factors: list[str] = field(default_factory=list)
    prompt_version: str = ""
    model_info: str = ""
    input_paths: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_analysis(
        cls,
        case: AnalysisCase,
        analyzer_result: AnalyzerResult,
        *,
        prompt_version: str,
        model_info: str,
    ) -> "CaseOutput":
        return cls(
            case_id=case.case_id,
            spot_id=case.spot_id,
            status=analyzer_result.status,
            input_scheme=case.input_scheme,
            abnormal_detected=analyzer_result.abnormal_detected,
            primary_category=analyzer_result.primary_category,
            abnormal_type=analyzer_result.abnormal_type,
            analysis_log=analyzer_result.analysis_log,
            abnormal_report=analyzer_result.abnormal_report,
            action_guide=analyzer_result.action_guide,
            decision_basis=analyzer_result.decision_basis,
            ignored_factors=analyzer_result.ignored_factors,
            prompt_version=prompt_version,
            model_info=model_info,
            input_paths={
                "case_dir": str(case.case_dir),
                "reference_image_path": str(case.reference_image_path),
                "current_image_path": str(case.current_image_path),
                "diff_visualization_path": str(case.diff_visualization_path),
            },
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
