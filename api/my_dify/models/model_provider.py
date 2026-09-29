from datetime import datetime, timezone
from uuid import uuid4
from ..extensions.database import db


class ModelProviderModel(db.Model):
    __tablename__ = "model_providers"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    base_url = db.Column(db.String(500), nullable=False)
    api_key_encrypted = db.Column(db.Text, nullable=False)
    default_model = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
