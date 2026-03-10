"""
LangGraph node functions. Each node takes AgentState and returns a partial state update.
"""

from __future__ import annotations

import json
import logging

from groq import Groq

from app.config import get_settings
from app.agent.state import AgentState
from app.agent.prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    LOG_EXTRACTION_PROMPT,
    EDIT_EXTRACTION_PROMPT,
    FOLLOWUP_SUGGESTION_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)
from app.agent.tools import log_interaction, edit_interaction

logger = logging.getLogger(__name__)

settings = get_settings()
groq_client = Groq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"  # gemma2-9b-it was decommissioned by Groq; this is the official replacement


def _call_groq(prompt: str, temperature: float = 0.0) -> str:
    """Make a chat completion call to Groq."""
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (code fences)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
        logger.error("Failed to parse JSON from LLM response: %s", text)
        return {"intent": "general", "extracted_fields": {}}


def _parse_json_array(text: str) -> list[str]:
    """Extract a JSON array from LLM response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, list):
            return [str(item) for item in result]
    except json.JSONDecodeError:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start != -1 and end > start:
            try:
                result = json.loads(cleaned[start:end])
                if isinstance(result, list):
                    return [str(item) for item in result]
            except json.JSONDecodeError:
                pass
    logger.error("Failed to parse JSON array from LLM response: %s", text)
    return []


def _format_chat_history(chat_history: list[dict]) -> str:
    if not chat_history:
        return "(no prior messages)"
    lines = []
    for msg in chat_history[-6:]:  # last 6 messages for context
        role = msg.get("role", "user")
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


# ---- Node: parse_input ----

def parse_input(state: AgentState) -> dict:
    """Classify intent and extract fields from user input."""
    chat_history_str = _format_chat_history(state.get("chat_history", []))
    current_form = state.get("current_form_state", {})
    user_input = state["user_input"]

    # Step 1: Classify intent
    intent_prompt = INTENT_CLASSIFICATION_PROMPT.format(
        current_form_state=json.dumps(current_form, indent=2),
        chat_history=chat_history_str,
        user_input=user_input,
    )
    intent_raw = _call_groq(intent_prompt, temperature=0.0).strip().lower()

    # Normalize intent
    if "log" in intent_raw:
        intent = "log"
    elif "edit" in intent_raw:
        intent = "edit"
    else:
        intent = "general"

    # Step 2: Extract fields (only for log/edit intents)
    extracted = {}
    if intent == "log":
        extract_prompt = LOG_EXTRACTION_PROMPT.format(
            chat_history=chat_history_str,
            user_input=user_input,
        )
        raw = _call_groq(extract_prompt, temperature=0.0)
        extracted = _parse_json(raw)
    elif intent == "edit":
        extract_prompt = EDIT_EXTRACTION_PROMPT.format(
            current_form_state=json.dumps(current_form, indent=2),
            chat_history=chat_history_str,
            user_input=user_input,
        )
        raw = _call_groq(extract_prompt, temperature=0.0)
        extracted = _parse_json(raw)

    return {
        "intent": intent,
        "extracted_fields": extracted,
    }


# ---- Node: handle_log ----

def handle_log(state: AgentState) -> dict:
    """Run the log_interaction tool and generate follow-up suggestions."""
    raw_fields = state.get("extracted_fields", {})
    normalized = log_interaction(raw_fields)

    # Generate AI follow-up suggestions
    interaction_summary = json.dumps(normalized, indent=2)
    followup_prompt = FOLLOWUP_SUGGESTION_PROMPT.format(
        interaction_details=interaction_summary
    )
    followup_raw = _call_groq(followup_prompt, temperature=0.3)
    followups = _parse_json_array(followup_raw)

    return {
        "extracted_fields": normalized,
        "ai_suggested_followups": followups if followups else None,
    }


# ---- Node: handle_edit ----

def handle_edit(state: AgentState) -> dict:
    """Run the edit_interaction tool — only update changed fields."""
    raw_fields = state.get("extracted_fields", {})
    current = state.get("current_form_state", {})
    normalized = edit_interaction(raw_fields, current)

    return {
        "extracted_fields": normalized,
        "ai_suggested_followups": None,
    }


# ---- Node: respond ----

def respond(state: AgentState) -> dict:
    """Generate a natural language confirmation for the user."""
    intent = state.get("intent", "general")
    extracted = state.get("extracted_fields", {})
    followups = state.get("ai_suggested_followups")

    if intent == "general":
        # For general queries, just have a helpful conversation
        history_str = _format_chat_history(state.get("chat_history", []))
        prompt = (
            f"You are a helpful AI assistant for a pharmaceutical CRM. "
            f"Chat history:\n{history_str}\n\n"
            f"User message: {state['user_input']}\n\n"
            f"Respond helpfully and concisely."
        )
        reply = _call_groq(prompt, temperature=0.5)
        return {"response": reply}

    prompt = RESPONSE_GENERATION_PROMPT.format(
        intent=intent,
        intent_verb="logged" if intent == "log" else "updated",
        extracted_fields=json.dumps(extracted, indent=2),
        ai_suggested_followups=json.dumps(followups) if followups else "None",
    )
    reply = _call_groq(prompt, temperature=0.5)
    return {"response": reply}
