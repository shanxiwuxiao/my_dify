from datetime import datetime,timezone
from typing import Protocol
from ..core.model_runtime.openai_compatible import OpenAICompatibleClient
from .chat_service import ChatService
from .model_provider_service import ModelProviderService
from .monitoring_service import MonitoringService


class ModelConfiguration(Protocol):
    provider_id: str | None


class ModelRuntimeService:
    def __init__(self, default_chat_service: ChatService, providers: ModelProviderService, timeout: float, monitoring: MonitoringService):
        self._default = default_chat_service; self._providers = providers; self._timeout = timeout; self._monitoring=monitoring

    def for_config(self, config: ModelConfiguration) -> ChatService:
        service=self._default
        if config.provider_id:
            provider = self._providers.get(config.provider_id)
            service=ChatService(OpenAICompatibleClient(provider.base_url,self._providers.api_key(provider),provider.default_model,self._timeout))
        return MonitoredChatService(service,self._monitoring,getattr(config,"app_id",getattr(config,"id",None)))


class MonitoredChatService:
    def __init__(self,inner:ChatService,monitoring:MonitoringService,app_id:str|None):self._inner=inner;self._monitoring=monitoring;self._app_id=app_id
    def _call(self,method,messages,model,temperature):
        started=datetime.now(timezone.utc);size=sum(len(x["content"]) for x in messages)
        try:
            answer=method(messages,model=model,temperature=temperature);self._monitoring.record(self._app_id,model,"succeeded",size,len(answer),started);return answer
        except Exception as exc:self._monitoring.record(self._app_id,model,"failed",size,0,started,exc);raise
    def chat_messages(self,messages,*,model=None,temperature=None):return self._call(self._inner.chat_messages,messages,model,temperature)
    def chat(self,message,*,system_prompt="",model_name=None,temperature=None):return self.chat_messages(self._inner._build_messages(message,system_prompt),model=model_name,temperature=temperature)
    def stream_chat_messages(self,messages,*,model=None,temperature=None):
        started=datetime.now(timezone.utc);size=sum(len(x["content"]) for x in messages);chunks=[]
        try:
            for chunk in self._inner.stream_chat_messages(messages,model=model,temperature=temperature):chunks.append(chunk);yield chunk
            self._monitoring.record(self._app_id,model,"succeeded",size,len("".join(chunks)),started)
        except Exception as exc:self._monitoring.record(self._app_id,model,"failed",size,0,started,exc);raise
    def stream_chat(self,message,*,system_prompt="",model_name=None,temperature=None):return self.stream_chat_messages(self._inner._build_messages(message,system_prompt),model=model_name,temperature=temperature)
