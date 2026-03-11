import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FollowupCreate(BaseModel):
    hcp_name: str
    task: str
    due_date: Optional[str] = None      # "YYYY-MM-DD"
    followup_type: str = "Call"          # Meeting | Call | Email
    status: str = "pending"             # pending | completed
    linked_interaction_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class FollowupResponse(BaseModel):
    id: uuid.UUID
    hcp_name: str
    task: str
    due_date: Optional[str] = None
    followup_type: str
    status: str
    linked_interaction_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
