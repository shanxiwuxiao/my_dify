"""Flask application factory."""

from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory, session
from werkzeug.middleware.proxy_fix import ProxyFix

from .commands.database import init_db_command
from .configs.settings import Settings
from .controllers.app_chat import app_chat_bp
from .controllers.auth import auth_bp
from .controllers.apps import apps_bp
from .controllers.chat import chat_bp
from .controllers.conversation_chat import conversation_chat_bp
from .controllers.conversations import conversations_bp
from .controllers.health import health_bp
from .controllers.model_providers import model_providers_bp
from .controllers.knowledge import knowledge_bp
from .controllers.workflows import workflows_bp
from .controllers.agent import agent_bp
from .controllers.observability import observability_bp
from .core.credential_cipher import CredentialCipher
from .core.model_runtime.openai_compatible import OpenAICompatibleClient
from .extensions.database import db, migrate
from .repositories.app_repository import AppRepository
from .repositories.conversation_repository import ConversationRepository
from .repositories.message_repository import MessageRepository
from .repositories.model_provider_repository import ModelProviderRepository
from .services.app_service import AppService
from .services.chat_service import ChatService
from .services.conversation_chat_service import ConversationChatService
from .services.conversation_service import ConversationService
from .services.model_provider_service import ModelProviderService
from .services.model_runtime_service import ModelRuntimeService
from .services.knowledge_service import KnowledgeService
from .services.workflow_service import WorkflowService
from .services.tool_service import ToolService
from .services.agent_service import AgentService
from .services.monitoring_service import MonitoringService
from .services.evaluation_service import EvaluationService

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

    model_provider_service = ModelProviderService(
        ModelProviderRepository(), CredentialCipher(resolved_settings.secret_key)
    )
    resolved_app_service = app_service or AppService(
        AppRepository(), providers=model_provider_service
    )
    monitoring_service = MonitoringService()
    model_runtime_service = ModelRuntimeService(resolved_chat_service, model_provider_service, resolved_settings.model_timeout, monitoring_service)
    knowledge_service = KnowledgeService()
    tool_service = ToolService(knowledge_service)
    workflow_service = WorkflowService(resolved_app_service, knowledge_service, model_runtime_service, tool_service)
    agent_service = AgentService(resolved_app_service, model_runtime_service, tool_service)
    evaluation_service = EvaluationService(resolved_app_service, model_runtime_service)
    conversation_service = ConversationService(
        ConversationRepository(),
        resolved_app_service,
    )
    conversation_chat_service = ConversationChatService(
        conversation_service,
        MessageRepository(),
        model_runtime_service,
        knowledge_service,
    )

    # Vue is compiled to ``web/dist`` during the production image build.  Flask
    # serves those files so the browser and API share one origin in production.
    web_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    app = Flask(__name__, static_folder=None)

    app.config["SQLALCHEMY_DATABASE_URI"] = resolved_settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = resolved_settings.secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = resolved_settings.session_cookie_secure
    app.config["MAX_CONTENT_LENGTH"] = resolved_settings.max_content_length
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    migrate.init_app(app, db)

    app.extensions["chat_service"] = resolved_chat_service
    app.extensions["app_service"] = resolved_app_service
    app.extensions["conversation_service"] = conversation_service
    app.extensions["conversation_chat_service"] = conversation_chat_service
    app.extensions["model_provider_service"] = model_provider_service
    app.extensions["model_runtime_service"] = model_runtime_service
    app.extensions["knowledge_service"] = knowledge_service
    app.extensions["workflow_service"] = workflow_service
    app.extensions["tool_service"] = tool_service
    app.extensions["agent_service"] = agent_service
    app.extensions["monitoring_service"] = monitoring_service
    app.extensions["evaluation_service"] = evaluation_service
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(apps_bp)
    app.register_blueprint(app_chat_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(conversation_chat_bp)
    app.register_blueprint(model_providers_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(workflows_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(observability_bp)
    app.cli.add_command(init_db_command)

    @app.before_request
    def require_api_authentication():
        public_paths = {"/health", "/api/auth/register", "/api/auth/login"}
        if request.path.startswith("/api/") and request.path not in public_paths:
            if not session.get("user_id"):
                return jsonify(code="unauthorized", message="Authentication required"), 401

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if resolved_settings.session_cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(code="request_too_large", message="Request body is too large"), 413

    @app.get("/")
    @app.get("/<path:path>")
    def serve_frontend(path: str = ""):
        """Serve Vue assets and fall back to index.html for Vue Router."""
        if path.startswith("api/"):
            abort(404)

        requested_file = web_dist / path
        if path and requested_file.is_file():
            return send_from_directory(web_dist, path)
        if (web_dist / "index.html").is_file():
            return send_from_directory(web_dist, "index.html")
        abort(404)

    return app
