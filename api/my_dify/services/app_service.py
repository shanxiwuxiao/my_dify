"""Application management use cases."""

from ..models.app import AppModel
from ..repositories.app_repository import AppRepository
from ..schemas.app import AppCreate, AppUpdate
from .exceptions import AppNotFoundError


class AppService:
    def __init__(self, repository: AppRepository):
        self._repository = repository

    def create_app(self, data: AppCreate) -> AppModel:
        app = AppModel(**data.model_dump())
        return self._repository.create(app)

    def list_apps(self) -> list[AppModel]:
        return self._repository.list_all()

    def get_app(self, app_id: str) -> AppModel:
        app = self._repository.get_by_id(app_id)
        if app is None:
            raise AppNotFoundError(app_id)
        return app

    def update_app(self, app_id: str, data: AppUpdate) -> AppModel:
        app = self.get_app(app_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(app, field_name, value)
        return self._repository.save(app)

    def delete_app(self, app_id: str) -> None:
        app = self.get_app(app_id)
        self._repository.delete(app)
