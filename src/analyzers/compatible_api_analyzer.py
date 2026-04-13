from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from src.analyzers.base import AnalyzerContext, AnalyzerResult, BaseAnalyzer


JSON_SCHEMA = {
    "name": "abnormal_change_result",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "abnormal_detected": {"type": "boolean"},
            "primary_category": {"type": "string"},
            "abnormal_type": {"type": "string"},
            "analysis_log": {"type": "array", "items": {"type": "string"}},
            "abnormal_report": {"type": "string"},
            "action_guide": {"type": "string"},
            "decision_basis": {"type": "array", "items": {"type": "string"}},
            "ignored_factors": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string"}
        },
        "required": [
            "abnormal_detected",
            "primary_category",
            "abnormal_type",
            "analysis_log",
            "abnormal_report",
            "action_guide",
            "decision_basis",
            "ignored_factors",
            "status"
        ]
    }
}


class CompatibleAPIAnalyzer(BaseAnalyzer):
    name = "compatible_api"

    def __init__(
        self,
        *,
        provider_name: str,
        model_name: str,
        endpoint_url: str,
        api_key: str | None,
        headers: dict[str, str] | None,
        timeout_seconds: int,
    ) -> None:
        self._provider_name = provider_name
        self._model_name = model_name
        self._endpoint_url = endpoint_url
        self._api_key = api_key
        self._headers = headers or {}
        self._timeout_seconds = timeout_seconds
        self.name = f"{provider_name}:{model_name}"

    def analyze(self, context: AnalyzerContext) -> AnalyzerResult:
        payload = {
            "model": self._model_name,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": context.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": context.user_prompt},
                        _build_image_input(context.case.reference_image_path),
                        _build_image_input(context.case.current_image_path),
                        _build_image_input(context.case.diff_visualization_path),
                    ],
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": JSON_SCHEMA,
            },
        }

        headers = {"Content-Type": "application/json", **self._headers}
        if self._api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._api_key}"

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(self._endpoint_url, headers=headers, json=payload)
            response.raise_for_status()

        payload = _extract_json_payload(response.json())
        return AnalyzerResult(
            abnormal_detected=payload["abnormal_detected"],
            primary_category=payload["primary_category"],
            abnormal_type=payload["abnormal_type"],
            analysis_log=payload["analysis_log"],
            abnormal_report=payload["abnormal_report"],
            action_guide=payload["action_guide"],
            decision_basis=payload["decision_basis"],
            ignored_factors=payload["ignored_factors"],
            status=payload["status"],
        )


def _extract_json_payload(response_data: dict[str, object]) -> dict[str, object]:
    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("Compatible API response missing 'choices'")

    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("Compatible API response missing 'message'")

    content = message.get("content")
    if isinstance(content, str):
        return json.loads(content)

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                text = item.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        if text_parts:
            return json.loads("\n".join(text_parts))

    raise ValueError("Compatible API response content could not be parsed")


def _build_image_input(image_path: Path) -> dict[str, object]:
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }[image_path.suffix.lower()]
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{media_type};base64,{encoded}",
            "detail": "high",
        },
    }
