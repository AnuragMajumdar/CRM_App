from __future__ import annotations

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.interaction import (
    ChatRequest,
    ChatResponse,
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
)
from app.services.interaction_service import (
    create_interaction,
    get_interaction,
    update_interaction,
)
from app.agent.graph import agent

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------- Chat endpoint ----------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a user message to the LangGraph agent.
    Returns extracted fields and a reply to populate the form.
    """
    try:
        result = agent.invoke({
            "user_input": request.message,
            "current_form_state": request.current_form_state,
            "chat_history": request.chat_history,
            "intent": None,
            "extracted_fields": None,
            "ai_suggested_followups": None,
            "response": None,
        })

        intent = result.get("intent")
        tool_used = None
        if intent == "log":
            tool_used = "log_interaction"
        elif intent == "edit":
            tool_used = "edit_interaction"

        return ChatResponse(
            reply=result.get("response", "I processed your message."),
            tool_used=tool_used,
            extracted_fields=result.get("extracted_fields") or None,
            ai_suggested_followups=result.get("ai_suggested_followups"),
        )

    except Exception as e:
        logger.exception("Agent invocation failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ---------- CRUD endpoints ----------

@router.post("/interaction", response_model=InteractionResponse, status_code=201)
async def save_interaction(
    data: InteractionCreate, db: AsyncSession = Depends(get_db)
):
    """Save a finalized interaction to the database."""
    interaction = await create_interaction(db, data)
    return _to_response(interaction)


@router.get("/interaction/{interaction_id}", response_model=InteractionResponse)
async def read_interaction(
    interaction_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Retrieve a single interaction by ID."""
    interaction = await get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _to_response(interaction)


@router.put("/interaction/{interaction_id}", response_model=InteractionResponse)
async def modify_interaction(
    interaction_id: uuid.UUID,
    data: InteractionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update specific fields of an existing interaction."""
    interaction = await update_interaction(db, interaction_id, data)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return _to_response(interaction)


def _to_response(interaction) -> InteractionResponse:
    """Convert ORM model to response, handling time/date serialization."""
    return InteractionResponse(
        id=interaction.id,
        hcp_name=interaction.hcp_name,
        interaction_type=interaction.interaction_type,
        date=interaction.date.strftime("%Y-%m-%d") if interaction.date else None,
        time=interaction.time.strftime("%H:%M") if interaction.time else None,
        attendees=interaction.attendees,
        topics_discussed=interaction.topics_discussed,
        materials_shared=interaction.materials_shared,
        samples_distributed=interaction.samples_distributed,
        sentiment=interaction.sentiment,
        outcomes=interaction.outcomes,
        follow_up_actions=interaction.follow_up_actions,
        ai_suggested_followups=interaction.ai_suggested_followups,
        created_at=interaction.created_at,
    )
