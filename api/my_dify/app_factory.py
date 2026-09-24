"""Flask application factory."""

from flask import Flask

from .commands.database import init_db_command
from .configs.settings import Settings
from .controllers.app_chat import app_chat_bp
from .controllers.apps import apps_bp
from .controllers.chat import chat_bp
from .controllers.conversation_chat import conversation_chat_bp
from .controllers.conversations import conversations_bp
from .controllers.health import health_bp
from .core.model_runtime.openai_compatible import OpenAICompatibleClient
from .extensions.database import db
from .repositories.app_repository import AppRepository
from .repositories.conversation_repository import ConversationRepository
from .repositories.message_repository import MessageRepository
from .services.app_service import AppService
from .services.chat_service import ChatService
from .services.conversation_chat_service import ConversationChatService
from .services.conversation_service import ConversationService

def create_app(
    settings: Settings | None = None,
    chat_service: ChatService | None = None,
    app_service: AppService | None = None,
) -> Flask:
    """Create the Flask app and assemble its application-level dependencies."""
    resolved_settings = settings or Settings()
    resolved_chat_service = chat_service

    if resolved_chat_service is None:
        model_client = OpenAICompatibleClient(
            base_url=resolved_settings.model_base_url,
            api_key=resolved_settings.model_api_key,
            model=resolved_settings.model_name,
            timeout=resolved_settings.model_timeout,
        )
        resolved_chat_service = ChatService(model_client)

    resolved_app_service = app_service or AppService(AppRepository())
    conversation_service = ConversationService(
        ConversationRepository(),
        resolved_app_service,
    )
    conversation_chat_service = ConversationChatService(
        conversation_service,
        MessageRepository(),
        resolved_chat_service,
    )

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = resolved_settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    app.extensions["chat_service"] = resolved_chat_service
    app.extensions["app_service"] = resolved_app_service
    app.extensions["conversation_service"] = conversation_service
    app.extensions["conversation_chat_service"] = conversation_chat_service
    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(apps_bp)
    app.register_blueprint(app_chat_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(conversation_chat_bp)
    app.cli.add_command(init_db_command)
    return app
