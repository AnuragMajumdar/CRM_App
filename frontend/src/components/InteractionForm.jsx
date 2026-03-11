import { useSelector, useDispatch } from "react-redux";
import { setField, resetForm, setSaveStatus } from "../store/interactionSlice";
import { resetChat } from "../store/chatSlice";
import { saveInteraction } from "../api/client";
import VoiceNoteButton from "./VoiceNoteButton";
import "./InteractionForm.css";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference"];

export default function InteractionForm() {
  const form = useSelector((s) => s.interaction.form);
  const saveStatus = useSelector((s) => s.interaction.saveStatus);
  const highlighted = useSelector((s) => s.interaction.highlightedFields);
  const dispatch = useDispatch();

  /** Returns true when the AI just updated this field. */
  const isHighlighted = (field) => highlighted.includes(field);

  /** CSS class helper — appends "ai-updated" when the field was just populated. */
  const hl = (field, base = "form-group") =>
    `${base}${isHighlighted(field) ? " ai-updated" : ""}`;

  const set = (field) => (e) =>
    dispatch(setField({ field, value: e.target.value }));

  /* ---- Materials / Samples as tag inputs ---- */
  const handleTagKeyDown = (field) => (e) => {
    if (e.key === "Enter" && e.target.value.trim()) {
      e.preventDefault();
      const current = form[field] || [];
      dispatch(
        setField({ field, value: [...current, e.target.value.trim()] })
      );
      e.target.value = "";
    }
  };

  const removeTag = (field, idx) => {
    const updated = [...(form[field] || [])];
    updated.splice(idx, 1);
    dispatch(setField({ field, value: updated }));
  };

  /* ---- Attendees as tag input ---- */
  const handleAttendeesKeyDown = (e) => {
    if (e.key === "Enter" && e.target.value.trim()) {
      e.preventDefault();
      const current = form.attendees || [];
      dispatch(
        setField({
          field: "attendees",
          value: [...current, e.target.value.trim()],
        })
      );
      e.target.value = "";
    }
  };

  const removeAttendee = (idx) => {
    const updated = [...(form.attendees || [])];
    updated.splice(idx, 1);
    dispatch(setField({ field: "attendees", value: updated }));
  };

  /* ---- Save ---- */
  const handleSave = async () => {
    dispatch(setSaveStatus("saving"));
    try {
      await saveInteraction(form);
      dispatch(setSaveStatus("saved"));
    } catch {
      dispatch(setSaveStatus("error"));
    }
  };

  const handleReset = () => {
    dispatch(resetForm());
    dispatch(resetChat());
  };

  return (
    <div className="form-panel">
      <div className="form-panel-header">
        <h2>Log HCP Interaction</h2>
      </div>

      <div className="form-section">
        <div className="form-section-title">Interaction Details</div>

        {/* Row: HCP Name + Interaction Type */}
        <div className="form-row two-col">
          <div className={hl("hcp_name")}>
            <label>HCP Name</label>
            <input
              type="text"
              placeholder="Search or select HCP..."
              value={form.hcp_name}
              onChange={set("hcp_name")}
            />
          </div>
          <div className={hl("interaction_type")}>
            <label>Interaction Type</label>
            <select
              value={form.interaction_type}
              onChange={set("interaction_type")}
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Row: Date + Time */}
        <div className="form-row two-col">
          <div className={hl("date")}>
            <label>Date</label>
            <input type="date" value={form.date} onChange={set("date")} />
          </div>
          <div className={hl("time")}>
            <label>Time</label>
            <input type="time" value={form.time} onChange={set("time")} />
          </div>
        </div>

        {/* Attendees */}
        <div className={hl("attendees")}>
          <label>Attendees</label>
          <div className="tag-input-wrapper">
            {(form.attendees || []).map((a, i) => (
              <span className="tag" key={i}>
                {a}
                <button
                  type="button"
                  className="tag-remove"
                  onClick={() => removeAttendee(i)}
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              placeholder="Enter names or search..."
              onKeyDown={handleAttendeesKeyDown}
            />
          </div>
        </div>

        {/* Topics Discussed */}
        <div className={hl("topics_discussed")}>
          <div className="label-with-voice">
            <label>Topics Discussed</label>
            <VoiceNoteButton />
          </div>
          <textarea
            rows={3}
            placeholder="Enter key discussion points..."
            value={form.topics_discussed}
            onChange={set("topics_discussed")}
          />
        </div>
      </div>

      {/* Materials Shared / Samples Distributed */}
      <div className="form-section">
        <div className="form-section-title">
          Materials Shared / Samples Distributed
        </div>

        <div className={hl("materials_shared", "subsection")}>
          <div className="subsection-header">
            <span className="subsection-label">Materials Shared</span>
          </div>
          <div className="tag-input-wrapper">
            {(form.materials_shared || []).map((m, i) => (
              <span className="tag" key={i}>
                {m}
                <button
                  type="button"
                  className="tag-remove"
                  onClick={() => removeTag("materials_shared", i)}
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              placeholder={
                (form.materials_shared || []).length === 0
                  ? "Type and press Enter to add..."
                  : ""
              }
              onKeyDown={handleTagKeyDown("materials_shared")}
            />
          </div>
          {(form.materials_shared || []).length === 0 && (
            <p className="empty-hint">No materials added.</p>
          )}
        </div>

        <div className={hl("samples_distributed", "subsection")}>
          <div className="subsection-header">
            <span className="subsection-label">Samples Distributed</span>
          </div>
          <div className="tag-input-wrapper">
            {(form.samples_distributed || []).map((s, i) => (
              <span className="tag" key={i}>
                {s}
                <button
                  type="button"
                  className="tag-remove"
                  onClick={() => removeTag("samples_distributed", i)}
                >
                  ×
                </button>
              </span>
            ))}
            <input
              type="text"
              placeholder={
                (form.samples_distributed || []).length === 0
                  ? "Type and press Enter to add..."
                  : ""
              }
              onKeyDown={handleTagKeyDown("samples_distributed")}
            />
          </div>
          {(form.samples_distributed || []).length === 0 && (
            <p className="empty-hint">No samples added.</p>
          )}
        </div>
      </div>

      {/* Sentiment */}
      <div className={`form-section${isHighlighted("sentiment") ? " ai-updated" : ""}`}>
        <div className="form-section-title">Observed/Inferred HCP Sentiment</div>
        <div className="sentiment-row">
          {["Positive", "Neutral", "Negative"].map((s) => (
            <label key={s} className={`sentiment-option ${s.toLowerCase()}`}>
              <input
                type="radio"
                name="sentiment"
                value={s}
                checked={form.sentiment === s}
                onChange={set("sentiment")}
              />
              <span className={`sentiment-icon ${s.toLowerCase()}`}>
                {s === "Positive" && "😊"}
                {s === "Neutral" && "😐"}
                {s === "Negative" && "😞"}
              </span>
              <span>{s}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Outcomes */}
      <div className={`form-section${isHighlighted("outcomes") ? " ai-updated" : ""}`}>
        <div className="form-section-title">Outcomes</div>
        <textarea
          rows={3}
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={set("outcomes")}
        />
      </div>

      {/* Follow-up Actions */}
      <div className={`form-section${isHighlighted("follow_up_actions") ? " ai-updated" : ""}`}>
        <div className="form-section-title">Follow-up Actions</div>
        <textarea
          rows={3}
          placeholder="Enter next steps or tasks..."
          value={form.follow_up_actions}
          onChange={set("follow_up_actions")}
        />

        {/* AI Suggested Follow-ups */}
        {(form.ai_suggested_followups || []).length > 0 && (
          <div className="ai-followups">
            <p className="ai-followups-label">AI Suggested Follow-ups:</p>
            {form.ai_suggested_followups.map((f, i) => (
              <button
                key={i}
                type="button"
                className="ai-followup-item"
                onClick={() =>
                  dispatch(
                    setField({
                      field: "follow_up_actions",
                      value: form.follow_up_actions
                        ? `${form.follow_up_actions}\n${f}`
                        : f,
                    })
                  )
                }
              >
                + {f}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="form-actions">
        <button className="btn-secondary" onClick={handleReset}>
          Reset
        </button>
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={saveStatus === "saving"}
        >
          {saveStatus === "saving"
            ? "Saving..."
            : saveStatus === "saved"
            ? "Saved ✓"
            : "Save Interaction"}
        </button>
      </div>
    </div>
  );
}
