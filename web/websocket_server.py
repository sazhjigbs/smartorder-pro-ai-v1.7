# -*- coding: utf-8 -*-
"""WebSocket Server - Real-time data streaming"""
import asyncio
import json
import websockets
from datetime import datetime

class WebSocketServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        
    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"Received: {data}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if self.clients:
            data = json.dumps(message)
            await asyncio.gather(
                *[client.send(data) for client in self.clients],
                return_exceptions=True
            )
    
    async def start(self):
        """Start WebSocket server"""
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

# Usage
if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())
