import time
import os
import re
from collections import deque
from typing import List, Callable, Deque

class LogCollector:
    def __init__(self, file_paths: List[str], error_patterns: List[str], callback: Callable[[str, str, List[str]], None]):
        """
        :param file_paths: List of absolute paths to log files
        :param error_patterns: List of regex strings to trigger detection
        :param callback: Function to call when error is found (file_path, line, context)
        """
        self.file_paths = file_paths
        self.patterns = [re.compile(p, re.IGNORECASE) for p in error_patterns]
        self.callback = callback
        self.buffers: dict[str, Deque[str]] = {fp: deque(maxlen=100) for fp in file_paths}
        self.files = {}

    def start(self):
        # Open all files
        for fp in self.file_paths:
            if os.path.exists(fp):
                f = open(fp, 'r')
                # Seek to end to start monitoring new logs only
                f.seek(0, os.SEEK_END)
                self.files[fp] = f
            else:
                print(f"Warning: Log file not found: {fp}")

        print(f"Monitoring {len(self.files)} files...")
        
        try:
            while True:
                read_something = False
                for fp, f in self.files.items():
                    line = f.readline()
                    if line:
                        read_something = True
                        self._process_line(fp, line)
                    else:
                        continue
                
                if not read_something:
                    time.sleep(0.5)
        except KeyboardInterrupt:
            print("Stopping collector...")
        finally:
            for f in self.files.values():
                f.close()

    def _process_line(self, file_path: str, line: str):
        self.buffers[file_path].append(line)
        
        # Check patterns
        for pattern in self.patterns:
            if pattern.search(line):
                print(f"Error detected in {file_path}")
                # Get context (last 100 lines)
                context = list(self.buffers[file_path])
                self.callback(file_path, line, context)
                # Clear buffer or debounce? For now, let's just trigger. 
                # Ideally we debounce to avoid spamming for same error block.
                # Simple debounce: clear buffer so we don't trigger immediatley again on same block context
                # OR just let it flow. I'll leave it as is.
                break
