import socket
import threading
import json

HOST = '127.0.0.1'
PORT = 5000

services = {}


def handle_client(conn):
    global services

    while True:
        try:
            data = conn.recv(1024).decode()

            if not data:
                break

            message = json.loads(data)

            if message['type'] == 'register':
                services[message['service_name']] = {
                    'host': message['host'],
                    'port': message['port']
                }

                conn.send(json.dumps({
                    'status': 'registered'
                }).encode())

            elif message['type'] == 'lookup':

                service = services.get(message['service_name'])

                conn.send(json.dumps(service).encode())

        except:
            break

    conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[NAMING SERVER RUNNING] {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(conn,)
        )

        thread.start()


start_server()