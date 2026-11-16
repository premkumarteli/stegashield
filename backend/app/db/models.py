"""SQLAlchemy 2.x ORM models for StegaShield.

CRITICAL SECURITY REQUIREMENT:
Never persist passwords, plaintext secret data, encryption keys, or derived keys
in any database table or log. Only metadata, metrics, and file references are saved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy 2.x models."""
    pass


class Operation(Base):
    """Audit log of user-initiated operations (embed, extract, analyze, detect)."""

    __tablename__ = "operations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)  # embed, extract, analyze, detect
    cover_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stego_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # text, file
    method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # lsb_replacement, lsb_matching
    mse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    psnr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ssim: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    detections: Mapped[list[Detection]] = relationship(
        "Detection",
        back_populates="operation",
        cascade="all, delete-orphan",
    )


class Detection(Base):
    """Steganalysis evaluation result (Chi-square and RS analysis)."""

    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    operation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("operations.id", ondelete="CASCADE"),
        nullable=True,
    )
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    chi2_stat: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=False)
    rs_payload_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String(32), nullable=False)  # clean, suspicious, likely_stego
    details_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    operation: Mapped[Optional[Operation]] = relationship(
        "Operation",
        back_populates="detections",
    )


class TempFile(Base):
    """Temporary file metadata tracking 30-minute expiration TTL."""

    __tablename__ = "temp_files"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Experiment(Base):
    """Attack Lab matrix run configuration, status, and summary."""

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # running, completed, failed
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    summary_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    csv_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list[ExperimentItem]] = relationship(
        "ExperimentItem",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ExperimentItem(Base):
    """Individual attack trial cell within an Attack Lab matrix experiment."""

    __tablename__ = "experiment_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    cover_name: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    ratio: Mapped[float] = mapped_column(Float, nullable=False)
    detector: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False)

    experiment: Mapped[Experiment] = relationship(
        "Experiment",
        back_populates="items",
    )
