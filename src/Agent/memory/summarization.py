from langchain_openai import ChatOpenAI

from src.config.settings import get_llm_settings

BASE_SYSTEM_PROMPT = (
    "You are ShopWise, a helpful shopping assistant. "
    "Help the customer find products and answer their questions about the shop."
)

SUMMARY_INSTRUCTION = """Progressively summarize the lines of the conversation provided, adding onto the previous summary.

Return the new summary as plain paragraphs. Do not use bullet points, and do not narrate what you are doing.
Preserve important concrete details exactly as stated, such as the user's name, numbers, preferences, and any remembered facts.

Previous summary (may be empty):
{summary}
"""


def build_system_prompt(summary: str) -> str:
    if not summary:
        return BASE_SYSTEM_PROMPT
    return (
        f"{BASE_SYSTEM_PROMPT}\n\n"
        "Here is a summary of the conversation so far:\n\n"
        f"{summary}\n\n"
        "Use the summary to answer follow-up questions. "
        "The user may not repeat details already captured in the summary."
    )


def get_llm() -> ChatOpenAI:
    settings = get_llm_settings()
    return ChatOpenAI(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
        temperature=0,
    )
