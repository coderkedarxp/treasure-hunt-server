import asyncio
import websockets
import json
import random
import os

# Game state
players = {}  # {websocket: {"username": str, "score": int}}
clients = set()
questions = [
    {"q": "What’s 2+2?", "options": ["3", "4", "5"], "answer": "4"},
    {"q": "Color of the sky?", "options": ["Red", "Blue", "Green"], "answer": "Blue"}
]
current_question = None
game_active = False

async def broadcast(message):
    if clients:
        await asyncio.gather(*(client.send(json.dumps(message)) for client in clients))

async def start_game():
    global current_question, game_active
    if len(players) >= 3 and not game_active:
        game_active = True
        while game_active:
            current_question = random.choice(questions)
            await broadcast({
                "type": "question",
                "question": current_question["q"],
                "options": current_question["options"]
            })
            await asyncio.sleep(10)  # 10 seconds to answer
            current_question = None
            await broadcast({"type": "timeout"})
            await asyncio.sleep(2)  # Short break

async def handle_client(websocket):
    clients.add(websocket)
    try:
        # Handle join
        username_msg = await websocket.recv()
        data = json.loads(username_msg)
        if data["type"] == "join" and "username" in data:
            username = data["username"]
            players[websocket] = {"username": username, "score": 0}
            await broadcast({
                "type": "update",
                "players": {p["username"]: p["score"] for ws, p in players.items()}
            })
            if not game_active:
                asyncio.create_task(start_game())
        else:
            await websocket.close()
            return

        # Game loop
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "answer" and current_question:
                answer = data["answer"]
                if answer == current_question["answer"]:
                    players[websocket]["score"] += 1
                    if players[websocket]["score"] >= 5:  # Win condition
                        await broadcast({"type": "win", "winner": username})
                        game_active = False
                        break
                    await broadcast({
                        "type": "update",
                        "players": {p["username"]: p["score"] for ws, p in players.items()}
                    })
    except:
        pass
    finally:
        if websocket in players:
            del players[websocket]
            clients.remove(websocket)
            await broadcast({
                "type": "update",
                "players": {p["username"]: p["score"] for ws, p in players.items()}
            })

async def main():
    port = int(os.environ.get("PORT", 8000))
    async with websockets.serve(handle_client, "0.0.0.0", port):
        print(f"Server running on port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())