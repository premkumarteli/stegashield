"""Attack Lab experiment orchestration service with mutex locking and SSE progress streaming."""

import asyncio
from datetime import datetime, timezone
import io
import json
import time
from typing import Any, AsyncGenerator

from fastapi import HTTPException, status
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

from app.core.attack_lab import export_csv, run_experiment
from app.db.repositories import ExperimentRepository
import app.db.session as db_session_module
from app.schemas.attack_lab import ExperimentStartResponse


class ExperimentService:
    """Manages Attack Lab experiment matrix execution, concurrency mutex, and SSE broadcasts."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._active_experiment_id: str | None = None
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._latest_event: dict[str, dict[str, Any]] = {}

    def is_running(self, db: Session | None = None) -> bool:
        """Check if an experiment is actively executing."""
        if self._lock.locked() or self._active_experiment_id is not None:
            return True
        if db is not None:
            running = ExperimentRepository.get_running_experiment(db)
            if running is not None:
                return True
        return False

    def _generate_default_covers(self) -> list[tuple[str, Image.Image]]:
        """Generate diverse benchmark patterns if no cover files were uploaded."""
        covers: list[tuple[str, Image.Image]] = []

        # 1. 2D smooth gradient
        x = np.linspace(0, 255, 64, dtype=np.float32)
        y = np.linspace(0, 255, 64, dtype=np.float32)
        xx, yy = np.meshgrid(x, y)
        grad_r = xx.astype(np.uint8)
        grad_g = yy.astype(np.uint8)
        grad_b = ((xx + yy) / 2).astype(np.uint8)
        gradient_img = Image.fromarray(np.stack([grad_r, grad_g, grad_b], axis=-1), mode="RGB")
        covers.append(("synthetic_gradient.png", gradient_img))

        # 2. 2D sinusoidal interference pattern
        sx = np.sin(np.linspace(0, 4 * np.pi, 64)) * 127.5 + 127.5
        sy = np.cos(np.linspace(0, 4 * np.pi, 64)) * 127.5 + 127.5
        sxx, syy = np.meshgrid(sx, sy)
        sin_img = Image.fromarray(
            np.stack([sxx.astype(np.uint8), syy.astype(np.uint8), ((sxx + syy) / 2).astype(np.uint8)], axis=-1),
            mode="RGB",
        )
        covers.append(("synthetic_sinusoid.png", sin_img))

        return covers

    async def start_experiment(
        self,
        db: Session,
        session_id: str,
        methods: list[str],
        ratios: list[float],
        detectors: list[str],
        cover_files: list[tuple[str, bytes]] | None = None,
    ) -> ExperimentStartResponse:
        """Attempt to acquire mutex and initiate Attack Lab experiment run."""
        if self.is_running(db):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An experiment is already in progress. Please wait for completion.",
            )

        # Validate inputs
        if not methods:
            methods = ["lsb_replacement", "lsb_matching"]
        if not ratios:
            ratios = [0.05, 0.1, 0.25, 0.5, 1.0]
        if not detectors:
            detectors = ["chi_square", "rs"]

        config_data = {
            "methods": methods,
            "ratios": ratios,
            "detectors": detectors,
            "cover_count": len(cover_files) if cover_files else 2,
        }

        # Create experiment record
        exp = ExperimentRepository.create(
            db=db,
            session_id=session_id,
            config_json=json.dumps(config_data),
            status="running",
        )

        self._active_experiment_id = exp.id
        self._subscribers[exp.id] = []

        # Launch execution as background task
        asyncio.create_task(
            self._execute_matrix(
                experiment_id=exp.id,
                methods=methods,
                ratios=ratios,
                detectors=detectors,
                cover_files=cover_files,
            )
        )

        return ExperimentStartResponse(
            experiment_id=exp.id,
            status="running",
            message="Attack Lab experiment successfully started.",
        )

    async def _execute_matrix(
        self,
        experiment_id: str,
        methods: list[str],
        ratios: list[float],
        detectors: list[str],
        cover_files: list[tuple[str, bytes]] | None,
    ) -> None:
        """Execute experiment matrix in background, publish events, and update DB."""
        await self._lock.acquire()
        try:
            # Prepare covers
            prepared_covers: list[tuple[str, Image.Image]]
            if cover_files and len(cover_files) > 0:
                prepared_covers = []
                for fname, bdata in cover_files:
                    try:
                        im = Image.open(io.BytesIO(bdata)).convert("RGB")
                        prepared_covers.append((fname, im))
                    except Exception:
                        pass
                if not prepared_covers:
                    prepared_covers = self._generate_default_covers()
            else:
                prepared_covers = self._generate_default_covers()

            total_steps = len(prepared_covers) * len(methods) * len(ratios)

            await self._broadcast_event(
                experiment_id,
                {
                    "experiment_id": experiment_id,
                    "status": "running",
                    "current_step": 0,
                    "total_steps": total_steps,
                    "percent": 0.0,
                    "item": None,
                    "summary": None,
                },
            )

            # Map detector aliases if needed
            mapped_detectors = []
            for d in detectors:
                norm = d.lower().strip()
                if norm in ("chi_square", "chi2"):
                    mapped_detectors.append("chi_square")
                elif norm in ("rs", "rs_analysis"):
                    mapped_detectors.append("rs_analysis")
                else:
                    mapped_detectors.append(d)

            # Run in worker thread so async event loop remains responsive
            start_time = time.perf_counter()
            summary = await asyncio.to_thread(
                run_experiment,
                cover_images=prepared_covers,
                methods=methods,
                ratios=ratios,
                detectors=mapped_detectors,
            )
            elapsed_total_ms = (time.perf_counter() - start_time) * 1000

            csv_text = export_csv(summary)

            # Prepare items to insert in DB
            items_for_db: list[dict[str, Any]] = []
            for itm in summary.get("items", []):
                verdict_str = "likely_stego" if itm.get("detected_as_stego") == 1 else "clean"
                score_val = float(itm.get("chi2_p_value", itm.get("rs_estimated_ratio", 0.0)))
                items_for_db.append(
                    {
                        "cover_name": itm.get("image_name", "unknown"),
                        "method": itm.get("method", "unknown"),
                        "ratio": itm.get("payload_ratio", 0.0),
                        "detector": "composite",
                        "score": score_val,
                        "verdict": verdict_str,
                        "execution_time_ms": elapsed_total_ms / max(1, len(summary.get("items", [1]))),
                    }
                )

            # Update DB in separate session
            with db_session_module.SessionLocal() as db_session:
                ExperimentRepository.update_status(
                    db=db_session,
                    experiment_id=experiment_id,
                    status="completed",
                    summary_json=json.dumps(summary),
                    csv_data=csv_text,
                    completed_at=datetime.now(timezone.utc),
                )
                ExperimentRepository.add_items(db=db_session, experiment_id=experiment_id, items_data=items_for_db)

            # Final completed event
            await self._broadcast_event(
                experiment_id,
                {
                    "experiment_id": experiment_id,
                    "status": "completed",
                    "current_step": total_steps,
                    "total_steps": total_steps,
                    "percent": 100.0,
                    "item": None,
                    "summary": summary,
                },
            )

        except Exception as err:
            with db_session_module.SessionLocal() as db_session:
                ExperimentRepository.update_status(
                    db=db_session,
                    experiment_id=experiment_id,
                    status="failed",
                    completed_at=datetime.now(timezone.utc),
                )
            await self._broadcast_event(
                experiment_id,
                {
                    "experiment_id": experiment_id,
                    "status": "failed",
                    "error": str(err),
                },
            )
        finally:
            self._active_experiment_id = None
            if self._lock.locked():
                self._lock.release()

    async def _broadcast_event(self, experiment_id: str, event_data: dict[str, Any]) -> None:
        """Store latest state and send event to all active subscriber queues."""
        self._latest_event[experiment_id] = event_data
        queues = self._subscribers.get(experiment_id, [])
        for q in queues:
            await q.put(event_data)

    async def stream_progress(self, experiment_id: str, db: Session) -> AsyncGenerator[str, None]:
        """SSE generator yielding live event-stream messages for a given experiment ID."""
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        if experiment_id not in self._subscribers:
            self._subscribers[experiment_id] = []
        self._subscribers[experiment_id].append(q)

        try:
            # First, check if already completed in DB
            exp = ExperimentRepository.get_by_id(db, experiment_id)
            if exp and exp.status in ("completed", "failed"):
                summary_data = json.loads(exp.summary_json) if exp.summary_json else None
                evt = {
                    "experiment_id": experiment_id,
                    "status": exp.status,
                    "current_step": 100,
                    "total_steps": 100,
                    "percent": 100.0,
                    "summary": summary_data,
                }
                yield f"event: progress\ndata: {json.dumps(evt)}\n\n"
                return

            # If there's a cached latest event, send it immediately
            if experiment_id in self._latest_event:
                latest = self._latest_event[experiment_id]
                yield f"event: progress\ndata: {json.dumps(latest)}\n\n"
                if latest.get("status") in ("completed", "failed"):
                    return

            # Listen for updates until completed or failed
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"event: progress\ndata: {json.dumps(event)}\n\n"
                    if event.get("status") in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive comment
                    yield ": keepalive\n\n"

        finally:
            if experiment_id in self._subscribers and q in self._subscribers[experiment_id]:
                self._subscribers[experiment_id].remove(q)

    def get_csv_export(self, db: Session, experiment_id: str) -> str:
        """Fetch RFC 4180 CSV export content for completed experiment."""
        exp = ExperimentRepository.get_by_id(db, experiment_id)
        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment '{experiment_id}' not found.",
            )
        if not exp.csv_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Experiment has not completed or has no CSV export available.",
            )
        return exp.csv_data


experiment_service = ExperimentService()
