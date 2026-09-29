from datetime import datetime, timezone
from uuid import uuid4
from ..extensions.database import db


class WorkflowModel(db.Model):
    __tablename__ = "workflows"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    app_id = db.Column(db.String(36), db.ForeignKey("apps.id", ondelete="SET NULL"), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class WorkflowRunModel(db.Model):
    __tablename__ = "workflow_runs"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    workflow_id = db.Column(db.String(36), db.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    inputs = db.Column(db.JSON, nullable=False)
    outputs = db.Column(db.JSON, nullable=False, default=dict)
    node_runs = db.Column(db.JSON, nullable=False, default=list)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
