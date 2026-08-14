from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str
    content: str


class LLM(ABC):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream_chat(self, messages: list[ChatMessage], **kwargs) -> Iterator[str]:
        raise NotImplementedError

    @abstractmethod
    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
