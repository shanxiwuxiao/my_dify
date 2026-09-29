from flask import Blueprint,current_app,jsonify,request
from ..services.evaluation_service import EvaluationNotFoundError
from ..services.exceptions import AppNotFoundError

observability_bp=Blueprint("observability",__name__)
@observability_bp.get("/api/monitoring/summary")
def summary():return jsonify(current_app.extensions["monitoring_service"].summary())
@observability_bp.get("/api/evaluation-datasets")
def list_datasets():
    items=[{"id":x.id,"name":x.name,"case_count":len(x.cases),"created_at":x.created_at.isoformat()} for x in current_app.extensions["evaluation_service"].list()];return jsonify(items=items,total=len(items))
@observability_bp.post("/api/evaluation-datasets")
def create_dataset():
    name=str((request.get_json(silent=True) or {}).get("name","")).strip()
    if not name:return jsonify(code="invalid_request",message="Name is required"),400
    x=current_app.extensions["evaluation_service"].create(name);return jsonify(id=x.id,name=x.name,case_count=0,created_at=x.created_at.isoformat()),201
@observability_bp.post("/api/evaluation-datasets/<dataset_id>/cases")
def add_case(dataset_id):
    data=request.get_json(silent=True) or {};input_text=str(data.get("input","")).strip();expected=str(data.get("expected","")).strip()
    if not input_text or not expected:return jsonify(code="invalid_request",message="Input and expected are required"),400
    try:x=current_app.extensions["evaluation_service"].add_case(dataset_id,input_text,expected)
    except EvaluationNotFoundError:return jsonify(code="dataset_not_found",message="Dataset not found"),404
    return jsonify(id=x.id,input=x.input,expected=x.expected),201
@observability_bp.get("/api/evaluation-datasets/<dataset_id>/cases")
def list_cases(dataset_id):
    try:dataset=current_app.extensions["evaluation_service"].get(dataset_id)
    except EvaluationNotFoundError:return jsonify(code="dataset_not_found",message="Dataset not found"),404
    return jsonify(items=[{"id":x.id,"input":x.input,"expected":x.expected} for x in dataset.cases],total=len(dataset.cases))
@observability_bp.delete("/api/evaluation-datasets/<dataset_id>/cases/<case_id>")
def delete_case(dataset_id,case_id):
    try:current_app.extensions["evaluation_service"].delete_case(dataset_id,case_id)
    except EvaluationNotFoundError:return jsonify(code="case_not_found",message="Evaluation case not found"),404
    return "",204
@observability_bp.post("/api/evaluation-datasets/<dataset_id>/runs")
def run_evaluation(dataset_id):
    app_id=str((request.get_json(silent=True) or {}).get("app_id","")).strip()
    try:x=current_app.extensions["evaluation_service"].run(dataset_id,app_id)
    except EvaluationNotFoundError:return jsonify(code="dataset_not_found",message="Dataset not found"),404
    except AppNotFoundError:return jsonify(code="app_not_found",message="Application not found"),404
    return jsonify(id=x.id,dataset_id=x.dataset_id,app_id=x.app_id,passed=x.passed,total=x.total,pass_rate=x.passed/x.total if x.total else 0,results=x.results,created_at=x.created_at.isoformat()),201
@observability_bp.get("/api/evaluation-datasets/<dataset_id>/runs")
def list_evaluation_runs(dataset_id):
    try:runs=current_app.extensions["evaluation_service"].list_runs(dataset_id)
    except EvaluationNotFoundError:return jsonify(code="dataset_not_found",message="Dataset not found"),404
    items=[{"id":x.id,"app_id":x.app_id,"passed":x.passed,"total":x.total,"pass_rate":x.passed/x.total if x.total else 0,"results":x.results,"created_at":x.created_at.isoformat()} for x in runs]
    return jsonify(items=items,total=len(items))
