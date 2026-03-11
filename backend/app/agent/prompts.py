# ---------------------------------------------------------------------------
#  Prompt 0 — Intent classification (lightweight, runs first)
# ---------------------------------------------------------------------------

INTENT_CLASSIFICATION_PROMPT = """\
You are an AI assistant for a pharmaceutical CRM system.
A field representative is chatting about an HCP (Healthcare Professional) interaction.

Classify the user's message into exactly ONE intent:

"log"     — The user is describing a NEW interaction or providing details for the first time.
"edit"    — The user is CORRECTING or UPDATING specific fields that are already filled in.
"general" — The user is asking a question, greeting, or chatting about something unrelated.

Rules:
- If the current form is mostly empty and the user describes an interaction → "log"
- If the current form already has data and the user says words like "actually", "correction", "change", "update", "sorry", "wrong" → "edit"
- If the message does not describe any interaction details → "general"

Current form state:
{current_form_state}

Chat history:
{chat_history}

User message: {user_input}

Respond with ONLY one word: log, edit, or general
No punctuation. No explanation. Just the single word."""


# ---------------------------------------------------------------------------
#  Prompt 1 — log_interaction extraction
# ---------------------------------------------------------------------------

LOG_EXTRACTION_PROMPT = """\
You are a structured-data extraction engine for a pharmaceutical CRM.

A field representative described an HCP interaction. Extract EVERY mentioned detail into the JSON fields below. Only include a field if the user explicitly stated or clearly implied it. Never guess.

Extractable fields (include only those mentioned):

| Field                | Type            | Allowed values / format                     |
|----------------------|-----------------|---------------------------------------------|
| hcp_name             | string          | Full name of the doctor or HCP              |
| interaction_type     | string          | "Meeting" or "Call" or "Email" or "Conference" |
| date                 | string          | YYYY-MM-DD — use "today" if they say "today" |
| time                 | string          | HH:MM in 24-hour format                     |
| attendees            | list of strings | Names of other people who attended           |
| topics_discussed     | string          | Summary of discussion topics                 |
| materials_shared     | list of strings | Brochures, PDFs, documents shared            |
| samples_distributed  | list of strings | Drug samples given                           |
| sentiment            | string          | "Positive" or "Neutral" or "Negative"        |
| outcomes             | string          | Agreements, decisions, results               |
| follow_up_actions    | string          | Next steps the rep should take               |

Chat history:
{chat_history}

User message: {user_input}

Return ONLY a valid JSON object with the extracted fields. No markdown, no explanation, no extra text.

Example input:  "Today I met Dr Smith and discussed product X efficacy. Sentiment was positive and I shared brochures."
Example output: {{"hcp_name":"Dr Smith","date":"today","topics_discussed":"Product X efficacy","sentiment":"Positive","materials_shared":["brochures"]}}

Now extract from the user message above:"""


# ---------------------------------------------------------------------------
#  Prompt 2 — edit_interaction correction extraction
# ---------------------------------------------------------------------------

EDIT_EXTRACTION_PROMPT = """\
You are a structured-data correction engine for a pharmaceutical CRM.

The form already has data. The user wants to CORRECT or UPDATE specific fields.
Extract ONLY the fields the user explicitly wants to change. Do NOT include unchanged fields.

Current form state:
{current_form_state}

Extractable fields (include ONLY those the user wants to change):

| Field                | Type            | Allowed values / format                     |
|----------------------|-----------------|---------------------------------------------|
| hcp_name             | string          | Full name of the doctor or HCP              |
| interaction_type     | string          | "Meeting" or "Call" or "Email" or "Conference" |
| date                 | string          | YYYY-MM-DD                                   |
| time                 | string          | HH:MM in 24-hour format                     |
| attendees            | list of strings | Names of other people who attended           |
| topics_discussed     | string          | Summary of discussion topics                 |
| materials_shared     | list of strings | Brochures, PDFs, documents shared            |
| samples_distributed  | list of strings | Drug samples given                           |
| sentiment            | string          | "Positive" or "Neutral" or "Negative"        |
| outcomes             | string          | Agreements, decisions, results               |
| follow_up_actions    | string          | Next steps the rep should take               |

Chat history:
{chat_history}

User message: {user_input}

Return ONLY a valid JSON object containing the changed fields. No markdown, no explanation, no extra text.
If the user changes 2 fields, return only those 2 fields. Do NOT copy the example output — extract from the actual user message.

Example input:  "Change the sentiment to positive and add follow up: send results by email."
Example output: {{"sentiment":"Positive","follow_up_actions":"send results by email"}}

Now extract ONLY the corrections from the user message above:"""


# ---------------------------------------------------------------------------
#  Follow-up suggestion prompt
# ---------------------------------------------------------------------------

FOLLOWUP_SUGGESTION_PROMPT = """\
You are an AI assistant for a pharmaceutical CRM.

Based on the HCP interaction details below, suggest 2-3 specific, actionable follow-up actions that the field representative should take.

Interaction details:
{interaction_details}

Return ONLY a JSON array of short action strings. No markdown, no explanation.

Example: ["Schedule follow-up meeting in 2 weeks","Send OncoBoost Phase III PDF","Add Dr. Sharma to advisory board invite list"]"""


# ---------------------------------------------------------------------------
#  Response generation prompt
# ---------------------------------------------------------------------------

VOICE_NOTE_EXTRACTION_PROMPT = """\
You are a structured-data extraction engine for a pharmaceutical CRM.

A field representative recorded a voice note describing an HCP interaction.
Below is the transcribed text. Extract ALL mentioned details into JSON.

Fields to extract (include only those mentioned, set missing fields to null):

| Field                | Type            | Allowed values / format                     |
|----------------------|-----------------|---------------------------------------------|
| hcp_name             | string          | Full name of the doctor or HCP              |
| interaction_type     | string          | "Meeting" or "Call" or "Email" or "Conference" |
| date                 | string          | YYYY-MM-DD — use "today" if they say "today" |
| time                 | string          | HH:MM in 24-hour format                     |
| attendees            | list of strings | Names of other people who attended           |
| topics_discussed     | string          | Summary of discussion topics                 |
| materials_shared     | list of strings | Brochures, PDFs, documents shared            |
| samples_distributed  | list of strings | Drug samples given                           |
| sentiment            | string          | "Positive" or "Neutral" or "Negative"        |
| outcomes             | string          | Agreements, decisions, results               |
| follow_up_actions    | string          | Next steps the rep should take               |

Rules:
- Output ONLY a valid JSON object. No markdown, no explanation, no extra text.
- If a field is not mentioned in the transcript, set it to null.
- Normalize sentiment strictly to "Positive", "Neutral", or "Negative".
- If the transcript mentions sharing brochures, PDFs, or documents, put them in materials_shared.
- If the transcript mentions giving drug samples, put them in samples_distributed.

Transcribed voice note:
{transcribed_text}

Return ONLY the JSON object:"""


RESPONSE_GENERATION_PROMPT = """\
You are a friendly AI assistant helping a pharmaceutical field representative log HCP interactions.

Generate a short confirmation message (2-3 sentences max) based on what just happened.

Action performed: {intent}
Fields that were {intent_verb}: {extracted_fields}
Current form state (full context): {current_form_state}
AI suggested follow-ups: {ai_suggested_followups}

Rules:
- If action is "log": Confirm you captured the interaction. Name the key details briefly.
- If action is "edit": Confirm which fields changed and their new values. Use the HCP name from the current form state — do NOT invent or guess a different name.
- If action is "followup": Confirm the follow-up was scheduled. Mention the HCP name, task, and due date.
- If action is "history": Briefly acknowledge the history lookup. The actual history data will be provided separately.
- Be conversational and professional. Do NOT list raw JSON keys.
- Use the doctor's name from current form state if available. NEVER guess or hallucinate a name.
- Keep it concise."""


# ---------------------------------------------------------------------------
#  Extended intent classification (supports followup + history intents)
# ---------------------------------------------------------------------------

EXTENDED_INTENT_CLASSIFICATION_PROMPT = """\
You are an AI assistant for a pharmaceutical CRM system.
A field representative is chatting about an HCP (Healthcare Professional) interaction.

Classify the user's message into exactly ONE intent:

"log"      — The user is describing a NEW interaction or providing details for the first time.
"edit"     — The user is CORRECTING or UPDATING specific fields that are already filled in.
"followup" — The user wants to SCHEDULE a follow-up task (call, meeting, email) with an HCP.
"history"  — The user is ASKING about past interactions or history with a specific HCP.
"general"  — The user is asking a question, greeting, or chatting about something unrelated.

Rules:
- If the current form is mostly empty and the user describes an interaction → "log"
- If the current form already has data and the user says words like "actually", "correction", "change", "update", "sorry", "wrong" → "edit"
- If the user mentions scheduling, setting up, planning a follow-up, reminder, or future task → "followup"
- If the user asks about history, past interactions, previous meetings, last visit, track record → "history"
- If the message does not match any above → "general"

Current form state:
{current_form_state}

Chat history:
{chat_history}

User message: {user_input}

Respond with ONLY one word: log, edit, followup, history, or general
No punctuation. No explanation. Just the single word."""


# ---------------------------------------------------------------------------
#  Followup extraction prompt
# ---------------------------------------------------------------------------

FOLLOWUP_EXTRACTION_PROMPT = """\
You are a structured-data extraction engine for a pharmaceutical CRM.

A field representative wants to schedule a follow-up task with an HCP. Extract the details.

Fields to extract (include only those mentioned):

| Field          | Type   | Allowed values / format                          |
|----------------|--------|--------------------------------------------------|
| hcp_name       | string | Full name of the doctor or HCP                   |
| task           | string | Description of the follow-up task                |
| due_date       | string | YYYY-MM-DD — resolve relative dates like "next Tuesday", "in 2 weeks", "tomorrow" relative to today ({today}) |
| followup_type  | string | "Meeting" or "Call" or "Email"                    |
| notes          | string | Any additional context or notes                   |

Chat history:
{chat_history}

User message: {user_input}

Return ONLY a valid JSON object with the extracted fields. No markdown, no explanation.

Example input: "Schedule a follow-up call with Dr. Smith next Tuesday to discuss trial results"
Example output: {{"hcp_name":"Dr. Smith","task":"Discuss trial results","due_date":"{example_due_date}","followup_type":"Call"}}

Now extract from the user message above:"""


# ---------------------------------------------------------------------------
#  History lookup extraction prompt
# ---------------------------------------------------------------------------

HISTORY_EXTRACTION_PROMPT = """\
You are a structured-data extraction engine for a pharmaceutical CRM.

A field representative is asking about their interaction history with an HCP. Extract the query parameters.

Fields to extract (include only those mentioned):

| Field        | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| hcp_name     | string | Full name of the doctor or HCP being asked about |
| limit        | int    | How many past interactions to return (default 5)  |

Chat history:
{chat_history}

User message: {user_input}

Return ONLY a valid JSON object with the extracted fields. No markdown, no explanation.

Example input: "What's my history with Dr. Patel?"
Example output: {{"hcp_name":"Dr. Patel"}}

Now extract from the user message above:"""
