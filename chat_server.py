import socket
import threading
import json
from lamport_clock import LamportClock

# Load configuration from config file (no hardcoded addresses)
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] config.json not found. Please create configuration file.")
        exit(1)

config = load_config()
HOST = config['chat_server']['host']
PORT = config['chat_server']['port']
NAMING_SERVER_HOST = config['naming_server']['host']
NAMING_SERVER_PORT = config['naming_server']['port']

clients = []
messages = []

clock = LamportClock()


# Register chat server to naming server
def register_with_naming_server():

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect((NAMING_SERVER_HOST, NAMING_SERVER_PORT))

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

            # Store chat event with both client and server timestamps
            messages.append({
                'username': message['username'],
                'text': message['text'],
                'client_timestamp': received_time,  # When user typed it
                'server_timestamp': updated_time,    # When server received it
                'timestamp': received_time           # Display timestamp (client's)
            })

            # Event Ordering System - Sort by client timestamp (true chronological order)
            # Use server timestamp as tiebreaker for simultaneous messages
            messages.sort(key=lambda x: (x['client_timestamp'], x['server_timestamp']))

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