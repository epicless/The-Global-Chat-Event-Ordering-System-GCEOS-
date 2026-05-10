import socket
import threading
import json
from lamport_clock import LamportClock

# Load configuration from file (Pillar 1: No hardcoded IPs)
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

clients = []  # List of connected client sockets
messages = []  # List of all messages with timestamps
clock = LamportClock()  # Server's Lamport Clock


def register_with_naming_server():
    # Register this chat server with the naming server
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


def broadcast(message):
    # Send message to all connected clients (Pillar 2: Multicast)
    for client in clients:
        try:
            client.send(message.encode())
        except:
            pass


def handle_client(conn, addr):
    print(f"[CONNECTED] {addr}")

    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                break

            message = json.loads(data)

            # Update Lamport Clock (Pillar 3: Synchronization)
            received_time = message['timestamp']
            updated_time = clock.update(received_time)

            # Store message with dual timestamps for true chronological ordering
            messages.append({
                'username': message['username'],
                'text': message['text'],
                'client_timestamp': received_time,  # When user typed it
                'server_timestamp': updated_time,    # When server received it
                'timestamp': received_time           # Display timestamp
            })

            # Sort by client timestamp first, server timestamp as tiebreaker
            messages.sort(key=lambda x: (x['client_timestamp'], x['server_timestamp']))

            # Display ordered events on server console
            print("\n====== ORDERED EVENTS ======")
            for msg in messages:
                print(f"[{msg['timestamp']}] {msg['username']}: {msg['text']}")
            print("============================")

            # Broadcast ordered messages to all clients
            ordered_chat = {
                'type': 'ordered_messages',
                'messages': messages
            }
            broadcast(json.dumps(ordered_chat))

        except Exception as e:
            print("[SERVER ERROR]", e)
            break

    # Cleanup on disconnect
    if conn in clients:
        clients.remove(conn)
    conn.close()
    print(f"[DISCONNECTED] {addr}")


def start_server():
    # Register with naming server first
    register_with_naming_server()

    # Create and bind TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[CHAT SERVER RUNNING] {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)

        # Handle each client in a separate thread
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE USERS] {len(clients)}")


if __name__ == "__main__":
    start_server()