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

                # Skip if inputs is None (dead branch)
                if inputs is None:
                    # Emit skipped event here since we can await
                    await self.websocket.send_json({
                        "type": "node_skipped",
                        "node_id": current_node_id
                    })
                    continue

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
                # Check branching
                parent_node = self.node_map.get(source_id)
                if parent_node and parent_node.type == 'neural-condition':
                    parent_output = self.execution_results[source_id]
                    
                    # Handle the new complex output object
                    parent_result = "false"
                    parent_data = ""
                    
                    if isinstance(parent_output, dict) and "signal" in parent_output:
                        parent_result = parent_output["signal"]
                        parent_data = parent_output["data"]
                    else:
                        # Fallback for legacy or other nodes
                        parent_result = str(parent_output)
                        parent_data = str(parent_output)

                    # Using getattr safely in case Pydantic model field is missing (though I added it)
                    edge_handle = getattr(edge, 'sourceHandle', None)
                    
                    logger.info(f"DEBUG BRANCH: Edge {edge.id} Source: {source_id} -> Target: {node_id}. Handle: {edge_handle} vs Result: {parent_result}")

                    # If edge has a specific handle, it MUST match the result
                    if edge_handle and edge_handle != parent_result:
                        logger.info(f"Skipping input from {source_id} to {node_id} because path {edge_handle} is not active (Result: {parent_result})")
                        continue
                        
                    # If we pass the check, we pass the DATA
                    inputs[source_id] = parent_data
                    continue # Skip default assignment
                
                inputs[source_id] = self.execution_results[source_id]
        
        # CRITICAL FIX: If a node expects inputs (has incoming edges) but received NONE because they were filtered out,
        # it means this branch is DEAD. We should NOT execute this node.
        if incoming_edges and not inputs:
             logger.info(f"Node {node_id} skipped because all incoming inputs were blocked by conditions.")
             return None 

        return inputs

    async def _execute_node(self, node: Node, inputs: Dict[str, Any]):
        """
        Execute Node Logic.
        """
        if inputs is None:
            return # Skip execution transparently
            
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
                    
                    # Calculate Usage Stats (Approximate for MVP)
                    # Standard rule of thumb: 1 token ~= 4 characters
                    input_tokens = len(json.dumps(messages)) // 4
                    output_tokens = len(result) // 4
                    
                    await self.websocket.send_json({
                        "type": "node_usage",
                        "node_id": node.id,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens
                        }
                    })

                except ValueError as e:
                     logger.error(f"Value Error in LLM: {e}")
                     error_msg = str(e)
                     await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": error_msg})
                     raise e
                except Exception as e:
                     logger.error(f"General Error in LLM: {e}")
                     await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": f"LLM Fail: {str(e)}"})
                     raise e

            elif node.type == 'neural-condition':
                # CONDITIONAL LOGIC
                condition_type = node.data.node_config.get("conditionType", "contains")
                target_value = node.data.node_config.get("targetValue", "")
                
                # Aggregate all input text
                input_text = "\n".join([str(val) for val in inputs.values()])
                
                is_match = False
                if condition_type == "contains":
                    is_match = target_value.lower() in input_text.lower()
                elif condition_type == "equals":
                    is_match = input_text.strip().lower() == target_value.strip().lower()
                elif condition_type == "not_contains":
                    is_match = target_value.lower() not in input_text.lower()
                
                result = {
                    "signal": "true" if is_match else "false",
                    "data": input_text
                }
                await asyncio.sleep(0.1)

            elif node.type == 'neural-output':
                # Output node aggregates inputs
                result = "\n".join([str(val) for val in inputs.values()])
                await asyncio.sleep(0.1)

            # Store result
            self.execution_results[node.id] = result

            # For the Frontend UI, we want to show the "Signal" (true/false) on the Condition Node,
            # but the actual text content on other nodes.
            ui_result = result
            if isinstance(result, dict) and "signal" in result:
                ui_result = result["signal"]

            # Notify UI: Node Finished
            await self.websocket.send_json({
                "type": "node_finish",
                "node_id": node.id,
                "result": ui_result
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