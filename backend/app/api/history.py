"""Session-scoped operation history API router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_session_id
from app.db.repositories import OperationRepository
from app.schemas.history import HistoryClearResponse, HistoryResponse, OperationItemResponse

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=HistoryResponse)
def get_session_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    """Retrieve audit history of operations associated with the anonymous caller session."""
    ops = OperationRepository.list_by_session(db, session_id=session_id, limit=limit, offset=offset)
    items = [OperationItemResponse.model_validate(op) for op in ops]
    return HistoryResponse(operations=items)


@router.delete("", response_model=HistoryClearResponse)
def clear_session_history(
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> HistoryClearResponse:
    """Clear all operation history records scoped to the current anonymous caller session."""
    deleted_count = OperationRepository.delete_by_session(db, session_id=session_id)
    return HistoryClearResponse(cleared=True, deleted_count=deleted_count)
