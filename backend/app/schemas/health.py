"""Health schema."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str
    version: str
    database: str
