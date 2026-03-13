from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import session, models

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/")
def get_stats(db: Session = Depends(session.get_db)):
    total_logs = db.query(func.count(models.Log.id)).scalar() or 0
    active_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.status == "OPEN"
    ).scalar() or 0
    total_services = db.query(func.count(models.Service.id)).scalar() or 0
    error_logs = db.query(func.count(models.Log.id)).filter(
        models.Log.level.in_(["ERROR", "CRITICAL"])
    ).scalar() or 0
    warn_logs = db.query(func.count(models.Log.id)).filter(
        models.Log.level == "WARNING"
    ).scalar() or 0
    info_logs = db.query(func.count(models.Log.id)).filter(
        models.Log.level == "INFO"
    ).scalar() or 0

    health = 100.0
    if total_logs > 0:
        error_ratio = error_logs / total_logs
        warn_ratio = warn_logs / total_logs
        health = max(0.0, round((1 - error_ratio * 0.8 - warn_ratio * 0.2) * 100, 1))

    # Recent logs (last 20)
    recent_logs = db.query(models.Log).order_by(
        models.Log.timestamp.desc()
    ).limit(20).all()
    recent_data = []
    for log in recent_logs:
        svc = db.query(models.Service).filter(models.Service.id == log.service_id).first()
        recent_data.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "service": svc.name if svc else "unknown",
            "level": log.level,
            "message": log.message[:120],
            "severity_score": log.severity_score,
        })

    # ALL services with their status and recent log counts
    services = db.query(models.Service).order_by(models.Service.name).all()
    services_data = []
    for svc in services:
        log_count = db.query(func.count(models.Log.id)).filter(
            models.Log.service_id == svc.id
        ).scalar() or 0
        error_count = db.query(func.count(models.Log.id)).filter(
            models.Log.service_id == svc.id,
            models.Log.level.in_(["ERROR", "CRITICAL"])
        ).scalar() or 0
        services_data.append({
            "id": svc.id,
            "name": svc.name,
            "status": svc.status,
            "log_count": log_count,
            "error_count": error_count,
        })

    # Active incidents list
    open_incidents = db.query(models.Incident).filter(
        models.Incident.status == "OPEN"
    ).order_by(models.Incident.created_at.desc()).limit(5).all()
    incidents_data = [{
        "id": inc.id,
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
    } for inc in open_incidents]

    return {
        "total_logs": total_logs,
        "active_incidents": active_incidents,
        "total_services": total_services,
        "error_logs": error_logs,
        "warn_logs": warn_logs,
        "info_logs": info_logs,
        "system_health": health,
        "recent_logs": recent_data,
        "services": services_data,
        "open_incidents": incidents_data,
    }
