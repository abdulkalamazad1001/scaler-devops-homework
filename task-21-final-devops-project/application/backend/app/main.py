import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .logging_config import setup_logging
from .models import Task
from .schemas import StatsOut, TaskCreate, TaskOut, TaskUpdate

setup_logging(settings.log_level)
log = logging.getLogger("taskboard")

TASKS_CREATED = Counter("taskboard_tasks_created_total", "Tasks created through the API.")
QUIET_PATHS = {"/health", "/ready", "/metrics"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    # In containers Alembic creates the schema before Uvicorn starts.
    # Tests set CREATE_TABLES_ON_STARTUP=true to use a throwaway SQLite file.
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    log.info("startup", extra={"fields": {"version": settings.app_version, "env": settings.app_env}})
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, endpoint="/metrics")


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path not in QUIET_PATHS or response.status_code >= 400:
        level = logging.ERROR if response.status_code >= 500 else logging.INFO
        log.log(level, "request", extra={"fields": {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        }})
    return response


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness: the process is running and can answer HTTP."""
    return {"status": "UP"}


@app.get("/ready")
def ready(response: Response, db: Session = Depends(get_db)):
    """Readiness: the database is reachable, so requests can be served."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        log.exception("readiness check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "NOT_READY"}
    return {"status": "READY"}


@app.get("/version")
def version():
    return {"version": settings.app_version, "env": settings.app_env}


@app.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return list(db.scalars(select(Task).order_by(Task.id.desc())))


@app.get("/api/tasks/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all()
    counts = {row_status: count for row_status, count in rows}
    return StatsOut(
        total=sum(counts.values()),
        todo=counts.get("TODO", 0),
        inProgress=counts.get("IN_PROGRESS", 0),
        done=counts.get("DONE", 0),
    )


@app.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    TASKS_CREATED.inc()
    return task


@app.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
