from flask import Blueprint,current_app,jsonify,request
from pydantic import ValidationError
from ..schemas.workflow import WorkflowCreate,WorkflowRunRequest
from ..services.workflow_service import WorkflowNotFoundError,WorkflowService

workflows_bp=Blueprint("workflows",__name__)
def _service()->WorkflowService:return current_app.extensions["workflow_service"]
def _workflow(item):return {"id":item.id,"name":item.name,"app_id":item.app_id,"definition":item.definition,"created_at":item.created_at.isoformat(),"updated_at":item.updated_at.isoformat()}
def _run(item):return {"id":item.id,"workflow_id":item.workflow_id,"status":item.status,"inputs":item.inputs,"outputs":item.outputs,"node_runs":item.node_runs,"error":item.error,"created_at":item.created_at.isoformat(),"finished_at":item.finished_at.isoformat() if item.finished_at else None}
def _missing():return jsonify(code="workflow_not_found",message="Workflow not found"),404

@workflows_bp.get("/api/workflows")
def list_workflows():
    items=[_workflow(x) for x in _service().list()];return jsonify(items=items,total=len(items))
@workflows_bp.post("/api/workflows")
def create_workflow():
    try:data=WorkflowCreate.model_validate(request.get_json())
    except (ValidationError,TypeError):return jsonify(code="invalid_workflow",message="Invalid workflow graph"),400
    return jsonify(_workflow(_service().create(data))),201
@workflows_bp.get("/api/workflows/<workflow_id>")
def get_workflow(workflow_id):
    try:return jsonify(_workflow(_service().get(workflow_id)))
    except WorkflowNotFoundError:return _missing()
@workflows_bp.put("/api/workflows/<workflow_id>")
def update_workflow(workflow_id):
    try:data=WorkflowCreate.model_validate(request.get_json());return jsonify(_workflow(_service().update(workflow_id,data)))
    except (ValidationError,TypeError):return jsonify(code="invalid_workflow",message="Invalid workflow graph"),400
    except WorkflowNotFoundError:return _missing()
@workflows_bp.delete("/api/workflows/<workflow_id>")
def delete_workflow(workflow_id):
    try:_service().delete(workflow_id)
    except WorkflowNotFoundError:return _missing()
    return "",204
@workflows_bp.post("/api/workflows/<workflow_id>/runs")
def run_workflow(workflow_id):
    try:data=WorkflowRunRequest.model_validate(request.get_json(silent=True) or {});run=_service().run(workflow_id,data.inputs)
    except (ValidationError,TypeError):return jsonify(code="invalid_request",message="Invalid inputs"),400
    except WorkflowNotFoundError:return _missing()
    return jsonify(_run(run)),201
@workflows_bp.get("/api/workflows/<workflow_id>/runs")
def list_runs(workflow_id):
    try:items=[_run(x) for x in _service().list_runs(workflow_id)]
    except WorkflowNotFoundError:return _missing()
    return jsonify(items=items,total=len(items))
