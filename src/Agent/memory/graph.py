from langchain_core.messages import RemoveMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from Agent.memory.checkpoint import get_checkpointer
from Agent.memory.state import AgentState
from Agent.memory.summarization import SUMMARY_INSTRUCTION, build_system_prompt, get_llm
from Agent.tools.retrieval import retrieve_products
from src.config.settings import get_agent_memory_settings


def build_graph(
    *,
    threshold: int | None = None,
    recent: int | None = None,
    checkpointer=None,
):
    settings = get_agent_memory_settings()
    threshold = settings.summary_threshold if threshold is None else threshold
    recent = settings.recent_messages if recent is None else recent
    recent = max(recent, 1)
    if checkpointer is None:
        checkpointer = get_checkpointer()

    llm = get_llm()
    agent_llm = llm.bind_tools([retrieve_products])

    def agent_node(state: AgentState) -> dict:
        prompt = SystemMessage(content=build_system_prompt(state.get("summary", "")))
        response = agent_llm.invoke([prompt, *state["messages"]])
        return {"messages": [response]}

    def summarize(state: AgentState) -> dict:
        messages = state["messages"]
        if len(messages) <= threshold:
            return {}
        to_trim = messages[:-recent]
        if not to_trim:
            return {}
        content = [SystemMessage(content=SUMMARY_INSTRUCTION.format(summary=state.get("summary", "")))]
        content.extend(to_trim)
        response = llm.invoke(content)
        return {
            "summary": response.content,
            "messages": [RemoveMessage(id=message.id) for message in to_trim],
        }

    def route_after_agent(state: AgentState) -> str:
        return tools_condition(state)

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode([retrieve_products]))
    builder.add_node("summarize", summarize)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent", route_after_agent, {"tools": "tools", "__end__": "summarize"}
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("summarize", END)

    return builder.compile(checkpointer=checkpointer)
