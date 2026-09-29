from ..extensions.database import db
from ..models.model_provider import ModelProviderModel


class ModelProviderRepository:
    def create(self, provider: ModelProviderModel) -> ModelProviderModel:
        db.session.add(provider); db.session.commit(); db.session.refresh(provider)
        return provider

    def list(self, owner_id: str) -> list[ModelProviderModel]:
        return list(db.session.execute(db.select(ModelProviderModel).where(ModelProviderModel.owner_id == owner_id).order_by(ModelProviderModel.created_at.desc())).scalars())

    def get(self, provider_id: str, owner_id: str) -> ModelProviderModel | None:
        return db.session.execute(db.select(ModelProviderModel).where(ModelProviderModel.id == provider_id, ModelProviderModel.owner_id == owner_id)).scalar_one_or_none()

    def delete(self, provider: ModelProviderModel) -> None:
        db.session.delete(provider); db.session.commit()
