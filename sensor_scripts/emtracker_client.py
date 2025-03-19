import socket
import time

SERVER_IP = "128.189.146.71"
PORT = 4999

def send_emtracker_data():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    client.send(b"EMTracker")  

    while True:
        timestamp = time.time()
        em_data = f"{timestamp}, EMTracker Position Data"
        client.send(em_data.encode())
        time.sleep(0.1)

send_emtracker_data()


