import { useState, useRef } from "react";
import { useDispatch } from "react-redux";
import { updateInteractionFields, clearHighlights } from "../store/interactionSlice";
import { addMessage } from "../store/chatSlice";
import { sendVoiceNote } from "../api/client";

/**
 * VoiceNoteButton — records audio via the MediaRecorder API,
 * sends it to POST /api/voice-note, and dispatches extracted fields to Redux.
 */
export default function VoiceNoteButton() {
  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const dispatch = useDispatch();

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : "audio/mp4",
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks so the browser releases the microphone
        stream.getTracks().forEach((t) => t.stop());

        const blob = new Blob(chunksRef.current, {
          type: mediaRecorder.mimeType,
        });

        if (blob.size === 0) return;

        setProcessing(true);
        dispatch(
          addMessage({
            role: "user",
            content: "🎤 Voice note recorded — processing...",
          })
        );

        try {
          const res = await sendVoiceNote(blob);

          // Merge extracted fields into the form
          const hasFields =
            res.extracted_fields &&
            Object.keys(res.extracted_fields).length > 0;
          const hasFollowups =
            res.ai_suggested_followups &&
            res.ai_suggested_followups.length > 0;

          if (hasFields || hasFollowups) {
            const payload = {
              ...(hasFields ? res.extracted_fields : {}),
              ...(hasFollowups
                ? { ai_suggested_followups: res.ai_suggested_followups }
                : {}),
            };
            dispatch(updateInteractionFields(payload));
            setTimeout(() => dispatch(clearHighlights()), 2000);
          }

          // Show transcription + reply in chat
          let assistantContent = res.reply || "Voice note processed.";
          if (res.transcription) {
            assistantContent =
              `📝 Transcription: "${res.transcription}"\n\n` +
              assistantContent;
          }
          if (hasFields) {
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
            const labels = Object.keys(res.extracted_fields)
              .map((k) => FIELD_LABELS[k] || k)
              .join(", ");
            assistantContent += `\n\n✅ Updated: ${labels}`;
          }
          dispatch(
            addMessage({ role: "assistant", content: assistantContent })
          );
        } catch (err) {
          dispatch(
            addMessage({
              role: "assistant",
              content: `Voice note error: ${err.message}`,
            })
          );
        } finally {
          setProcessing(false);
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      dispatch(
        addMessage({
          role: "assistant",
          content: `Microphone access denied: ${err.message}`,
        })
      );
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const handleClick = () => {
    if (processing) return;
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <button
      type="button"
      className={`voice-note-btn ${recording ? "recording" : ""} ${processing ? "processing" : ""}`}
      onClick={handleClick}
      disabled={processing}
      title={
        processing
          ? "Processing voice note..."
          : recording
          ? "Click to stop recording"
          : "Summarize from Voice Note (Requires Consent)"
      }
    >
      {processing ? (
        <span className="voice-note-spinner" />
      ) : (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M8 1C6.9 1 6 1.9 6 3V8C6 9.1 6.9 10 8 10C9.1 10 10 9.1 10 8V3C10 1.9 9.1 1 8 1Z"
            fill="currentColor"
          />
          <path
            d="M12 8C12 10.21 10.21 12 8 12C5.79 12 4 10.21 4 8H3C3 10.72 5.04 12.93 7.5 13.41V15H8.5V13.41C10.96 12.93 13 10.72 13 8H12Z"
            fill="currentColor"
          />
        </svg>
      )}
      {recording ? "Stop Recording" : processing ? "Processing..." : "Summarize from Voice Note (Requires Consent)"}
    </button>
  );
}
