"""Attack Lab request and response schemas."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ExperimentConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    methods: list[str] = Field(default_factory=lambda: ["lsb_replacement", "lsb_matching"])
    ratios: list[float] = Field(default_factory=lambda: [0.05, 0.1, 0.25, 0.5, 1.0])
    detectors: list[str] = Field(default_factory=lambda: ["chi_square", "rs"])


class ExperimentStartResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    experiment_id: str
    status: str
    message: str


class ExperimentProgressEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    experiment_id: str
    status: str
    current_step: int
    total_steps: int
    percent: float
    current_item: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
