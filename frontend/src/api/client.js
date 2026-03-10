const API_BASE = "/api";

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
