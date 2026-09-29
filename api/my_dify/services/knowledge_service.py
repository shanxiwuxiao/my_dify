from __future__ import annotations

import json
from flask import session
from ..core.embeddings import LocalHashEmbedding
from ..extensions.database import db
from ..models.app import AppModel
from ..models.knowledge import DocumentModel, DocumentSegmentModel, KnowledgeBaseModel


class KnowledgeNotFoundError(Exception): pass


class KnowledgeService:
    def __init__(self): self._embedding = LocalHashEmbedding()
    def _owner(self) -> str: return str(session["user_id"])
    def get(self, knowledge_base_id: str) -> KnowledgeBaseModel:
        item = db.session.execute(db.select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_base_id, KnowledgeBaseModel.owner_id == self._owner())).scalar_one_or_none()
        if item is None: raise KnowledgeNotFoundError(knowledge_base_id)
        return item
    def create(self, name: str, description: str) -> KnowledgeBaseModel:
        item = KnowledgeBaseModel(owner_id=self._owner(), name=name.strip(), description=description)
        db.session.add(item); db.session.commit(); db.session.refresh(item); return item
    def list(self): return list(db.session.execute(db.select(KnowledgeBaseModel).where(KnowledgeBaseModel.owner_id == self._owner()).order_by(KnowledgeBaseModel.created_at.desc())).scalars())
    def delete(self, knowledge_base_id: str): db.session.delete(self.get(knowledge_base_id)); db.session.commit()
    @staticmethod
    def _chunks(content: str, size: int = 800, overlap: int = 120):
        start = 0
        while start < len(content):
            chunk = content[start:start + size].strip()
            if chunk: yield chunk
            if start + size >= len(content): break
            start += size - overlap
    def add_document(self, knowledge_base_id: str, name: str, content: str) -> DocumentModel:
        knowledge = self.get(knowledge_base_id)
        document = DocumentModel(knowledge_base_id=knowledge.id, name=name.strip(), content=content)
        for position, chunk in enumerate(self._chunks(content)):
            document.segments.append(DocumentSegmentModel(position=position, content=chunk, embedding=json.dumps(self._embedding.embed(chunk))))
        db.session.add(document); db.session.commit(); db.session.refresh(document); return document
    def list_documents(self, knowledge_base_id: str): return self.get(knowledge_base_id).documents
    def delete_document(self, knowledge_base_id: str, document_id: str):
        self.get(knowledge_base_id)
        document=db.session.execute(db.select(DocumentModel).where(DocumentModel.id==document_id,DocumentModel.knowledge_base_id==knowledge_base_id)).scalar_one_or_none()
        if document is None:raise KnowledgeNotFoundError(document_id)
        db.session.delete(document);db.session.commit()
    def search(self, knowledge_base_id: str, query: str, top_k: int = 4):
        knowledge = self.get(knowledge_base_id); query_vector = self._embedding.embed(query); scored = []
        for document in knowledge.documents:
            for segment in document.segments:
                score = self._embedding.similarity(query_vector, json.loads(segment.embedding))
                scored.append({"segment_id": segment.id, "document_id": document.id, "document_name": document.name, "content": segment.content, "score": score})
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]
    def bind_app(self, app: AppModel, ids: list[str]):
        bases = [self.get(item_id) for item_id in ids]
        app.knowledge_bases = bases; db.session.commit()
    def retrieve_for_app(self, app: AppModel, query: str, top_k: int = 4):
        results = []
        for knowledge in app.knowledge_bases: results.extend(self.search(knowledge.id, query, top_k))
        return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
