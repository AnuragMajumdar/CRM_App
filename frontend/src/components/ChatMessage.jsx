import "./ChatMessage.css";

export default function ChatMessage({ role, content }) {
  return (
    <div className={`chat-msg ${role}`}>
      <div className={`chat-bubble ${role}`}>{content}</div>
    </div>
  );
}
