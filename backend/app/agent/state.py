from __future__ import annotations

from typing import TypedDict, Optional


class AgentState(TypedDict):
    user_input: str
    current_form_state: dict
    chat_history: list[dict]        # [{"role": "user"|"assistant", "content": "..."}]
    intent: Optional[str]           # "log" | "edit" | "general"
    extracted_fields: Optional[dict]
    ai_suggested_followups: Optional[list[str]]
    response: Optional[str]
