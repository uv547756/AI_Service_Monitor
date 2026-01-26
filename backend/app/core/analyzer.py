import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.error import ErrorData

class ErrorAnalyzer:
    def __init__(self):
        load_dotenv("backend/.env")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback or just raise?
            # For user experience, let's look for both or strictly switch.
            # User asked to switch, so strict switch.
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key)
        self.model_id = "gpt-4o"

    def analyze_and_fix(self, error_data: ErrorData) -> AnalysisResult:
        """
        Sends error to the LLM and get structured commands to execute
        :param error_data: Error logs from client
        :returns
        """
        machine = error_data.machine
        error = error_data.error

        system_prompt = """
        You are a senior Linux system administrator.
        You analyze system errors and suggest SAFE, IDEMPOTENT fixes only.
        Never suggest destructive commands.
        Prefer systemctl, service management, log inspection, and configuration validation.
        You MUST output valid JSON that EXACTLY matches this schema.
        Do NOT rename fields.
        Do NOT omit fields.
        Do NOT add extra fields.
        Do NOT use markdown.

        Schema:
{
  "diagnosis": "string",
  "commands": [
    {
      "command": "string",
      "explanation": "string",
      "risk_level": "low|medium|high",
      "expected_output": "string",
      "confidence": "like 50%, 70%",
      "requires_sudo": "boolean"
    }
  ],
  "verification": "string"
}
        """
        prompt = f"""
        Machine Context:
        - OS: {machine.os}
        - Hostname: {machine.hostname}
        - Kernel: {machine.kernel_version}
        - Services: {', '.join(machine.services)}

        Error:
        - Source: {error.source}
        - Service: {error.service}
        - Message: {error.message}

        Raw Log:
        {error.raw_log}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            
            data = json.loads(raw)
            return AnalysisResult.model_validate(data)
        except Exception as e:
            # Catch OpenAI errors or JSON errors
            raise RuntimeError(
                f"LLM Analysis failed: {e}"
            ) from e

# Test

TEST_ERROR_DATA = {
    "error_id": "err-20260108-001",
    "severity": "high",
    "machine": {
        "machine_id": "web-01",
        "hostname": "web-01",
        "os": "Ubuntu 22.04 LTS",
        "services": ["nginx", "postgresql", "redis"],
    },
    "error": {
        "source": "systemd",
        "service": "nginx",
        "message": "Failed to start nginx: address already in use",
        "raw_log": """
Jan 08 18:10:21 web-01 systemd[1]: nginx.service: Failed with result 'exit-code'.
Jan 08 18:10:21 web-01 nginx[1234]: nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
"""
    }
}

if __name__ == "__main__":
    import json
    analyzer = ErrorAnalyzer()
    print("Sending data:\n")
    error_data = ErrorData.model_validate(TEST_ERROR_DATA)
    result = analyzer.analyze_and_fix(error_data)
    # print("Raw output:\n")
    # print(result)
    print("\nParsed JSON:\n")
    print(result.model_dump_json(indent=2))
    # for cmd in result.commands:
    #     print(cmd.command, cmd.risk_level)