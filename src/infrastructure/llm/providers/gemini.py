from google import genai

from src.config.settings import get_llm_settings
from infrastructure.llm.interface import ChatMessage, LLM


class GeminiLLM(LLM):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_llm_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model
        self._client = genai.Client(api_key=self.api_key)

    def chat(self, messages: list[ChatMessage], **kwargs) -> str:
        response = self._client.models.generate_content(
            model=self.model,
            contents=[m.content for m in messages],
            **kwargs,
        )
        return response.text

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([ChatMessage(role="user", content=prompt)], **kwargs)

    def close(self) -> None:
        return None
