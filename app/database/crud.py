from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

# Service CRUD
def create_service(db: Session, service: schemas.ServiceCreate):
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

def get_service_by_name(db: Session, name: str):
    return db.query(models.Service).filter(models.Service.name == name).first()

def get_services(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Service).offset(skip).limit(limit).all()

# Log CRUD
def create_log(db: Session, log: schemas.LogCreate):
    db_log = models.Log(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_logs(db: Session, skip: int = 0, limit: int = 100, service_id: int = None):
    query = db.query(models.Log)
    if service_id:
        query = query.filter(models.Log.service_id == service_id)
    return query.order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()

# Incident CRUD
def create_incident(db: Session, incident: schemas.IncidentCreate):
    db_incident = models.Incident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incidents(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.Incident)
    if status:
        query = query.filter(models.Incident.status == status)
    return query.order_by(models.Incident.created_at.desc()).offset(skip).limit(limit).all()

def update_incident(db: Session, incident_id: int, updates: dict):
    db.query(models.Incident).filter(models.Incident.id == incident_id).update(updates)
    db.commit()
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()

# Metric CRUD
def create_metric(db: Session, metric: schemas.MetricCreate):
    db_metric = models.Metric(**metric.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric

def get_metrics(db: Session, name: str, service_id: int = None, limit: int = 100):
    query = db.query(models.Metric).filter(models.Metric.name == name)
    if service_id:
        query = query.filter(models.Metric.service_id == service_id)
    return query.order_by(models.Metric.timestamp.desc()).limit(limit).all()
