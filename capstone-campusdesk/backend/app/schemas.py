from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TicketInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=4000)
    category: Literal["network", "hardware", "software", "access", "other"] = "other"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["open", "in_progress", "resolved"] = "open"
    requester: str = Field(min_length=2, max_length=80)
    location: str = Field(min_length=2, max_length=80)
    assignee: str = Field(default="Unassigned", min_length=2, max_length=80)


class TicketOutput(TicketInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
