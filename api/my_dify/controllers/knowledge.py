from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError
from ..schemas.knowledge import DocumentCreate, DocumentResponse, KnowledgeBaseCreate, KnowledgeBaseResponse, SearchRequest
from ..services.app_service import AppService
from ..services.exceptions import AppNotFoundError
from ..services.knowledge_service import KnowledgeNotFoundError, KnowledgeService

knowledge_bp = Blueprint("knowledge", __name__)
def _service() -> KnowledgeService: return current_app.extensions["knowledge_service"]
def _kb(item): return KnowledgeBaseResponse.model_validate(item).model_dump(mode="json")
def _doc(item): return DocumentResponse.model_validate(item).model_dump(mode="json")
def _missing(): return jsonify(code="knowledge_not_found", message="Knowledge base not found"), 404


@knowledge_bp.post("/api/knowledge-bases")
def create_knowledge():
    try: data = KnowledgeBaseCreate.model_validate(request.get_json())
    except (ValidationError, TypeError): return jsonify(code="invalid_request", message="Invalid request"), 400
    return jsonify(_kb(_service().create(data.name, data.description))), 201


@knowledge_bp.get("/api/knowledge-bases")
def list_knowledge():
    items = [_kb(item) for item in _service().list()]; return jsonify(items=items, total=len(items))


@knowledge_bp.delete("/api/knowledge-bases/<knowledge_id>")
def delete_knowledge(knowledge_id: str):
    try: _service().delete(knowledge_id)
    except KnowledgeNotFoundError: return _missing()
    return "", 204


@knowledge_bp.post("/api/knowledge-bases/<knowledge_id>/documents")
def add_document(knowledge_id: str):
    try:
        data = DocumentCreate.model_validate(request.get_json())
        document = _service().add_document(knowledge_id, data.name, data.content)
    except (ValidationError, TypeError): return jsonify(code="invalid_request", message="Invalid request"), 400
    except KnowledgeNotFoundError: return _missing()
    return jsonify(_doc(document)), 201


@knowledge_bp.get("/api/knowledge-bases/<knowledge_id>/documents")
def list_documents(knowledge_id: str):
    try: items = [_doc(item) for item in _service().list_documents(knowledge_id)]
    except KnowledgeNotFoundError: return _missing()
    return jsonify(items=items, total=len(items))


@knowledge_bp.delete("/api/knowledge-bases/<knowledge_id>/documents/<document_id>")
def delete_document(knowledge_id: str, document_id: str):
    try:_service().delete_document(knowledge_id,document_id)
    except KnowledgeNotFoundError:return _missing()
    return "",204


@knowledge_bp.post("/api/knowledge-bases/<knowledge_id>/search")
def search_knowledge(knowledge_id: str):
    try:
        data = SearchRequest.model_validate(request.get_json())
        return jsonify(items=_service().search(knowledge_id, data.query, data.top_k))
    except (ValidationError, TypeError): return jsonify(code="invalid_request", message="Invalid request"), 400
    except KnowledgeNotFoundError: return _missing()


@knowledge_bp.put("/api/apps/<app_id>/knowledge-bases")
def bind_knowledge(app_id: str):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("knowledge_base_ids"), list): return jsonify(code="invalid_request", message="Invalid request"), 400
    try:
        app = current_app.extensions["app_service"].get_app(app_id)
        _service().bind_app(app, payload["knowledge_base_ids"])
    except AppNotFoundError: return jsonify(code="app_not_found", message="Application not found"), 404
    except KnowledgeNotFoundError: return _missing()
    return jsonify(knowledge_base_ids=[item.id for item in app.knowledge_bases])


@knowledge_bp.get("/api/apps/<app_id>/knowledge-bases")
def get_bound_knowledge(app_id: str):
    try: app = current_app.extensions["app_service"].get_app(app_id)
    except AppNotFoundError: return jsonify(code="app_not_found", message="Application not found"), 404
    return jsonify(knowledge_base_ids=[item.id for item in app.knowledge_bases])
