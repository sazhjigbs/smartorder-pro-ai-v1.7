#!/usr/bin/env python3
"""
WebSocket Server for SmartOrder PRO AI v2.4
Real-time data streaming on port 8182
by MAIGA ABOUBAKR - SAFELOGIC
"""

import asyncio
import websockets
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_DIR = Path("/opt/smartorder-pro/config")
POSITIONS_FILE = CONFIG_DIR / "positions.json"
WALLET_FILE = CONFIG_DIR / "paper_wallet.json"
PNL_FILE = CONFIG_DIR / "pnl_tracker.json"

# Connected clients
clients = set()

async def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    return None

async def get_positions():
    """Get current positions"""
    data = await load_json_file(POSITIONS_FILE)
    return data if data else []

async def get_wallet():
    """Get wallet data"""
    wallet = await load_json_file(WALLET_FILE)
    pnl = await load_json_file(PNL_FILE)
    
    if wallet and pnl:
        return {
            "balance_usdt": wallet.get("balance_usdt", 0),
            "total_pnl": pnl.get("total_pnl", 0),
            "total_trades": pnl.get("total_trades", 0)
        }
    return None

async def broadcast_message(message):
    """Broadcast message to all connected clients"""
    if clients:
        await asyncio.gather(
            *[client.send(json.dumps(message)) for client in clients],
            return_exceptions=True
        )

async def stream_updates():
    """Stream periodic updates to clients"""
    while True:
        try:
            # Send positions update
            positions = await get_positions()
            if positions:
                await broadcast_message({
                    "type": "positions",
                    "data": positions,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send wallet update
            wallet = await get_wallet()
            if wallet:
                await broadcast_message({
                    "type": "wallet",
                    "data": wallet,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send heartbeat
            await broadcast_message({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in stream_updates: {e}")
        
        # Wait 3 seconds before next update
        await asyncio.sleep(3)

async def handler(websocket, path):
    """Handle WebSocket connections"""
    clients.add(websocket)
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected. Total clients: {len(clients)}")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Connected to SmartOrder PRO AI WebSocket",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from client {client_id}: {data}")
                
                # Handle specific requests
                if data.get("action") == "get_positions":
                    positions = await get_positions()
                    await websocket.send(json.dumps({
                        "type": "positions",
                        "data": positions,
                        "timestamp": datetime.now().isoformat()
                    }))
                elif data.get("action") == "get_wallet":
                    wallet = await get_wallet()
                    await websocket.send(json.dumps({
                        "type": "wallet",
                        "data": wallet,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    finally:
        clients.remove(websocket)
        logger.info(f"Client {client_id} removed. Total clients: {len(clients)}")

async def main():
    """Main server function"""
    logger.info("Starting WebSocket server on 0.0.0.0:8182")
    
    # Start the update streaming task
    update_task = asyncio.create_task(stream_updates())
    
    # Start the WebSocket server
    async with websockets.serve(handler, "0.0.0.0", 8182):
        logger.info("WebSocket server started successfully")
        logger.info("Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
