import ast
import operator
from datetime import datetime, timezone
from typing import Any
from .knowledge_service import KnowledgeService


class ToolError(Exception): pass


class ToolService:
    def __init__(self, knowledge: KnowledgeService): self._knowledge=knowledge
    def definitions(self):
        return [
            {"name":"calculator","description":"计算基础算术表达式","parameters":{"expression":"string"}},
            {"name":"current_time","description":"获取当前 UTC 时间","parameters":{}},
            {"name":"knowledge_search","description":"搜索知识库","parameters":{"knowledge_base_id":"string","query":"string","top_k":"integer"}},
        ]
    def invoke(self,name:str,arguments:dict[str,Any]):
        if name=="current_time":return {"utc":datetime.now(timezone.utc).isoformat()}
        if name=="knowledge_search":return self._knowledge.search(str(arguments["knowledge_base_id"]),str(arguments["query"]),int(arguments.get("top_k",4)))
        if name=="calculator":return {"result":self._calculate(str(arguments["expression"]))}
        raise ToolError("unknown tool")
    def _calculate(self,expression:str):
        operations={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.USub:operator.neg}
        def evaluate(node):
            if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)):return node.value
            if isinstance(node,ast.BinOp) and type(node.op) in operations:return operations[type(node.op)](evaluate(node.left),evaluate(node.right))
            if isinstance(node,ast.UnaryOp) and type(node.op) in operations:return operations[type(node.op)](evaluate(node.operand))
            raise ToolError("unsafe expression")
        if len(expression)>200:raise ToolError("expression too long")
        return evaluate(ast.parse(expression,mode="eval").body)
