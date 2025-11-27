import asyncio
import json
from typing import Dict, List, Set, Any
from fastapi import WebSocket
from app.schemas.workflow import WorkflowGraph, Node
from app.services.llm_service import LLMService

from app.core.logging import logger

class WorkflowExecutor:
    def __init__(self, graph: WorkflowGraph, websocket: WebSocket):
        self.graph = graph
        self.websocket = websocket
        self.node_map = {node.id: node for node in graph.nodes}
        self.execution_results: Dict[str, Any] = {} # node_id -> result
        self.api_key = graph.apiKey # Prefer key sent from client

    async def run(self):
        """
        Execute the workflow using Topological Sort logic.
        """
        logger.info("Starting workflow execution")
        await self.websocket.send_json({"type": "execution_start"})
        
        try:
            # ... (rest of code) ...
            # Replace prints with logger.info/error
            # 1. Build Adjacency List and In-Degree count
            adj_list: Dict[str, List[str]] = {node.id: [] for node in self.graph.nodes}
            in_degree: Dict[str, int] = {node.id: 0 for node in self.graph.nodes}
            
            for edge in self.graph.edges:
                adj_list[edge.source].append(edge.target)
                in_degree[edge.target] += 1

            # 2. Queue for nodes with 0 dependencies
            queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
            
            if not queue and self.graph.nodes:
                 await self.websocket.send_json({
                    "type": "error", 
                    "message": "Cycle detected or empty graph. Cannot execute."
                })
                 return

            # 3. Execution Loop
            while queue:
                # For Phase 1, we process strictly sequentially to keep debugging easy
                # Later we can use asyncio.gather for parallel nodes in the queue
                current_node_id = queue.pop(0)
                current_node = self.node_map[current_node_id]

                # Get inputs from parent nodes
                inputs = self._gather_inputs(current_node_id)

                # EXECUTE NODE
                await self._execute_node(current_node, inputs)

                # Process neighbors
                for neighbor_id in adj_list[current_node_id]:
                    in_degree[neighbor_id] -= 1
                    if in_degree[neighbor_id] == 0:
                        queue.append(neighbor_id)

            await self.websocket.send_json({"type": "execution_complete"})

        except Exception as e:
            await self.websocket.send_json({
                "type": "execution_error",
                "node_id": "system",
                "error": str(e)
            })
            logger.error(f"Execution Error: {e}")

    def _gather_inputs(self, node_id: str) -> Dict[str, Any]:
        """Collect outputs from incoming edges"""
        inputs = {}
        # Find all edges pointing to this node
        incoming_edges = [e for e in self.graph.edges if e.target == node_id]
        
        for edge in incoming_edges:
            source_id = edge.source
            if source_id in self.execution_results:
                # In a real scenario, we might map specific handles
                # For now, we just merge the 'output' of the parent
                inputs[source_id] = self.execution_results[source_id]
        return inputs

    async def _execute_node(self, node: Node, inputs: Dict[str, Any]):
        """
        Execute Node Logic.
        """
        # Notify UI: Node Started
        await self.websocket.send_json({
            "type": "node_start",
            "node_id": node.id
        })

        result = ""
        
        try:
            if node.type == 'neural-input':
                # Input node just passes its own data forward
                result = node.data.inputValue or "Empty Input"
                await asyncio.sleep(0.1) 

            elif node.type == 'neural-llm':
                # REAL LLM GENERATION
                prompt_context = ""
                for key, val in inputs.items():
                    prompt_context += f"Input from Node {key}:\n{val}\n\n"
                
                system_prompt = "You are a helpful AI assistant in a node-based workflow."
                user_prompt = prompt_context
                
                # Get config from node data
                model_name = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                temperature = node.data.node_config.get("temperature", 0.7)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                try:
                    logger.info(f"Executing LLM Node {node.id} with Model: {model_name}")
                    llm = LLMService(api_key=self.api_key)
                    current_text = ""
                    
                    logger.info(f"Sending request to OpenRouter...")
                    async for chunk in llm.stream_completion(
                        messages=messages, 
                        model=model_name,
                        temperature=temperature
                    ):
                        # print(f"Chunk received: {chunk}") # Too verbose for big outputs
                        current_text += chunk
                        await self.websocket.send_json({
                            "type": "token_stream",
                            "node_id": node.id,
                            "token": chunk
                        })
                    
                    logger.info(f"LLM Execution Complete. Length: {len(current_text)}")
                    result = current_text
                except ValueError as e:
                     logger.error(f"Value Error in LLM: {e}")
                     error_msg = str(e)
                     await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": error_msg})
                     raise e
                except Exception as e:
                     logger.error(f"General Error in LLM: {e}")
                     await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": f"LLM Fail: {str(e)}"})
                     raise e

            elif node.type == 'neural-output':
                # Output node aggregates inputs
                result = "\n".join([str(val) for val in inputs.values()])
                await asyncio.sleep(0.1)

            # Store result
            self.execution_results[node.id] = result

            # Notify UI: Node Finished
            await self.websocket.send_json({
                "type": "node_finish",
                "node_id": node.id,
                "result": result
            })

        except Exception as e:
            # Error already sent for specific cases, but catch-all here
            if not isinstance(e, ValueError): # ValueError handled above
                await self.websocket.send_json({
                    "type": "node_error",
                    "node_id": node.id,
                    "error": str(e)
                })
            raise e
