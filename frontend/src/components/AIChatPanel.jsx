import { useState, useRef, useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { addMessage, setStatus } from "../store/chatSlice";
import { updateInteractionFields, clearHighlights } from "../store/interactionSlice";
import { sendChatMessage } from "../api/client";
import ChatMessage from "./ChatMessage";
import "./AIChatPanel.css";

/** Human-readable labels for field keys, shown in the "fields updated" badge. */
const FIELD_LABELS = {
  hcp_name: "HCP Name",
  interaction_type: "Type",
  date: "Date",
  time: "Time",
  attendees: "Attendees",
  topics_discussed: "Topics",
  materials_shared: "Materials",
  samples_distributed: "Samples",
  sentiment: "Sentiment",
  outcomes: "Outcomes",
  follow_up_actions: "Follow-ups",
};

export default function AIChatPanel() {
  const [input, setInput] = useState("");
  const messages = useSelector((s) => s.chat.messages);
  const status = useSelector((s) => s.chat.status);
  const sessionId = useSelector((s) => s.chat.sessionId);
  const form = useSelector((s) => s.interaction.form);
  const dispatch = useDispatch();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || status === "loading") return;

    setInput("");
    dispatch(addMessage({ role: "user", content: text }));
    dispatch(setStatus("loading"));

    // Build the chat history to send to the backend for context.
    // Include the message we just added (the user's current message).
    const history = [
      ...messages,
      { role: "user", content: text },
    ];

    try {
      const res = await sendChatMessage(sessionId, text, form, history);

      // ---- Merge extracted fields into Redux form state ----
      const hasFields =
        res.extracted_fields && Object.keys(res.extracted_fields).length > 0;
      const hasFollowups =
        res.ai_suggested_followups && res.ai_suggested_followups.length > 0;

      if (hasFields || hasFollowups) {
        // Build a single payload so one dispatch updates everything and the
        // highlightedFields list captures every key that changed.
        const payload = {
          ...(hasFields ? res.extracted_fields : {}),
          ...(hasFollowups
            ? { ai_suggested_followups: res.ai_suggested_followups }
            : {}),
        };

        dispatch(updateInteractionFields(payload));

        // Auto-clear highlights after 2 seconds.
        setTimeout(() => dispatch(clearHighlights()), 2000);
      }

      // Build assistant message — append a summary of which fields were set.
      const updatedKeys = hasFields ? Object.keys(res.extracted_fields) : [];
      let assistantContent = res.reply;
      if (updatedKeys.length > 0) {
        const labels = updatedKeys
          .map((k) => FIELD_LABELS[k] || k)
          .join(", ");
        assistantContent += `\n\n✅ Updated: ${labels}`;
      }

      // Display scheduled followup confirmation
      if (res.followup_data) {
        const f = res.followup_data;
        assistantContent += `\n\n📅 Follow-up scheduled: ${f.followup_type || "Task"} with ${f.hcp_name || "HCP"}`;
        if (f.due_date) assistantContent += ` on ${f.due_date}`;
        if (f.task) assistantContent += `\n   Task: ${f.task}`;
        if (f.status) assistantContent += ` (${f.status})`;
      }

      // Display HCP interaction history
      if (res.hcp_history && res.hcp_history.length > 0) {
        assistantContent += `\n\n📋 Interaction history:`;
        res.hcp_history.forEach((h, idx) => {
          assistantContent += `\n${idx + 1}. ${h.date || "No date"} — ${h.interaction_type || "Interaction"}`;
          if (h.topics_discussed) assistantContent += `: ${h.topics_discussed}`;
          if (h.sentiment) assistantContent += ` (${h.sentiment})`;
        });
      } else if (res.hcp_history !== undefined && res.hcp_history !== null && res.hcp_history.length === 0) {
        assistantContent += `\n\nNo interaction history found for this HCP.`;
      }

      dispatch(addMessage({ role: "assistant", content: assistantContent }));
    } catch (err) {
      dispatch(
        addMessage({
          role: "assistant",
          content: `Error: ${err.message}. Please try again.`,
        })
      );
    } finally {
      dispatch(setStatus("idle"));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-icon">🤖</div>
        <div>
          <div className="chat-header-title">AI Assistant</div>
          <div className="chat-header-subtitle">Log interaction via chat</div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-placeholder">
            Log interaction details here (e.g., &quot;Met Dr. Smith, discussed
            Product X efficacy, positive sentiment, shared brochure&quot;) or
            ask for help.
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
        {status === "loading" && (
          <div className="chat-msg assistant">
            <div className="chat-bubble assistant typing">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <input
          type="text"
          className="chat-input"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={status === "loading"}
        />
        <button
          className="chat-send-btn"
          onClick={handleSend}
          disabled={!input.trim() || status === "loading"}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M14.5 1.5L7 9M14.5 1.5L10 14.5L7 9M14.5 1.5L1.5 6L7 9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Log
        </button>
      </div>
    </div>
  );
}
