import asyncio
import threading
import os
import uuid
import platform
import json
from typing import List
from datetime import datetime, timezone

from client.agent.collector import LogCollector
from client.agent.sender import ErrorSender
from client.agent.executor import CommandExecutor
from client.agent.schemas import ErrorData, MachineContext, ErrorLog, SeverityLevel, HeartbeatRequest, JobResult
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Load Config
CONFIG_FILE = "client/agent/config.json"
DEFAULT_CONFIG = {
    "machine_id": str(uuid.getnode()),
    "services": ["demo_service"],
    "log_files": ["/tmp/test_error.log"]
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config, using defaults: {e}")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

CONFIG = load_config()
LOG_FILES = CONFIG.get("log_files", DEFAULT_CONFIG["log_files"])
ERROR_PATTERNS = [r"error", r"fail", r"exception", r"critical", r"emerg"]

async def main():
    print(f"Starting Agent connecting to {BACKEND_URL}")
    print(f"Config loaded for Machine ID: {CONFIG.get('machine_id')}")
    print(f"Monitoring: {LOG_FILES}")
    
    # Components
    sender = ErrorSender(BACKEND_URL)
    executor = CommandExecutor(LOG_FILES) # Pass logs to executor
    
    # State
    pending_errors = set()
    error_queue = asyncio.Queue()
    
    # Machine Info
    machine_info = MachineContext(
        machine_id=CONFIG.get("machine_id"), 
        hostname=platform.node(),
        os=f"{platform.system()} {platform.release()}",
        services=CONFIG.get("services", ["default"]),
    )

    # Capture loop for thread-safe scheduling
    loop = asyncio.get_running_loop()

    # Callback from Collector (Threaded)
    def on_error_detected(file_path: str, line: str, context: List[str]):
        # loop variable is captured from outer scope
        
        # Create Payload
        error_data = ErrorData(
            error_id=f"err-{uuid.uuid4().hex[:8]}",
            severity=SeverityLevel.unknown,
            machine=machine_info,
            error=ErrorLog(
                source="log_file",
                service=os.path.basename(file_path),
                message=line.strip(),
                raw_log="\n".join(context)
            )
        )
        # Schedule for sending
        loop.call_soon_threadsafe(error_queue.put_nowait, error_data)

    # Start Collector in Background Thread
    collector = LogCollector(LOG_FILES, ERROR_PATTERNS, on_error_detected)
    t = threading.Thread(target=collector.start, daemon=True)
    t.start()

    # Async Loop
    last_heartbeat = 0
    HEARTBEAT_INTERVAL = 5 # seconds

    try:
        while True:
            current_time = asyncio.get_event_loop().time()
            
            # --- Heartbeat ---
            if current_time - last_heartbeat > HEARTBEAT_INTERVAL:
                # print("Sending heartbeat...")
                try:
                    hb = HeartbeatRequest(
                        machine_id=machine_info.machine_id,
                        hostname=machine_info.hostname,
                        services=machine_info.services
                    )
                    jobs = await sender.send_heartbeat(hb)
                    last_heartbeat = current_time
                    
                    if jobs:
                        print(f"Received {len(jobs)} jobs.")
                        for job in jobs:
                            # Execute Job
                            output = executor.execute_job(job)
                            
                            # Log output locally
                            print(f"    Result: {output[:200]}..." if len(output) > 200 else f"    Result: {output}")

                            # Send Result
                            success = "Error" not in output and "Execution failed" not in output
                            result = JobResult(
                                job_id=job.job_id,
                                machine_id=machine_info.machine_id,
                                output=output,
                                success=success
                            )
                            await sender.send_job_result(result)
                except Exception as e:
                    print(f"Heartbeat Loop Error: {e}")

            # --- Error Processing ---
            # 1. Process new errors
            while not error_queue.empty():
                err = await error_queue.get()
                print(f"Sending error {err.error_id}...")
                server_id = await sender.send_error(err)
                if server_id:
                    print(f"Server acknowledged {server_id}. Waiting for approval...")
                    pending_errors.add(server_id)
                else:
                    print("Failed to send error.")

            # 2. Poll pending errors
            # DEPRECATED: We now use Heartbeat Jobs for execution.
            # We just track them in pending_errors for logging or until ACK?
            
            # for eid in list(pending_errors):
            #     status, result = await sender.check_command(eid)
            #     ... 
            # (Removed loop to prevent double execution)
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping Agent...")
    finally:
        await sender.close()

if __name__ == "__main__":
    # Ensure log file exists (if configured ones are absolute paths like /tmp/...)
    for f in LOG_FILES:
        # Only touch file if it's in temp or known safe place? 
        # User defined config might point to real logs. We shouldn't overwrite real logs.
        # Check if it looks like the test file.
        if "test_error" in f and not os.path.exists(f):
             with open(f, 'w') as fp:
                fp.write("--- Log Start ---\n")
                
    asyncio.run(main())
