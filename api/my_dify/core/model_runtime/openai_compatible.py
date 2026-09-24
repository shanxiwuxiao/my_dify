"""Client for OpenAI-compatible chat completion APIs."""

import json
from collections.abc import Iterator
from typing import Any

import httpx

from .base import ModelMessage
from .exceptions import ModelConfigurationError, ModelRequestError


class OpenAICompatibleClient:
    """Generate text through an OpenAI-compatible HTTP endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._http_client = http_client or httpx.Client(timeout=timeout)

    def _build_payload(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None,
        temperature: float | None,
        stream: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self._model,
            "messages": messages,
            "stream": stream,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        return payload

    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Send messages and return the assistant's text content."""
        if not self._api_key.strip():
            raise ModelConfigurationError("Model API key is not configured")

        try:
            response = self._http_client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=self._build_payload(
                    messages,
                    model=model,
                    temperature=temperature,
                    stream=False,
                ),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelRequestError("Model provider request failed") from exc

        try:
            payload: Any = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelRequestError("Model provider returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise ModelRequestError("Model provider returned an empty answer")

        return content

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        """Yield text deltas from an OpenAI-compatible streaming response."""
        if not self._api_key.strip():
            raise ModelConfigurationError("Model API key is not configured")

        try:
            with self._http_client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=self._build_payload(
                    messages,
                    model=model,
                    temperature=temperature,
                    stream=True,
                ),
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue

                    data = line.removeprefix("data:").strip()
                    if not data:
                        continue
                    if data == "[DONE]":
                        return

                    try:
                        payload: Any = json.loads(data)
                        content = payload["choices"][0]["delta"].get("content")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
                        raise ModelRequestError(
                            "Model provider returned an invalid streaming response"
                        ) from exc

                    if isinstance(content, str) and content:
                        yield content
        except ModelRequestError:
            raise
        except httpx.HTTPError as exc:
            raise ModelRequestError("Model provider request failed") from exc
