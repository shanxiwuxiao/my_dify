from my_dify.configs.settings import Settings


def test_settings_have_default_model_name(monkeypatch) -> None:
    monkeypatch.delenv("MY_DIFY_MODEL_NAME", raising=False)

    settings = Settings(_env_file=None)

    assert settings.model_name == "gpt-4.1-mini"


def test_environment_overrides_default_model_name(monkeypatch) -> None:
    monkeypatch.setenv("MY_DIFY_MODEL_NAME", "local-model")

    settings = Settings(_env_file=None)

    assert settings.model_name == "local-model"


def test_render_postgres_url_uses_psycopg_driver() -> None:
    settings = Settings(
        database_url="postgresql://user:password@localhost/my_dify",
        _env_file=None,
    )

    assert settings.database_url.startswith("postgresql+psycopg://")
