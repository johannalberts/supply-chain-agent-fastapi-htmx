from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON


class TaskStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskTypeEnum(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    RETRY = "RETRY"


# User Model
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Supply Chain Report Model
class SupplyChainReport(SQLModel, table=True):
    __tablename__ = "supply_chain_reports"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    industry: str = Field(index=True)
    fragility_score: int
    executive_summary: str
    critical_alerts: List[str] = Field(default=[], sa_column=Column(JSON))
    risk_metrics: List[dict] = Field(default=[], sa_column=Column(JSON))
    sources: List[dict] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to task status
    task_status: Optional["TaskStatus"] = Relationship(back_populates="report")


# Task Status Model
class TaskStatus(SQLModel, table=True):
    __tablename__ = "task_statuses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: UUID = Field(default_factory=uuid4, unique=True, index=True)
    task_type: TaskTypeEnum = Field(default=TaskTypeEnum.MANUAL)
    industry: str = Field(index=True)
    
    status: TaskStatusEnum = Field(default=TaskStatusEnum.PENDING, index=True)
    progress: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)
    
    # Foreign key to report
    report_id: Optional[int] = Field(default=None, foreign_key="supply_chain_reports.id")
    report: Optional[SupplyChainReport] = Relationship(back_populates="task_status")
    
    @property
    def is_completed(self) -> bool:
        return self.status in [
            TaskStatusEnum.COMPLETED,
            TaskStatusEnum.FAILED,
            TaskStatusEnum.CANCELLED
        ]
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return None
