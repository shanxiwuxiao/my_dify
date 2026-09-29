from datetime import datetime, timezone
from uuid import uuid4
from ..extensions.database import db

app_knowledge_bases = db.Table(
    "app_knowledge_bases",
    db.Column("app_id", db.String(36), db.ForeignKey("apps.id", ondelete="CASCADE"), primary_key=True),
    db.Column("knowledge_base_id", db.String(36), db.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), primary_key=True),
)


class KnowledgeBaseModel(db.Model):
    __tablename__ = "knowledge_bases"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), default="", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    documents = db.relationship("DocumentModel", back_populates="knowledge_base", cascade="all, delete-orphan")


class DocumentModel(db.Model):
    __tablename__ = "documents"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    knowledge_base_id = db.Column(db.String(36), db.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    knowledge_base = db.relationship("KnowledgeBaseModel", back_populates="documents")
    segments = db.relationship("DocumentSegmentModel", back_populates="document", cascade="all, delete-orphan", order_by="DocumentSegmentModel.position")


class DocumentSegmentModel(db.Model):
    __tablename__ = "document_segments"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.Text, nullable=False)
    document = db.relationship("DocumentModel", back_populates="segments")
