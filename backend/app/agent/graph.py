"""
LangGraph agent graph definition.

Graph flow:
  START -> parse_input -> route_tool
    route_tool:
      "log"     -> handle_log  -> respond -> END
      "edit"    -> handle_edit -> respond -> END
      "general" -> respond -> END
"""

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import parse_input, handle_log, handle_edit, respond


def route_tool(state: AgentState) -> str:
    """Conditional edge: route based on classified intent."""
    intent = state.get("intent", "general")
    if intent == "log":
        return "handle_log"
    elif intent == "edit":
        return "handle_edit"
    else:
        return "respond"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("parse_input", parse_input)
    graph.add_node("handle_log", handle_log)
    graph.add_node("handle_edit", handle_edit)
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
            "respond": "respond",
        },
    )

    # After tool handling, always go to respond
    graph.add_edge("handle_log", "respond")
    graph.add_edge("handle_edit", "respond")

    # respond -> END
    graph.add_edge("respond", END)

    return graph.compile()


# Singleton compiled graph
agent = build_graph()
