from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def reject_nul(value: str) -> str:
    # PostgreSQL text columns cannot store NUL; reject it as bad input instead of failing with a 500.
    if "\x00" in value:
        raise ValueError("must not contain NUL characters")
    return value


SafeStr = Annotated[str, AfterValidator(reject_nul)]


class TicketInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: SafeStr = Field(min_length=3, max_length=120)
    description: SafeStr = Field(default="", max_length=4000)
    category: Literal["network", "hardware", "software", "access", "other"] = "other"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    status: Literal["open", "in_progress", "resolved"] = "open"
    requester: SafeStr = Field(min_length=2, max_length=80)
    location: SafeStr = Field(min_length=2, max_length=80)
    assignee: SafeStr = Field(default="Unassigned", min_length=2, max_length=80)


class TicketOutput(TicketInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
