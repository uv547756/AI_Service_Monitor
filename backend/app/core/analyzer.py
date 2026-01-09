import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError
from backend.app.schemas.analysis import AnalysisResult
from backend.app.schemas.error import ErrorData

class ErrorAnalyzer:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GENAI_API_KEY")
        if not api_key:
            raise RuntimeError("GENAI_API_KEY not set")
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"
        # print(self.client.schemas.list()[:])

    def analyze_and_fix(self, error_data: ErrorData) -> AnalysisResult:
        """
        Sends error to the LLM and get structured commands to execute
        :param error_data: Error logs from client
        :returns
        """
        machine_context = error_data["machine_context"]
        error_log = error_data["error_log"]

        system_prompt = """
        You are a senior Linux system administrator.
        You analyze system errors and suggest SAFE, IDEMPOTENT fixes only.
        Never suggest destructive commands.
        Prefer systemctl, service management, log inspection, and configuration validation.
        Always respond in valid JSON only.
        """

        prompt = f"""
            Machine Context:
            - OS: {machine_context['os']}
            - Hostname: {machine_context['hostname']}
            - Services: {', '.join(machine_context['services'])}
            
            Error Log:
            {error_log}
            
            Provide a JSON response with this structure:
            {{
                "diagnosis": "Brief explanation of the issue",
                "commands": [
                    {{
                        "command": "the actual command to run",
                        "explanation": "why this command is needed",
                        "risk_level": "low|medium|high",
                        "expected_output": "what output indicates success"
                    }}
                ],
                "verification": "how to verify the fix worked"
            }}
            
            Only suggest safe and idempotent commands. Prefer systemctl, service management, log rotation, etc.
"""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",

            ),
        )
        raw = response.text
        try:
            data = json.loads(raw)
            return AnalysisResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise RuntimeError(
                f"Invalid LLM output:\n {raw}"
            ) from e




# Test

TEST_ERROR_DATA = {
    "machine_context": {
        "os": "Ubuntu 22.04 LTS",
        "hostname": "web-01",
        "services": ["nginx", "postgresql", "redis"]
    },
    "error_log": """
Jan 08 18:10:21 web-01 systemd[1]: nginx.service: Failed with result 'exit-code'.
Jan 08 18:10:21 web-01 systemd[1]: Failed to start A high performance web server and a reverse proxy server.
Jan 08 18:10:21 web-01 nginx[1234]: nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
"""
}


if __name__ == "__main__":
    import json
    analyzer = ErrorAnalyzer()
    print("Sending data:\n")
    result = analyzer.analyze_and_fix(TEST_ERROR_DATA)
    # print("Raw output:\n")
    # print(result)
    print("\nParsed JSON:\n")
    print(result.model_dump_json(indent=2))
    # for cmd in result.commands:
    #     print(cmd.command, cmd.risk_level)
