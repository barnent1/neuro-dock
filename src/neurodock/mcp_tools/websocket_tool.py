"""
Modular handler for the MCP WebSocket endpoint.
Handles bidirectional communication for VSCode/Copilot and other MCP clients.
Implements robust error handling and logging.
"""

import logging
from fastapi import WebSocket, WebSocketDisconnect, status
from neurodock.mcp_tools.memory_tool import handle_memory_store
from neurodock.mcp_tools.task_tool import handle_task_create
from neurodock.mcp_tools.context_tool import handle_context_query

logger = logging.getLogger(__name__)

async def handle_websocket(websocket: WebSocket):
    """
    Main handler for the /ws WebSocket endpoint.
    Accepts the connection and processes incoming MCP commands.
    """
    await websocket.accept()
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                import json
                data = json.loads(data_text)
            except Exception as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_json({
                    "success": False,
                    "message": f"Invalid JSON: {e}"
                })
                continue

            command = data.get("command")
            payload = data.get("payload", {})
            request_id = data.get("requestId", "unknown")
            response = {"requestId": request_id}

            try:
                if command == "store_memory":
                    result = await handle_memory_store(payload)
                    response.update(result)
                elif command == "create_task":
                    result = await handle_task_create(payload)
                    response.update(result)
                elif command == "query_context":
                    result = await handle_context_query(payload)
                    response.update(result)
                else:
                    response.update({
                        "success": False,
                        "message": f"Unknown command: {command}"
                    })
                await websocket.send_json(response)
            except Exception as e:
                logger.error(f"Error handling command '{command}': {e}")
                await websocket.send_json({
                    "requestId": request_id,
                    "success": False,
                    "message": f"Error handling command '{command}': {e}"
                })
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        if websocket.client_state != websocket.client_state.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            await websocket.send_json({
                "success": False,
                "message": f"WebSocket error: {e}"
            })
