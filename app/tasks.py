from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "supply_chain_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'daily-supply-chain-research': {
        'task': 'app.tasks.scheduled_research_task',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def run_research_task(self, task_id: str, industry: str):
    """
    Celery task for running supply chain research asynchronously
    
    Args:
        task_id: UUID string of the TaskStatus record
        industry: Industry to research
    """
    from datetime import datetime
    from sqlmodel import Session, select
    from app.database import engine
    from app.models import TaskStatus, SupplyChainReport, TaskStatusEnum
    from app.agent import supply_chain_app
    
    try:
        with Session(engine) as session:
            # Get task status
            statement = select(TaskStatus).where(TaskStatus.task_id == task_id)
            task_status = session.exec(statement).first()
            
            if not task_status:
                return {'task_id': task_id, 'status': 'CANCELLED', 'error': 'Task not found'}
            
            # Update to processing
            task_status.status = TaskStatusEnum.PROCESSING
            task_status.started_at = datetime.utcnow()
            task_status.progress = 10
            session.add(task_status)
            session.commit()
            
            # Update progress
            task_status.progress = 25
            session.add(task_status)
            session.commit()
            
            # Initial state for LangGraph
            initial_state = {
                "industry": industry,
                "raw_data": [],
                "sources": [],
                "risk_report": "",
                "critical_alerts": [],
                "fragility_score": 0,
                "risk_metrics": []
            }
            
            task_status.progress = 50
            session.add(task_status)
            session.commit()
            
            # Run the agent
            final_state = supply_chain_app.invoke(initial_state)
            
            task_status.progress = 90
            session.add(task_status)
            session.commit()
            
            # Create report
            report = SupplyChainReport(
                industry=industry,
                fragility_score=final_state["fragility_score"],
                executive_summary=final_state["risk_report"],
                critical_alerts=final_state["critical_alerts"],
                risk_metrics=final_state["risk_metrics"],
                sources=final_state.get("sources", [])
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            
            # Update task status
            task_status.status = TaskStatusEnum.COMPLETED
            task_status.progress = 100
            task_status.completed_at = datetime.utcnow()
            task_status.report_id = report.id
            session.add(task_status)
            session.commit()
            
            return {
                'task_id': task_id,
                'status': 'COMPLETED',
                'report_id': report.id,
                'industry': industry
            }
            
    except Exception as exc:
        # Update task to failed
        try:
            with Session(engine) as session:
                statement = select(TaskStatus).where(TaskStatus.task_id == task_id)
                task_status = session.exec(statement).first()
                if task_status:
                    task_status.status = TaskStatusEnum.FAILED
                    task_status.error_message = str(exc)
                    task_status.completed_at = datetime.utcnow()
                    session.add(task_status)
                    session.commit()
        except:
            pass
        raise


@celery_app.task
def scheduled_research_task():
    """Scheduled task to run research for key industries"""
    from uuid import uuid4
    from datetime import datetime
    from sqlmodel import Session, select
    from app.database import engine
    from app.models import TaskStatus, TaskTypeEnum, TaskStatusEnum
    
    industries = ["Technology", "Automotive", "Pharmaceuticals"]
    
    with Session(engine) as session:
        for industry in industries:
            task_id = str(uuid4())
            task_status = TaskStatus(
                task_id=task_id,
                task_type=TaskTypeEnum.SCHEDULED,
                industry=industry,
                status=TaskStatusEnum.PENDING
            )
            session.add(task_status)
            session.commit()
            
            # Queue the research task
            run_research_task.delay(task_id, industry)
    
    return f"Scheduled research for {len(industries)} industries"
