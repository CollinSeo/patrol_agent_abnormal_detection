from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_RUNTIME_CONFIG_PATH = Path("config/runtime.local.json")


@dataclass(frozen=True)
class Settings:
    analyzer_backend: str
    provider_name: str
    model_name: str
    endpoint_url: str | None
    api_key: str | None
    headers: dict[str, str]
    timeout_seconds: int


def load_settings() -> Settings:
    file_settings = _load_runtime_file(DEFAULT_RUNTIME_CONFIG_PATH)

    return Settings(
        analyzer_backend=_pick_value(file_settings, "analyzer_backend", "ANALYZER_BACKEND", "auto"),
        provider_name=_pick_value(file_settings, "provider_name", "PROVIDER_NAME", "mock"),
        model_name=_pick_value(file_settings, "model_name", "MODEL_NAME", "mock"),
        endpoint_url=_pick_value(file_settings, "endpoint_url", "MODEL_ENDPOINT_URL", None),
        api_key=_pick_value(file_settings, "api_key", "MODEL_API_KEY", None),
        headers=_pick_headers(file_settings),
        timeout_seconds=int(_pick_value(file_settings, "timeout_seconds", "MODEL_TIMEOUT_SECONDS", 120)),
    )


def _load_runtime_file(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_value(settings: dict[str, object], json_key: str, env_key: str, default: object) -> object:
    if env_key in os.environ:
        return os.environ[env_key]
    return settings.get(json_key, default)


def _pick_headers(settings: dict[str, object]) -> dict[str, str]:
    env_value = os.getenv("MODEL_HEADERS_JSON")
    if env_value:
        parsed = json.loads(env_value)
        return {str(key): str(value) for key, value in parsed.items()}

    file_headers = settings.get("headers", {})
    if not isinstance(file_headers, dict):
        return {}
    return {str(key): str(value) for key, value in file_headers.items()}
