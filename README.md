# HCP Interaction CRM

An AI-first Customer Relationship Management system for logging and managing Healthcare Professional (HCP) interactions. Built with FastAPI, LangGraph, React, and PostgreSQL.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
  - [1. PostgreSQL Database](#1-postgresql-database)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [API Endpoints](#api-endpoints)
- [LangGraph Agent](#langgraph-agent)
  - [Agent State](#agent-state)
  - [Graph Flow](#graph-flow)
  - [Nodes](#nodes)
  - [Tools](#tools)
  - [Prompts](#prompts)
- [Database Schema](#database-schema)
- [Testing the Agent](#testing-the-agent)
- [Checking the Database](#checking-the-database)

---

## Overview

This application allows pharmaceutical field representatives to log, edit, and track their interactions with Healthcare Professionals (HCPs) using natural language. An AI agent powered by LangGraph and Groq's LLM:

- Understands free-form text and voice notes
- Extracts structured interaction data automatically
- Suggests follow-up actions
- Schedules follow-up tasks
- Retrieves interaction history per HCP

---
![HCP Photo](<LLM App.png>)

## Architecture

```
Browser (React + Redux)
    |
    | HTTP (proxied via Vite dev server)
    v
FastAPI Backend (Port 8000)
    |
    |-- /api/chat        --> LangGraph Agent --> Groq LLM (llama-3.1-8b-instant)
    |-- /api/voice-note  --> Groq Whisper (speech-to-text) --> LangGraph Agent
    |-- /api/interaction --> PostgreSQL (async via asyncpg)
    |-- /api/followup    --> PostgreSQL
    |-- /api/hcp-history --> PostgreSQL
    v
PostgreSQL Database (Port 5432)
```

**Tech Stack:**

| Layer | Technology |
|---|---|
| Frontend | React 19, Redux Toolkit, Vite |
| Backend | Python, FastAPI, Uvicorn |
| AI Agent | LangGraph, LangChain Core |
| LLM | Groq API (llama-3.1-8b-instant) |
| Speech-to-Text | Groq Whisper (whisper-large-v3) |
| Database | PostgreSQL (async via asyncpg) |
| ORM | SQLAlchemy 2.0 (async) |

---

## Project Structure

```
LangGraph Project/
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment variable template
│   └── app/
│       ├── config.py                   # Settings (DATABASE_URL, GROQ_API_KEY)
│       ├── db/
│       │   └── database.py             # SQLAlchemy engine, session, init_db
│       ├── models/
│       │   └── interaction.py          # Interaction ORM model
│       ├── schemas/
│       │   └── interaction.py          # Pydantic request/response schemas
│       ├── services/
│       │   ├── interaction_service.py  # CRUD logic for interactions
│       │   └── followup_service.py     # CRUD logic for followups
│       ├── api/
│       │   └── routes.py               # All API route handlers
│       └── agent/
│           ├── graph.py                # LangGraph graph definition
│           ├── nodes.py                # Node function implementations
│           ├── tools.py                # Tool functions (validation/normalization)
│           ├── prompts.py              # All LLM prompt templates
│           └── state.py                # AgentState TypedDict
│
└── frontend/
    ├── package.json
    ├── vite.config.js                  # Dev server + proxy config
    └── src/
        ├── main.jsx                    # React entry point
        ├── App.jsx                     # Root component
        ├── api/
        │   └── client.js               # API fetch wrappers
        ├── components/
        │   ├── InteractionForm.jsx     # Form for logging interactions
        │   ├── AIChatPanel.jsx         # AI chat interface
        │   ├── ChatMessage.jsx         # Individual chat message
        │   └── VoiceNoteButton.jsx     # Microphone recording button
        └── store/
            ├── store.js                # Redux store
            ├── chatSlice.js            # Chat state management
            └── interactionSlice.js     # Interaction state management
```

---

## Prerequisites

Before starting, ensure the following are installed:

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js LTS** — [nodejs.org](https://nodejs.org/)
- **PostgreSQL 15+** — Install via Homebrew: `brew install postgresql@15`
- **Groq API Key** — Free at [console.groq.com/keys](https://console.groq.com/keys)

---

## Local Setup

### 1. PostgreSQL Database

**Start PostgreSQL:**

```bash
brew services start postgresql@15
```

**Add psql to your PATH (if not already):**

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Create the database:**

```bash
psql -h localhost -p 5432 -d postgres -c "CREATE DATABASE hcp_crm;"
```

> The app auto-creates all tables on first startup — no migrations needed.

---

### 2. Backend Setup

**Navigate to the backend directory:**

```bash
cd backend
```

**Create and activate a Python virtual environment:**

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Create the environment file:**

```bash
cp .env.example .env
```

**Edit `.env` and add your Groq API key:**

```
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/hcp_crm
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> Get your Groq API key at [console.groq.com/keys](https://console.groq.com/keys). The key starts with `gsk_`.

---

### 3. Frontend Setup

**Navigate to the frontend directory:**

```bash
cd frontend
```

**Install dependencies:**

```bash
npm install
```

---

## Running the App

You need two terminals running simultaneously.

**Terminal 1 — Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`
Health check: `http://localhost:8000/health`

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:5173`

> The frontend proxies all `/api/*` requests to `http://localhost:8000` automatically via Vite config.

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres@localhost:5432/hcp_crm` |
| `GROQ_API_KEY` | Groq API key for LLM and Whisper | `gsk_xxxxxxxxxxxxxxxxxxxx` |

---

## API Endpoints

Base URL: `http://localhost:8000/api`

### Chat

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send a message to the LangGraph agent |

**Request body:**
```json
{
  "message": "Log a meeting with Dr. Sarah Johnson today",
  "current_form_state": {},
  "chat_history": []
}
```

**Response:**
```json
{
  "reply": "I've logged the meeting with Dr. Sarah Johnson...",
  "tool_used": "log_interaction",
  "extracted_fields": { "hcp_name": "Dr. Sarah Johnson", ... },
  "ai_suggested_followups": ["Send follow-up email", "..."],
  "followup_data": null,
  "hcp_history": null
}
```

---

### Voice Note

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/voice-note` | Upload audio, transcribe via Groq Whisper, extract fields |

Accepts `multipart/form-data` with an `audio_file` field (`.webm`, `.mp3`, `.wav`).

---

### Interactions (CRUD)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/interaction` | Save a finalized interaction to the database |
| `GET` | `/interaction/{id}` | Retrieve an interaction by UUID |
| `PUT` | `/interaction/{id}` | Update specific fields of an interaction |

---

### Followups

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/followup` | Manually create a follow-up task |
| `GET` | `/followups` | List all follow-ups (filter by `hcp_name`, `status`) |
| `GET` | `/hcp-history` | Get interaction history for an HCP (query: `hcp_name`, `limit`) |

---

## LangGraph Agent

The core intelligence of the app. Built with LangGraph, it processes every chat message through a directed graph of nodes.

### Agent State

Defined in `app/agent/state.py`. Passed through every node:

```python
class AgentState(TypedDict):
    user_input: str                          # The user's message
    current_form_state: dict                 # Current form data in the UI
    chat_history: list[dict]                 # Last 6 messages for context
    intent: Optional[str]                    # Classified intent
    extracted_fields: Optional[dict]         # Fields extracted by LLM
    ai_suggested_followups: Optional[list]   # AI-generated follow-up suggestions
    response: Optional[str]                  # Final reply to the user
```

---

### Graph Flow

```
START
  └── parse_input  (classifies intent into 5 types)
        |
        ├── intent = "log"        ──> handle_log       ──> respond ──> END
        ├── intent = "edit"       ──> handle_edit      ──> respond ──> END
        ├── intent = "voice_note" ──> handle_voice     ──> respond ──> END
        ├── intent = "followup"   ──> handle_followup  ──> respond ──> END
        ├── intent = "history"    ──> handle_history   ──> respond ──> END
        └── intent = "general"   ──────────────────────> respond ──> END
```

---

### Nodes

All nodes are defined in `app/agent/nodes.py`.

#### `parse_input` (entry point)

Uses `EXTENDED_INTENT_CLASSIFICATION_PROMPT` to classify the user's message into one of 5 intents: `log`, `edit`, `followup`, `history`, or `general`.

For `log` and `edit` intents, it also runs a second LLM call to extract the relevant fields using `LOG_EXTRACTION_PROMPT` or `EDIT_EXTRACTION_PROMPT`.

**Input:** `user_input`, `current_form_state`, `chat_history`
**Output:** `intent`, `extracted_fields`

---

#### `handle_log`

Processes a new interaction log. Calls the `log_interaction` tool to validate and normalize all extracted fields. Then makes a third LLM call using `FOLLOWUP_SUGGESTION_PROMPT` to generate 2–3 AI-suggested follow-up actions.

**Input:** `extracted_fields`
**Output:** normalized `extracted_fields`, `ai_suggested_followups`
**Tool called:** `log_interaction`

---

#### `handle_edit`

Processes a correction to the current form. Calls the `edit_interaction` tool to validate only the changed fields. Does not generate follow-up suggestions.

**Input:** `extracted_fields`, `current_form_state`
**Output:** normalized `extracted_fields`
**Tool called:** `edit_interaction`

---

#### `handle_voice`

Processes a voice note transcription. Uses `VOICE_NOTE_EXTRACTION_PROMPT` to extract structured fields from the transcribed text, then calls `summarize_voice_interaction` to normalize them. Also generates AI follow-up suggestions.

**Input:** `user_input` (transcribed text), pre-set `intent = "voice_note"`
**Output:** normalized `extracted_fields`, `ai_suggested_followups`
**Tool called:** `summarize_voice_interaction`

---

#### `handle_followup`

Processes a follow-up scheduling request. Uses `FOLLOWUP_EXTRACTION_PROMPT` to extract task details (HCP name, task description, due date, type). Calls `schedule_followup` tool to normalize and resolve relative dates (e.g., "next Tuesday", "in 2 weeks"). The result is persisted to the `followups` table in the database by the API route.

**Input:** `user_input`, `chat_history`
**Output:** normalized `extracted_fields` (task details)
**Tool called:** `schedule_followup`

---

#### `handle_history`

Processes an HCP history lookup request. Uses `HISTORY_EXTRACTION_PROMPT` to extract the HCP name and optional result limit. Calls `validate_history_query` to clean the parameters. The API route then queries the database and returns results.

**Input:** `user_input`, `chat_history`
**Output:** normalized `extracted_fields` (hcp_name, limit)
**Tool called:** `validate_history_query`

---

#### `respond`

The final node in every path. Generates a natural language confirmation message using `RESPONSE_GENERATION_PROMPT`. For `general` intent, it responds conversationally without a template.

**Input:** `intent`, `extracted_fields`, `ai_suggested_followups`, `current_form_state`
**Output:** `response` (string shown to the user)

---

### Tools

All tools are defined in `app/agent/tools.py`. They perform validation and normalization — no LLM calls, pure Python logic.

#### Tool 1: `log_interaction`

Validates and normalizes all extracted fields for a new interaction log.

- Normalizes `sentiment` → `"Positive"` / `"Neutral"` / `"Negative"`
- Normalizes `interaction_type` → `"Meeting"` / `"Call"` / `"Email"` / `"Conference"`
- Parses `date` from multiple formats (YYYY-MM-DD, DD/MM/YYYY, "today", "yesterday")
- Parses `time` into 24-hour HH:MM format
- Converts comma-separated strings into lists for `attendees`, `materials_shared`, `samples_distributed`

---

#### Tool 2: `edit_interaction`

Same normalization as `log_interaction` but only applied to the fields the user explicitly changed. Unchanged fields are not touched.

---

#### Tool 3: `summarize_voice_interaction`

Same normalization as `log_interaction`, applied to fields extracted from a voice note transcription.

---

#### Tool 4: `schedule_followup`

Validates follow-up scheduling fields and resolves relative date expressions:

| Expression | Resolved to |
|---|---|
| `"today"` | Current date |
| `"tomorrow"` | Current date + 1 day |
| `"next Tuesday"` | Next occurrence of Tuesday |
| `"in 2 weeks"` | Current date + 14 days |
| `"in 3 days"` | Current date + 3 days |

Also normalizes `followup_type` and sets default `status = "pending"`.

---

#### Tool 5: `validate_history_query`

Validates HCP history lookup parameters. Ensures `hcp_name` is a clean string and `limit` is a valid integer between 1 and 20 (default: 5).

---

### Prompts

All prompts are in `app/agent/prompts.py`.

| Prompt | Used by | Purpose |
|---|---|---|
| `INTENT_CLASSIFICATION_PROMPT` | (legacy) | 3-intent classification (log/edit/general) |
| `EXTENDED_INTENT_CLASSIFICATION_PROMPT` | `parse_input` | 5-intent classification (log/edit/followup/history/general) |
| `LOG_EXTRACTION_PROMPT` | `parse_input` | Extract all interaction fields from a log message |
| `EDIT_EXTRACTION_PROMPT` | `parse_input` | Extract only changed fields from an edit message |
| `VOICE_NOTE_EXTRACTION_PROMPT` | `handle_voice` | Extract fields from voice note transcription |
| `FOLLOWUP_EXTRACTION_PROMPT` | `handle_followup` | Extract follow-up task details |
| `HISTORY_EXTRACTION_PROMPT` | `handle_history` | Extract HCP name and limit for history lookup |
| `FOLLOWUP_SUGGESTION_PROMPT` | `handle_log`, `handle_voice` | Generate 2–3 AI-suggested follow-up actions |
| `RESPONSE_GENERATION_PROMPT` | `respond` | Generate natural language confirmation to user |

---

## Database Schema

### `interactions` table

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Auto-generated unique ID |
| `hcp_name` | String | Doctor or HCP full name |
| `interaction_type` | String | Meeting / Call / Email / Conference |
| `date` | Date | Date of the interaction |
| `time` | Time | Time of the interaction (24h) |
| `attendees` | String[] | List of attendees |
| `topics_discussed` | Text | Summary of topics |
| `materials_shared` | String[] | Brochures, PDFs shared |
| `samples_distributed` | String[] | Drug samples given |
| `sentiment` | String | Positive / Neutral / Negative |
| `outcomes` | Text | Decisions, agreements, results |
| `follow_up_actions` | Text | Next steps for the rep |
| `ai_suggested_followups` | String[] | AI-generated follow-up suggestions |
| `created_at` | DateTime (TZ) | Record creation timestamp |

### `followups` table

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Auto-generated unique ID |
| `hcp_name` | String | HCP the follow-up is for |
| `task` | String | Description of the follow-up task |
| `due_date` | Date | When the follow-up is due |
| `followup_type` | String | Meeting / Call / Email |
| `status` | String | pending / completed |
| `linked_interaction_id` | UUID | Optional link to an interaction |
| `notes` | Text | Additional context |
| `created_at` | DateTime (TZ) | Record creation timestamp |

> Tables are auto-created on backend startup via SQLAlchemy's `init_db()` — no migration files needed.

---

## Testing the Agent

Use these prompts in the AI Chat Panel at `http://localhost:5173` to test each node and tool:

### Log a new interaction (`handle_log` + `log_interaction`)

```
Log a meeting with Dr. Sarah Johnson on March 10, 2026 at 2:00 PM. Attendees were John Smith and Emily Davis. We discussed diabetes medication and new clinical trials. Shared product brochure and dosage guide. Distributed 5 samples of Metformin. The outcome was positive, doctor showed strong interest. Follow up with a detailed case study next week.
```

```
Log a call with Dr. Raj Patel yesterday. Topics discussed were hypertension treatment options. Sentiment was neutral.
```

### Edit an existing interaction (`handle_edit` + `edit_interaction`)

Run after logging an interaction above:

```
Change the sentiment to positive and add follow up action: send clinical trial results by email
```

```
Update the interaction type to conference and add attendee Dr. Mike Lee
```

### Schedule a follow-up (`handle_followup` + `schedule_followup`)

```
Schedule a follow-up call with Dr. Raj Patel next Tuesday to discuss the clinical trial results
```

```
Set up a meeting with Dr. Sarah Johnson in 2 weeks to review the diabetes medication outcomes
```

### Look up HCP history (`handle_history` + `validate_history_query`)

```
What's my interaction history with Dr. Raj Patel?
```

```
Show me the last 3 interactions with Dr. Sarah Johnson
```

### General conversation (`respond` only — no tool)

```
What types of interactions can I log in this system?
```

```
What information should I capture after a meeting with a doctor?
```

### Voice note (`handle_voice` + `summarize_voice_interaction`)

Click the **microphone button** in the UI and say:

```
Met with Dr. Chen today. It was a conference. Discussed oncology drug pricing and new treatment protocols. Shared the Phase 3 trial summary. Sentiment was positive. Follow up by sending the full report next week.
```

---

## Checking the Database

### Option A — pgAdmin (GUI)

1. Download from [pgadmin.org](https://www.pgadmin.org/download/)
2. Create a new server connection:
   - Host: `localhost`
   - Port: `5432`
   - Database: `hcp_crm`
   - Username: `postgres`
3. Expand: `Servers > hcp_crm > Databases > hcp_crm > Schemas > public > Tables`
4. Right-click `interactions` → **View/Edit Data** → **All Rows**

### Option B — psql CLI

```bash
psql -h localhost -p 5432 -d hcp_crm -U postgres
```

```sql
-- List all tables
\dt

-- View all interactions
SELECT * FROM interactions;

-- View all followups
SELECT * FROM followups;

-- Search by HCP name
SELECT * FROM interactions WHERE hcp_name = 'Dr. Raj Patel';

-- Quit
\q
```

### Option C — Swagger UI

Visit `http://localhost:8000/docs` to call any API endpoint directly from the browser.
