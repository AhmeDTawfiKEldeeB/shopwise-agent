from openai import OpenAI

from src.config.settings import get_llm_settings
from infrastructure.llm.interface import ChatMessage, LLM


class GroqLLM(LLM):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        settings = get_llm_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.base_url = base_url or settings.groq_base_url
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def _to_messages(messages: list[ChatMessage]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def chat(self, messages: list[ChatMessage], **kwargs) -> str:
        payload = {"model": self.model, "messages": self._to_messages(messages)}
        payload.update(kwargs)
        response = self._client.chat.completions.create(**payload)
        return response.choices[0].message.content

    def stream_chat(self, messages: list[ChatMessage], **kwargs) -> iter:
        payload = {
            "model": self.model,
            "messages": self._to_messages(messages),
            "stream": True,
        }
        payload.update(kwargs)
        stream = self._client.chat.completions.create(**payload)
        for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

    def generate(self, prompt: str, **kwargs) -> str:
        return self.chat([ChatMessage(role="user", content=prompt)], **kwargs)

    def stream_generate(self, prompt: str, **kwargs) -> iter:
        yield from self.stream_chat(
            [ChatMessage(role="user", content=prompt)], **kwargs
        )

    def close(self) -> None:
        self._client.close()
