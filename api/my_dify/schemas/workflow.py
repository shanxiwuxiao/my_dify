from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


class WorkflowNode(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    type: Literal["start", "template", "condition", "knowledge", "tool", "llm", "end"]
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str | None = None


class WorkflowDefinition(BaseModel):
    nodes: list[WorkflowNode] = Field(min_length=2, max_length=100)
    edges: list[WorkflowEdge] = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)): raise ValueError("node ids must be unique")
        if sum(node.type == "start" for node in self.nodes) != 1: raise ValueError("exactly one start node is required")
        if not any(node.type == "end" for node in self.nodes): raise ValueError("an end node is required")
        if any(edge.source not in ids or edge.target not in ids for edge in self.edges): raise ValueError("edge references missing node")
        indegree = {node_id: 0 for node_id in ids}; outgoing = {node_id: [] for node_id in ids}
        for edge in self.edges: indegree[edge.target] += 1; outgoing[edge.source].append(edge.target)
        queue = [node_id for node_id, degree in indegree.items() if degree == 0]; visited = 0
        while queue:
            current = queue.pop(); visited += 1
            for target in outgoing[current]:
                indegree[target] -= 1
                if indegree[target] == 0: queue.append(target)
        if visited != len(ids): raise ValueError("workflow must not contain cycles")
        return self


class WorkflowCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    app_id: str | None = None
    definition: WorkflowDefinition


class WorkflowRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)
