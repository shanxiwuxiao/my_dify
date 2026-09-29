import json
from typing import Any
from .app_service import AppService
from .model_runtime_service import ModelRuntimeService
from .tool_service import ToolError,ToolService


class AgentService:
    def __init__(self,apps:AppService,runtime:ModelRuntimeService,tools:ToolService):self._apps=apps;self._runtime=runtime;self._tools=tools
    def run(self,app_id:str,query:str,max_steps:int=5):
        config=self._apps.runtime_config(app_id);chat=self._runtime.for_config(config);trace=[];context=""
        tool_text=json.dumps(self._tools.definitions(),ensure_ascii=False)
        for step in range(max_steps):
            prompt=f"""你是工具型 Agent。可用工具：{tool_text}
用户问题：{query}
已执行结果：{context}
如果需要工具，只输出 JSON：{{"tool":"工具名","arguments":{{}}}}；可以回答时只输出 JSON：{{"answer":"答案"}}。"""
            raw=chat.chat(prompt,system_prompt=config.system_prompt,model_name=config.model_name,temperature=config.temperature)
            try:data=json.loads(raw)
            except json.JSONDecodeError:return {"answer":raw,"trace":trace}
            if isinstance(data,dict) and "answer" in data:return {"answer":str(data["answer"]),"trace":trace}
            if not isinstance(data,dict) or "tool" not in data:raise ToolError("invalid agent decision")
            result=self._tools.invoke(str(data["tool"]),data.get("arguments",{}));trace.append({"step":step+1,"tool":data["tool"],"arguments":data.get("arguments",{}),"result":result});context=json.dumps(trace,ensure_ascii=False)
        raise ToolError("agent reached maximum steps")
