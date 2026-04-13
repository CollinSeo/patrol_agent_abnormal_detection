from __future__ import annotations

from src.analyzers.base import AnalyzerContext, AnalyzerResult, BaseAnalyzer


class MockAnalyzer(BaseAnalyzer):
    name = "mock"

    def analyze(self, context: AnalyzerContext) -> AnalyzerResult:
        case = context.case
        return AnalyzerResult(
            abnormal_detected=False,
            primary_category="구조적 입력/판단 상태",
            abnormal_type="판단 불가",
            analysis_log=[
                "reference image path registered",
                "current image path registered",
                "diff visualization path registered",
                "prompt package generated from template",
                "mock analyzer used because no real VLM backend is connected",
            ],
            abnormal_report=(
                f"케이스 `{case.case_id}`에 대한 입력 경로와 프롬프트는 정상적으로 구성되었지만, "
                "현재는 실제 VLM 백엔드가 연결되지 않아 이미지 내용 기반 최종 판정을 수행하지 않았다."
            ),
            action_guide="실제 판정을 위해 VLM 연동을 연결한 뒤 동일 케이스를 재실행한다.",
            decision_basis=[
                "prompt rendering succeeded",
                "input triplet resolved",
                "analysis backend not configured",
            ],
            ignored_factors=[
                "black mask region should be ignored by final analyzer",
                "minor alignment error should not be overcounted",
            ],
            status="mocked",
        )
