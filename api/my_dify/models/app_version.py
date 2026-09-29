from datetime import datetime, timezone
from uuid import uuid4
from ..extensions.database import db


class AppVersionModel(db.Model):
    __tablename__ = "app_versions"
    __table_args__ = (db.UniqueConstraint("app_id", "version", name="uq_app_version"),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    app_id = db.Column(db.String(36), db.ForeignKey("apps.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = db.Column(db.String(36), db.ForeignKey("model_providers.id", ondelete="SET NULL"), nullable=True)
    version = db.Column(db.Integer, nullable=False)
    system_prompt = db.Column(db.Text, default="", nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    app = db.relationship("AppModel", back_populates="versions")
