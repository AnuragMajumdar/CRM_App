import InteractionForm from "./components/InteractionForm";
import AIChatPanel from "./components/AIChatPanel";
import "./App.css";

export default function App() {
  return (
    <div className="app-container">
      <InteractionForm />
      <AIChatPanel />
    </div>
  );
}
