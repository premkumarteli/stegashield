"""
StegaShield E2E Test Client - Base Definitions & Result Dataclasses.
Requirement-driven contracts for opaque-box E2E test execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class EmbedResult:
    """Standardized result of an embedding operation."""
    success: bool
    status_code: int
    stego_bytes: Optional[bytes] = None
    metrics: Dict[str, float] = field(default_factory=dict)  # {"mse": float, "psnr": float, "ssim": float}
    capacity_used: Optional[float] = None
    operation_id: Optional[str] = None
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


@dataclass
class ExtractResult:
    """Standardized result of an extraction operation."""
    success: bool
    status_code: int
    payload_text: Optional[str] = None
    payload_bytes: Optional[bytes] = None
    is_file: bool = False
    filename: Optional[str] = None
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


@dataclass
class AnalyzeResult:
    """Standardized result of an analysis (diff/heatmap/bitplane/histogram) operation."""
    success: bool
    status_code: int
    metrics: Dict[str, float] = field(default_factory=dict)
    diff_heatmap_bytes: Optional[bytes] = None
    bitplane_bytes: Optional[Dict[str, bytes]] = None
    histogram_data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


@dataclass
class DetectResult:
    """Standardized result of steganalysis detection (Chi-square & RS analysis)."""
    success: bool
    status_code: int
    chi2_score: float = 0.0
    chi2_p_value: float = 0.0
    df: int = 0
    rs_estimated_ratio: float = 0.0
    classification: str = "clean"  # "clean", "suspicious", "likely_stego"
    detector_details: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


@dataclass
class AttackLabResult:
    """Standardized result of an Attack Lab automated experiment run."""
    success: bool
    status_code: int
    experiment_id: Optional[str] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    items: List[Dict[str, Any]] = field(default_factory=list)
    csv_content: Optional[str] = None
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


class StegaShieldClient(ABC):
    """Abstract interface for StegaShield clients across live network, ASGI, and direct core modes."""

    @property
    @abstractmethod
    def mode(self) -> str:
        """Returns the client mode: 'live_http', 'asgi_testclient', or 'direct_core'."""
        pass

    @abstractmethod
    def embed(
        self,
        cover_bytes: bytes,
        filename: str = "cover.png",
        password: str = "",
        method: str = "lsb_replacement",
        payload_text: Optional[str] = None,
        payload_file_bytes: Optional[bytes] = None,
        payload_filename: Optional[str] = None,
    ) -> EmbedResult:
        """Embeds text or file payload into cover image."""
        pass

    @abstractmethod
    def extract(
        self,
        stego_bytes: bytes,
        filename: str = "stego.png",
        password: str = "",
    ) -> ExtractResult:
        """Extracts payload from stego image with password verification."""
        pass

    @abstractmethod
    def analyze(
        self,
        original_bytes: bytes,
        stego_bytes: bytes,
        original_filename: str = "original.png",
        stego_filename: str = "stego.png",
    ) -> AnalyzeResult:
        """Calculates distortion metrics, diff heatmap, bitplane, and histogram."""
        pass

    @abstractmethod
    def detect(
        self,
        image_bytes: bytes,
        filename: str = "image.png",
    ) -> DetectResult:
        """Executes Chi-square and RS steganalysis on target image."""
        pass

    @abstractmethod
    def run_attack_lab(
        self,
        cover_images: List[Tuple[str, bytes]],
        methods: List[str],
        ratios: List[float],
        detectors: List[str],
    ) -> AttackLabResult:
        """Executes automated Attack Lab experiment matrix."""
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieves session-scoped operations history."""
        pass

    @abstractmethod
    def clear_history(self) -> bool:
        """Clears session operations history."""
        pass
