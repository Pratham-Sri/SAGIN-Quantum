import asyncio
import websockets
import socket
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelemetryRelay")

# Connected React Clients
CONNECTIONS = set()

# We act as a UDP server to ingest routing details from controller.py
UDP_IP = "127.0.0.1"
UDP_PORT = 8081

# And act as a WS server to broadcast to the React Visualizer
WS_HOST = "0.0.0.0"
WS_PORT = 8080

async def handle_ws(websocket):
    """Handle new frontend connections."""
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)

async def udp_listener():
    """Listen for incoming JSON packets via UDP and broadcast to WS clients."""
    loop = asyncio.get_running_loop()
    
    class TelemetryProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            try:
                # The msg is JSON payload
                msg = data.decode()
                # Broadcast sequentially to all open clients
                for ws in list(CONNECTIONS):
                    asyncio.create_task(ws.send(msg))
            except Exception as e:
                logger.error(f"Error handling UDP datagram: {e}")

    logger.info(f"Starting UDP listener on {UDP_IP}:{UDP_PORT}")
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: TelemetryProtocol(),
        local_addr=(UDP_IP, UDP_PORT)
    )
    return transport

async def main():
    logger.info(f"Starting WebSocket server on ws://{WS_HOST}:{WS_PORT}")
    async with websockets.serve(handle_ws, WS_HOST, WS_PORT):
        # Start the UDP relay
        transport = await udp_listener()
        
        # Keep alive
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
