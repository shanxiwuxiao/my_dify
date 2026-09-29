from datetime import datetime,timezone
from flask import session
from ..extensions.database import db
from ..models.observability import ModelCallLogModel


class MonitoringService:
    def record(self,app_id,model,status,input_chars,output_chars,started,error=None):
        user_id=session.get("user_id")
        if not user_id:return
        duration=int((datetime.now(timezone.utc)-started).total_seconds()*1000)
        db.session.add(ModelCallLogModel(owner_id=user_id,app_id=app_id,model_name=model,status=status,input_chars=input_chars,output_chars=output_chars,duration_ms=duration,error=str(error)[:500] if error else None));db.session.commit()
    def summary(self):
        rows=list(db.session.execute(db.select(ModelCallLogModel).where(ModelCallLogModel.owner_id==session["user_id"]).order_by(ModelCallLogModel.created_at.desc()).limit(200)).scalars())
        return {"total_calls":len(rows),"failed_calls":sum(x.status=="failed" for x in rows),"input_chars":sum(x.input_chars for x in rows),"output_chars":sum(x.output_chars for x in rows),"average_duration_ms":round(sum(x.duration_ms for x in rows)/len(rows)) if rows else 0,"items":[{"id":x.id,"app_id":x.app_id,"model_name":x.model_name,"status":x.status,"input_chars":x.input_chars,"output_chars":x.output_chars,"duration_ms":x.duration_ms,"error":x.error,"created_at":x.created_at.isoformat()} for x in rows]}
