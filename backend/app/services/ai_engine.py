"""
AI analysis engine — supports OpenAI, Google Gemini, and Ollama.

Constructs a diagnostic prompt from log context and system info,
then parses the structured JSON response.
"""
import json
import logging
import re
from typing import Optional

from ..config import settings
from ..schemas import AIAnalysisResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert Linux systems engineer analyzing server logs.
Given the log context, service name, and system information, produce a JSON diagnosis.

Respond ONLY with valid JSON in this exact schema:
{
  "severity": "low | medium | high | critical",
  "confidence": <float 0-1>,
  "summary": "<one-line summary>",
  "root_cause": "<detailed root cause analysis>",
  "recommended_command": "<single shell command to fix, or empty string>",
  "safe_to_auto_execute": <bool>
}

Rules:
- severity must be one of: low, medium, high, critical
- confidence is your certainty (0.0 to 1.0)
- recommended_command should be a safe, specific command. Never suggest destructive commands.
- safe_to_auto_execute should be true ONLY for trivially safe commands (restart, reload, clear cache)
"""


def _build_user_prompt(
    trigger_message: str,
    log_context: str,
    service: Optional[str],
    hostname: str,
    os_info: Optional[str],
    system_summary: str,
) -> str:
    return f"""## Trigger Log Line
{trigger_message}

## Service
{service or "unknown"}

## Machine
- Hostname: {hostname}
- OS: {os_info or "unknown"}
- {system_summary}

## Full Log Context (last ~200 lines)
```
{log_context[-8000:]}
```

Diagnose the issue and respond with JSON only."""


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------
async def _analyze_openai(user_prompt: str) -> AIAnalysisResult:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return AIAnalysisResult(**data), raw


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------
async def _analyze_gemini(user_prompt: str) -> AIAnalysisResult:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = await model.generate_content_async(
        f"{SYSTEM_PROMPT}\n\n{user_prompt}",
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=1024,
            response_mime_type="application/json",
        ),
    )
    raw = response.text
    data = json.loads(raw)
    return AIAnalysisResult(**data), raw


# ---------------------------------------------------------------------------
# Ollama provider (local, no API key needed)
# ---------------------------------------------------------------------------
async def _analyze_ollama(user_prompt: str) -> tuple[AIAnalysisResult, str]:
    import httpx

    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 1024,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    result = response.json()
    raw = result["message"]["content"]

    # Ollama may occasionally wrap JSON in markdown fences
    cleaned = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    data = json.loads(cleaned)
    return AIAnalysisResult(**data), raw


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def analyze_log(
    trigger_message: str,
    log_context: str,
    service: Optional[str],
    hostname: str,
    os_info: Optional[str] = None,
    system_summary: str = "",
) -> tuple[AIAnalysisResult, str]:
    """
    Run AI analysis on a log event.

    Returns (AIAnalysisResult, raw_json_string).
    Falls back to a default result on any error.
    """
    user_prompt = _build_user_prompt(
        trigger_message, log_context, service, hostname, os_info, system_summary
    )

    try:
        if settings.AI_PROVIDER == "ollama":
            return await _analyze_ollama(user_prompt)
        elif settings.AI_PROVIDER == "gemini":
            return await _analyze_gemini(user_prompt)
        else:
            return await _analyze_openai(user_prompt)
    except Exception as e:
        logger.error("AI analysis failed: %s", e, exc_info=True)
        fallback = AIAnalysisResult(
            severity="medium",
            confidence=0.0,
            summary=f"AI analysis unavailable: {e}",
            root_cause="Could not reach AI provider.",
            recommended_command="",
            safe_to_auto_execute=False,
        )
        return fallback, json.dumps(fallback.model_dump())
