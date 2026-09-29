"""Persistence operations for AI applications."""

from ..extensions.database import db
from ..models.app import AppModel


class AppRepository:
    def create(self, app: AppModel) -> AppModel:
        db.session.add(app)
        db.session.commit()
        db.session.refresh(app)
        return app

    def list_all(self, owner_id: str) -> list[AppModel]:
        statement = db.select(AppModel).where(AppModel.owner_id == owner_id).order_by(AppModel.created_at.desc())
        return list(db.session.execute(statement).scalars())

    def get_by_id(self, app_id: str, owner_id: str) -> AppModel | None:
        return db.session.execute(db.select(AppModel).where(AppModel.id == app_id, AppModel.owner_id == owner_id)).scalar_one_or_none()

    def save(self, app: AppModel) -> AppModel:
        db.session.commit()
        db.session.refresh(app)
        return app

    def delete(self, app: AppModel) -> None:
        db.session.delete(app)
        db.session.commit()
