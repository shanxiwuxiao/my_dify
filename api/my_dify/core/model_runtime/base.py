from collections.abc import Iterator
from typing import Literal, Protocol, TypedDict


class ModelMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class ModelClient(Protocol):
    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        ...

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        ...
