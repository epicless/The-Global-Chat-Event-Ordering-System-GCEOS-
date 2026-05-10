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
NAMING_SERVER_HOST = config['naming_server']['host']
NAMING_SERVER_PORT = config['naming_server']['port']

clock = LamportClock()  # Client's Lamport Clock


def lookup_server():
    # Discover chat server address from naming server (Pillar 1)
    naming_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    naming_client.connect((NAMING_SERVER_HOST, NAMING_SERVER_PORT))

    request = {
        'type': 'lookup',
        'service_name': 'chat_server'
    }

    naming_client.send(json.dumps(request).encode())
    response = json.loads(naming_client.recv(1024).decode())
    naming_client.close()

    return response['host'], response['port']


def receive_messages(client_socket):
    # Receive messages from server in background thread (Pillar 2: Asynchronous)
    while True:
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                break

            message = json.loads(data)

            if message['type'] == 'ordered_messages':
                print("\n========== ORDERED CHAT ==========")

                for msg in message['messages']:
                    # Update Lamport clock when receiving messages (Pillar 3)
                    updated_time = clock.update(msg['timestamp'])
                    print(f"[{updated_time}] {msg['username']}: {msg['text']}")

                print("==================================")
                print("You: ", end="", flush=True)

        except Exception as e:
            print("\n[RECEIVE ERROR]", e)
            break


def start_client():
    username = input("Enter username: ")

    # Discover chat server dynamically (no hardcoded address)
    host, port = lookup_server()

    # Connect to chat server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    print(f"Connected to Chat Server {host}:{port}\n")

    # Start receive thread (daemon = terminates with main thread)
    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )
    receive_thread.start()

    # Main thread: send messages
    while True:
        try:
            text = input("You: ")
            if text.strip() == "":
                continue

            # Increment Lamport clock before sending (Pillar 3)
            timestamp = clock.increment()

            # Create JSON message (Pillar 2: Message-oriented)
            message = {
                'type': 'chat',
                'username': username,
                'text': text,
                'timestamp': timestamp
            }

            client.send(json.dumps(message).encode())

        except KeyboardInterrupt:
            print("\n[INFO] Disconnecting...")
            break
        except Exception as e:
            print("\n[SEND ERROR]", e)
            break

    client.close()


if __name__ == "__main__":
    start_client()