from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.loaders import AnalysisCase


DEFAULT_PROMPT_TEMPLATE_PATH = Path("docs/prompt-template.md")


@dataclass(frozen=True)
class PromptBundle:
    prompt_version: str
    system_prompt: str
    user_prompt_template: str

    def render_user_prompt(self, case: AnalysisCase) -> str:
        return self.user_prompt_template.format(
            case_id=case.case_id,
            location=case.spot_id,
            reference_image_path=case.reference_image_path,
            current_image_path=case.current_image_path,
            diff_visualization_path=case.diff_visualization_path,
        )


def load_prompt_bundle(template_path: Path | str = DEFAULT_PROMPT_TEMPLATE_PATH) -> PromptBundle:
    path = Path(template_path)
    text = path.read_text(encoding="utf-8")

    system_prompt = _extract_code_block(text, "## 시스템 프롬프트 템플릿")
    user_prompt_template = _extract_code_block(text, "## 사용자 프롬프트 템플릿")

    return PromptBundle(
        prompt_version=f"document:{path.as_posix()}",
        system_prompt=system_prompt.strip(),
        user_prompt_template=user_prompt_template.strip(),
    )


def _extract_code_block(text: str, section_title: str) -> str:
    pattern = re.compile(rf"{re.escape(section_title)}\s+```(?:text|json)?\n(.*?)```", re.DOTALL)
    match = pattern.search(text)
    if match is None:
        raise ValueError(f"Could not find code block for section: {section_title}")
    return match.group(1)
