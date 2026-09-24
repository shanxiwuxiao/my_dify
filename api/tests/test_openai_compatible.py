import json

import httpx
import pytest

from my_dify.core.model_runtime.exceptions import ModelConfigurationError, ModelRequestError
from my_dify.core.model_runtime.openai_compatible import OpenAICompatibleClient


def test_generate_sends_expected_request_and_returns_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer secret"
        assert payload == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": False,
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "你好，我是模型"}}]},
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1/",
        api_key="secret",
        model="test-model",
        http_client=http_client,
    )

    assert model_client.generate(
        [{"role": "user", "content": "你好"}]
    ) == "你好，我是模型"


def test_generate_rejects_empty_api_key() -> None:
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="",
        model="test-model",
    )

    with pytest.raises(ModelConfigurationError):
        model_client.generate([{"role": "user", "content": "你好"}])


def test_generate_converts_http_error_to_model_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="test-model",
        http_client=httpx.Client(transport=transport),
    )

    with pytest.raises(ModelRequestError, match="request failed"):
        model_client.generate([{"role": "user", "content": "你好"}])


def test_generate_rejects_invalid_response_structure() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"choices": []})
    )
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="test-model",
        http_client=httpx.Client(transport=transport),
    )

    with pytest.raises(ModelRequestError, match="invalid response"):
        model_client.generate([{"role": "user", "content": "你好"}])


def test_generate_stream_sends_expected_request_and_yields_deltas() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer secret"
        assert payload == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "你好"}],
            "stream": True,
        }
        return httpx.Response(
            200,
            text=(
                'data: {"choices":[{"delta":{"role":"assistant","content":""}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"你"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"好"}}]}\n\n'
                "data: [DONE]\n\n"
            ),
            headers={"Content-Type": "text/event-stream"},
        )

    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1/",
        api_key="secret",
        model="test-model",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert list(
        model_client.generate_stream([{"role": "user", "content": "你好"}])
    ) == ["你", "好"]


def test_generate_stream_converts_http_error_to_model_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="test-model",
        http_client=httpx.Client(transport=transport),
    )

    with pytest.raises(ModelRequestError, match="request failed"):
        list(model_client.generate_stream([{"role": "user", "content": "你好"}]))


def test_generate_stream_rejects_invalid_json_event() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text="data: not-json\n\n",
            headers={"Content-Type": "text/event-stream"},
        )
    )
    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="test-model",
        http_client=httpx.Client(transport=transport),
    )

    with pytest.raises(ModelRequestError, match="invalid streaming response"):
        list(model_client.generate_stream([{"role": "user", "content": "你好"}]))


def test_generate_uses_model_messages_and_application_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {
            "model": "application-model",
            "messages": [
                {"role": "system", "content": "你是一名 Python 老师"},
                {"role": "user", "content": "解释装饰器"},
            ],
            "temperature": 0.3,
            "stream": False,
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "回答"}}]},
        )

    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="default-model",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    answer = model_client.generate(
        [
            {"role": "system", "content": "你是一名 Python 老师"},
            {"role": "user", "content": "解释装饰器"},
        ],
        model="application-model",
        temperature=0.3,
    )

    assert answer == "回答"


def test_generate_stream_uses_application_parameters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "application-model"
        assert payload["temperature"] == 1.2
        assert payload["stream"] is True
        return httpx.Response(200, text="data: [DONE]\n\n")

    model_client = OpenAICompatibleClient(
        base_url="https://example.com/v1",
        api_key="secret",
        model="default-model",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert list(
        model_client.generate_stream(
            [{"role": "user", "content": "写一个故事"}],
            model="application-model",
            temperature=1.2,
        )
    ) == []
