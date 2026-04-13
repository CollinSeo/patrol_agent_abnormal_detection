from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
TIMESTAMP_FORMAT = "%Y-%m-%dT%H%M%SZ"


@dataclass(frozen=True)
class AnalysisCase:
    case_id: str
    spot_id: str
    case_dir: Path
    reference_image_path: Path
    current_image_path: Path
    diff_visualization_path: Path
    input_scheme: str

    def to_dict(self) -> dict[str, str]:
        data = asdict(self)
        return {key: str(value) for key, value in data.items()}


def discover_cases(input_dir: Path | str) -> list[AnalysisCase]:
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {root}")

    cases: list[AnalysisCase] = []
    for case_dir in _iter_candidate_case_dirs(root):
        parsed_case = _parse_case_dir(case_dir)
        if parsed_case is not None:
            cases.append(parsed_case)

    cases.sort(key=lambda item: (item.spot_id, item.case_id))
    return cases


def _iter_candidate_case_dirs(root: Path) -> Iterable[Path]:
    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if any(child.is_file() and child.suffix.lower() in IMAGE_EXTENSIONS for child in directory.iterdir()):
            yield directory


def _parse_case_dir(case_dir: Path) -> AnalysisCase | None:
    image_files = [path for path in case_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
    if len(image_files) < 3:
        return None

    sample_case = _parse_sample_case(case_dir, image_files)
    if sample_case is not None:
        return sample_case

    return _parse_timestamp_case(case_dir, image_files)


def _parse_sample_case(case_dir: Path, image_files: list[Path]) -> AnalysisCase | None:
    reference_candidates = [path for path in image_files if path.stem == "time_0"]
    current_candidates = [path for path in image_files if path.stem.startswith("time_") and path.stem != "time_0" and not path.stem.startswith("dino_")]

    if len(reference_candidates) != 1 or len(current_candidates) != 1:
        return None

    reference_image = reference_candidates[0]
    current_image = current_candidates[0]
    diff_visualization = case_dir / f"dino_{current_image.stem}{current_image.suffix}"
    if not diff_visualization.exists():
        png_visualization = case_dir / f"dino_{current_image.stem}.png"
        if png_visualization.exists():
            diff_visualization = png_visualization
        else:
            return None

    return AnalysisCase(
        case_id=case_dir.name,
        spot_id=case_dir.parent.name,
        case_dir=case_dir,
        reference_image_path=reference_image,
        current_image_path=current_image,
        diff_visualization_path=diff_visualization,
        input_scheme="sample_test_images",
    )


def _parse_timestamp_case(case_dir: Path, image_files: list[Path]) -> AnalysisCase | None:
    raw_images = [path for path in image_files if not path.stem.startswith("dino_")]
    if len(raw_images) != 2:
        return None

    parsed_images: list[tuple[datetime, Path]] = []
    for image_path in raw_images:
        try:
            parsed_images.append((_parse_timestamp(image_path.stem), image_path))
        except ValueError:
            return None

    parsed_images.sort(key=lambda item: item[0])
    reference_image = parsed_images[0][1]
    current_image = parsed_images[1][1]

    diff_candidates = [
        path
        for path in image_files
        if path.stem == f"dino_{current_image.stem}"
    ]
    if len(diff_candidates) != 1:
        return None

    return AnalysisCase(
        case_id=case_dir.name,
        spot_id=case_dir.parent.name,
        case_dir=case_dir,
        reference_image_path=reference_image,
        current_image_path=current_image,
        diff_visualization_path=diff_candidates[0],
        input_scheme="timestamp_operational",
    )


def _parse_timestamp(stem: str) -> datetime:
    return datetime.strptime(stem, TIMESTAMP_FORMAT)
