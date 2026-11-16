"""Steganography request and response schemas."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DistortionMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mse: float
    psnr: float
    ssim: float


class EmbedResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation_id: str
    download_url: str
    filename: str
    metrics: DistortionMetrics
    capacity_stats: dict[str, Any] = Field(default_factory=dict)


class ExtractResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation_id: str
    payload_type: str  # text or file
    payload_text: str | None = None
    filename: str | None = None
    download_url: str | None = None
    size_bytes: int


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation_id: str
    mse: float
    psnr: float
    ssim: float
    heatmap_url: str
    bitplane_url: str
    pov_histogram: dict[str, Any]


class DetectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operation_id: str
    chi_square: dict[str, Any]
    rs_analysis: dict[str, Any]
    classification: str  # clean, suspicious, likely_stego
