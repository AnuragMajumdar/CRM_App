from __future__ import annotations

import os
import uuid
import logging
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from groq import Groq

from app.db.database import get_db
from app.config import get_settings
from app.schemas.interaction import (
    ChatRequest,
    ChatResponse,
    InteractionCreate,
    InteractionUpdate,
    InteractionResponse,
    VoiceNoteResponse,
)
from app.schemas.followup import FollowupCreate, FollowupResponse
from app.services.interaction_service import (
    create_interaction,
    get_interaction,
    update_interaction,
)
from app.services.followup_service import (
    create_followup,
    get_followups_by_hcp,
    get_all_followups,
    get_hcp_interaction_history,
)
from app.agent.graph import agent

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ---------- Chat endpoint ----------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
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
        elif intent == "followup":
            tool_used = "schedule_followup"
        elif intent == "history":
            tool_used = "lookup_hcp_history"

        # --- Handle followup persistence ---
        followup_data = None
        if intent == "followup":
            fields = result.get("extracted_fields") or {}
            if fields.get("hcp_name") and fields.get("task"):
                followup_obj = await create_followup(
                    db,
                    FollowupCreate(
                        hcp_name=fields["hcp_name"],
                        task=fields["task"],
                        due_date=fields.get("due_date"),
                        followup_type=fields.get("followup_type", "Call"),
                        status=fields.get("status", "pending"),
                        notes=fields.get("notes"),
                    ),
                )
                followup_data = {
                    "id": str(followup_obj.id),
                    "hcp_name": followup_obj.hcp_name,
                    "task": followup_obj.task,
                    "due_date": followup_obj.due_date.strftime("%Y-%m-%d") if followup_obj.due_date else None,
                    "followup_type": followup_obj.followup_type,
                    "status": followup_obj.status,
                    "notes": followup_obj.notes,
                }

        # --- Handle history lookup ---
        hcp_history = None
        if intent == "history":
            fields = result.get("extracted_fields") or {}
            hcp_name = fields.get("hcp_name")
            if hcp_name:
                limit = fields.get("limit", 5)
                interactions = await get_hcp_interaction_history(db, hcp_name, limit)
                hcp_history = [
                    {
                        "id": str(i.id),
                        "hcp_name": i.hcp_name,
                        "interaction_type": i.interaction_type,
                        "date": i.date.strftime("%Y-%m-%d") if i.date else None,
                        "topics_discussed": i.topics_discussed,
                        "materials_shared": i.materials_shared,
                        "samples_distributed": i.samples_distributed,
                        "sentiment": i.sentiment,
                        "outcomes": i.outcomes,
                        "follow_up_actions": i.follow_up_actions,
                    }
                    for i in interactions
                ]

        return ChatResponse(
            reply=result.get("response", "I processed your message."),
            tool_used=tool_used,
            extracted_fields=result.get("extracted_fields") or None,
            ai_suggested_followups=result.get("ai_suggested_followups"),
            followup_data=followup_data,
            hcp_history=hcp_history,
        )

    except Exception as e:
        logger.exception("Agent invocation failed")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ---------- Voice Note endpoint ----------

@router.post("/voice-note", response_model=VoiceNoteResponse)
async def voice_note(audio_file: UploadFile = File(...)):
    """
    Accept an audio file, transcribe it via Groq Whisper,
    then pass the transcription through the LangGraph agent
    to extract structured interaction fields.
    """
    try:
        # Step 1: Save uploaded audio to a temp file
        suffix = os.path.splitext(audio_file.filename or "audio.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Step 2: Transcribe using Groq Whisper API
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        with open(tmp_path, "rb") as audio:
            transcription_response = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio,
                response_format="text",
            )

        # Clean up temp file
        os.unlink(tmp_path)

        transcribed_text = str(transcription_response).strip()
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio — empty result.")

        logger.info("Voice note transcribed: %s", transcribed_text[:200])

        # Step 3: Pass transcription to LangGraph agent with voice_note intent
        result = agent.invoke({
            "user_input": transcribed_text,
            "current_form_state": {},
            "chat_history": [],
            "intent": "voice_note",
            "extracted_fields": None,
            "ai_suggested_followups": None,
            "response": None,
        })

        return VoiceNoteResponse(
            transcription=transcribed_text,
            reply=result.get("response", "Voice note processed successfully."),
            extracted_fields=result.get("extracted_fields") or {},
            ai_suggested_followups=result.get("ai_suggested_followups"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Voice note processing failed")
        raise HTTPException(status_code=500, detail=f"Voice note error: {str(e)}")


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


# ---------- Followup endpoints ----------

@router.post("/followup", response_model=FollowupResponse, status_code=201)
async def save_followup(
    data: FollowupCreate, db: AsyncSession = Depends(get_db)
):
    """Manually create a followup task."""
    followup = await create_followup(db, data)
    return _followup_to_response(followup)


@router.get("/followups", response_model=list[FollowupResponse])
async def list_followups(
    hcp_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List followups, optionally filtered by HCP name and/or status."""
    if hcp_name:
        followups = await get_followups_by_hcp(db, hcp_name)
    else:
        followups = await get_all_followups(db, status=status)

    if hcp_name and status:
        followups = [f for f in followups if f.status == status]

    return [_followup_to_response(f) for f in followups]


@router.get("/hcp-history")
async def hcp_history(
    hcp_name: str = Query(...),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Query interaction history for a specific HCP."""
    interactions = await get_hcp_interaction_history(db, hcp_name, limit)
    return [
        {
            "id": str(i.id),
            "hcp_name": i.hcp_name,
            "interaction_type": i.interaction_type,
            "date": i.date.strftime("%Y-%m-%d") if i.date else None,
            "time": i.time.strftime("%H:%M") if i.time else None,
            "topics_discussed": i.topics_discussed,
            "materials_shared": i.materials_shared,
            "samples_distributed": i.samples_distributed,
            "sentiment": i.sentiment,
            "outcomes": i.outcomes,
            "follow_up_actions": i.follow_up_actions,
            "created_at": i.created_at.isoformat(),
        }
        for i in interactions
    ]


def _followup_to_response(followup) -> FollowupResponse:
    """Convert Followup ORM model to response."""
    return FollowupResponse(
        id=followup.id,
        hcp_name=followup.hcp_name,
        task=followup.task,
        due_date=followup.due_date.strftime("%Y-%m-%d") if followup.due_date else None,
        followup_type=followup.followup_type,
        status=followup.status,
        linked_interaction_id=followup.linked_interaction_id,
        notes=followup.notes,
        created_at=followup.created_at,
    )
