"""History schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OperationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    operation_type: str
    cover_filename: str | None = None
    stego_filename: str | None = None
    payload_type: str | None = None
    method: str | None = None
    mse: float | None = None
    psnr: float | None = None
    ssim: float | None = None
    created_at: datetime


class HistoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    operations: list[OperationItemResponse]


class HistoryClearResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cleared: bool
    deleted_count: int
