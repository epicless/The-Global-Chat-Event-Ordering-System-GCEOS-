import socket
import threading
import json
from lamport_clock import LamportClock

HOST = '127.0.0.1'
PORT = 6000

clients = []
messages = []

clock = LamportClock()


# Register chat server to naming server
def register_with_naming_server():

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect(('127.0.0.1', 5000))

    message = {
        'type': 'register',
        'service_name': 'chat_server',
        'host': HOST,
        'port': PORT
    }

    client.send(json.dumps(message).encode())

    response = client.recv(1024).decode()

    print("[NAMING SERVER]", response)

    client.close()


# Broadcast message to all clients
def broadcast(message):

    for client in clients:

        try:
            client.send(message.encode())

        except:
            pass


# Handle each connected client
def handle_client(conn, addr):

    print(f"[CONNECTED] {addr}")

    while True:

        try:
            data = conn.recv(4096).decode()

            if not data:
                break

            message = json.loads(data)

            # Update Lamport Clock
            received_time = message['timestamp']

            updated_time = clock.update(received_time)

            # Store chat event
            messages.append({
                'username': message['username'],
                'text': message['text'],
                'timestamp': updated_time
            })

            # Event Ordering System
            messages.sort(key=lambda x: x['timestamp'])

            print("\n====== ORDERED EVENTS ======")

            for msg in messages:
                print(f"[{msg['timestamp']}] {msg['username']}: {msg['text']}")

            print("============================")

            # Send ordered messages
            ordered_chat = {
                'type': 'ordered_messages',
                'messages': messages
            }

            broadcast(json.dumps(ordered_chat))

        except Exception as e:
            print("[SERVER ERROR]", e)
            break

    if conn in clients:
        clients.remove(conn)

    conn.close()


# Start chat server
def start_server():

    register_with_naming_server()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))

    server.listen()

    print(f"[CHAT SERVER RUNNING] {HOST}:{PORT}")

    while True:

        conn, addr = server.accept()

        clients.append(conn)

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr)
        )

        thread.start()


start_server()