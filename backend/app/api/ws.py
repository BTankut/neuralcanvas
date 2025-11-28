from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.workflow import WorkflowGraph
from app.engine.executor import WorkflowExecutor, ParallelWorkflowExecutor
from app.core.logging import logger
import json

router = APIRouter()

@router.websocket("/execute")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    try:
        while True:
            # Wait for the client to send the graph JSON
            data = await websocket.receive_text()
            logger.info(f"Received graph data length: {len(data)}")
            graph_data = json.loads(data)
            
            # Validate against Schema
            try:
                graph = WorkflowGraph(**graph_data)
                logger.info(f"Graph validated. Nodes: {len(graph.nodes)}")
            except Exception as e:
                logger.error(f"Graph validation failed: {e}")
                await websocket.send_json({"type": "error", "message": f"Invalid Graph Data: {str(e)}"})
                continue

            # Execute with ParallelWorkflowExecutor (5 concurrent nodes)
            executor = ParallelWorkflowExecutor(graph, websocket, max_concurrent=5)
            await executor.run()
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
