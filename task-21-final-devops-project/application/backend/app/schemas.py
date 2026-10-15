from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["TODO", "IN_PROGRESS", "DONE"]
Priority = Literal["LOW", "MEDIUM", "HIGH"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Priority = "MEDIUM"
    status: Status = "TODO"
    assignee: str = Field(default="Unassigned", max_length=120)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: Priority | None = None
    status: Status | None = None
    assignee: str | None = Field(default=None, max_length=120)

    @field_validator("title", "description", "priority", "status", "assignee", mode="before")
    @classmethod
    def supplied_fields_not_null(cls, value):
        # Omitted fields are allowed; explicitly clearing non-null database columns is not.
        if value is None:
            raise ValueError("field must not be null")
        return value

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class TaskOut(TaskCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    total: int
    todo: int
    inProgress: int
    done: int
