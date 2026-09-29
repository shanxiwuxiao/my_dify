from flask import session
from ..extensions.database import db
from ..models.observability import EvaluationCaseModel,EvaluationDatasetModel,EvaluationRunModel
from .app_service import AppService
from .model_runtime_service import ModelRuntimeService


class EvaluationNotFoundError(Exception):pass
class EvaluationService:
    def __init__(self,apps:AppService,runtime:ModelRuntimeService):self._apps=apps;self._runtime=runtime
    def _owner(self):return str(session["user_id"])
    def get(self,dataset_id):
        item=db.session.execute(db.select(EvaluationDatasetModel).where(EvaluationDatasetModel.id==dataset_id,EvaluationDatasetModel.owner_id==self._owner())).scalar_one_or_none()
        if item is None:raise EvaluationNotFoundError(dataset_id)
        return item
    def list(self):return list(db.session.execute(db.select(EvaluationDatasetModel).where(EvaluationDatasetModel.owner_id==self._owner())).scalars())
    def create(self,name):item=EvaluationDatasetModel(owner_id=self._owner(),name=name);db.session.add(item);db.session.commit();db.session.refresh(item);return item
    def add_case(self,dataset_id,input_text,expected):item=EvaluationCaseModel(dataset_id=self.get(dataset_id).id,input=input_text,expected=expected);db.session.add(item);db.session.commit();db.session.refresh(item);return item
    def delete_case(self,dataset_id,case_id):
        dataset=self.get(dataset_id);case=next((x for x in dataset.cases if x.id==case_id),None)
        if case is None:raise EvaluationNotFoundError(case_id)
        db.session.delete(case);db.session.commit()
    def list_runs(self,dataset_id):
        dataset=self.get(dataset_id)
        return list(db.session.execute(db.select(EvaluationRunModel).where(EvaluationRunModel.dataset_id==dataset.id).order_by(EvaluationRunModel.created_at.desc())).scalars())
    def run(self,dataset_id,app_id):
        dataset=self.get(dataset_id);config=self._apps.runtime_config(app_id);chat=self._runtime.for_config(config);results=[]
        for case in dataset.cases:
            answer=chat.chat(case.input,system_prompt=config.system_prompt,model_name=config.model_name,temperature=config.temperature)
            passed=case.expected.lower() in answer.lower();results.append({"case_id":case.id,"input":case.input,"expected":case.expected,"answer":answer,"passed":passed})
        run=EvaluationRunModel(dataset_id=dataset.id,app_id=app_id,passed=sum(x["passed"] for x in results),total=len(results),results=results);db.session.add(run);db.session.commit();db.session.refresh(run);return run
