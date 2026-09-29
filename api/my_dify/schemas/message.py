"""Schemas for persisted conversation messages."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    status: str
    created_at: datetime


class ConversationChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    sources: list[dict[str, Any]] = Field(default_factory=list)
