from collections.abc import Iterator

from my_dify.core.model_runtime.base import ModelMessage
from my_dify.services.chat_service import ChatService


class FakeModelClient:
    def __init__(self):
        self.messages: list[ModelMessage] | None = None
        self.model: str | None = None
        self.temperature: float | None = None

    def generate(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        self.messages = messages
        self.model = model
        self.temperature = temperature
        return f"Generated: {messages[-1]['content']}"

    def generate_stream(
        self,
        messages: list[ModelMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Iterator[str]:
        self.messages = messages
        self.model = model
        self.temperature = temperature
        yield "Generated: "
        yield messages[-1]["content"]


def test_chat_service_delegates_chinese_message_to_model() -> None:
    service = ChatService(FakeModelClient())

    assert service.chat("你好") == "Generated: 你好"


def test_chat_service_delegates_english_message_to_model() -> None:
    service = ChatService(FakeModelClient())

    assert service.chat("What is Dify?") == "Generated: What is Dify?"


def test_chat_service_delegates_stream_to_model() -> None:
    service = ChatService(FakeModelClient())

    assert list(service.stream_chat("你好")) == ["Generated: ", "你好"]


def test_chat_service_builds_system_and_user_messages() -> None:
    model_client = FakeModelClient()
    service = ChatService(model_client)

    service.chat(
        "解释装饰器",
        system_prompt="你是一名 Python 老师",
        model_name="deepseek-flash",
        temperature=0.3,
    )

    assert model_client.messages == [
        {"role": "system", "content": "你是一名 Python 老师"},
        {"role": "user", "content": "解释装饰器"},
    ]
    assert model_client.model == "deepseek-flash"
    assert model_client.temperature == 0.3


def test_chat_service_omits_blank_system_prompt() -> None:
    model_client = FakeModelClient()
    service = ChatService(model_client)

    service.chat("你好", system_prompt="   ")

    assert model_client.messages == [{"role": "user", "content": "你好"}]
