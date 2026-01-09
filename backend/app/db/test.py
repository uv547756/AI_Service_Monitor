from backend.app.db.base import engine, SessionLocal
from backend.app.db.base import Base

from backend.app.db.models import Machines
from backend.app.db.models import Machine_Services
from backend.app.db.models import Errors
from backend.app.db.models import Analysis
from backend.app.db.models import Analysis_Commands

from datetime import datetime
import uuid


def run_test():
    print("🔧 Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("🖥️ Inserting machine...")
        machine = Machines(
            hostname="web-01",
            machine_name="Test Server",
            hwid="HWID-TEST-123",
            os="Ubuntu 22.04",
            arch="x86_64",
            ip_address="127.0.0.1",
        )
        db.add(machine)
        db.commit()
        db.refresh(machine)

        print("✅ Machine inserted:", machine.id)

        print("⚙️ Inserting service...")
        svc = Machine_Services(
            machine_id=machine.id,
            service_name="nginx"
        )
        db.add(svc)
        db.commit()

        print("🐞 Inserting error...")
        error = Errors(
            machine_id=machine.id,
            error_log="nginx failed to bind port 80",
            severity="high",
            detected_at=datetime.utcnow()
        )
        db.add(error)
        db.commit()
        db.refresh(error)

        print("📊 Inserting analysis...")
        analysis = Analysis(
            error_id=error.id,
            diagnosis="Port 80 already in use",
            verification="ss -tulpn | grep :80"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        print("🧾 Inserting analysis command...")
        cmd = Analysis_Commands(
            analysis_id=analysis.id,
            command="ss -tulpn | grep :80",
            explanation="Check which process uses port 80",
            risk_level="low",
            expected_output="Process bound to port 80",
            requires_sudo=False,
            idempotent=True
        )
        db.add(cmd)
        db.commit()

        print("🎉 DB TEST SUCCESSFUL")

    except Exception as e:
        db.rollback()
        print("❌ DB TEST FAILED:", e)
    finally:
        db.close()


if __name__ == "__main__":
    run_test()
