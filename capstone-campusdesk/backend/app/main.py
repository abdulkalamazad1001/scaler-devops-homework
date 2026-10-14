import logging
import time
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Ticket
from .schemas import TicketInput, TicketOutput

app = FastAPI(title="CampusDesk API", version="1.0.0")
requests = Counter("campusdesk_http_requests_total", "HTTP requests", ["method", "route", "status"])
latency = Histogram("campusdesk_http_request_duration_seconds", "HTTP latency", ["method", "route"])
logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def observe(request, call_next):
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        # Unhandled exceptions must count toward error-rate alerts as well.
        route = request.scope.get("route")
        path = route.path if route else "unmatched"
        if path != "/metrics":
            requests.labels(request.method, path, str(status)).inc()
            latency.labels(request.method, path).observe(time.perf_counter() - started)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "campusdesk"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1 FROM tickets LIMIT 1"))
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        raise HTTPException(503, "Database unavailable or migrations pending") from None
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Ticket.status, func.count()).group_by(Ticket.status)).all())
    urgent = db.scalar(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.priority == "urgent", Ticket.status != "resolved")
    )
    return {
        "total": sum(counts.values()),
        "open": counts.get("open", 0),
        "in_progress": counts.get("in_progress", 0),
        "resolved": counts.get("resolved", 0),
        "urgent": urgent,
    }


@app.get("/api/tickets", response_model=list[TicketOutput])
def list_tickets(
    status: Literal["open", "in_progress", "resolved"] | None = None,
    q: str = Query(default="", max_length=120),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(Ticket)
    if status:
        query = query.where(Ticket.status == status)
    if q:
        query = query.where(
            or_(
                Ticket.title.icontains(q, autoescape=True),
                Ticket.requester.icontains(q, autoescape=True),
                Ticket.location.icontains(q, autoescape=True),
            )
        )
    return db.scalars(
        query.order_by(Ticket.created_at.desc(), Ticket.id.desc()).offset(offset).limit(limit)
    ).all()


def find_ticket(ticket_id: int, db: Session) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    return ticket


@app.get("/api/tickets/{ticket_id}", response_model=TicketOutput)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return find_ticket(ticket_id, db)


@app.post("/api/tickets", response_model=TicketOutput, status_code=201)
def create_ticket(payload: TicketInput, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.put("/api/tickets/{ticket_id}", response_model=TicketOutput)
def update_ticket(ticket_id: int, payload: TicketInput, db: Session = Depends(get_db)):
    ticket = find_ticket(ticket_id, db)
    for key, value in payload.model_dump().items():
        setattr(ticket, key, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.delete("/api/tickets/{ticket_id}", status_code=204)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    db.delete(find_ticket(ticket_id, db))
    db.commit()
    return Response(status_code=204)
