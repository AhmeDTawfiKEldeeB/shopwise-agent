from langchain_openai import ChatOpenAI

from src.config.settings import get_llm_settings

BASE_SYSTEM_PROMPT = (
    "You are ShopWise, a helpful shopping assistant. "
    "Help the customer find products and answer their questions about the shop.\n\n"
    "Response rules:\n"
    "- Answer as concisely as the question deserves. Keep it short and direct; match the length of the user's query.\n"
    "- Do not add tables, long lists, or extra options unless the user explicitly asks for a comparison or breakdown.\n"
    "- Do not upsell or add promotional follow-ups (no 'want me to add to cart?', 'compare more', 'ask about bundles', etc.) unless the user asks.\n"
    "- No filler, no repetition, no closing pleasantries.\n"
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
    provider = settings.provider.lower()

    defaults = {
        "groq": (settings.groq_model, settings.groq_api_key, settings.groq_base_url),
        "openrouter": (settings.openrouter_model, settings.openrouter_api_key, settings.openrouter_base_url),
        "gemini": (settings.gemini_model, settings.gemini_api_key, settings.gemini_base_url),
    }
    default_model, default_key, default_url = defaults.get(provider, defaults["gemini"])

    model = settings.model or default_model
    api_key = settings.api_key or default_key
    base_url = settings.base_url or default_url

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
    )
