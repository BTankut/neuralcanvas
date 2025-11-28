import asyncio
import json
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket
from app.schemas.workflow import WorkflowGraph, Node
from app.services.llm_service import LLMService
from collections import defaultdict

from app.core.logging import logger

class WorkflowExecutor:
    def __init__(self, graph: WorkflowGraph, websocket: WebSocket):
        self.graph = graph
        self.websocket = websocket
        self.node_map = {node.id: node for node in graph.nodes}
        self.execution_results: Dict[str, Any] = {} # node_id -> result
        self.node_states: Dict[str, Dict[str, Any]] = {} # node_id -> state (for loops)
        self.node_memory: Dict[str, List[Dict[str, str]]] = {} # node_id -> chat_history (stateful memory)
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
                # REAL LLM GENERATION WITH STATEFUL MEMORY
                
                # 1. Initialize memory if empty
                if node.id not in self.node_memory:
                    system_prompt = node.data.node_config.get("systemPrompt", "You are a helpful AI assistant.")
                    self.node_memory[node.id] = [{"role": "system", "content": system_prompt}]
                
                # 2. Construct new User Input from incoming edges
                current_input = ""
                for key, val in inputs.items():
                    # If input comes from a loop or previous iteration, add context marker
                    current_input += f"Input from Node {key}:\n{val}\n\n"
                
                # 3. Add User Input to Memory
                self.node_memory[node.id].append({"role": "user", "content": current_input})
                
                # Get config
                model_name = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                temperature = node.data.node_config.get("temperature", 0.7)
                
                try:
                    logger.info(f"Executing LLM Node {node.id} with Memory Size: {len(self.node_memory[node.id])}")
                    llm = LLMService(api_key=self.api_key)
                    current_text = ""
                    fallback_used = False
                    final_model_used = model_name

                    # 4. Send FULL HISTORY to LLM with fallback support
                    async for response in llm.stream_completion_with_fallback(
                        messages=self.node_memory[node.id],
                        model=model_name,
                        temperature=temperature,
                        max_retries=3,
                        websocket=self.websocket,
                        node_id=node.id
                    ):
                        chunk = response.get("chunk", "")
                        current_text += chunk

                        # Track if fallback was used
                        if response.get("is_fallback", False):
                            fallback_used = True
                            final_model_used = response.get("model_used", model_name)

                        await self.websocket.send_json({
                            "type": "token_stream",
                            "node_id": node.id,
                            "token": chunk,
                            "model_used": response.get("model_used", model_name),
                            "is_fallback": response.get("is_fallback", False)
                        })

                    # 5. Save Assistant Response to Memory
                    self.node_memory[node.id].append({"role": "assistant", "content": current_text})

                    result = current_text

                    # Calculate Stats
                    input_tokens = len(json.dumps(self.node_memory[node.id])) // 4
                    output_tokens = len(result) // 4

                    await self.websocket.send_json({
                        "type": "node_usage",
                        "node_id": node.id,
                        "usage": {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens
                        },
                        "fallback_used": fallback_used,
                        "final_model_used": final_model_used
                    })

                except Exception as e:
                     logger.error(f"Error in LLM: {e}")
                     # Remove the last user message so we can retry cleanly if needed
                     self.node_memory[node.id].pop() 
                     await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})
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
                # SMART LOOP LOGIC
                max_iterations = node.data.node_config.get("max_iterations", 3)
                target_value = node.data.node_config.get("targetValue", "") # For termination condition
                
                # Check inputs for termination signal
                # If ANY input contains the target_value (e.g. "APPROVED"), we break the loop early.
                should_terminate = False
                input_text = "\n".join([str(val) for val in inputs.values()])
                
                if target_value and target_value.lower() in input_text.lower():
                    should_terminate = True
                    logger.info(f"Loop Node {node.id}: Termination condition '{target_value}' met.")

                # Initialize state
                if node.id not in self.node_states:
                    self.node_states[node.id] = {"iteration": 0}
                
                state = self.node_states[node.id]
                state["iteration"] += 1
                current_iter = state["iteration"]
                
                # Send status
                await self.websocket.send_json({
                    "type": "node_usage",
                    "node_id": node.id,
                    "usage": {
                        "current_iteration": current_iter,
                        "max_iterations": max_iterations,
                        "input_tokens": 0, "output_tokens": 0, "total_tokens": 0
                    }
                })

                if not should_terminate and current_iter <= max_iterations:
                    # CONTINUE LOOP
                    result = {
                        "signal": "loop",
                        "iteration": current_iter,
                        "data": str(inputs)
                    }
                else:
                    # FINISH LOOP (Either max iterations reached OR termination condition met)
                    result = {
                        "signal": "done",
                        "data": str(inputs)
                    }
                    # Reset for next run? No, keep history for now.

                await asyncio.sleep(0.2)

            elif node.type == 'neural-splitter':
                # MAPREDUCE: SPLITTER NODE
                # Splits long text into chunks for parallel processing
                document = "\n".join([str(val) for val in inputs.values()])
                chunk_size = node.data.node_config.get("chunk_size", 2000)
                overlap = node.data.node_config.get("overlap", 200)
                strategy = node.data.node_config.get("strategy", "semantic")

                chunks = []
                if strategy == "semantic":
                    # Split by paragraphs, respecting chunk_size
                    paragraphs = document.split('\n\n')
                    current_chunk = ""

                    for para in paragraphs:
                        if len(current_chunk) + len(para) <= chunk_size:
                            current_chunk += para + "\n\n"
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = para + "\n\n"

                    if current_chunk:
                        chunks.append(current_chunk.strip())

                elif strategy == "sliding":
                    # Sliding window with overlap
                    for i in range(0, len(document), chunk_size - overlap):
                        chunk = document[i:i + chunk_size]
                        if chunk:
                            chunks.append(chunk)

                else:  # "fixed"
                    # Fixed size chunks
                    for i in range(0, len(document), chunk_size):
                        chunk = document[i:i + chunk_size]
                        if chunk:
                            chunks.append(chunk)

                # If no chunks created, create at least one with full document
                if not chunks:
                    chunks = [document]

                result = {
                    "chunks": chunks,
                    "num_chunks": len(chunks),
                    "chunk_size": chunk_size
                }

                logger.info(f"Splitter Node {node.id}: Created {len(chunks)} chunks using {strategy} strategy")
                await asyncio.sleep(0.1)

            elif node.type == 'neural-reduce':
                # MAPREDUCE: REDUCER NODE
                # Aggregates multiple inputs into single output
                strategy = node.data.node_config.get("strategy", "hierarchical")
                model_name = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                temperature = node.data.node_config.get("temperature", 0.7)

                # Collect all inputs
                input_chunks = []
                for key, val in inputs.items():
                    if isinstance(val, dict) and "chunks" in val:
                        # Input from splitter node
                        input_chunks.extend(val["chunks"])
                    else:
                        # Regular text input
                        input_chunks.append(str(val))

                logger.info(f"Reduce Node {node.id}: Processing {len(input_chunks)} inputs with {strategy} strategy")

                try:
                    llm = LLMService(api_key=self.api_key)

                    if strategy == "concatenate":
                        # Simple concatenation then summarize
                        combined = "\n\n---\n\n".join(input_chunks)
                        prompt = node.data.node_config.get("prompt", "Summarize the following content:")

                        messages = [
                            {"role": "system", "content": "You are an expert at synthesizing information."},
                            {"role": "user", "content": f"{prompt}\n\n{combined}"}
                        ]

                        current_text = ""
                        async for response in llm.stream_completion_with_fallback(
                            messages=messages,
                            model=model_name,
                            temperature=temperature,
                            max_retries=3,
                            websocket=self.websocket,
                            node_id=node.id
                        ):
                            chunk = response.get("chunk", "")
                            current_text += chunk
                            await self.websocket.send_json({
                                "type": "token_stream",
                                "node_id": node.id,
                                "token": chunk
                            })

                        result = current_text

                    elif strategy == "hierarchical":
                        # Hierarchical reduction: batch inputs and reduce in layers
                        current_layer = input_chunks
                        batch_size = 3  # Reduce 3 chunks at a time

                        layer_num = 0
                        while len(current_layer) > 1:
                            layer_num += 1
                            next_layer = []

                            logger.info(f"Reduce Node {node.id}: Layer {layer_num} - reducing {len(current_layer)} chunks")

                            for i in range(0, len(current_layer), batch_size):
                                batch = current_layer[i:i+batch_size]
                                batch_combined = "\n\n---\n\n".join(batch)

                                prompt = node.data.node_config.get("prompt", "Summarize and synthesize the following content:")
                                messages = [
                                    {"role": "system", "content": "You are an expert at synthesizing information."},
                                    {"role": "user", "content": f"{prompt}\n\n{batch_combined}"}
                                ]

                                # Reduce this batch
                                batch_result = ""
                                async for response in llm.stream_completion_with_fallback(
                                    messages=messages,
                                    model=model_name,
                                    temperature=temperature,
                                    max_retries=3,
                                    websocket=self.websocket,
                                    node_id=node.id
                                ):
                                    chunk = response.get("chunk", "")
                                    batch_result += chunk

                                    # Only stream final layer to UI
                                    if len(current_layer) <= batch_size:
                                        await self.websocket.send_json({
                                            "type": "token_stream",
                                            "node_id": node.id,
                                            "token": chunk
                                        })

                                next_layer.append(batch_result)

                            current_layer = next_layer

                        result = current_layer[0] if current_layer else "No content to reduce"

                    else:
                        # Default: just concatenate
                        result = "\n\n---\n\n".join(input_chunks)

                    logger.info(f"Reduce Node {node.id}: Completed reduction")

                except Exception as e:
                    logger.error(f"Error in Reduce Node: {e}")
                    result = f"Error in reduction: {str(e)}"
                    await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

            elif node.type == 'neural-self-consistency':
                # SELF-CONSISTENCY: Generate multiple samples and vote
                model_name = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                num_samples = node.data.node_config.get("samples", 5)
                voting_method = node.data.node_config.get("voting", "majority")
                base_temperature = node.data.node_config.get("temperature", 0.7)

                # Get input text
                input_text = "\n".join([str(val) for val in inputs.values()])

                logger.info(f"Self-Consistency Node {node.id}: Generating {num_samples} samples with {voting_method} voting")

                try:
                    llm = LLMService(api_key=self.api_key)
                    responses = []

                    # Generate multiple samples with varying temperatures
                    for i in range(num_samples):
                        # Vary temperature slightly for diversity
                        temperature = base_temperature + (i * 0.1)
                        if temperature > 2.0:
                            temperature = 2.0

                        # Send progress update
                        await self.websocket.send_json({
                            "type": "node_progress",
                            "node_id": node.id,
                            "current": i + 1,
                            "total": num_samples,
                            "message": f"Generating sample {i + 1}/{num_samples}"
                        })

                        messages = [
                            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise answers."},
                            {"role": "user", "content": input_text}
                        ]

                        # Generate sample
                        sample_text = ""
                        async for response in llm.stream_completion_with_fallback(
                            messages=messages,
                            model=model_name,
                            temperature=temperature,
                            max_retries=3,
                            websocket=self.websocket,
                            node_id=node.id
                        ):
                            chunk = response.get("chunk", "")
                            sample_text += chunk

                        responses.append(sample_text.strip())
                        logger.info(f"Sample {i + 1} generated (temp={temperature:.1f})")

                    # Voting logic
                    if voting_method == "majority":
                        # Simple majority vote on exact matches
                        from collections import Counter
                        vote_counts = Counter(responses)
                        best_answer = vote_counts.most_common(1)[0][0]
                        confidence = vote_counts[best_answer] / num_samples

                        result = {
                            "answer": best_answer,
                            "confidence": confidence,
                            "votes": dict(vote_counts),
                            "all_responses": responses,
                            "voting_method": "majority"
                        }

                        logger.info(f"Majority vote winner: {confidence*100:.1f}% confidence")

                    elif voting_method == "first":
                        # Just use the first response (simplest)
                        result = {
                            "answer": responses[0],
                            "confidence": 1.0 / num_samples,
                            "all_responses": responses,
                            "voting_method": "first"
                        }

                    else:  # "longest" - assume more detailed = better
                        longest_response = max(responses, key=len)
                        result = {
                            "answer": longest_response,
                            "confidence": len(longest_response) / sum(len(r) for r in responses),
                            "all_responses": responses,
                            "voting_method": "longest"
                        }

                    # Stream final answer to UI
                    await self.websocket.send_json({
                        "type": "token_stream",
                        "node_id": node.id,
                        "token": f"\n\n✅ CONSENSUS ({result['confidence']*100:.0f}% confidence):\n\n{result['answer']}"
                    })

                except Exception as e:
                    logger.error(f"Error in Self-Consistency Node: {e}")
                    result = f"Error in self-consistency: {str(e)}"
                    await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

            elif node.type == 'neural-moa-proposer':
                # MOA: PROPOSER GROUP - Run multiple models in parallel
                proposer_models = node.data.node_config.get("models", ["openai/gpt-3.5-turbo", "anthropic/claude-3-haiku"])
                temperature = node.data.node_config.get("temperature", 0.7)

                # Get input text
                input_text = "\n".join([str(val) for val in inputs.values()])

                logger.info(f"MoA Proposer Node {node.id}: Running {len(proposer_models)} models in parallel")

                try:
                    llm = LLMService(api_key=self.api_key)
                    proposer_outputs = []
                    models_used = []

                    # Launch all proposers in parallel
                    async def generate_proposal(model_name: str, index: int):
                        try:
                            await self.websocket.send_json({
                                "type": "node_progress",
                                "node_id": node.id,
                                "current": index + 1,
                                "total": len(proposer_models),
                                "message": f"Proposer {index + 1}: {model_name}"
                            })

                            messages = [
                                {"role": "system", "content": "You are a helpful AI assistant. Provide thoughtful, well-reasoned answers."},
                                {"role": "user", "content": input_text}
                            ]

                            proposal_text = ""
                            async for response in llm.stream_completion_with_fallback(
                                messages=messages,
                                model=model_name,
                                temperature=temperature,
                                max_retries=3,
                                websocket=self.websocket,
                                node_id=node.id
                            ):
                                chunk = response.get("chunk", "")
                                proposal_text += chunk

                            return (model_name, proposal_text.strip())

                        except Exception as e:
                            logger.error(f"Proposer {model_name} failed: {e}")
                            return (model_name, f"[Error: {str(e)}]")

                    # Run all proposers concurrently
                    tasks = [generate_proposal(model, i) for i, model in enumerate(proposer_models)]
                    results = await asyncio.gather(*tasks)

                    # Collect successful results
                    for model_name, proposal in results:
                        if not proposal.startswith("[Error:"):
                            proposer_outputs.append(proposal)
                            models_used.append(model_name)

                    result = {
                        "proposer_outputs": proposer_outputs,
                        "models_used": models_used,
                        "success_rate": len(proposer_outputs) / len(proposer_models)
                    }

                    logger.info(f"MoA Proposer: {len(proposer_outputs)}/{len(proposer_models)} proposals succeeded")

                    # Send summary to UI
                    await self.websocket.send_json({
                        "type": "token_stream",
                        "node_id": node.id,
                        "token": f"\n\n✅ Generated {len(proposer_outputs)} proposals from:\n" + "\n".join([f"  • {m}" for m in models_used])
                    })

                except Exception as e:
                    logger.error(f"Error in MoA Proposer Node: {e}")
                    result = f"Error in MoA proposer: {str(e)}"
                    await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

            elif node.type == 'neural-moa-aggregator':
                # MOA: AGGREGATOR - Synthesize all proposals into best answer
                aggregator_model = node.data.node_config.get("model", "openai/gpt-4-turbo")
                temperature = node.data.node_config.get("temperature", 0.6)
                aggregation_strategy = node.data.node_config.get("strategy", "synthesis")

                # Collect all proposer outputs from parent nodes
                proposer_outputs = []
                models_used = []

                for key, val in inputs.items():
                    if isinstance(val, dict) and "proposer_outputs" in val:
                        proposer_outputs.extend(val["proposer_outputs"])
                        models_used.extend(val["models_used"])

                if not proposer_outputs:
                    result = "No proposer outputs received"
                    logger.warning(f"MoA Aggregator {node.id}: No proposals to aggregate")
                else:
                    logger.info(f"MoA Aggregator Node {node.id}: Aggregating {len(proposer_outputs)} proposals")

                    try:
                        llm = LLMService(api_key=self.api_key)

                        # Build aggregation prompt
                        formatted_proposals = ""
                        for i, (model, proposal) in enumerate(zip(models_used, proposer_outputs), 1):
                            formatted_proposals += f"\n\n--- Proposal {i} (from {model}) ---\n{proposal}"

                        if aggregation_strategy == "synthesis":
                            system_prompt = """You are an expert aggregator and synthesizer. Your task is to review multiple AI-generated responses to the same question and create a superior synthesis.

Instructions:
1. Identify the strongest insights from each response
2. Resolve any contradictions with clear reasoning
3. Combine the best elements into a comprehensive answer
4. Be more thorough and insightful than any individual response
5. Maintain clarity and conciseness"""

                            user_prompt = f"""Below are {len(proposer_outputs)} different responses to the same question from various AI models.

{formatted_proposals}

Please synthesize these responses into a single, superior answer that incorporates the best insights from each."""

                        elif aggregation_strategy == "critique":
                            system_prompt = "You are a critical evaluator. Analyze the responses and identify the most accurate and well-reasoned answer."
                            user_prompt = f"""Evaluate these {len(proposer_outputs)} responses and select or synthesize the best answer:

{formatted_proposals}

Provide your critical analysis and final recommendation."""

                        else:  # "best"
                            system_prompt = "You are an expert judge. Select the single best response from the options provided."
                            user_prompt = f"""Which of these {len(proposer_outputs)} responses is the best? Explain why and present it as your final answer.

{formatted_proposals}"""

                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]

                        # Stream aggregated result
                        aggregated_text = ""
                        async for response in llm.stream_completion_with_fallback(
                            messages=messages,
                            model=aggregator_model,
                            temperature=temperature,
                            max_retries=3,
                            websocket=self.websocket,
                            node_id=node.id
                        ):
                            chunk = response.get("chunk", "")
                            aggregated_text += chunk

                            await self.websocket.send_json({
                                "type": "token_stream",
                                "node_id": node.id,
                                "token": chunk
                            })

                        result = aggregated_text
                        logger.info(f"MoA Aggregator: Successfully synthesized {len(proposer_outputs)} proposals")

                    except Exception as e:
                        logger.error(f"Error in MoA Aggregator Node: {e}")
                        result = f"Error in aggregation: {str(e)}"
                        await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

            elif node.type == 'neural-debate':
                # DEBATE: Multi-round debate between AI agents
                num_debaters = node.data.node_config.get("debaters", 3)
                num_rounds = node.data.node_config.get("rounds", 2)
                debate_model = node.data.node_config.get("model", "openai/gpt-3.5-turbo")
                temperature = node.data.node_config.get("temperature", 0.8)

                # Get the question/topic
                question = "\n".join([str(val) for val in inputs.values()])

                logger.info(f"Debate Node {node.id}: {num_debaters} debaters, {num_rounds} rounds")

                try:
                    llm = LLMService(api_key=self.api_key)
                    debate_history = []

                    # Assign positions to debaters
                    positions = ["Pro", "Con", "Neutral"]
                    if num_debaters > 3:
                        positions.extend([f"Perspective {i}" for i in range(4, num_debaters + 1)])

                    for round_num in range(num_rounds):
                        logger.info(f"Debate Round {round_num + 1}/{num_rounds}")

                        await self.websocket.send_json({
                            "type": "node_progress",
                            "node_id": node.id,
                            "current": round_num + 1,
                            "total": num_rounds,
                            "message": f"Round {round_num + 1}/{num_rounds}"
                        })

                        round_responses = []

                        # Each debater responds in parallel
                        async def debater_response(debater_idx: int, position: str):
                            # Build context from debate history
                            context_prompt = f"""You are Debater {debater_idx + 1} with position: {position}

Topic for debate: {question}

"""
                            if debate_history:
                                context_prompt += "Previous rounds:\n"
                                for prev_round in debate_history:
                                    context_prompt += f"\n--- Round {prev_round['round']} ---\n"
                                    for i, resp in enumerate(prev_round['responses']):
                                        context_prompt += f"Debater {i + 1} ({prev_round['positions'][i]}): {resp}\n"

                            context_prompt += f"\nNow present your argument for Round {round_num + 1}. Be persuasive and address opposing viewpoints."

                            messages = [
                                {"role": "system", "content": f"You are an expert debater arguing from the {position} position. Be logical, persuasive, and consider counterarguments."},
                                {"role": "user", "content": context_prompt}
                            ]

                            response_text = ""
                            async for response in llm.stream_completion_with_fallback(
                                messages=messages,
                                model=debate_model,
                                temperature=temperature,
                                max_retries=3,
                                websocket=self.websocket,
                                node_id=node.id
                            ):
                                chunk = response.get("chunk", "")
                                response_text += chunk

                            return response_text.strip()

                        # Run all debaters in parallel for this round
                        tasks = [debater_response(i, positions[i % len(positions)]) for i in range(num_debaters)]
                        round_responses = await asyncio.gather(*tasks)

                        # Store round results
                        debate_history.append({
                            "round": round_num + 1,
                            "positions": [positions[i % len(positions)] for i in range(num_debaters)],
                            "responses": round_responses
                        })

                        # Stream round summary to UI
                        await self.websocket.send_json({
                            "type": "token_stream",
                            "node_id": node.id,
                            "token": f"\n\n--- ROUND {round_num + 1} COMPLETE ---\n"
                        })

                    result = {
                        "debate_history": debate_history,
                        "question": question,
                        "num_debaters": num_debaters,
                        "num_rounds": num_rounds
                    }

                    # Send final summary
                    summary = f"\n\n✅ Debate completed: {num_debaters} debaters × {num_rounds} rounds\n"
                    await self.websocket.send_json({
                        "type": "token_stream",
                        "node_id": node.id,
                        "token": summary
                    })

                    logger.info(f"Debate completed: {num_rounds} rounds")

                except Exception as e:
                    logger.error(f"Error in Debate Node: {e}")
                    result = f"Error in debate: {str(e)}"
                    await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

            elif node.type == 'neural-voting':
                # VOTING: Judge debates or aggregate multiple opinions
                voting_method = node.data.node_config.get("method", "judge")
                judge_model = node.data.node_config.get("model", "openai/gpt-4-turbo")
                temperature = node.data.node_config.get("temperature", 0.5)

                # Collect debate history or opinions from inputs
                debate_data = None
                opinions = []

                for key, val in inputs.items():
                    if isinstance(val, dict) and "debate_history" in val:
                        debate_data = val
                    else:
                        opinions.append(str(val))

                logger.info(f"Voting Node {node.id}: Method={voting_method}")

                try:
                    llm = LLMService(api_key=self.api_key)

                    if debate_data and voting_method == "judge":
                        # Judge evaluates debate
                        question = debate_data.get("question", "")
                        debate_history = debate_data.get("debate_history", [])

                        # Format debate for judge
                        formatted_debate = f"Topic: {question}\n\n"
                        for round_data in debate_history:
                            formatted_debate += f"--- Round {round_data['round']} ---\n"
                            for i, (pos, resp) in enumerate(zip(round_data['positions'], round_data['responses'])):
                                formatted_debate += f"\nDebater {i + 1} ({pos}):\n{resp}\n"

                        judge_prompt = f"""You are an impartial judge evaluating a debate.

{formatted_debate}

As the judge, you must:
1. Evaluate the strength of each debater's arguments
2. Identify which arguments are most logical and well-supported
3. Determine the most compelling overall position
4. Provide a clear verdict with reasoning

Please provide your detailed judgment and final verdict."""

                        messages = [
                            {"role": "system", "content": "You are an expert debate judge. Evaluate arguments objectively based on logic, evidence, and persuasiveness."},
                            {"role": "user", "content": judge_prompt}
                        ]

                        verdict_text = ""
                        async for response in llm.stream_completion_with_fallback(
                            messages=messages,
                            model=judge_model,
                            temperature=temperature,
                            max_retries=3,
                            websocket=self.websocket,
                            node_id=node.id
                        ):
                            chunk = response.get("chunk", "")
                            verdict_text += chunk

                            await self.websocket.send_json({
                                "type": "token_stream",
                                "node_id": node.id,
                                "token": chunk
                            })

                        result = verdict_text

                    elif voting_method == "consensus":
                        # Simple consensus check
                        all_text = "\n\n".join(opinions)

                        consensus_prompt = f"""Analyze these different opinions and determine if there's a consensus:

{all_text}

Identify:
1. Points of agreement
2. Points of disagreement
3. Overall consensus (if any)
4. Confidence level in the consensus"""

                        messages = [
                            {"role": "system", "content": "You are an expert at finding consensus and common ground."},
                            {"role": "user", "content": consensus_prompt}
                        ]

                        consensus_text = ""
                        async for response in llm.stream_completion_with_fallback(
                            messages=messages,
                            model=judge_model,
                            temperature=temperature,
                            max_retries=3,
                            websocket=self.websocket,
                            node_id=node.id
                        ):
                            chunk = response.get("chunk", "")
                            consensus_text += chunk

                            await self.websocket.send_json({
                                "type": "token_stream",
                                "node_id": node.id,
                                "token": chunk
                            })

                        result = consensus_text

                    else:  # "count" - simple majority
                        result = f"Collected {len(opinions)} opinions for voting"

                    logger.info(f"Voting completed with method: {voting_method}")

                except Exception as e:
                    logger.error(f"Error in Voting Node: {e}")
                    result = f"Error in voting: {str(e)}"
                    await self.websocket.send_json({"type": "node_error", "node_id": node.id, "error": str(e)})

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


class ParallelWorkflowExecutor(WorkflowExecutor):
    """
    Enhanced executor that supports parallel node execution.

    Key Features:
    - Executes up to max_concurrent_nodes in parallel
    - Intelligent dependency tracking
    - Error isolation (failures in one branch don't kill others)
    - Backward compatible with all existing node types
    """

    def __init__(self, graph: WorkflowGraph, websocket: WebSocket, max_concurrent: int = 5):
        super().__init__(graph, websocket)

        # Parallel execution state
        self.max_concurrent = max_concurrent
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.completed_nodes: Set[str] = set()
        self.failed_nodes: Set[str] = set()
        self.ready_nodes: Set[str] = set()

        # Dependency tracking
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)  # node_id -> parent node_ids
        self.dependents: Dict[str, Set[str]] = defaultdict(set)    # node_id -> child node_ids

        # Task mapping (for retrieving node_id from completed task)
        self.task_to_node: Dict[asyncio.Task, str] = {}

    def _build_dependency_graph(self):
        """Build dependency and dependent relationships from edges."""
        for edge in self.graph.edges:
            self.dependencies[edge.target].add(edge.source)
            self.dependents[edge.source].add(edge.target)

        logger.info(f"Built dependency graph: {len(self.dependencies)} nodes with dependencies")

    def _get_start_nodes(self) -> Set[str]:
        """Find nodes with no incoming edges (in-degree 0)."""
        start_nodes = {n.id for n in self.graph.nodes if not any(e.target == n.id for e in self.graph.edges)}
        logger.info(f"Found {len(start_nodes)} start nodes: {start_nodes}")
        return start_nodes

    def _is_node_ready(self, node_id: str) -> bool:
        """
        Check if a node is ready to execute.
        A node is ready when:
        1. All parent nodes have completed successfully
        2. The path to this node is not blocked by conditional/loop logic
        """
        # Already completed or failed
        if node_id in self.completed_nodes or node_id in self.failed_nodes:
            return False

        # Already running
        if node_id in self.running_tasks:
            return False

        # Check if all dependencies are satisfied
        for parent_id in self.dependencies.get(node_id, []):
            # Parent must have completed
            if parent_id not in self.completed_nodes:
                return False

            # Check if path is active (for conditional/loop nodes)
            if not self._check_branch_active(parent_id, node_id):
                # This path is blocked
                logger.debug(f"Node {node_id} blocked by inactive branch from {parent_id}")
                return False

        return True

    def _check_branch_active(self, parent_id: str, child_id: str) -> bool:
        """
        Check if the branch from parent to child is active.
        For conditional/loop nodes, this checks the sourceHandle.
        """
        parent_node = self.node_map.get(parent_id)

        # If parent is not conditional/loop, branch is always active
        if not parent_node or parent_node.type not in ['neural-condition', 'neural-loop']:
            return True

        # Find the edge connecting parent to child
        edge = next((e for e in self.graph.edges if e.source == parent_id and e.target == child_id), None)
        if not edge:
            return False

        # Get parent's result
        parent_result = self.execution_results.get(parent_id)
        if not parent_result:
            return False

        # Extract signal from result
        active_signal = None
        if isinstance(parent_result, dict) and "signal" in parent_result:
            active_signal = parent_result["signal"]
        elif isinstance(parent_result, str):
            active_signal = parent_result

        # Check if edge handle matches active signal
        edge_handle = getattr(edge, 'sourceHandle', None)
        if edge_handle and active_signal:
            return edge_handle == active_signal

        return True

    def _find_newly_ready_nodes(self) -> Set[str]:
        """Find all nodes that became ready after recent completions."""
        newly_ready = set()

        for node_id in self.node_map.keys():
            if self._is_node_ready(node_id):
                newly_ready.add(node_id)

        return newly_ready

    async def _execute_node_safe(self, node: Node, inputs: Dict[str, Any]):
        """
        Execute a node with error isolation.
        Errors in this node won't crash the entire workflow.
        """
        try:
            await self._execute_node(node, inputs)
            self.completed_nodes.add(node.id)
            logger.info(f"Node {node.id} completed successfully")

        except Exception as e:
            self.failed_nodes.add(node.id)
            logger.error(f"Node {node.id} failed: {e}")

            # Send error to frontend (already done in _execute_node, but ensure it's sent)
            await self.websocket.send_json({
                "type": "node_error",
                "node_id": node.id,
                "error": str(e)
            })

            # Don't raise - let other branches continue

    async def run_parallel(self):
        """
        Execute workflow with parallel node execution.
        Respects dependencies and executes up to max_concurrent nodes simultaneously.
        """
        logger.info(f"Starting PARALLEL workflow execution (max concurrent: {self.max_concurrent})")
        await self.websocket.send_json({"type": "execution_start"})

        try:
            # Build dependency graph
            self._build_dependency_graph()

            # Initialize ready nodes with start nodes
            self.ready_nodes = self._get_start_nodes()

            # Safety counter
            safety_counter = 0
            MAX_STEPS = 100

            while (self.running_tasks or self.ready_nodes) and safety_counter < MAX_STEPS:
                safety_counter += 1

                # Launch new tasks for ready nodes (up to concurrency limit)
                while self.ready_nodes and len(self.running_tasks) < self.max_concurrent:
                    node_id = self.ready_nodes.pop()

                    # Double-check readiness (might have changed)
                    if not self._is_node_ready(node_id):
                        continue

                    # Gather inputs
                    inputs = self._gather_inputs(node_id)

                    # Skip if all inputs blocked by conditions
                    if inputs is None:
                        await self.websocket.send_json({"type": "node_skipped", "node_id": node_id})
                        self.failed_nodes.add(node_id)  # Mark as failed to prevent re-queueing
                        continue

                    # Create and launch task
                    node = self.node_map[node_id]
                    task = asyncio.create_task(self._execute_node_safe(node, inputs or {}))
                    self.running_tasks[node_id] = task
                    self.task_to_node[task] = node_id

                    logger.info(f"Started node {node_id} ({len(self.running_tasks)} running)")

                # If no tasks running, we're done
                if not self.running_tasks:
                    break

                # Wait for at least one task to complete
                done, pending = await asyncio.wait(
                    self.running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for task in done:
                    completed_node_id = self.task_to_node[task]
                    del self.running_tasks[completed_node_id]
                    del self.task_to_node[task]

                    logger.info(f"Node {completed_node_id} finished ({len(self.running_tasks)} still running)")

                    # Find children that might now be ready
                    for child_id in self.dependents.get(completed_node_id, []):
                        if self._is_node_ready(child_id):
                            self.ready_nodes.add(child_id)
                            logger.debug(f"Node {child_id} is now ready")

                # Also check for any other newly ready nodes (e.g., loop re-queueing)
                newly_ready = self._find_newly_ready_nodes()
                self.ready_nodes.update(newly_ready)

            if safety_counter >= MAX_STEPS:
                logger.warning("Workflow stopped: Max execution steps reached (Infinite loop protection).")

            await self.websocket.send_json({
                "type": "execution_complete",
                "stats": {
                    "completed": len(self.completed_nodes),
                    "failed": len(self.failed_nodes),
                    "total": len(self.graph.nodes)
                }
            })

        except Exception as e:
            logger.error(f"Parallel execution error: {e}")
            await self.websocket.send_json({
                "type": "execution_error",
                "node_id": "system",
                "error": str(e)
            })

    async def run(self):
        """Override run() to use parallel execution."""
        await self.run_parallel()