import subprocess
import os
from typing import List
from client.agent.schemas import FixCommand, Job, JobType

class CommandExecutor:
    def __init__(self, log_files: List[str], sudo_password: str = None):
        self.log_files = log_files
        self.sudo_password = sudo_password

    def execute(self, commands: List[FixCommand]) -> str:
        """
        Executes commands and returns a consolidated log of execution.
        """
        output_log = f"--- Executing {len(commands)} approved commands ---\n"
        print(output_log.strip())
        
        for idx, cmd in enumerate(commands):
            msg = f"[{idx+1}/{len(commands)}] Running: {cmd.command}"
            output_log += msg + "\n"
            print(msg)
            print(f"    Reason: {cmd.explanation}")
            
            output, success, error_msg = self._run_command(cmd.command, cmd.requires_sudo)
            
            if success:
                print("    SUCCESS")
                output_log += "    SUCCESS\n"
                if output:
                     output_log += f"    Output: {output}\n"
            else:
                print(f"    FAILED: {error_msg}")
                output_log += f"    FAILED\n    Error: {error_msg}\n"
                if output:
                    output_log += f"    Output: {output}\n"
                output_log += "    Stopping execution chain due to failure.\n"
                break

        output_log += "--- Execution Complete ---"
        print("--- Execution Complete ---")
        return output_log

    def _run_command(self, cmd_str: str, requires_sudo: bool = False):
        final_cmd = cmd_str
        input_val = None
        
        if requires_sudo: 
            # Auto-detect sudo requirement if cmd_str starts with sudo even if not flagged? 
            # Or trust flag? Let's trust flag BUT also handle if user typed 'sudo ...'
            pass

        # If strict/explicit sudo check:
        # If command string has 'sudo', we treat it as needing sudo password if provided.
        # Check config mode?
        
        if self.sudo_password and ("sudo" in cmd_str.lower() or requires_sudo):
            if "sudo" not in cmd_str:
                 final_cmd = f"sudo -S {cmd_str}"
            else:
                 final_cmd = cmd_str.replace("sudo", "sudo -S")
            input_val = self.sudo_password + "\n"
        
        try:
            res = subprocess.run(
                final_cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                input=input_val,
                timeout=15 # Safety timeout
            )
            
            if res.returncode == 0:
                return res.stdout.strip(), True, None
            else:
                return res.stdout.strip(), False, f"(Exit Code: {res.returncode}) {res.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return None, False, "Command timed out (15s limit)."
        except Exception as e:
            return None, False, str(e)

    def execute_job(self, job: Job) -> str:
        print(f"Processing Job: {job.type} ({job.job_id})")
        
        if job.type == JobType.GET_LOGS:
            return self._handle_get_logs(job.args)
        elif job.type == JobType.GET_STATUS:
            return "Active and Monitoring."
        elif job.type == JobType.EXEC_CMD:
            return self._handle_exec_cmd(job.args)
        else:
            return f"Unknown job type: {job.type}"

    def _handle_exec_cmd(self, args: dict) -> str:
        command = args.get("command")
        if not command:
            return "Error: No command provided."
            
        print(f"--- Executing Remote Command: {command} ---")
        
        # Assume sudo needed if "sudo" is in string
        requires_sudo = "sudo" in command.lower()
        
        output, success, error = self._run_command(command, requires_sudo)
        
        if success:
             return output if output else "Success (No Output)"
        else:
             return f"Execution failed: {error}\nOutput: {output}"

    def _handle_get_logs(self, args: dict) -> str:
        service_filter = args.get("service")
        lines_count = args.get("lines", 50)
        
        output = ""
        found = False
        
        for fp in self.log_files:
            # If service filter provided, check if it matches filename
            if service_filter:
                if service_filter.lower() not in os.path.basename(fp).lower():
                    continue
            
            found = True
            output += f"--- Logs from {fp} (Last {lines_count} lines) ---\n"
            if os.path.exists(fp):
                try:
                    # Use tail command for efficiency
                    cmd = f"tail -n {lines_count} {fp}"
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    output += res.stdout
                    if res.stderr:
                        output += f"\n[stderr]: {res.stderr}"
                except Exception as e:
                    output += f"Error reading file: {e}\n"
            else:
                output += "File not found.\n"
            output += "\n"
            
        if not found and service_filter:
            output = f"No log files found matching service '{service_filter}'."
            
        return output
