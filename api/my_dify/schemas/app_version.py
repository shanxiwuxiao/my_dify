from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AppVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    app_id: str
    version: int
    system_prompt: str
    model_name: str
    temperature: float
    provider_id: str | None
    created_at: datetime
