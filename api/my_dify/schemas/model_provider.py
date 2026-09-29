from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ModelProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: HttpUrl
    api_key: str = Field(min_length=1, max_length=500)
    default_model: str = Field(min_length=1, max_length=100)


class ModelProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    base_url: str
    default_model: str
    api_key_masked: str
    created_at: datetime
