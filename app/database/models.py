from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="UP") # UP, DOWN, DEGRADED
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    logs = relationship("Log", back_populates="service")
    metrics = relationship("Metric", back_populates="service")

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    level = Column(String(50), index=True) # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    source = Column(String(255))
    severity_score = Column(Float, nullable=True) # 0.0 to 1.0 from AI
    processed = Column(Boolean, default=False)
    summary = Column(Text, nullable=True)
    
    service = relationship("Service", back_populates="logs")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(Text)
    severity = Column(String(50)) # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN") # OPEN, ACKNOWLEDGED, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    root_cause = Column(Text, nullable=True)
    remediation_steps = Column(Text, nullable=True)
    
    related_logs = Column(JSON, nullable=True) # IDs of affected logs

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    name = Column(String(255), index=True) # cpu_usage, memory_usage, etc.
    value = Column(Float)
    unit = Column(String(50))
    
    service = relationship("Service", back_populates="metrics")
