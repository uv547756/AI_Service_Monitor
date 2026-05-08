"""
SQLAlchemy ORM models for the log monitoring system.

Tables: machines, logs, issues, commands, executions
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_id():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Machines
# ---------------------------------------------------------------------------
class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True, default=_new_id)
    hostname = Column(String, unique=True, nullable=False, index=True)
    os_info = Column(String)
    cpu = Column(String)
    ram_total_gb = Column(Float)
    disk_total_gb = Column(Float)
    disk_used_pct = Column(Float)
    uptime = Column(String)
    ip_address = Column(String)
    status = Column(String, default="healthy")  # healthy | warning | critical
    last_seen = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    logs = relationship("Log", back_populates="machine", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="machine", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------
class Log(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, default=_new_id)
    machine_id = Column(String, ForeignKey("machines.id"), nullable=False, index=True)
    service = Column(String, index=True)
    severity = Column(String, index=True)  # info | warning | error | critical
    message = Column(Text)
    raw_context = Column(Text)  # surrounding 100-200 lines
    timestamp = Column(DateTime, default=_utcnow, index=True)

    machine = relationship("Machine", back_populates="logs")
    issue = relationship("Issue", back_populates="trigger_log", uselist=False)


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------
class Issue(Base):
    __tablename__ = "issues"

    id = Column(String, primary_key=True, default=_new_id)
    machine_id = Column(String, ForeignKey("machines.id"), nullable=False, index=True)
    log_id = Column(String, ForeignKey("logs.id"), nullable=True)
    service = Column(String)
    severity = Column(String)  # low | medium | high | critical
    confidence = Column(Float)
    summary = Column(Text)
    root_cause = Column(Text)
    ai_raw_response = Column(Text)
    status = Column(String, default="open")  # open | resolved | ignored
    created_at = Column(DateTime, default=_utcnow, index=True)

    machine = relationship("Machine", back_populates="issues")
    trigger_log = relationship("Log", back_populates="issue")
    commands = relationship("Command", back_populates="issue", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
class Command(Base):
    __tablename__ = "commands"

    id = Column(String, primary_key=True, default=_new_id)
    issue_id = Column(String, ForeignKey("issues.id"), nullable=False, index=True)
    machine_id = Column(String, nullable=False, index=True)
    command_text = Column(Text, nullable=False)
    safe_to_auto_execute = Column(Boolean, default=False)
    approval_status = Column(String, default="pending")  # pending | approved | rejected
    approved_by = Column(String)  # telegram user / manual / dashboard
    created_at = Column(DateTime, default=_utcnow)
    approved_at = Column(DateTime)
    telegram_chat_id = Column(String)    # stored when alert is sent
    telegram_message_id = Column(Integer) # stored when alert is sent

    issue = relationship("Issue", back_populates="commands")
    executions = relationship("Execution", back_populates="command", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Executions
# ---------------------------------------------------------------------------
class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=_new_id)
    command_id = Column(String, ForeignKey("commands.id"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending | running | success | failed
    exit_code = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    command = relationship("Command", back_populates="executions")
