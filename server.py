import tkinter as tk
from tkinter import messagebox
import logging
import asyncio
import websockets
import threading
import pyautogui
from pynput.mouse import Listener, Button

MAX_CLIENTS = 20
clients = {}
logger = logging.getLogger(__name__)
credentials_entered = False
confirm_button_created = False

async def authenticate_client(websocket, path):
    try:
        data = await websocket.recv()
        username, password = data.split(',')
        if any((username == entry[0].get() and password == entry[1].get()) for entry in clients.values()):
            await websocket.send("Authenticated")
        else:
            await websocket.send("Authentication Failed")
    except Exception as e:
        await websocket.send("Error occurred during authentication")
        logger.error(f"Error during authentication: {e}")

async def trigger_command():
    pyautogui.click()
    logger.info("Trigger command sent to all connected clients.")

async def send_click_command():
    def on_click(x, y, button, pressed):
        if button == Button.left and pressed:
            print("Left click detected on Server PC.")
            asyncio.run_coroutine_threadsafe(trigger_command(), loop)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    listener = Listener(on_click=on_click)
    listener.start()
    print("Listener started")
    # Close the listener to avoid resource leaks
    try:
        await asyncio.Future()  # Keep the function running
    finally:
        listener.stop()
        listener.join()
        print("Listener stopped")

    print("Listener stopped")

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
    async with websockets.serve(server, "localhost", 8765):
        print("WebSocket server started.")
        await asyncio.Future()

def start_server():
    global credentials_entered
    
    if not credentials_entered:
        messagebox.showerror("Error", "Please enter client credentials and confirm first.")
        logger.error("Server cannot be started without confirming client credentials.")
        return
    
    num_clients = num_clients_entry.get()
    try:
        num_clients = int(num_clients)
        if num_clients <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number of clients.")
        logger.error("Invalid input for number of clients.")
        return
    
    # Start the WebSocket server
    server_thread = threading.Thread(target=asyncio.run, args=(main(),))
    server_thread.start()

    # Start listening for mouse clicks
    threading.Thread(target=asyncio.run, args=(send_click_command(),)).start()

    # Update GUI status
    status_label.config(text="WebSocket server started.")
    logger.info("WebSocket server started.")

def confirm_credentials():
    global credentials_entered
    any_credentials_entered = any(username_entry.get() and password_entry.get() for username_entry, password_entry in clients.values())
    if any_credentials_entered:
        credentials_entered = True
        start_server_button.config(state=tk.NORMAL) 
        status_label.config(text="Credentials entered. You can now start the server.")
        logger.info("Credentials for at least one client have been confirmed.")
    else:
        messagebox.showerror("Error", "Please enter at least one set of client credentials.")

def on_enter(event):
    global credentials_entered
    global confirm_button_created
    
    for widget in root.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.destroy()
    clients.clear()
    num_clients_str = num_clients_entry.get()
    try:
        num_clients = min(int(num_clients_str), MAX_CLIENTS)
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number of clients.")
        logger.error("Invalid input for number of clients.")
        return

    for i in range(num_clients):
        client_frame = tk.Frame(root)
        client_frame.pack(pady=5)
        username_label = tk.Label(client_frame, text=f"Username for client {i+1}:")
        username_label.pack(side=tk.LEFT)
        username_entry = tk.Entry(client_frame)
        username_entry.pack(side=tk.LEFT)
        password_label = tk.Label(client_frame, text=f"Password for client {i+1}:")
        password_label.pack(side=tk.LEFT)
        password_entry = tk.Entry(client_frame)
        password_entry.pack(side=tk.LEFT)
        clients[f"client_{i+1}"] = (username_entry, password_entry)

    if not confirm_button_created:
        global confirm_button
        confirm_button = tk.Button(root, text="Confirm Credentials", command=confirm_credentials)
        confirm_button.pack(pady=10)
        confirm_button_created = True

    num_clients_entry.config(state=tk.DISABLED)

    status_label.config(text="Server not started.")
    logger.info("Enter client credentials below and confirm.")

    num_clients_entry.unbind("<Return>")
    num_clients_entry.bind("<Return>", on_enter)

root = tk.Tk()
root.title("WebSocket Server")

num_clients_label = tk.Label(root, text="Number of clients:")
num_clients_label.pack(pady=5)
num_clients_entry = tk.Entry(root)
num_clients_entry.pack(pady=5)
num_clients_entry.bind("<Return>", on_enter)

status_label = tk.Label(root, text="Server not started.")
status_label.pack(pady=10)

start_server_button = tk.Button(root, text="Start Server", command=start_server)
start_server_button.pack()
start_server_button.config(state=tk.NORMAL)  

root.mainloop()
