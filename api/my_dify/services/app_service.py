"""Application management use cases."""

from flask import session

from ..models.app import AppModel
from ..models.app_version import AppVersionModel
from ..repositories.app_repository import AppRepository
from ..repositories.app_version_repository import AppVersionRepository
from ..schemas.app import AppCreate, AppUpdate
from .exceptions import AppNotFoundError
from .model_provider_service import ModelProviderService


class AppService:
    def __init__(self, repository: AppRepository, version_repository: AppVersionRepository | None = None, providers: ModelProviderService | None = None):
        self._repository = repository
        self._versions = version_repository or AppVersionRepository()
        self._providers = providers

    def create_app(self, data: AppCreate) -> AppModel:
        if data.provider_id and self._providers: self._providers.get(data.provider_id)
        app = AppModel(owner_id=self._owner_id(), **data.model_dump())
        return self._repository.create(app)

    def list_apps(self) -> list[AppModel]:
        return self._repository.list_all(self._owner_id())

    def get_app(self, app_id: str) -> AppModel:
        app = self._repository.get_by_id(app_id, self._owner_id())
        if app is None:
            raise AppNotFoundError(app_id)
        return app

    @staticmethod
    def _owner_id() -> str:
        owner_id = session.get("user_id")
        if not owner_id:
            raise RuntimeError("authenticated user context is required")
        return owner_id

    def update_app(self, app_id: str, data: AppUpdate) -> AppModel:
        app = self.get_app(app_id)
        if data.provider_id and self._providers: self._providers.get(data.provider_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(app, field_name, value)
        return self._repository.save(app)

    def delete_app(self, app_id: str) -> None:
        app = self.get_app(app_id)
        self._repository.delete(app)

    def publish(self, app_id: str) -> AppVersionModel:
        app = self.get_app(app_id)
        version_number = self._versions.next_version(app.id)
        version = self._versions.create(AppVersionModel(
            app_id=app.id, version=version_number, system_prompt=app.system_prompt,
            model_name=app.model_name, temperature=app.temperature, provider_id=app.provider_id,
        ))
        app.published_version = version_number
        self._repository.save(app)
        return version

    def list_versions(self, app_id: str) -> list[AppVersionModel]:
        app = self.get_app(app_id)
        return self._versions.list_by_app(app.id)

    def runtime_config(self, app_id: str) -> AppModel | AppVersionModel:
        app = self.get_app(app_id)
        if app.published_version is None:
            return app
        return self._versions.get(app.id, app.published_version) or app
