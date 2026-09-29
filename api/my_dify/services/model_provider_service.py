from flask import session
from ..core.credential_cipher import CredentialCipher
from ..models.model_provider import ModelProviderModel
from ..repositories.model_provider_repository import ModelProviderRepository
from ..schemas.model_provider import ModelProviderCreate


class ProviderNotFoundError(Exception):
    pass


class ModelProviderService:
    def __init__(self, repository: ModelProviderRepository, cipher: CredentialCipher):
        self._repository = repository; self._cipher = cipher

    def _owner(self) -> str:
        return str(session["user_id"])

    def create(self, data: ModelProviderCreate) -> ModelProviderModel:
        return self._repository.create(ModelProviderModel(owner_id=self._owner(), name=data.name.strip(), base_url=str(data.base_url).rstrip('/'), api_key_encrypted=self._cipher.encrypt(data.api_key), default_model=data.default_model.strip()))

    def list(self) -> list[ModelProviderModel]: return self._repository.list(self._owner())

    def get(self, provider_id: str) -> ModelProviderModel:
        provider = self._repository.get(provider_id, self._owner())
        if provider is None: raise ProviderNotFoundError(provider_id)
        return provider

    def api_key(self, provider: ModelProviderModel) -> str: return self._cipher.decrypt(provider.api_key_encrypted)

    def delete(self, provider_id: str) -> None: self._repository.delete(self.get(provider_id))
