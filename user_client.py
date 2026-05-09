import socket
import threading
import json
from lamport_clock import LamportClock

clock = LamportClock()


# Lookup chat server from naming server
def lookup_server():

    naming_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    naming_client.connect(('127.0.0.1', 5000))

    request = {
        'type': 'lookup',
        'service_name': 'chat_server'
    }

    naming_client.send(json.dumps(request).encode())

    response = json.loads(
        naming_client.recv(1024).decode()
    )

    naming_client.close()

    return response['host'], response['port']


# Receive messages from chat server
def receive_messages(client_socket):

    while True:
        try:
            data = client_socket.recv(4096).decode()

            if not data:
                break

            message = json.loads(data)

            # Ordered chat messages
            if message['type'] == 'ordered_messages':

                print("\n========== ORDERED CHAT ==========")

                for msg in message['messages']:

                    updated_time = clock.update(msg['timestamp'])

                    print(f"[{updated_time}] {msg['username']}: {msg['text']}")

                print("==================================")

                # Redraw input line
                print("You: ", end="", flush=True)

        except Exception as e:
            print("\n[RECEIVE ERROR]", e)
            break


# Main client
def start_client():

    username = input("Enter username: ")

    host, port = lookup_server()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client.connect((host, port))

    print(f"Connected to Chat Server {host}:{port}")

    # Start receiving thread
    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client,),
        daemon=True
    )

    receive_thread.start()

    # Send messages continuously
    while True:

        try:
            text = input("You: ")

            if text.strip() == "":
                continue

            timestamp = clock.increment()

            message = {
                'type': 'chat',
                'username': username,
                'text': text,
                'timestamp': timestamp
            }

            client.send(json.dumps(message).encode())

        except Exception as e:
            print("\n[SEND ERROR]", e)
            break

    client.close()


start_client()