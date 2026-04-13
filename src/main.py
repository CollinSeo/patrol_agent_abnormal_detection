from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.analyzers import CompatibleAPIAnalyzer, MockAnalyzer
from src.config import load_settings
from src.loaders import discover_cases
from src.pipeline import run_pipeline


def _build_analyzer(backend: str, settings) -> MockAnalyzer | CompatibleAPIAnalyzer:
    resolved_backend = backend
    if backend == "auto":
        resolved_backend = settings.analyzer_backend
        if resolved_backend == "auto":
            resolved_backend = "compatible_api" if settings.endpoint_url else "mock"

    if resolved_backend == "compatible_api":
        if not settings.endpoint_url:
            raise RuntimeError("endpoint_url is required for --backend compatible_api")
        return CompatibleAPIAnalyzer(
            provider_name=settings.provider_name,
            model_name=settings.model_name,
            endpoint_url=settings.endpoint_url,
            api_key=settings.api_key,
            headers=settings.headers,
            timeout_seconds=settings.timeout_seconds,
        )

    return MockAnalyzer()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Abnormal change detection agent CLI")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("test_images"),
        help="Root directory containing analysis cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory where case outputs will be written",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="How to print CLI summary output",
    )
    parser.add_argument(
        "--mode",
        choices=("discover", "run"),
        default="run",
        help="Discover cases only or run the pipeline",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "mock", "compatible_api"),
        default="auto",
        help="Analyzer backend to use",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()

    if args.mode == "discover":
        cases = discover_cases(args.input_dir)

        if args.output_format == "json":
            print(json.dumps([case.to_dict() for case in cases], indent=2, ensure_ascii=False))
        else:
            print(f"Discovered {len(cases)} case(s) in {args.input_dir}")
            for case in cases:
                print(f"- {case.case_id} [{case.input_scheme}]")
                print(f"  spot: {case.spot_id}")
                print(f"  reference: {case.reference_image_path}")
                print(f"  current: {case.current_image_path}")
                print(f"  diff: {case.diff_visualization_path}")
        return 0

    analyzer = _build_analyzer(args.backend, settings)
    outputs = run_pipeline(args.input_dir, args.output_dir, analyzer)
    if args.output_format == "json":
        print(json.dumps([case_output.to_dict() for case_output in outputs], indent=2, ensure_ascii=False))
    else:
        print(f"Processed {len(outputs)} case(s) from {args.input_dir}")
        print(f"Outputs written to {args.output_dir}")
        for case_output in outputs:
            print(f"- {case_output.case_id}: status={case_output.status}, model={case_output.model_info}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
