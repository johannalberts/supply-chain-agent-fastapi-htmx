from uuid import uuid4
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.auth import require_auth
from app.models import TaskStatus, SupplyChainReport, TaskStatusEnum, TaskTypeEnum
from app.tasks import run_research_task

router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory="app/templates")


@router.get("/tasks", response_class=HTMLResponse)
async def get_tasks(
    request: Request,
    session: Session = Depends(get_session),
    status: Optional[str] = None,
    limit: int = 100
):
    """Get list of tasks (HTMX endpoint)"""
    require_auth(request, session)
    
    # Build query
    statement = select(TaskStatus).order_by(TaskStatus.created_at.desc()).limit(limit)
    
    if status:
        statement = statement.where(TaskStatus.status == TaskStatusEnum(status))
    
    tasks = session.exec(statement).all()
    
    # Format tasks for template
    formatted_tasks = []
    for task in tasks:
        formatted_tasks.append({
            "task_id": str(task.task_id),
            "industry": task.industry,
            "status": task.status.value,
            "progress": task.progress,
            "created_at": task.created_at.strftime("%b %d, %Y %I:%M %p"),
            "error_message": task.error_message,
            "report_id": task.report_id
        })
    
    return templates.TemplateResponse(
        "components/task_list.html",
        {"request": request, "tasks": formatted_tasks}
    )


@router.post("/research")
async def create_research(
    request: Request,
    industry: str = Form(...),
    session: Session = Depends(get_session)
):
    """Create a new research task (HTMX endpoint)"""
    require_auth(request, session)
    
    # Create task status record
    task_id = uuid4()
    task_status = TaskStatus(
        task_id=task_id,
        task_type=TaskTypeEnum.MANUAL,
        industry=industry,
        status=TaskStatusEnum.PENDING
    )
    
    session.add(task_status)
    session.commit()
    
    # Queue the Celery task
    run_research_task.delay(str(task_id), industry)
    
    return {"task_id": str(task_id), "industry": industry, "status": "PENDING"}


@router.get("/report/{report_id}", response_class=HTMLResponse)
async def get_report(
    report_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    """Get report details (HTMX endpoint)"""
    require_auth(request, session)
    
    report = session.get(SupplyChainReport, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Format report for template
    formatted_report = {
        "id": report.id,
        "industry": report.industry,
        "fragility_score": report.fragility_score,
        "executive_summary": report.executive_summary,
        "critical_alerts": report.critical_alerts,
        "risk_metrics": report.risk_metrics,
        "sources": report.sources,
        "created_at": report.created_at.strftime("%B %d, %Y at %I:%M %p")
    }
    
    return templates.TemplateResponse(
        "components/report_detail.html",
        {"request": request, "report": formatted_report}
    )


@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    request: Request,
    session: Session = Depends(get_session)
):
    """Get task status (for polling)"""
    require_auth(request, session)
    
    statement = select(TaskStatus).where(TaskStatus.task_id == task_id)
    task = session.exec(statement).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": str(task.task_id),
        "status": task.status.value,
        "progress": task.progress,
        "report_id": task.report_id
    }
