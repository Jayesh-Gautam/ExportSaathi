"""
Action plan data models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .enums import TaskCategory


class Task(BaseModel):
    """Task in the action plan."""
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    category: TaskCategory = Field(..., description="Task category")
    completed: bool = Field(default=False, description="Whether task is completed")
    estimated_duration: Optional[str] = Field(None, description="Estimated duration")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_gst_lut",
                "title": "Apply for GST LUT",
                "description": "Submit Letter of Undertaking for GST exemption",
                "category": "documentation",
                "completed": False,
                "estimated_duration": "2-3 hours",
                "dependencies": []
            }
        }


class DayPlan(BaseModel):
    """Plan for a specific day."""
    day: int = Field(..., ge=1, le=7, description="Day number (1-7)")
    title: str = Field(..., description="Day title")
    tasks: List[Task] = Field(..., description="Tasks for the day")

    @field_validator('tasks')
    @classmethod
    def validate_tasks_not_empty(cls, v: List) -> List:
        """Ensure each day has at least one task."""
        if not v:
            raise ValueError('Each day must have at least one task')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "day": 1,
                "title": "Documentation Setup",
                "tasks": [
                    {
                        "id": "task_gst_lut",
                        "title": "Apply for GST LUT",
                        "description": "Submit Letter of Undertaking",
                        "category": "documentation",
                        "completed": False,
                        "estimated_duration": "2-3 hours",
                        "dependencies": []
                    }
                ]
            }
        }


class ActionPlan(BaseModel):
    """7-day action plan for export readiness."""
    days: List[DayPlan] = Field(..., description="Daily plans")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress percentage")

    @field_validator('days')
    @classmethod
    def validate_days_count(cls, v: List[DayPlan]) -> List[DayPlan]:
        """Validate that there are exactly 7 days."""
        if len(v) != 7:
            raise ValueError('Action plan must have exactly 7 days')
        # Validate day numbers are 1-7 and unique
        day_numbers = [day.day for day in v]
        if sorted(day_numbers) != list(range(1, 8)):
            raise ValueError('Days must be numbered 1-7 without duplicates')
        return v

    @field_validator('progress_percentage')
    @classmethod
    def validate_progress_calculation(cls, v: float, info) -> float:
        """Validate progress percentage matches completed tasks."""
        data = info.data
        if 'days' in data and data['days']:
            total_tasks = sum(len(day.tasks) for day in data['days'])
            if total_tasks > 0:
                completed_tasks = sum(
                    sum(1 for task in day.tasks if task.completed)
                    for day in data['days']
                )
                calculated_progress = (completed_tasks / total_tasks) * 100
                # Allow small tolerance for floating point
                if abs(v - calculated_progress) > 0.1:
                    raise ValueError(
                        f'Progress percentage ({v}) does not match calculated progress ({calculated_progress:.1f})'
                    )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "days": [
                    {
                        "day": 1,
                        "title": "Documentation Setup",
                        "tasks": [
                            {
                                "id": "task_1",
                                "title": "Apply for GST LUT",
                                "description": "Submit Letter of Undertaking",
                                "category": "documentation",
                                "completed": False,
                                "estimated_duration": "2-3 hours",
                                "dependencies": []
                            }
                        ]
                    }
                ],
                "progress_percentage": 0.0
            }
        }
