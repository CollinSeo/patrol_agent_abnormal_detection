from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from src.loaders import AnalysisCase


MIN_REQUIRED_MATCHES = 12
RANSAC_REPROJECTION_THRESHOLD = 5.0
MIN_REQUIRED_INLIERS = 20
MIN_INLIER_RATIO = 0.35
MIN_OVERLAP_RATIO = 0.6
MAX_MEAN_CORNER_SHIFT_RATIO = 0.35
MIN_AREA_RATIO = 0.3
MAX_AREA_RATIO = 2.2


class AlignmentError(ValueError):
    def __init__(self, reason: str, metrics: dict[str, object] | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.metrics = metrics or {}


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
        raise AlignmentError(
            f"Failed to load images for case: {case.case_id}",
            {"case_id": case.case_id},
        )

    original_reference_shape = reference.shape[:2]
    original_current_shape = current.shape[:2]
    original_diff_shape = diff.shape[:2]

    target_height, target_width = current.shape[:2]
    target_size = (target_width, target_height)
    if reference.shape[:2] != current.shape[:2]:
        reference = cv2.resize(reference, target_size, interpolation=cv2.INTER_LINEAR)
    if diff.shape[:2] != current.shape[:2]:
        diff = cv2.resize(diff, target_size, interpolation=cv2.INTER_LINEAR)

    homography, alignment_metrics = _estimate_homography(reference, current)
    if homography is None:
        raise AlignmentError(
            f"Alignment failed for case {case.case_id}: {alignment_metrics['failure_reason']}",
            alignment_metrics,
        )

    output_size = target_size

    warped_reference = cv2.warpPerspective(reference, homography, output_size)

    overlap_mask = _build_overlap_mask(reference.shape[:2], homography, output_size)
    overlap_ratio = float(np.count_nonzero(overlap_mask)) / float(overlap_mask.size)
    if overlap_ratio < MIN_OVERLAP_RATIO:
        failure_metrics = {
            **alignment_metrics,
            "overlap_ratio": overlap_ratio,
            "failure_reason": f"overlap ratio {overlap_ratio:.3f} below threshold {MIN_OVERLAP_RATIO:.3f}",
        }
        raise AlignmentError(
            f"Alignment failed for case {case.case_id}: {failure_metrics['failure_reason']}",
            failure_metrics,
        )

    masked_reference = _apply_mask(warped_reference, overlap_mask)
    masked_current = _apply_mask(current, overlap_mask)
    masked_diff = _apply_mask(diff, overlap_mask)

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
        "alignment_target": "current_image",
        "resize_target_shape": [target_height, target_width],
        "original_reference_shape": list(original_reference_shape),
        "original_current_shape": list(original_current_shape),
        "original_diff_shape": list(original_diff_shape),
        **alignment_metrics,
        "overlap_ratio": overlap_ratio,
        "mask_path": str(mask_out),
        "artifacts_dir": str(artifact_dir),
        "raw_reference_image_path": str(case.reference_image_path),
        "raw_current_image_path": str(case.current_image_path),
        "raw_diff_visualization_path": str(case.diff_visualization_path),
        "aligned_reference_image_path": str(reference_out),
        "masked_current_image_path": str(current_out),
        "prepared_diff_visualization_path": str(diff_out),
    }
    return AlignmentResult(case=aligned_case, preprocess_summary=preprocess_summary)


def _estimate_homography(reference: np.ndarray, current: np.ndarray) -> tuple[np.ndarray | None, dict[str, object]]:
    gray_reference = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    gray_current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    keypoints_reference, descriptors_reference = sift.detectAndCompute(gray_reference, None)
    keypoints_current, descriptors_current = sift.detectAndCompute(gray_current, None)

    if descriptors_reference is None or descriptors_current is None:
        return None, {
            "match_count": 0,
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "failure_reason": "missing SIFT descriptors",
        }

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    knn_matches = matcher.knnMatch(descriptors_reference, descriptors_current, k=2)

    good_matches = []
    for pair in knn_matches:
        if len(pair) != 2:
            continue
        first, second = pair
        if first.distance < 0.75 * second.distance:
            good_matches.append(first)

    if len(good_matches) < MIN_REQUIRED_MATCHES:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "failure_reason": f"good match count {len(good_matches)} below threshold {MIN_REQUIRED_MATCHES}",
        }

    reference_points = np.float32([keypoints_reference[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    current_points = np.float32([keypoints_current[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    homography, inlier_mask = cv2.findHomography(reference_points, current_points, cv2.RANSAC, RANSAC_REPROJECTION_THRESHOLD)
    if homography is None or inlier_mask is None:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": 0,
            "inlier_ratio": 0.0,
            "failure_reason": "homography estimation failed",
        }

    inlier_count = int(inlier_mask.ravel().sum())
    inlier_ratio = float(inlier_count) / float(len(good_matches))
    if inlier_count < MIN_REQUIRED_INLIERS:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "failure_reason": f"inlier count {inlier_count} below threshold {MIN_REQUIRED_INLIERS}",
        }
    if inlier_ratio < MIN_INLIER_RATIO:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "failure_reason": f"inlier ratio {inlier_ratio:.3f} below threshold {MIN_INLIER_RATIO:.3f}",
        }

    geometry_metrics = _measure_geometry(reference.shape[:2], current.shape[:2], homography)
    if geometry_metrics["mean_corner_shift_ratio"] > MAX_MEAN_CORNER_SHIFT_RATIO:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            **geometry_metrics,
            "failure_reason": (
                f"mean corner shift ratio {geometry_metrics['mean_corner_shift_ratio']:.3f} "
                f"above threshold {MAX_MEAN_CORNER_SHIFT_RATIO:.3f}"
            ),
        }
    if geometry_metrics["area_ratio"] < MIN_AREA_RATIO or geometry_metrics["area_ratio"] > MAX_AREA_RATIO:
        return None, {
            "match_count": len(good_matches),
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            **geometry_metrics,
            "failure_reason": (
                f"projected area ratio {geometry_metrics['area_ratio']:.3f} outside "
                f"[{MIN_AREA_RATIO:.3f}, {MAX_AREA_RATIO:.3f}]"
            ),
        }

    return homography, {
        "match_count": len(good_matches),
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_ratio,
        **geometry_metrics,
    }


def _measure_geometry(
    source_shape: tuple[int, int],
    destination_shape: tuple[int, int],
    homography: np.ndarray,
) -> dict[str, float]:
    source_height, source_width = source_shape
    destination_height, destination_width = destination_shape
    source_corners = np.float32(
        [[0, 0], [source_width - 1, 0], [source_width - 1, source_height - 1], [0, source_height - 1]]
    ).reshape(-1, 1, 2)
    projected_corners = cv2.perspectiveTransform(source_corners, homography).reshape(-1, 2)
    destination_corners = np.float32(
        [[0, 0], [destination_width - 1, 0], [destination_width - 1, destination_height - 1], [0, destination_height - 1]]
    )

    diagonal = float(np.hypot(destination_width, destination_height))
    corner_distances = np.linalg.norm(projected_corners - destination_corners, axis=1)
    mean_corner_shift_ratio = float(corner_distances.mean() / diagonal)

    source_area = float(source_width * source_height)
    projected_area = float(abs(cv2.contourArea(projected_corners.astype(np.float32))))
    area_ratio = projected_area / source_area if source_area else 0.0

    return {
        "mean_corner_shift_ratio": mean_corner_shift_ratio,
        "area_ratio": area_ratio,
    }


def _build_overlap_mask(source_shape: tuple[int, int], homography: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    source_height, source_width = source_shape
    source_mask = np.full((source_height, source_width), 255, dtype=np.uint8)
    warped_mask = cv2.warpPerspective(source_mask, homography, output_size)
    _, binary_mask = cv2.threshold(warped_mask, 1, 255, cv2.THRESH_BINARY)
    return binary_mask


def _apply_mask(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return cv2.bitwise_and(image, image, mask=mask)
