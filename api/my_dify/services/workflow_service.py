from __future__ import annotations
import re
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from flask import session
from ..extensions.database import db
from ..models.workflow import WorkflowModel, WorkflowRunModel
from ..schemas.workflow import WorkflowCreate, WorkflowDefinition, WorkflowNode
from .app_service import AppService
from .knowledge_service import KnowledgeService
from .model_runtime_service import ModelRuntimeService
from .tool_service import ToolService


class WorkflowNotFoundError(Exception): pass


class WorkflowService:
    def __init__(self, apps: AppService, knowledge: KnowledgeService, runtime: ModelRuntimeService, tools: ToolService):
        self._apps=apps; self._knowledge=knowledge; self._runtime=runtime; self._tools=tools
    def _owner(self): return str(session["user_id"])
    def get(self, workflow_id: str):
        item=db.session.execute(db.select(WorkflowModel).where(WorkflowModel.id==workflow_id,WorkflowModel.owner_id==self._owner())).scalar_one_or_none()
        if item is None: raise WorkflowNotFoundError(workflow_id)
        return item
    def list(self): return list(db.session.execute(db.select(WorkflowModel).where(WorkflowModel.owner_id==self._owner()).order_by(WorkflowModel.updated_at.desc())).scalars())
    def create(self,data:WorkflowCreate):
        if data.app_id: self._apps.get_app(data.app_id)
        item=WorkflowModel(owner_id=self._owner(),app_id=data.app_id,name=data.name.strip(),definition=data.definition.model_dump(mode="json"))
        db.session.add(item);db.session.commit();db.session.refresh(item);return item
    def update(self,workflow_id:str,data:WorkflowCreate):
        item=self.get(workflow_id)
        if data.app_id:self._apps.get_app(data.app_id)
        item.name=data.name.strip();item.app_id=data.app_id;item.definition=data.definition.model_dump(mode="json")
        db.session.commit();db.session.refresh(item);return item
    def delete(self,workflow_id:str):db.session.delete(self.get(workflow_id));db.session.commit()
    @staticmethod
    def _render(template:str,values:dict[str,Any]):
        return re.sub(r"{{\s*([\w.-]+)\s*}}",lambda match:str(values.get(match.group(1),"")),template)
    def _execute_node(self,node:WorkflowNode,values:dict[str,Any],workflow:WorkflowModel):
        config=node.config;kind=node.type
        if kind=="start":return dict(values)
        if kind=="template":return self._render(str(config.get("template","")),values)
        if kind=="condition":
            actual=values.get(str(config.get("variable","")));expected=config.get("value");operator=config.get("operator","equals")
            return actual==expected if operator=="equals" else str(expected) in str(actual)
        if kind=="knowledge":
            query=self._render(str(config.get("query","{{query}}")),values)
            return self._knowledge.search(str(config["knowledge_base_id"]),query,int(config.get("top_k",4)))
        if kind=="tool":
            arguments={key:self._render(str(value),values) if isinstance(value,str) else value for key,value in dict(config.get("arguments",{})).items()}
            return self._tools.invoke(str(config["name"]),arguments)
        if kind=="llm":
            prompt=self._render(str(config.get("prompt","{{query}}")),values)
            app=self._apps.runtime_config(workflow.app_id) if workflow.app_id else SimpleNamespace(provider_id=None)
            return self._runtime.for_config(app).chat(prompt,model_name=getattr(app,"model_name",None),temperature=getattr(app,"temperature",None))
        if kind=="end":return values.get(str(config.get("output","result")),values)
        raise ValueError(f"unsupported node type: {kind}")
    def run(self,workflow_id:str,inputs:dict[str,Any]):
        workflow=self.get(workflow_id);definition=WorkflowDefinition.model_validate(workflow.definition)
        run=WorkflowRunModel(workflow_id=workflow.id,status="running",inputs=inputs,outputs={},node_runs=[])
        db.session.add(run);db.session.commit()
        values=dict(inputs);node_map={node.id:node for node in definition.nodes};outgoing={node.id:[] for node in definition.nodes}
        for edge in definition.edges:outgoing[edge.source].append(edge)
        queue=[next(node.id for node in definition.nodes if node.type=="start")];visited=set();traces=[];final_output=None
        try:
            while queue:
                node_id=queue.pop(0)
                if node_id in visited:continue
                node=node_map[node_id];started=datetime.now(timezone.utc);output=self._execute_node(node,values,workflow)
                key=str(node.config.get("output_key",node.id));values[key]=output
                traces.append({"node_id":node.id,"type":node.type,"output":output,"duration_ms":int((datetime.now(timezone.utc)-started).total_seconds()*1000)})
                if node.type=="end":final_output=output
                for edge in outgoing[node_id]:
                    if node.type!="condition" or edge.condition is None or edge.condition.lower()==str(bool(output)).lower():queue.append(edge.target)
                visited.add(node_id)
            run.status="succeeded";run.outputs={"result":final_output,"variables":values};run.node_runs=traces
        except Exception as exc:
            run.status="failed";run.error=str(exc);run.node_runs=traces
        run.finished_at=datetime.now(timezone.utc);db.session.commit();db.session.refresh(run);return run
    def list_runs(self,workflow_id:str):
        workflow=self.get(workflow_id)
        return list(db.session.execute(db.select(WorkflowRunModel).where(WorkflowRunModel.workflow_id==workflow.id).order_by(WorkflowRunModel.created_at.desc())).scalars())
