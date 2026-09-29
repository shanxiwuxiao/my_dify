"""Database-related Flask CLI commands."""

import click

from ..extensions.database import db
from ..models import app as _app_model  # noqa: F401
from ..models import conversation as _conversation_model  # noqa: F401
from ..models import message as _message_model  # noqa: F401
from ..models import user as _user_model  # noqa: F401
from ..models import app_version as _app_version_model  # noqa: F401
from ..models import model_provider as _model_provider_model  # noqa: F401
from ..models import knowledge as _knowledge_model  # noqa: F401
from ..models import workflow as _workflow_model  # noqa: F401
from ..models import observability as _observability_model  # noqa: F401


@click.command("init-db")
def init_db_command() -> None:
    """Create all database tables for local development."""
    db.create_all()
    click.echo("Initialized the database.")
