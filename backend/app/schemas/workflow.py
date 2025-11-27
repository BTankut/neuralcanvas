from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Position(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: Optional[str] = None
    # Dynamic dict to hold any node-specific data (model, prompt, etc.)
    node_config: Dict[str, Any] = Field(default_factory=dict) 
    inputValue: Optional[str] = None
    outputValue: Optional[str] = None
    
    class Config:
        extra = "allow"

class Node(BaseModel):
    id: str
    type: str
    position: Position
    data: NodeData

class Edge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    animated: bool = False

class WorkflowGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    apiKey: Optional[str] = None
