from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from ..database import crud, schemas, session, models
from ..ai_engine.anomaly_detector import anomaly_detector

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/snapshot")
def metrics_snapshot(db: Session = Depends(session.get_db)):
    """Return latest metric value per (service, metric_name) for dashboard charts."""
    services = db.query(models.Service).all()
    metric_names = ["cpu_usage", "memory_usage", "request_rate", "error_rate", "response_time"]

    snapshot = {}
    for svc in services:
        snapshot[svc.name] = {}
        for mname in metric_names:
            latest = db.query(models.Metric).filter(
                models.Metric.service_id == svc.id,
                models.Metric.name == mname
            ).order_by(models.Metric.timestamp.desc()).first()
            if latest:
                snapshot[svc.name][mname] = {
                    "value": round(latest.value, 2),
                    "unit": latest.unit,
                    "timestamp": latest.timestamp.isoformat(),
                }

    # Time series for charts (last 12 data points per metric)
    timeseries = {}
    for mname in metric_names:
        rows = db.query(
            models.Metric.timestamp,
            func.avg(models.Metric.value).label("avg_val")
        ).filter(
            models.Metric.name == mname
        ).group_by(models.Metric.timestamp).order_by(
            models.Metric.timestamp.desc()
        ).limit(12).all()

        rows = list(reversed(rows))
        timeseries[mname] = {
            "labels": [r.timestamp.strftime("%H:%M") for r in rows],
            "values": [round(r.avg_val, 2) for r in rows],
        }

    return {"snapshot": snapshot, "timeseries": timeseries}


@router.get("/", response_model=List[schemas.Metric])
def list_metrics(
    name: Optional[str] = Query(None),
    service_id: Optional[int] = Query(None),
    limit: int = 50,
    db: Session = Depends(session.get_db)
):
    query = db.query(models.Metric)
    if name:
        query = query.filter(models.Metric.name == name)
    if service_id:
        query = query.filter(models.Metric.service_id == service_id)
    return query.order_by(models.Metric.timestamp.desc()).limit(limit).all()


@router.post("/", response_model=schemas.Metric)
def record_metric(metric_in: schemas.MetricCreate, db: Session = Depends(session.get_db)):
    db_metric = crud.create_metric(db, metric_in)
    history = crud.get_metrics(db, name=metric_in.name, service_id=metric_in.service_id, limit=20)
    values = [h.value for h in history]
    if len(values) >= 10:
        anomalies = anomaly_detector.detect(values)
        if anomalies and anomalies[0]:
            pass  # Auto-incident creation hook
    return db_metric


@router.get("/anomalies")
def detect_anomalies(name: str, service_id: Optional[int] = None, db: Session = Depends(session.get_db)):
    metrics = crud.get_metrics(db, name=name, service_id=service_id, limit=100)
    values = [m.value for m in metrics]
    anomalies = anomaly_detector.detect(values)
    return [metrics[i] for i, is_anomaly in enumerate(anomalies) if is_anomaly]
