import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import crud, schemas, session, models

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("/export")
def export_incidents_csv(db: Session = Depends(session.get_db)):
    """Download all incidents as a CSV file."""
    incidents = db.query(models.Incident).order_by(models.Incident.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Severity", "Status", "Created At", "Updated At", "Description", "Root Cause", "Remediation"])
    for inc in incidents:
        writer.writerow([
            inc.id, inc.title, inc.severity, inc.status,
            inc.created_at.isoformat() if inc.created_at else "",
            inc.updated_at.isoformat() if inc.updated_at else "",
            inc.description or "",
            inc.root_cause or "",
            inc.remediation_steps or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=opspilot_incidents.csv"}
    )


@router.get("/", response_model=List[schemas.Incident])
def list_incidents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(session.get_db)
):
    query = db.query(models.Incident)
    if status and status.upper() != "ALL":
        query = query.filter(models.Incident.status == status.upper())
    if severity and severity.upper() != "ALL":
        query = query.filter(models.Incident.severity == severity.upper())
    return query.order_by(models.Incident.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.Incident)
def create_incident(incident_in: schemas.IncidentCreate, db: Session = Depends(session.get_db)):
    return crud.create_incident(db, incident_in)


@router.get("/{incident_id}", response_model=schemas.Incident)
def get_incident(incident_id: int, db: Session = Depends(session.get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=schemas.Incident)
def update_incident_status(
    incident_id: int,
    status: str = Query(...),
    db: Session = Depends(session.get_db)
):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return crud.update_incident(db, incident_id, {"status": status.upper()})


@router.delete("/{incident_id}")
def delete_incident(incident_id: int, db: Session = Depends(session.get_db)):
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(incident)
    db.commit()
    return {"message": "Deleted"}
