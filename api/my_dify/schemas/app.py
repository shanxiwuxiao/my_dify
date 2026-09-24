"""Schemas used by application management endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AppCreate(BaseModel):
    """Payload used to create an AI application."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(default="", max_length=10000)
    model_name: str = Field(default="deepseek-flash", min_length=1, max_length=100)
    temperature: float = Field(default=0.7, ge=0, le=2)

    @field_validator("name", "model_name", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("value cannot be empty")
        return value


class AppUpdate(BaseModel):
    """Partial payload used to update an AI application."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    system_prompt: str | None = Field(default=None, max_length=10000)
    model_name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=0, le=2)

    @field_validator("name", "model_name", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("value cannot be empty")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> "AppUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        if any(getattr(self, field_name) is None for field_name in self.model_fields_set):
            raise ValueError("updated fields cannot be null")
        return self


class AppResponse(BaseModel):
    """Public representation of an AI application."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    system_prompt: str
    model_name: str
    temperature: float
    created_at: datetime
    updated_at: datetime
