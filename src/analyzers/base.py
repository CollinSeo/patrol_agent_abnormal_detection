from __future__ import annotations

from dataclasses import dataclass, field

from src.loaders import AnalysisCase


@dataclass(frozen=True)
class AnalyzerContext:
    case: AnalysisCase
    prompt_version: str
    system_prompt: str
    user_prompt: str


@dataclass(frozen=True)
class AnalyzerResult:
    abnormal_detected: bool
    primary_category: str
    abnormal_type: str
    analysis_log: list[str]
    abnormal_report: str
    action_guide: str
    decision_basis: list[str] = field(default_factory=list)
    ignored_factors: list[str] = field(default_factory=list)
    status: str = "ok"


class BaseAnalyzer:
    name = "base"

    def analyze(self, context: AnalyzerContext) -> AnalyzerResult:
        raise NotImplementedError
