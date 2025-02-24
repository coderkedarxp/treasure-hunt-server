import asyncio
import websockets
import json
import random
import os

# Game state
GRID_SIZE = 10
treasure = (random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1))
players = {}  # {websocket: (x, y)}
clients = set()

async def broadcast(message):
    if clients:
        await asyncio.gather(*(client.send(json.dumps(message)) for client in clients))

async def handle_client(websocket):
    clients.add(websocket)
    player_pos = (0, 0)  # Starting position
    players[websocket] = player_pos
    await broadcast({"type": "update", "players": {id(client): pos for client, pos in players.items()}})
    
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "move":
                dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[data["direction"]]
                x, y = players[websocket]
                new_x, new_y = max(0, min(GRID_SIZE-1, x + dx)), max(0, min(GRID_SIZE-1, y + dy))
                players[websocket] = (new_x, new_y)
                
                if (new_x, new_y) == treasure:
                    await broadcast({"type": "win", "winner": id(websocket)})
                    break
                else:
                    await broadcast({"type": "update", "players": {id(client): pos for client, pos in players.items()}})
    except:
        pass
    finally:
        clients.remove(websocket)
        del players[websocket]
        await broadcast({"type": "update", "players": {id(client): pos for client, pos in players.items()}})

async def main():
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 locally, use PORT env var on Render
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"Server running on port {port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())