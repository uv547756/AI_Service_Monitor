import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Machines(Base):
    __tablename__ = "machines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    hostname = Column(String, nullable=False)
    machine_name = Column(String, nullable=True)
    hwid = Column(String, nullable=False, unique=True)
    os = Column(String, nullable=False)
    arch = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class Machine_Services(Base):
    __tablename__ = "machine_services"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    machine_id = Column(UUID(as_uuid=True),ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    service_name = Column(String, nullable=False)

class Errors(Base):
    __tablename__ = "errors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"))
    error_log = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Analysis(Base):
    __tablename__ = "analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    error_id = Column(UUID(as_uuid=True), ForeignKey("errors.id", ondelete="CASCADE"), nullable=False)
    diagnosis = Column(String, nullable=False)
    verification = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Analysis_Commands(Base):
    __tablename__ = "analysis_commands"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False)
    command = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    risk_level = Column(String, nullable=False)
    expected_output = Column(String, nullable=False)
    requires_sudo = Column(Boolean, default=False, nullable=False)
    idempotent = Column(Boolean, default=True, nullable=False)
