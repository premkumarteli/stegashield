"""Attack Lab empirical matrix experimentation API router."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_session_id
from app.schemas.attack_lab import ExperimentStartResponse
from app.services.experiment_service import experiment_service

router = APIRouter(prefix="/attack-lab", tags=["Attack Lab"])


@router.post("/run", response_model=ExperimentStartResponse)
async def start_attack_lab_experiment(
    request: Request,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> ExperimentStartResponse:
    """Initiate Attack Lab matrix sweep across embedding methods, ratios, and detectors.

    Enforces mutex locking: returns HTTP 409 Conflict if another experiment is currently running.
    """
    content_type = request.headers.get("content-type", "")

    methods: list[str] = ["lsb_replacement", "lsb_matching"]
    ratios: list[float] = [0.05, 0.1, 0.25, 0.5, 1.0]
    detectors: list[str] = ["chi_square", "rs"]
    cover_files: list[tuple[str, bytes]] = []

    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "methods" in body and isinstance(body["methods"], list):
                    methods = body["methods"]
                if "ratios" in body and isinstance(body["ratios"], list):
                    ratios = [float(r) for r in body["ratios"]]
                if "detectors" in body and isinstance(body["detectors"], list):
                    detectors = body["detectors"]
        except Exception:
            pass
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        if "methods" in form:
            m_list = form.getlist("methods")
            if m_list:
                methods = [str(m) for m in m_list]
        if "ratios" in form:
            r_list = form.getlist("ratios")
            if r_list:
                ratios = [float(r) for r in r_list]
        if "detectors" in form:
            d_list = form.getlist("detectors")
            if d_list:
                detectors = [str(d) for d in d_list]
        for key, val in form.items():
            if hasattr(val, "read") and hasattr(val, "filename"):
                bdata = await val.read()
                if len(bdata) > 0:
                    cover_files.append((val.filename or "cover.png", bdata))

    return await experiment_service.start_experiment(
        db=db,
        session_id=session_id,
        methods=methods,
        ratios=ratios,
        detectors=detectors,
        cover_files=cover_files if cover_files else None,
    )


@router.get("/progress/{experiment_id}")
async def get_experiment_progress(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """SSE event-stream delivering real-time experiment progress updates."""
    generator = experiment_service.stream_progress(experiment_id, db)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/export/{experiment_id}")
def export_experiment_csv(
    experiment_id: str,
    db: Session = Depends(get_db),
) -> Response:
    """Download RFC 4180 compliant CSV benchmark report for completed experiment."""
    csv_text = experiment_service.get_csv_export(db, experiment_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="attack_lab_{experiment_id}.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )
