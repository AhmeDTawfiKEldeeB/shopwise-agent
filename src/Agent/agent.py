from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.config.settings import get_llm_settings
from Agent.tools.retrieval import retrieve_products


def build_agent():
    settings = get_llm_settings()
    llm = ChatOpenAI(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
    )
    return create_agent(model=llm, tools=[retrieve_products])


def ask(question: str) -> str:
    agent = build_agent()
    result = agent.invoke({"messages": [("human", question)]})
    return result["messages"][-1].content
