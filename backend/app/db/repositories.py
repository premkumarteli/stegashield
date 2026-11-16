"""Database repositories for CRUD operations on StegaShield entities."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Detection, Experiment, ExperimentItem, Operation, TempFile


class OperationRepository:
    """Repository for user operations (embed, extract, analyze, detect)."""

    @staticmethod
    def create(
        db: Session,
        session_id: str,
        operation_type: str,
        cover_filename: str | None = None,
        stego_filename: str | None = None,
        payload_type: str | None = None,
        method: str | None = None,
        mse: float | None = None,
        psnr: float | None = None,
        ssim: float | None = None,
    ) -> Operation:
        op = Operation(
            session_id=session_id,
            operation_type=operation_type,
            cover_filename=cover_filename,
            stego_filename=stego_filename,
            payload_type=payload_type,
            method=method,
            mse=mse,
            psnr=psnr,
            ssim=ssim,
            created_at=datetime.now(timezone.utc),
        )
        db.add(op)
        db.commit()
        db.refresh(op)
        return op

    @staticmethod
    def get_by_id(db: Session, operation_id: str) -> Operation | None:
        return db.scalar(select(Operation).where(Operation.id == operation_id))

    @staticmethod
    def list_by_session(
        db: Session,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Operation]:
        stmt = (
            select(Operation)
            .where(Operation.session_id == session_id)
            .order_by(Operation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def delete_by_session(db: Session, session_id: str) -> int:
        stmt = delete(Operation).where(Operation.session_id == session_id)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount


class DetectionRepository:
    """Repository for steganalysis detection records."""

    @staticmethod
    def create(
        db: Session,
        session_id: str,
        chi2_stat: float,
        p_value: float,
        rs_payload_ratio: float,
        classification: str,
        details_json: str,
        operation_id: str | None = None,
    ) -> Detection:
        det = Detection(
            operation_id=operation_id,
            session_id=session_id,
            chi2_stat=chi2_stat,
            p_value=p_value,
            rs_payload_ratio=rs_payload_ratio,
            classification=classification,
            details_json=details_json,
            created_at=datetime.now(timezone.utc),
        )
        db.add(det)
        db.commit()
        db.refresh(det)
        return det

    @staticmethod
    def get_by_id(db: Session, detection_id: str) -> Detection | None:
        return db.scalar(select(Detection).where(Detection.id == detection_id))

    @staticmethod
    def list_by_session(db: Session, session_id: str) -> list[Detection]:
        stmt = (
            select(Detection)
            .where(Detection.session_id == session_id)
            .order_by(Detection.created_at.desc())
        )
        return list(db.scalars(stmt).all())


class TempFileRepository:
    """Repository for tracking temporary files and their TTL."""

    @staticmethod
    def create(
        db: Session,
        session_id: str,
        filename: str,
        file_path: str,
        content_type: str,
        size_bytes: int,
        expires_at: datetime,
    ) -> TempFile:
        tf = TempFile(
            session_id=session_id,
            filename=filename,
            file_path=file_path,
            content_type=content_type,
            size_bytes=size_bytes,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        db.add(tf)
        db.commit()
        db.refresh(tf)
        return tf

    @staticmethod
    def get_by_id(db: Session, file_id: str) -> TempFile | None:
        return db.scalar(select(TempFile).where(TempFile.id == file_id))

    @staticmethod
    def delete(db: Session, file_id: str) -> bool:
        tf = TempFileRepository.get_by_id(db, file_id)
        if tf:
            db.delete(tf)
            db.commit()
            return True
        return False

    @staticmethod
    def get_expired(db: Session, now: datetime) -> list[TempFile]:
        now_utc = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        all_files = list(db.scalars(select(TempFile)).all())
        expired: list[TempFile] = []
        for tf in all_files:
            exp = tf.expires_at if tf.expires_at.tzinfo is not None else tf.expires_at.replace(tzinfo=timezone.utc)
            if exp <= now_utc:
                expired.append(tf)
        return expired

    @staticmethod
    def delete_expired(db: Session, now: datetime) -> list[TempFile]:
        expired = TempFileRepository.get_expired(db, now)
        for tf in expired:
            db.delete(tf)
        if expired:
            db.commit()
        return expired


class ExperimentRepository:
    """Repository for Attack Lab matrix experiments and trials."""

    @staticmethod
    def create(
        db: Session,
        session_id: str,
        config_json: str,
        status: str = "running",
    ) -> Experiment:
        exp = Experiment(
            session_id=session_id,
            status=status,
            config_json=config_json,
            created_at=datetime.now(timezone.utc),
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def get_by_id(db: Session, experiment_id: str) -> Experiment | None:
        return db.scalar(select(Experiment).where(Experiment.id == experiment_id))

    @staticmethod
    def get_running_experiment(db: Session) -> Experiment | None:
        return db.scalar(select(Experiment).where(Experiment.status == "running").limit(1))

    @staticmethod
    def update_status(
        db: Session,
        experiment_id: str,
        status: str,
        summary_json: str | None = None,
        csv_data: str | None = None,
        completed_at: datetime | None = None,
    ) -> Experiment | None:
        exp = ExperimentRepository.get_by_id(db, experiment_id)
        if exp is None:
            return None
        exp.status = status
        if summary_json is not None:
            exp.summary_json = summary_json
        if csv_data is not None:
            exp.csv_data = csv_data
        if completed_at is not None:
            exp.completed_at = completed_at
        db.commit()
        db.refresh(exp)
        return exp

    @staticmethod
    def add_items(
        db: Session,
        experiment_id: str,
        items_data: list[dict[str, Any]],
    ) -> list[ExperimentItem]:
        items: list[ExperimentItem] = []
        for d in items_data:
            item = ExperimentItem(
                experiment_id=experiment_id,
                cover_name=str(d.get("cover_name", "unknown")),
                method=str(d.get("method", "unknown")),
                ratio=float(d.get("ratio", 0.0)),
                detector=str(d.get("detector", "unknown")),
                score=float(d.get("score", 0.0)),
                verdict=str(d.get("verdict", "unknown")),
                execution_time_ms=float(d.get("execution_time_ms", 0.0)),
            )
            items.append(item)
            db.add(item)
        db.commit()
        return items
