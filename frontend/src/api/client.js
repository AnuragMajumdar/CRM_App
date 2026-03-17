// API base URL - use env var in dev, hardcoded for production
const API_BASE = "https://crm-app-qvt1.onrender.com/api";

export async function sendChatMessage(sessionId, message, currentFormState, chatHistory) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      current_form_state: currentFormState,
      chat_history: chatHistory,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Chat failed: ${res.status}`);
  }
  return res.json();
}

export async function sendVoiceNote(audioBlob) {
  const formData = new FormData();
  formData.append("audio_file", audioBlob, "voice_note.webm");
  const res = await fetch(`${API_BASE}/voice-note`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Voice note failed: ${res.status}`);
  }
  return res.json();
}

export async function saveInteraction(formData) {
  const res = await fetch(`${API_BASE}/interaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Save failed: ${res.status}`);
  }
  return res.json();
}
