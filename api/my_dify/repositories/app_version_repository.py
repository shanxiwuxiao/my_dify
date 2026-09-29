from ..extensions.database import db
from ..models.app_version import AppVersionModel


class AppVersionRepository:
    def next_version(self, app_id: str) -> int:
        current = db.session.execute(db.select(db.func.max(AppVersionModel.version)).where(AppVersionModel.app_id == app_id)).scalar_one()
        return (current or 0) + 1

    def create(self, version: AppVersionModel) -> AppVersionModel:
        db.session.add(version); db.session.commit(); db.session.refresh(version)
        return version

    def list_by_app(self, app_id: str) -> list[AppVersionModel]:
        return list(db.session.execute(db.select(AppVersionModel).where(AppVersionModel.app_id == app_id).order_by(AppVersionModel.version.desc())).scalars())

    def get(self, app_id: str, version: int) -> AppVersionModel | None:
        return db.session.execute(db.select(AppVersionModel).where(AppVersionModel.app_id == app_id, AppVersionModel.version == version)).scalar_one_or_none()
