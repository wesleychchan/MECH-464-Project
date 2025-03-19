import socket
import threading
import time

clients = {}
log_file = "synchronized_data.log"

def log_data(client_name, data):
    timestamp = time.time()
    with open(log_file, "a") as f:
        f.write(f"{timestamp}, {client_name}, {data}\n")

def handle_client(client_socket, client_name):
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(f"[{client_name}] {data}")
            log_data(client_name, data)  # Log data
        except:
            break
    client_socket.close()
    del clients[client_name]
    print(f"{client_name} disconnected.")

def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")

        client_name = client_socket.recv(1024).decode()
        clients[client_name] = client_socket
        print(f"{client_name} connected.")

        threading.Thread(target=handle_client, args=(client_socket, client_name)).start()

start_server(host="0.0.0.0", port=4999)
