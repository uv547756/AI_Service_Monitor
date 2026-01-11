from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# What the LLM analyser returns
# Adding a field here makes it mandatory on the LLM output unless it's set to Optional = None
# Mention the same field in sys_prompt to make the LLM actually give it out, else a field will be added
# with null as output
class FixCommand(BaseModel):
    command: str
    explanation: str
    risk_level: Literal["low", "medium", "high"]
    expected_output: str
    requires_sudo: bool = False
    confidence: Optional[str] = None

# Also like previous, but also adds short summary
class AnalysisResult(BaseModel):
    diagnosis: str
    commands: List[FixCommand]
    verification: str
