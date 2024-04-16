import asyncio
import logging
import websockets

MAX_CLIENTS = 20
connected_clients = set()  # Track active connections
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set logging level to INFO

async def authenticate_client(websocket, path):
    try:
        data = await websocket.recv()
        username, password = data.split(',')
        await websocket.send("Authenticated")
        connected_clients.add(websocket)  # Add the client to the set of connected clients
    except Exception as e:
        await websocket.send("Error occurred during authentication")
        logger.error(f"Error during authentication: {e}")

async def trigger_command():
    for client in connected_clients:
        try:
            await client.send("Left click detected on Server PC.")
            logger.info("Message sent to all connected clients.")  # Log message sent to clients
        except Exception as e:
            logger.error(f"Error sending message to client: {e}")
            connected_clients.remove(client)
    logger.info("Trigger command sent to all connected clients.")
    print("Message sent to all connected clients.")

async def server(websocket, path):
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            if message == "trigger_command":
                await trigger_command()
            response = f"Received: {message}"
            await websocket.send(response)
            print(f"Sent response: {message}")
    except Exception as e:
        logger.error(f"Error occurred in server: {e}")

async def main():
    async with websockets.serve(server, "0.0.0.0", 8765):
        print("WebSocket server started.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
