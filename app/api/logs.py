import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import crud, schemas, session, models
from ..ai_engine.classifier import classifier
from ..ai_engine.summarizer import summarizer
from ..ai_engine.embeddings import embedder
from ..vector_store.faiss_index import vector_store

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/ingest", response_model=schemas.Log)
def ingest_log(log_in: schemas.LogIngest, db: Session = Depends(session.get_db)):
    db_service = crud.get_service_by_name(db, log_in.service_name)
    if not db_service:
        db_service = crud.create_service(db, schemas.ServiceCreate(name=log_in.service_name))

    ai_result = classifier.classify(log_in.message)

    log_data = schemas.LogCreate(
        service_id=db_service.id,
        level=ai_result["label"],
        message=log_in.message,
        source=log_in.source or "api"
    )
    db_log = crud.create_log(db, log_data)
    db_log.severity_score = ai_result["score"]

    embedding = embedder.embed(log_in.message)
    if embedding is not None:
        vector_store.add_logs(
            [{"id": db_log.id, "message": db_log.message, "service_name": log_in.service_name}],
            [embedding]
        )

    db.commit()
    db.refresh(db_log)
    return db_log


@router.get("/export")
def export_logs_csv(
    service_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    db: Session = Depends(session.get_db)
):
    """Download all logs as a CSV file."""
    query = db.query(models.Log, models.Service.name.label("service_name")).join(
        models.Service, models.Log.service_id == models.Service.id, isouter=True
    )
    if service_id:
        query = query.filter(models.Log.service_id == service_id)
    if level:
        query = query.filter(models.Log.level == level.upper())
    rows = query.order_by(models.Log.timestamp.desc()).limit(5000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Timestamp", "Service", "Level", "Message", "Severity Score", "Source"])
    for log, svc_name in rows:
        writer.writerow([
            log.id,
            log.timestamp.isoformat() if log.timestamp else "",
            svc_name or "",
            log.level,
            log.message,
            round(log.severity_score, 4) if log.severity_score else "",
            log.source or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=opspilot_logs.csv"}
    )


@router.get("/", response_model=List[schemas.LogWithService])
def list_logs(
    skip: int = 0,
    limit: int = 50,
    service_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    db: Session = Depends(session.get_db)
):
    query = db.query(models.Log)
    if service_id:
        query = query.filter(models.Log.service_id == service_id)
    if level and level.upper() != "ALL":
        query = query.filter(models.Log.level == level.upper())
    logs = query.order_by(models.Log.timestamp.desc()).offset(skip).limit(limit).all()

    result = []
    for log in logs:
        svc = db.query(models.Service).filter(models.Service.id == log.service_id).first()
        result.append(schemas.LogWithService(
            id=log.id,
            service_id=log.service_id,
            service_name=svc.name if svc else "unknown",
            level=log.level,
            message=log.message,
            source=log.source,
            timestamp=log.timestamp,
            severity_score=log.severity_score,
            processed=log.processed,
            summary=log.summary,
        ))
    return result


@router.get("/count")
def count_logs(
    service_id: Optional[int] = Query(None),
    level: Optional[str] = Query(None),
    db: Session = Depends(session.get_db)
):
    query = db.query(models.Log)
    if service_id:
        query = query.filter(models.Log.service_id == service_id)
    if level and level.upper() != "ALL":
        query = query.filter(models.Log.level == level.upper())
    return {"count": query.count()}


@router.post("/summarize")
def summarize_logs_endpoint(log_ids: List[int], db: Session = Depends(session.get_db)):
    logs = db.query(models.Log).filter(models.Log.id.in_(log_ids)).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")
    combined_text = " ".join([l.message for l in logs])
    summary = summarizer.summarize(combined_text)
    return {"summary": summary}
