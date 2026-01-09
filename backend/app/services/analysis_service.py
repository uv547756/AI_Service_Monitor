from backend.app.core.analyzer import ErrorAnalyzer
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.error import ErrorData

analyzer = ErrorAnalyzer()

def analyze_error(error: ErrorData) -> AnalysisResult:
    return analyzer.analyze_and_fix(error)
