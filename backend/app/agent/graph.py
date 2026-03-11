"""
LangGraph agent graph definition.

Graph flow:
  START -> parse_input -> route_tool
    route_tool:
      "log"        -> handle_log      -> respond -> END
      "edit"       -> handle_edit     -> respond -> END
      "voice_note" -> handle_voice    -> respond -> END
      "followup"   -> handle_followup -> respond -> END
      "history"    -> handle_history  -> respond -> END
      "general"    -> respond -> END
"""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    parse_input,          # kept for backward-compat; not registered in graph
    parse_input_extended,
    handle_log,
    handle_edit,
    handle_voice,
    handle_followup,
    handle_history,
    respond,
)


def route_tool(state: AgentState) -> str:
    """Conditional edge: route based on classified intent."""
    intent = state.get("intent", "general")
    if intent == "log":
        return "handle_log"
    elif intent == "edit":
        return "handle_edit"
    elif intent == "voice_note":
        return "handle_voice"
    elif intent == "followup":
        return "handle_followup"
    elif intent == "history":
        return "handle_history"
    else:
        return "respond"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    # Add nodes — uses parse_input_extended for 5-intent classification
    graph.add_node("parse_input", parse_input_extended)
    graph.add_node("handle_log", handle_log)
    graph.add_node("handle_edit", handle_edit)
    graph.add_node("handle_voice", handle_voice)
    graph.add_node("handle_followup", handle_followup)
    graph.add_node("handle_history", handle_history)
    graph.add_node("respond", respond)

    # Set entry point
    graph.set_entry_point("parse_input")

    # Conditional routing after parse_input
    graph.add_conditional_edges(
        "parse_input",
        route_tool,
        {
            "handle_log": "handle_log",
            "handle_edit": "handle_edit",
            "handle_voice": "handle_voice",
            "handle_followup": "handle_followup",
            "handle_history": "handle_history",
            "respond": "respond",
        },
    )

    # After tool handling, always go to respond
    graph.add_edge("handle_log", "respond")
    graph.add_edge("handle_edit", "respond")
    graph.add_edge("handle_voice", "respond")
    graph.add_edge("handle_followup", "respond")
    graph.add_edge("handle_history", "respond")

    # respond -> END
    graph.add_edge("respond", END)

    return graph.compile()


# Singleton compiled graph
agent = build_graph()
