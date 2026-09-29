from flask import Blueprint,current_app,jsonify,request
from pydantic import BaseModel,Field,ValidationError
from ..services.agent_service import AgentService
from ..services.exceptions import AppNotFoundError
from ..services.tool_service import ToolError,ToolService

agent_bp=Blueprint("agent",__name__)
class AgentRequest(BaseModel):
    query:str=Field(min_length=1,max_length=10000)
    max_steps:int=Field(default=5,ge=1,le=10)
@agent_bp.get("/api/tools")
def list_tools():return jsonify(items=current_app.extensions["tool_service"].definitions())
@agent_bp.post("/api/apps/<app_id>/agent")
def run_agent(app_id):
    try:data=AgentRequest.model_validate(request.get_json());result=current_app.extensions["agent_service"].run(app_id,data.query,data.max_steps)
    except (ValidationError,TypeError):return jsonify(code="invalid_request",message="Invalid request"),400
    except AppNotFoundError:return jsonify(code="app_not_found",message="Application not found"),404
    except ToolError as exc:return jsonify(code="agent_error",message=str(exc)),422
    return jsonify(result)
