"""
Seed script — populates the database with realistic sample data for development.

Usage:
    cd backend && python -m app.seed
"""
import asyncio
import random
from datetime import datetime, timezone, timedelta

from .database import init_db, async_session
from .models import Machine, Log, Issue, Command, Execution


SAMPLE_MACHINES = [
    {
        "hostname": "web-prod-01",
        "os_info": "Ubuntu 22.04 LTS",
        "cpu": "Intel Xeon E5-2686 v4 @ 2.30GHz (4 cores)",
        "ram_total_gb": 16.0,
        "disk_total_gb": 500.0,
        "disk_used_pct": 67.3,
        "uptime": "45 days, 12:30:42",
        "ip_address": "10.0.1.10",
        "status": "warning",
    },
    {
        "hostname": "db-prod-01",
        "os_info": "Debian 12 Bookworm",
        "cpu": "AMD EPYC 7R13 (8 cores)",
        "ram_total_gb": 64.0,
        "disk_total_gb": 2000.0,
        "disk_used_pct": 82.1,
        "uptime": "120 days, 3:15:00",
        "ip_address": "10.0.1.20",
        "status": "critical",
    },
    {
        "hostname": "app-staging-01",
        "os_info": "Ubuntu 24.04 LTS",
        "cpu": "Intel Core i7-12700 (6 cores)",
        "ram_total_gb": 32.0,
        "disk_total_gb": 1000.0,
        "disk_used_pct": 34.5,
        "uptime": "7 days, 8:45:20",
        "ip_address": "10.0.2.10",
        "status": "healthy",
    },
    {
        "hostname": "cache-prod-01",
        "os_info": "Alpine Linux 3.19",
        "cpu": "ARM Graviton3 (4 cores)",
        "ram_total_gb": 8.0,
        "disk_total_gb": 100.0,
        "disk_used_pct": 23.0,
        "uptime": "200 days, 15:00:00",
        "ip_address": "10.0.1.30",
        "status": "healthy",
    },
    {
        "hostname": "worker-prod-01",
        "os_info": "CentOS Stream 9",
        "cpu": "Intel Xeon Platinum 8375C (16 cores)",
        "ram_total_gb": 128.0,
        "disk_total_gb": 4000.0,
        "disk_used_pct": 55.8,
        "uptime": "30 days, 22:10:00",
        "ip_address": "10.0.1.40",
        "status": "warning",
    },
]

SAMPLE_LOGS = [
    {"service": "nginx", "severity": "error", "message": "upstream timed out (110: Connection timed out) while connecting to upstream"},
    {"service": "docker", "severity": "error", "message": "container 'api-service' OOMKilled — exceeded memory limit of 512MB"},
    {"service": "sshd", "severity": "warning", "message": "Failed password for invalid user admin from 203.0.113.42 port 55432"},
    {"service": "postgresql", "severity": "critical", "message": "FATAL: remaining connection slots are reserved for non-replication superuser connections"},
    {"service": "systemd", "severity": "error", "message": "logwatch-worker.service: Main process exited, code=exited, status=137/n/a"},
    {"service": "nginx", "severity": "warning", "message": "client intended to send too large body: 15728640 bytes"},
    {"service": "kernel", "severity": "critical", "message": "Out of memory: Killed process 3142 (java) total-vm:8388608kB, anon-rss:4194304kB"},
    {"service": "redis", "severity": "warning", "message": "WARNING: overcommit_memory is set to 0! Background save may fail under low memory condition"},
    {"service": "cron", "severity": "error", "message": "/etc/cron.daily/certbot: certbot renew failed with exit code 1"},
    {"service": "docker", "severity": "warning", "message": "WARNING: bridge-nf-call-iptables is disabled"},
]

SAMPLE_ISSUES = [
    {
        "severity": "high",
        "confidence": 0.91,
        "summary": "Nginx upstream timeout — backend service unresponsive",
        "root_cause": "The API backend container is not responding to health checks. Likely caused by high CPU usage from a recent deployment or a deadlocked thread pool.",
        "command": "sudo systemctl restart api-backend.service",
    },
    {
        "severity": "critical",
        "confidence": 0.95,
        "summary": "PostgreSQL connection pool exhausted",
        "root_cause": "All available PostgreSQL connections are in use. A connection leak in the application is keeping connections open without releasing them.",
        "command": "sudo -u postgres psql -c 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = '\\''idle'\\'' AND query_start < now() - interval '\\''5 minutes'\\'''",
    },
    {
        "severity": "critical",
        "confidence": 0.88,
        "summary": "OOM Killer terminated Java process",
        "root_cause": "The Java application exceeded the system memory limit. The JVM heap size (-Xmx) is set too high relative to available physical memory.",
        "command": "sudo systemctl restart java-app.service",
    },
    {
        "severity": "medium",
        "confidence": 0.76,
        "summary": "SSL certificate renewal failure",
        "root_cause": "Certbot failed to renew the SSL certificate. The HTTP-01 challenge likely failed because port 80 is blocked or the domain DNS is not pointing to this server.",
        "command": "sudo certbot renew --force-renewal",
    },
    {
        "severity": "high",
        "confidence": 0.84,
        "summary": "Docker container OOMKilled — api-service",
        "root_cause": "The api-service container exceeded its 512MB memory limit. Recent code changes or a memory leak in the application may be the cause.",
        "command": "docker restart api-service",
    },
]


async def seed():
    await init_db()
    async with async_session() as db:
        now = datetime.now(timezone.utc)

        # Create machines
        machines = []
        for m_data in SAMPLE_MACHINES:
            m = Machine(
                **m_data,
                last_seen=now - timedelta(minutes=random.randint(1, 60)),
            )
            db.add(m)
            machines.append(m)
        await db.flush()

        # Create logs
        logs = []
        for i, l_data in enumerate(SAMPLE_LOGS):
            machine = machines[i % len(machines)]
            log = Log(
                machine_id=machine.id,
                service=l_data["service"],
                severity=l_data["severity"],
                message=l_data["message"],
                raw_context=f"... 200 lines of {l_data['service']} log context ...\n{l_data['message']}\n... continued ...",
                timestamp=now - timedelta(minutes=random.randint(5, 1440)),
            )
            db.add(log)
            logs.append(log)
        await db.flush()

        # Create issues with commands
        for i, issue_data in enumerate(SAMPLE_ISSUES):
            machine = machines[i % len(machines)]
            log = logs[i % len(logs)]
            issue = Issue(
                machine_id=machine.id,
                log_id=log.id,
                service=log.service,
                severity=issue_data["severity"],
                confidence=issue_data["confidence"],
                summary=issue_data["summary"],
                root_cause=issue_data["root_cause"],
                ai_raw_response="{}",
                status=random.choice(["open", "open", "open", "resolved"]),
                created_at=log.timestamp,
            )
            db.add(issue)
            await db.flush()

            statuses = ["pending", "approved", "rejected", "approved"]
            approval = random.choice(statuses)
            cmd = Command(
                issue_id=issue.id,
                machine_id=machine.id,
                command_text=issue_data["command"],
                safe_to_auto_execute=False,
                approval_status=approval,
                approved_by="telegram:admin" if approval != "pending" else None,
                approved_at=now if approval != "pending" else None,
            )
            db.add(cmd)
            await db.flush()

            # Add execution for approved commands
            if approval == "approved" and random.random() > 0.3:
                ex = Execution(
                    command_id=cmd.id,
                    status=random.choice(["success", "success", "failed"]),
                    exit_code=0 if random.random() > 0.3 else 1,
                    stdout="Service restarted successfully." if random.random() > 0.3 else "",
                    stderr="" if random.random() > 0.3 else "Error: permission denied",
                    started_at=now - timedelta(minutes=5),
                    completed_at=now - timedelta(minutes=4),
                )
                db.add(ex)

        await db.commit()
        print(f"✅ Seeded {len(machines)} machines, {len(logs)} logs, {len(SAMPLE_ISSUES)} issues")


if __name__ == "__main__":
    asyncio.run(seed())
