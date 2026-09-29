from datetime import datetime, timezone
from uuid import uuid4
from ..extensions.database import db


class ModelCallLogModel(db.Model):
    __tablename__="model_call_logs"
    id=db.Column(db.String(36),primary_key=True,default=lambda:str(uuid4()))
    owner_id=db.Column(db.String(36),db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    app_id=db.Column(db.String(36),db.ForeignKey("apps.id",ondelete="SET NULL"),nullable=True,index=True)
    model_name=db.Column(db.String(100),nullable=True)
    status=db.Column(db.String(20),nullable=False)
    input_chars=db.Column(db.Integer,nullable=False)
    output_chars=db.Column(db.Integer,nullable=False)
    duration_ms=db.Column(db.Integer,nullable=False)
    error=db.Column(db.String(500),nullable=True)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False,index=True)


class EvaluationDatasetModel(db.Model):
    __tablename__="evaluation_datasets"
    id=db.Column(db.String(36),primary_key=True,default=lambda:str(uuid4()))
    owner_id=db.Column(db.String(36),db.ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    name=db.Column(db.String(100),nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    cases=db.relationship("EvaluationCaseModel",cascade="all, delete-orphan",back_populates="dataset")


class EvaluationCaseModel(db.Model):
    __tablename__="evaluation_cases"
    id=db.Column(db.String(36),primary_key=True,default=lambda:str(uuid4()))
    dataset_id=db.Column(db.String(36),db.ForeignKey("evaluation_datasets.id",ondelete="CASCADE"),nullable=False,index=True)
    input=db.Column(db.Text,nullable=False)
    expected=db.Column(db.Text,nullable=False)
    dataset=db.relationship("EvaluationDatasetModel",back_populates="cases")


class EvaluationRunModel(db.Model):
    __tablename__="evaluation_runs"
    id=db.Column(db.String(36),primary_key=True,default=lambda:str(uuid4()))
    dataset_id=db.Column(db.String(36),db.ForeignKey("evaluation_datasets.id",ondelete="CASCADE"),nullable=False)
    app_id=db.Column(db.String(36),db.ForeignKey("apps.id",ondelete="CASCADE"),nullable=False)
    passed=db.Column(db.Integer,nullable=False);total=db.Column(db.Integer,nullable=False)
    results=db.Column(db.JSON,nullable=False);created_at=db.Column(db.DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
