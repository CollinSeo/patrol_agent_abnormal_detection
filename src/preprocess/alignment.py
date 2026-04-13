from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from src.loaders import AnalysisCase


MIN_REQUIRED_MATCHES = 12
RANSAC_REPROJECTION_THRESHOLD = 5.0


@dataclass(frozen=True)
class AlignmentResult:
    case: AnalysisCase
    preprocess_summary: dict[str, object]


def align_case_images(case: AnalysisCase, output_dir: Path | str) -> AlignmentResult:
    artifact_dir = Path(output_dir) / case.spot_id / case.case_id / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    reference = cv2.imread(str(case.reference_image_path), cv2.IMREAD_COLOR)
    current = cv2.imread(str(case.current_image_path), cv2.IMREAD_COLOR)
    diff = cv2.imread(str(case.diff_visualization_path), cv2.IMREAD_COLOR)
    if reference is None or current is None or diff is None:
        raise ValueError(f"Failed to load images for case: {case.case_id}")

    homography, match_count, inlier_count = _estimate_homography(reference, current)
    if homography is None:
        raise ValueError(f"Alignment failed for case {case.case_id}: insufficient feature matches")

    reference_height, reference_width = reference.shape[:2]
    output_size = (reference_width, reference_height)

    warped_current = cv2.warpPerspective(current, homography, output_size)
    warped_diff = cv2.warpPerspective(diff, homography, output_size)

    overlap_mask = _build_overlap_mask(current.shape[:2], homography, output_size)
    masked_reference = _apply_mask(reference, overlap_mask)
    masked_current = _apply_mask(warped_current, overlap_mask)
    masked_diff = _apply_mask(warped_diff, overlap_mask)

    reference_out = artifact_dir / "reference_aligned.png"
    current_out = artifact_dir / "current_aligned.png"
    diff_out = artifact_dir / "diff_aligned.png"
    mask_out = artifact_dir / "alignment_mask.png"

    cv2.imwrite(str(reference_out), masked_reference)
    cv2.imwrite(str(current_out), masked_current)
    cv2.imwrite(str(diff_out), masked_diff)
    cv2.imwrite(str(mask_out), overlap_mask)

    aligned_case = AnalysisCase(
        case_id=case.case_id,
        spot_id=case.spot_id,
        case_dir=case.case_dir,
        reference_image_path=reference_out,
        current_image_path=current_out,
        diff_visualization_path=diff_out,
        input_scheme=f"{case.input_scheme}:aligned",
    )

    preprocess_summary = {
        "alignment_method": "sift_homography",
        "match_count": match_count,
        "inlier_count": inlier_count,
        "mask_path": str(mask_out),
        "artifacts_dir": str(artifact_dir),
        "raw_reference_image_path": str(case.reference_image_path),
        "raw_current_image_path": str(case.current_image_path),
        "raw_diff_visualization_path": str(case.diff_visualization_path),
        "aligned_reference_image_path": str(reference_out),
        "aligned_current_image_path": str(current_out),
        "aligned_diff_visualization_path": str(diff_out),
    }
    return AlignmentResult(case=aligned_case, preprocess_summary=preprocess_summary)


def _estimate_homography(reference: np.ndarray, current: np.ndarray) -> tuple[np.ndarray | None, int, int]:
    gray_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    gray_current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    keypoints_reference, descriptors_reference = sift.detectAndCompute(gray_reference, None)
    keypoints_current, descriptors_current = sift.detectAndCompute(gray_current, None)

    if descriptors_reference is None or descriptors_current is None:
        return None, 0, 0

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    knn_matches = matcher.knnMatch(descriptors_current, descriptors_reference, k=2)

    good_matches = []
    for pair in knn_matches:
        if len(pair) != 2:
            continue
        first, second = pair
        if first.distance < 0.75 * second.distance:
            good_matches.append(first)

    if len(good_matches) < MIN_REQUIRED_MATCHES:
        return None, len(good_matches), 0

    current_points = np.float32([keypoints_current[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    reference_points = np.float32([keypoints_reference[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    homography, inlier_mask = cv2.findHomography(current_points, reference_points, cv2.RANSAC, RANSAC_REPROJECTION_THRESHOLD)
    if homography is None or inlier_mask is None:
        return None, len(good_matches), 0

    inlier_count = int(inlier_mask.ravel().sum())
    if inlier_count < MIN_REQUIRED_MATCHES:
        return None, len(good_matches), inlier_count
    return homography, len(good_matches), inlier_count


def _build_overlap_mask(source_shape: tuple[int, int], homography: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    source_height, source_width = source_shape
    source_mask = np.full((source_height, source_width), 255, dtype=np.uint8)
    warped_mask = cv2.warpPerspective(source_mask, homography, output_size)
    _, binary_mask = cv2.threshold(warped_mask, 1, 255, cv2.THRESH_BINARY)
    return binary_mask


def _apply_mask(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return cv2.bitwise_and(image, image, mask=mask)
