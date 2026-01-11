from sqladmin import ModelView
from app.models import User, TaskStatus, SupplyChainReport


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""
    column_list = [User.id, User.username, User.email, User.is_active, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.created_at]
    column_default_sort = [(User.created_at, True)]
    
    # Don't show password hash in forms
    form_excluded_columns = [User.hashed_password]
    column_details_exclude_list = [User.hashed_password]
    
    # Metadata
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"


class TaskStatusAdmin(ModelView, model=TaskStatus):
    """Admin view for TaskStatus model"""
    column_list = [
        TaskStatus.id,
        TaskStatus.task_id,
        TaskStatus.industry,
        TaskStatus.status,
        TaskStatus.progress,
        TaskStatus.task_type,
        TaskStatus.created_at
    ]
    column_searchable_list = [TaskStatus.industry]
    column_sortable_list = [
        TaskStatus.id,
        TaskStatus.status,
        TaskStatus.progress,
        TaskStatus.created_at
    ]
    column_default_sort = [(TaskStatus.created_at, True)]
    column_filters = [TaskStatus.status, TaskStatus.task_type]
    
    # Metadata
    name = "Task"
    name_plural = "Tasks"
    icon = "fa-solid fa-tasks"


class ReportAdmin(ModelView, model=SupplyChainReport):
    """Admin view for SupplyChainReport model"""
    column_list = [
        SupplyChainReport.id,
        SupplyChainReport.industry,
        SupplyChainReport.fragility_score,
        SupplyChainReport.created_at
    ]
    column_searchable_list = [SupplyChainReport.industry]
    column_sortable_list = [
        SupplyChainReport.id,
        SupplyChainReport.fragility_score,
        SupplyChainReport.created_at
    ]
    column_default_sort = [(SupplyChainReport.created_at, True)]
    column_details_exclude_list = [SupplyChainReport.critical_alerts]
    
    # Metadata
    name = "Report"
    name_plural = "Reports"
    icon = "fa-solid fa-file-alt"
