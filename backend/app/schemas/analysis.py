from pydantic import BaseModel
from typing import List, Literal

# What the LLM analyser returns
class FixCommand(BaseModel):
    command: str
    explanation: str
    risk_level: Literal["low", "medium", "high"]
    expected_output: str
    requires_sudo: bool = False

# Also like previous, but also adds short summary
class AnalysisResult(BaseModel):
    diagnosis: str
    commands: List[FixCommand]
    verification: str
