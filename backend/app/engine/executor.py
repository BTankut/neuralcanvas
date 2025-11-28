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
        self.node_states: Dict[str, Dict[str, Any]] = {} # node_id -> state (for loops)
        self.api_key = graph.apiKey # Prefer key sent from client

    async def run(self):
        """
        Execute the workflow using a dynamic queue based on Data Availability.
        Supports cycles/loops by re-queueing nodes when they receive new input.
        """
        logger.info("Starting workflow execution")
        await self.websocket.send_json({"type": "execution_start"})
        
        try:
            # 1. Initialize Queue with Start Nodes (Nodes with NO incoming edges)
            # Actually, strictly nodes with in-degree 0 in the static graph analysis
            start_nodes = [n.id for n in self.graph.nodes if not any(e.target == n.id for e in self.graph.edges)]
            
            # If graph has loops but no clear start, we might need a better heuristic, 
            # but usually there is an Input Node.
            queue = list(start_nodes)
            
            # Track executing tasks to avoid double-queueing if already pending?
            # For now simple list queue.
            
            # To prevent infinite loops crashing the server, safety counter
            safety_counter = 0
            MAX_STEPS = 100

            while queue and safety_counter < MAX_STEPS:
                safety_counter += 1
                current_node_id = queue.pop(0)
                current_node = self.node_map[current_node_id]

                # Get inputs
                inputs = self._gather_inputs(current_node_id)

                # Branching Logic Check:
                # If inputs is None, it means the node was explicitly skipped by logic.
                # If inputs is empty dict {}, it might just be a start node or logic didn't pass yet.
                
                # Special case: Input Node usually has no inputs but should run.
                if not inputs and current_node.type != 'neural-input':
                     # Check if it was skipped by a Condition
                     # _gather_inputs returns None if ALL incoming edges were blocked.
                     if inputs is None:
                         await self.websocket.send_json({"type": "node_skipped", "node_id": current_node_id})
                         # Propagate skip to neighbors? 
                         # For MVP, just don't add neighbors to queue. Logic stops here.
                         continue
                     
                     # If it returns empty dict but has incoming edges, it means inputs are NOT READY yet.
                     # (e.g. waiting for loop back). So we skip execution for now.
                     incoming_edges = [e for e in self.graph.edges if e.target == current_node_id]
                     if incoming_edges:
                         continue

                # Execute
                await self._execute_node(current_node, inputs or {}) # Pass empty dict for InputNode

                # Process neighbors
                # Find all edges starting from this node
                outgoing_edges = [e for e in self.graph.edges if e.source == current_node_id]
                
                for edge in outgoing_edges:
                    target_id = edge.target
                    # Add target to queue.
                    # In a loop, this will add the loop start back to queue.
                    # Data availability check happens at the START of the loop (gather_inputs).
                    
                    # Logic Filter for Queueing:
                    # If this is a conditional/loop node, only queue the neighbor connected to the ACTIVE handle.
                    # This prevents queuing nodes on dead paths.
                    
                    node_result = self.execution_results.get(current_node_id)
                    active_signal = None
                    
                    if isinstance(node_result, dict) and "signal" in node_result:
                        active_signal = node_result["signal"]
                    elif node_result in ["true", "false"]: # Legacy string signal
                        active_signal = node_result
                    
                    # Check edge handle constraint
                    edge_handle = getattr(edge, 'sourceHandle', None)
                    
                    if edge_handle and active_signal:
                        if edge_handle != active_signal:
                            continue # Don't queue this neighbor, path is blocked.
                    
                    # Add to queue if not already there (to prevent duplicates in same tick)
                    # But allows re-adding for loops later.
                    if target_id not in queue:
                        queue.append(target_id)

            if safety_counter >= MAX_STEPS:
                logger.warning("Workflow stopped: Max execution steps reached (Infinite loop protection).")

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
                if parent_node and (parent_node.type == 'neural-condition' or parent_node.type == 'neural-loop'):
                    parent_output = self.execution_results[source_id]
                    
                    # Handle complex output object
                    parent_result = "false"
                    parent_data = ""
                    
                    if isinstance(parent_output, dict) and "signal" in parent_output:
                        parent_result = parent_output["signal"]
                        parent_data = parent_output.get("data", "")
                    else:
                        parent_result = str(parent_output)
                        parent_data = str(parent_output)

                    edge_handle = getattr(edge, 'sourceHandle', None)
                    
                    # Strict check: Edge must match the active signal
                    if edge_handle and edge_handle != parent_result:
                        logger.info(f"Skipping input from {source_id} to {node_id} because path {edge_handle} is not active (Result: {parent_result})")
                        continue
                        
                    # If loop continues, we might need to clear the target node's previous result
                    # to allow it to re-execute? The main loop handles re-queueing.
                    inputs[source_id] = parent_data
                    continue 
                
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

            elif node.type == 'neural-search':
                # WEB SEARCH LOGIC
                from duckduckgo_search import DDGS
                
                # Determine query: Config overrides Input
                query = node.data.node_config.get("searchQuery", "")
                if not query:
                    # Use input text if config is empty
                    query = "\n".join([str(val) for val in inputs.values()])
                
                if not query:
                    result = "No search query provided."
                else:
                    logger.info(f"Searching web for: {query}")
                    try:
                        # Run synchronous DDGS in a thread to avoid blocking async loop
                        def perform_search(q):
                            with DDGS() as ddgs:
                                return list(ddgs.text(q, max_results=3))
                        
                        loop = asyncio.get_event_loop()
                        results = await loop.run_in_executor(None, perform_search, query)
                        
                        # Format results
                        formatted = []
                        for r in results:
                            formatted.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}")
                        
                        result = "\n---\n".join(formatted) if formatted else "No results found."
                        
                    except Exception as search_err:
                        logger.error(f"Search failed: {search_err}")
                        result = f"Search Error: {str(search_err)}"

            elif node.type == 'neural-llm':
                # REAL LLM GENERATION
                prompt_context = ""
                for key, val in inputs.items():
                    prompt_context += f"Input from Node {key}:\n{val}\n\n"
                
                # Get config from node data
                model_name = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                temperature = node.data.node_config.get("temperature", 0.7)
                system_prompt = node.data.node_config.get("systemPrompt", "You are a helpful AI assistant in a node-based workflow.")
                
                user_prompt = prompt_context
                
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

            elif node.type == 'neural-loop':
                # LOOP LOGIC
                max_iterations = node.data.node_config.get("max_iterations", 3)
                
                # Initialize state if not exists
                if node.id not in self.node_states:
                    self.node_states[node.id] = {"iteration": 0}
                
                state = self.node_states[node.id]
                state["iteration"] += 1
                current_iter = state["iteration"]
                
                logger.info(f"Loop Node {node.id}: Iteration {current_iter}/{max_iterations}")
                
                # Send status update to frontend
                await self.websocket.send_json({
                    "type": "node_usage", # Reuse usage event to update iteration count UI
                    "node_id": node.id,
                    "usage": {
                        "current_iteration": current_iter,
                        "max_iterations": max_iterations,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0
                    }
                })

                if current_iter <= max_iterations:
                    # CONTINUE LOOP
                    result = {
                        "signal": "loop",
                        "iteration": current_iter,
                        "data": str(inputs) # Pass inputs through
                    }
                    
                    # IMPORTANT: We need to reset downstream nodes in the loop so they can run again!
                    # Ideally we should traverse the 'loop' edge and clear execution_results for those nodes.
                    # For this MVP, we will allow re-execution by NOT adding this Loop node to 'executed_nodes' list 
                    # in a way that blocks it, OR by explicitly managing the queue.
                    # Actually, the queue management in 'run' loop handles re-adding neighbors.
                    # But we need to clear 'self.execution_results' for the target node of the loop 
                    # so it thinks it's fresh? No, DAG logic might just overwrite.
                    # Let's trust the overwriting behavior for now.
                    
                else:
                    # FINISH LOOP
                    result = {
                        "signal": "done",
                        "data": str(inputs)
                    }
                    # Reset state for next full run (optional, or keep it for history)
                    # self.node_states[node.id] = {"iteration": 0} 

                await asyncio.sleep(0.2)

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