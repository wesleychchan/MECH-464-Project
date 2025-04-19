"""
    Do not run this on the same computer as the server - it should be running with camera_client
"""

import socket
import time
import json

SERVER_IP = "0.0.0.0"  # Change to the actual server IP
PORT = 4999
RETRY_DELAY = 5  # Seconds to wait before retrying connection

def get_data():
    """Return the sensor or array data. Modify this function to supply actual data."""
    data = [0.1, 0.2, 0.3]
    return data

def send_data():
    try:
        # Establish connection with the server.
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, PORT))
        print("Connected to server.")

        # Optional handshake message.
        client.send(b"ClientConnected")

        while True:
            # Block until the server sends a request message.
            server_msg = client.recv(1024)
            if not server_msg:
                # An empty message indicates the server closed the connection.
                print("Server closed the connection.")
                break

            # Trim any whitespace and decode.
            request = server_msg.strip()
            print(f"Received request: {request}")

            # Check if the request is a trigger to send data.
            if request == b"RequestEMData":
                timestamp = time.time()
                data_payload = {
                    "timestamp": timestamp,
                    "data": get_data()
                }
                # Send the JSON-encoded payload.
                client.send(json.dumps(data_payload).encode())
                print(f"Sent data: {data_payload}")
            else:
                print("Received an unrecognized request; ignoring.")

    except (socket.error, ConnectionRefusedError) as e:
        print(f"Connection error: {e}. Retrying in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
    finally:
        client.close()
        print("Connection closed. Attempting reconnection...")

if __name__ == "__main__":
    while True:
        send_data()
