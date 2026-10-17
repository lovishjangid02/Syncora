from services.project_service import ProjectService
from services.member_service import MemberService
from services.task_service import TaskService
from services.report_service import ReportService
from services.activity_service import ActivityService

# Singleton service instances
project_service = ProjectService()
member_service = MemberService()
task_service = TaskService()
report_service = ReportService()
activity_service = ActivityService()

__all__ = [
    "ProjectService", "project_service",
    "MemberService", "member_service",
    "TaskService", "task_service",
    "ReportService", "report_service",
    "ActivityService", "activity_service"
]
