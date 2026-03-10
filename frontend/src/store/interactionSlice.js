import { createSlice } from "@reduxjs/toolkit";

const today = new Date();
const dateStr = today.toISOString().split("T")[0];
const timeStr = today.toTimeString().slice(0, 5);

// Fields that must always be arrays in the form state.
const ARRAY_FIELDS = new Set([
  "attendees",
  "materials_shared",
  "samples_distributed",
  "ai_suggested_followups",
]);

/**
 * Coerce a value to the correct type for a given form field.
 * - Array fields: string → split by comma → trimmed array.
 *                 already-array → kept as-is.
 * - Everything else: passed through as a string.
 */
function coerceValue(field, value) {
  if (ARRAY_FIELDS.has(field)) {
    if (Array.isArray(value)) return value.map((v) => String(v).trim()).filter(Boolean);
    if (typeof value === "string" && value.trim()) {
      return value.split(",").map((v) => v.trim()).filter(Boolean);
    }
    return [];
  }
  // Scalar fields — convert to string (handles numbers, booleans from LLM).
  if (value === null || value === undefined) return "";
  return String(value);
}

const initialState = {
  form: {
    hcp_name: "",
    interaction_type: "Meeting",
    date: dateStr,
    time: timeStr,
    attendees: [],
    topics_discussed: "",
    materials_shared: [],
    samples_distributed: [],
    sentiment: "Neutral",
    outcomes: "",
    follow_up_actions: "",
    ai_suggested_followups: [],
  },
  // Tracks which fields were last touched by the AI so the UI can highlight them.
  highlightedFields: [],
  saveStatus: "idle", // idle | saving | saved | error
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    /** Manual single-field update (user typing in the form). */
    setField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
      // Clear highlight on manual edit.
      state.highlightedFields = state.highlightedFields.filter((f) => f !== field);
    },

    /**
     * updateInteractionFields — the primary action for AI-driven form population.
     *
     * Accepts a partial object of fields extracted by the backend.
     * - Only keys present in the payload are touched; everything else is preserved.
     * - Values are coerced to the correct type (string vs array).
     * - The set of updated keys is stored in `highlightedFields` so the UI can
     *   flash a visual indicator.
     *
     * Works identically for both `log_interaction` (many fields) and
     * `edit_interaction` (one or two fields).
     */
    updateInteractionFields(state, action) {
      const fields = action.payload;
      if (!fields || typeof fields !== "object") return;

      const touched = [];

      Object.entries(fields).forEach(([key, value]) => {
        if (!(key in state.form)) return;           // ignore unknown keys
        if (value === null || value === undefined) return; // skip nulls

        const coerced = coerceValue(key, value);
        state.form[key] = coerced;
        touched.push(key);
      });

      state.highlightedFields = touched;
    },

    /** Clear the highlight list (called on a timer from the UI). */
    clearHighlights(state) {
      state.highlightedFields = [];
    },

    /** Backwards-compat alias — existing code that calls mergeFields still works. */
    mergeFields(state, action) {
      interactionSlice.caseReducers.updateInteractionFields(state, action);
    },

    resetForm(state) {
      const now = new Date();
      state.form = {
        ...initialState.form,
        date: now.toISOString().split("T")[0],
        time: now.toTimeString().slice(0, 5),
      };
      state.highlightedFields = [];
      state.saveStatus = "idle";
    },

    setSaveStatus(state, action) {
      state.saveStatus = action.payload;
    },
  },
});

export const {
  setField,
  updateInteractionFields,
  clearHighlights,
  mergeFields,
  resetForm,
  setSaveStatus,
} = interactionSlice.actions;

export default interactionSlice.reducer;
