"""Request and response schemas for chat endpoints."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Validated payload accepted by the chat endpoint."""

    message: str = Field(
        max_length=2000,
        description="聊天消息，去除首尾空格后不能为空，最长 2000 个字符",
    )

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: Any) -> Any:
        """Strip surrounding whitespace before length and emptiness checks."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("message cannot be empty")
        return value


class ChatResponse(BaseModel):
    """Successful response returned by the chat endpoint."""

    answer: str
