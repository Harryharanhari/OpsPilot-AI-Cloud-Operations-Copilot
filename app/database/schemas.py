from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Service
class ServiceBase(BaseSchema):
    name: str
    description: Optional[str] = None
    status: str = "UP"

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    last_seen: datetime


# Log
class LogBase(BaseSchema):
    service_id: int
    level: str
    message: str
    source: Optional[str] = None

class LogCreate(LogBase):
    pass

class Log(LogBase):
    id: int
    timestamp: datetime
    severity_score: Optional[float] = None
    processed: bool = False
    summary: Optional[str] = None

class LogWithService(LogBase):
    id: int
    service_name: str
    timestamp: datetime
    severity_score: Optional[float] = None
    processed: bool = False
    summary: Optional[str] = None


# Incident
class IncidentBase(BaseSchema):
    title: str
    description: str
    severity: str
    status: str = "OPEN"

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    root_cause: Optional[str] = None
    remediation_steps: Optional[str] = None
    related_logs: Optional[Any] = None


# Metric
class MetricBase(BaseSchema):
    service_id: int
    name: str
    value: float
    unit: str

class MetricCreate(MetricBase):
    pass

class Metric(MetricBase):
    id: int
    timestamp: datetime


# Ingestion Schema (no service_id needed - looks up by name)
class LogIngest(BaseModel):
    service_name: str
    level: str = "INFO"
    message: str
    source: Optional[str] = "api"
    timestamp: Optional[datetime] = None
