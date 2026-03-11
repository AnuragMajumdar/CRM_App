import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatRequest(BaseModel):
    session_id: str
    message: str
    current_form_state: dict = Field(default_factory=dict)
    chat_history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    extracted_fields: Optional[dict] = None
    ai_suggested_followups: Optional[list[str]] = None
    followup_data: Optional[dict] = None
    hcp_history: Optional[list[dict]] = None


# ---------- Voice Note ----------

class VoiceNoteResponse(BaseModel):
    transcription: str
    reply: str
    extracted_fields: dict = Field(default_factory=dict)
    ai_suggested_followups: Optional[list[str]] = None


# ---------- Interaction CRUD ----------

class InteractionCreate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: str = "Meeting"
    date: Optional[str] = None       # accept "YYYY-MM-DD" string from frontend
    time: Optional[str] = None       # accept "HH:MM" string from frontend
    attendees: Optional[list[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[list[str]] = None
    samples_distributed: Optional[list[str]] = None
    sentiment: str = "Neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[list[str]] = None


class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[list[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[list[str]] = None
    samples_distributed: Optional[list[str]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[list[str]] = None


class InteractionResponse(BaseModel):
    id: uuid.UUID
    hcp_name: Optional[str] = None
    interaction_type: str
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[list[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[list[str]] = None
    samples_distributed: Optional[list[str]] = None
    sentiment: str
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[list[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
