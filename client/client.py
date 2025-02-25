import asyncio
import websockets
import json
import sys

async def game_loop():
    uri = "wss://treasure-hunt-game-qvvk.onrender.com/"   
    async with websockets.connect(uri) as websocket:
        async def receive():
            while True:
                message = json.loads(await websocket.recv())
                if message["type"] == "update":
                    print("Player positions:", message["players"])
                elif message["type"] == "win":
                    print(f"Player {message['winner']} found the treasure!")
                    sys.exit(0)

        asyncio.create_task(receive())
        
        while True:
            move = input("Move (up/down/left/right): ")
            if move in ["up", "down", "left", "right"]:
                await websocket.send(json.dumps({"type": "move", "direction": move}))
            await asyncio.sleep(0.1)

asyncio.run(game_loop())