import socket
import threading
import json

# Load configuration from file (Pillar 1: No hardcoded IPs)
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] config.json not found. Please create configuration file.")
        exit(1)

config = load_config()
HOST = config['naming_server']['host']
PORT = config['naming_server']['port']

services = {}  # Service registry: {service_name: {host, port}}


def handle_client(conn):
    global services

    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break

            message = json.loads(data)

            # Handle service registration
            if message['type'] == 'register':
                services[message['service_name']] = {
                    'host': message['host'],
                    'port': message['port']
                }
                conn.send(json.dumps({'status': 'registered'}).encode())
                print(f"[REGISTERED] {message['service_name']} at {message['host']}:{message['port']}")

            # Handle service lookup
            elif message['type'] == 'lookup':
                service = services.get(message['service_name'])
                conn.send(json.dumps(service).encode())
                if service:
                    print(f"[LOOKUP] {message['service_name']} -> {service['host']}:{service['port']}")

        except Exception as e:
            print(f"[ERROR] {e}")
            break

    conn.close()


def start_server():
    # Create and bind TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[NAMING SERVER RUNNING] {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"[CONNECTION] {addr}")

        # Handle each client in a separate thread
        thread = threading.Thread(target=handle_client, args=(conn,))
        thread.start()


if __name__ == "__main__":
    start_server()