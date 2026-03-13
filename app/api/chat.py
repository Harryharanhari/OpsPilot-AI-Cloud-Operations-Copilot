from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..database import session, models
from ..ai_engine.embeddings import embedder
from ..vector_store.faiss_index import vector_store

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    context: list
    suggestions: Optional[List[str]] = []


# Rich rule-based response engine for when LLM isn't available
def _build_answer(query: str, context_logs: list, db: Session) -> str:
    q = query.lower()

    # --- Pattern matching for smart answers ---
    if any(k in q for k in ["error", "fail", "crash", "exception"]):
        errors = db.query(models.Log).filter(
            models.Log.level.in_(["ERROR", "CRITICAL"])
        ).order_by(models.Log.timestamp.desc()).limit(5).all()

        if errors:
            services = set()
            for e in errors:
                svc = db.query(models.Service).filter(models.Service.id == e.service_id).first()
                if svc:
                    services.add(svc.name)
            svc_list = ", ".join(services) if services else "unknown services"
            return (
                f"🔴 Found {len(errors)} recent errors across: **{svc_list}**.\n\n"
                f"Latest: `{errors[0].message[:150]}`\n\n"
                f"**Self-Healing Suggestions:**\n"
                f"• Check service health endpoints for {svc_list}\n"
                f"• Review resource constraints (CPU/memory limits)\n"
                f"• Inspect network connectivity and timeouts\n"
                f"• Consider rolling restart of affected pods"
            )

    if any(k in q for k in ["incident", "outage", "down", "alert"]):
        incidents = db.query(models.Incident).filter(
            models.Incident.status == "OPEN"
        ).order_by(models.Incident.created_at.desc()).limit(5).all()

        if incidents:
            inc_list = "\n".join([f"• **INC-{i.id}** [{i.severity}] {i.title}" for i in incidents])
            return (
                f"🚨 {len(incidents)} active incident(s) require attention:\n\n"
                f"{inc_list}\n\n"
                f"**Recommended Actions:**\n"
                f"• Acknowledge critical incidents immediately\n"
                f"• Assign on-call engineer\n"
                f"• Initiate incident runbook procedures"
            )
        return "✅ No active incidents right now. All systems appear operational."

    if any(k in q for k in ["warn", "warning", "slow", "timeout", "latency"]):
        warns = db.query(models.Log).filter(
            models.Log.level == "WARNING"
        ).order_by(models.Log.timestamp.desc()).limit(3).all()
        if warns:
            msgs = "\n".join([f"• `{w.message[:100]}`" for w in warns])
            return (
                f"⚠️ {db.query(models.Log).filter(models.Log.level == 'WARNING').count()} warnings detected.\n\n"
                f"Recent:\n{msgs}\n\n"
                f"**Suggestions:**\n"
                f"• Monitor affected services for escalation\n"
                f"• Check connection pool sizes and timeouts\n"
                f"• Review recent deployments for regressions"
            )

    if any(k in q for k in ["health", "status", "ok", "operational"]):
        total = db.query(models.Log).count()
        errors = db.query(models.Log).filter(models.Log.level.in_(["ERROR", "CRITICAL"])).count()
        health = max(0, round((1 - errors / total) * 100, 1)) if total > 0 else 100
        status = "🟢 Healthy" if health > 90 else ("🟡 Degraded" if health > 70 else "🔴 Critical")
        return (
            f"{status} — System Health: **{health}%**\n\n"
            f"• Total logs: {total:,}\n"
            f"• Error logs: {errors:,}\n"
            f"• Active incidents: {db.query(models.Incident).filter(models.Incident.status == 'OPEN').count()}\n"
            f"• Monitored services: {db.query(models.Service).count()}"
        )

    if any(k in q for k in ["cpu", "memory", "resource", "usage"]):
        return (
            "📊 **Resource Utilization Analysis**\n\n"
            "Check the **Metrics** page for real-time CPU and memory charts.\n\n"
            "**Self-Healing Suggestions:**\n"
            "• If CPU > 80%: scale out service replicas\n"
            "• If Memory > 85%: check for memory leaks, increase limits\n"
            "• Enable auto-scaling policies on the affected services"
        )

    # Fallback: use vector search context
    if context_logs:
        msgs = [l.get("message", "") for l in context_logs[:2]]
        services = list({l.get("service_name", "unknown") for l in context_logs})
        return (
            f"🔍 Found {len(context_logs)} semantically relevant log(s).\n\n"
            f"Related to: **{', '.join(services)}**\n\n"
            f"Top match: `{msgs[0][:150]}`\n\n"
            f"**Suggestions:**\n"
            f"• Review logs for `{services[0]}` service\n"
            f"• Check the Logs page with service filter applied\n"
            f"• Monitor for pattern recurrence"
        )

    return (
        "🤖 I can help with:\n\n"
        "• **Error analysis** — ask about errors, crashes\n"
        "• **Incident status** — ask about active incidents\n"
        "• **System health** — ask for overall status\n"
        "• **Performance** — ask about CPU, memory, latency\n\n"
        "Try: *\"Show me recent errors\"* or *\"Are there any active incidents?\"*"
    )


@router.post("/", response_model=ChatResponse)
def ask_ai(request: ChatRequest, db: Session = Depends(session.get_db)):
    # Semantic search for context
    context_logs = []
    try:
        embedding = embedder.embed(request.query)
        if embedding is not None:
            context_logs = vector_store.search(request.query, top_k=5)
    except Exception:
        pass

    answer = _build_answer(request.query, context_logs, db)

    suggestions = [
        "Show me recent errors",
        "Are there active incidents?",
        "What is the system health?",
        "Show CPU and memory usage",
        "Any warnings in the last hour?",
        "Suggest remediation for failures",
    ]

    return ChatResponse(answer=answer, context=context_logs, suggestions=suggestions)
