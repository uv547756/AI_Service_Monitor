"""
System information collector — gathers machine metadata.
"""
import platform
import socket
import os


def get_system_info() -> dict:
    """
    Collect comprehensive system metadata.

    Returns a dict matching the MachineBase schema.
    """
    info = {
        "hostname": socket.gethostname(),
        "os_info": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu": _get_cpu_info(),
        "ram_total_gb": _get_ram_gb(),
        "disk_total_gb": _get_disk_total_gb(),
        "disk_used_pct": _get_disk_used_pct(),
        "uptime": _get_uptime(),
        "ip_address": _get_ip(),
    }
    return info


def _get_cpu_info() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            lines = f.readlines()
        model = ""
        count = 0
        for line in lines:
            if line.startswith("model name"):
                model = line.split(":")[1].strip()
                count += 1
        return f"{model} ({count} cores)" if model else f"{platform.processor()} ({os.cpu_count()} cores)"
    except Exception:
        return f"{platform.processor() or platform.machine()} ({os.cpu_count()} cores)"


def _get_ram_gb() -> float:
    try:
        with open("/proc/meminfo") as f:
            line = f.readline()
        kb = int(line.split()[1])
        return round(kb / 1048576, 1)
    except Exception:
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 1)
        except ImportError:
            return 0.0


def _get_disk_total_gb() -> float:
    try:
        stat = os.statvfs("/")
        return round((stat.f_blocks * stat.f_frsize) / (1024**3), 1)
    except Exception:
        return 0.0


def _get_disk_used_pct() -> float:
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        return round((used / total) * 100, 1) if total > 0 else 0.0
    except Exception:
        return 0.0


def _get_uptime() -> str:
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.readline().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{days} days, {hours:02d}:{minutes:02d}"
    except Exception:
        return "unknown"


def _get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
