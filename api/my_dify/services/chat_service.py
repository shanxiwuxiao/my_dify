"""Chat use cases."""

from collections.abc import Iterator

from ..core.model_runtime.base import ModelClient, ModelMessage


class ChatService:
    """Generate chat answers without depending on Flask or a provider SDK."""

    def __init__(self, model_client: ModelClient):
        self._model_client = model_client

    @staticmethod
    def _build_messages(message: str, system_prompt: str) -> list[ModelMessage]:
        messages: list[ModelMessage] = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": message})
        return messages

    def chat(
        self,
        message: str,
        *,
        system_prompt: str = "",
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate an answer through the configured model client."""
        return self.chat_messages(
            self._build_messages(message, system_prompt),
            model=model_name,
            temperature=temperature,
        )

    def stream_chat(
        self,
        message: str,
        *,
        system_prompt: str = "",
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        """Yield answer deltas through the configured model client."""
        return self.stream_chat_messages(
            self._build_messages(message, system_prompt),
            model=model_name,
            temperature=temperature,
        )

    def chat_messages(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate an answer from an already prepared message history."""
        return self._model_client.generate(
            messages,
            model=model,
            temperature=temperature,
        )

    def stream_chat_messages(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        """Stream an answer from an already prepared message history."""
        return self._model_client.generate_stream(
            messages,
            model=model,
            temperature=temperature,
        )
