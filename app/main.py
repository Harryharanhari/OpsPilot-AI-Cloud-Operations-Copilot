from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import uvicorn

from .config import settings
from .database import session, crud, models
from .api import logs, incidents, chat, metrics, stats

# Initialize Database Tables
models.Base.metadata.create_all(bind=session.engine)

app = FastAPI(title=settings.PROJECT_NAME, description="AI Cloud Operations Copilot")

# Static Files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# API Routers
app.include_router(logs.router)
app.include_router(incidents.router)
app.include_router(chat.router)
app.include_router(metrics.router)
app.include_router(stats.router)


# ── Page Routes ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard",
        "active_page": "dashboard"
    })


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request, db: Session = Depends(session.get_db)):
    # Load services for the filter dropdown
    services = crud.get_services(db, limit=100)
    db_logs = db.query(models.Log).order_by(
        models.Log.timestamp.desc()
    ).limit(50).all()

    logs_data = []
    for log in db_logs:
        svc = db.query(models.Service).filter(models.Service.id == log.service_id).first()
        logs_data.append({
            "id": log.id,
            "timestamp": log.timestamp,
            "service_name": svc.name if svc else "unknown",
            "service_id": log.service_id,
            "level": log.level,
            "message": log.message,
            "severity_score": log.severity_score,
            "source": log.source,
        })

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "title": "System Logs",
        "active_page": "logs",
        "logs": logs_data,
        "services": services,
        "total": db.query(models.Log).count(),
    })


@app.get("/incidents", response_class=HTMLResponse)
async def incidents_page(request: Request, db: Session = Depends(session.get_db)):
    db_incidents = crud.get_incidents(db)
    return templates.TemplateResponse("incidents.html", {
        "request": request,
        "title": "Active Incidents",
        "active_page": "incidents",
        "incidents": db_incidents,
    })


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "title": "AI Copilot",
        "active_page": "chat"
    })


@app.get("/metrics", response_class=HTMLResponse)
async def metrics_page(request: Request, db: Session = Depends(session.get_db)):
    services = crud.get_services(db, limit=50)
    return templates.TemplateResponse("metrics.html", {
        "request": request,
        "title": "System Metrics",
        "active_page": "metrics",
        "services": services,
    })


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(session.get_db)):
    from sqlalchemy import func
    total_logs = db.query(func.count(models.Log.id)).scalar() or 0
    total_incidents = db.query(func.count(models.Incident.id)).scalar() or 0
    open_incidents = db.query(func.count(models.Incident.id)).filter(
        models.Incident.status == "OPEN"
    ).scalar() or 0
    resolved = db.query(func.count(models.Incident.id)).filter(
        models.Incident.status == "RESOLVED"
    ).scalar() or 0
    error_logs = db.query(func.count(models.Log.id)).filter(
        models.Log.level.in_(["ERROR", "CRITICAL"])
    ).scalar() or 0
    services = crud.get_services(db, limit=100)
    recent_incidents = crud.get_incidents(db, limit=10)

    return templates.TemplateResponse("reports.html", {
        "request": request,
        "title": "Operational Reports",
        "active_page": "reports",
        "stats": {
            "total_logs": total_logs,
            "total_incidents": total_incidents,
            "open_incidents": open_incidents,
            "resolved_incidents": resolved,
            "error_logs": error_logs,
            "total_services": len(services),
        },
        "incidents": recent_incidents,
        "services": services,
    })


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
