from fastapi import APIRouter
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.error import ErrorData
from backend.app.services.analysis_service import analyze_error

router = APIRouter(prefix="/errors", tags=["errors"])

@router.post('/', response_model=AnalysisResult)
def submit_error(error: ErrorData):
    return analyze_error(error)