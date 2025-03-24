"""
    Run this on the same computer as the camera client. 
"""

import socket
import time
import csv
import threading

HOST = "0.0.0.0"
PORT = 4999
LOG_FILE = "../data/synchronized_data.csv"
CYCLE_INTERVAL = 0.1  # Delay between cycles (adjust as needed)
BUFFER_SIZE = 4096

# Global storage for the connected clients
clients = {"RealSense": None, "EMTracker": None}
clients_lock = threading.Lock()

def log_header():
    """Initialize CSV file with header."""
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ServerCycleTimestamp", "CameraTimestamp", "CameraData",
            "EMTimestampCorrected", "EMData", "RTT_Delay"
        ])

def log_data(server_ts, cam_ts, cam_data, em_ts_corr, em_data, delay):
    """Append a synchronized data row to the CSV file."""
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([server_ts, cam_ts, cam_data, em_ts_corr, em_data, delay])
    print(f"Logged row at {server_ts}")

def accept_clients(server_sock):
    """
    Accept incoming connections until both expected clients are connected.
    Each client is identified by its initial handshake message.
    """
    print("Waiting for clients to connect...")
    while True:
        client_sock, addr = server_sock.accept()
        print(f"Connection from {addr}")
        # Read handshake message
        try:
            handshake = client_sock.recv(BUFFER_SIZE)
            if not handshake:
                client_sock.close()
                continue
            client_type = handshake.decode().strip()
            with clients_lock:
                if client_type in clients and clients[client_type] is None:
                    clients[client_type] = client_sock
                    print(f"{client_type} client connected from {addr}")
                else:
                    print(f"Unknown or duplicate client type '{client_type}' from {addr}")
                    client_sock.close()
        except Exception as e:
            print(f"Error handling client from {addr}: {e}")
            client_sock.close()

        with clients_lock:
            if clients["RealSense"] is not None and clients["EMTracker"] is not None:
                print("Both clients connected.")
                break

def synchronized_cycle():
    """
    For each cycle, request camera data first.
    Then, measure round-trip time for the EM data request and adjust the EM timestamp.
    Finally, log the synchronized data.
    """
    camera_sock = clients["RealSense"]
    em_sock = clients["EMTracker"]

    while True:
        try:
            # --- Camera Data Cycle ---
            # Request camera data
            camera_sock.send(b"RequestCameraData")
            cam_response = camera_sock.recv(BUFFER_SIZE).decode().strip()
            # Expecting a comma-separated message: "t_cam, <additional camera info>"
            cam_parts = cam_response.split(",", 1)
            if len(cam_parts) < 1:
                print("Invalid camera data received.")
                continue
            t_cam = float(cam_parts[0].strip())
            cam_extra = cam_parts[1].strip() if len(cam_parts) > 1 else ""
            print(f"Received camera data: t_cam={t_cam}, extra='{cam_extra}'")

            # --- EM Data Cycle with RTT measurement ---
            t_req = time.time()  # Record time immediately before sending request
            em_sock.send(b"RequestEMData")
            em_response = em_sock.recv(BUFFER_SIZE).decode().strip()
            t_resp = time.time()  # Record time immediately after reception

            # Compute estimated one-way delay (RTT/2)
            delay = (t_resp - t_req) / 2

            # Expect EM client to return a comma-separated message: "t_EM, <additional EM info>"
            em_parts = em_response.split(",", 1)
            if len(em_parts) < 1:
                print("Invalid EM data received.")
                continue
            t_em = float(em_parts[0].strip())
            em_extra = em_parts[1].strip() if len(em_parts) > 1 else ""
            t_em_corrected = t_em - delay
            print(f"Received EM data: original t_em={t_em}, delay={delay:.4f}, corrected t_em={t_em_corrected:.4f}, extra='{em_extra}'")

            # --- Collate and Log ---
            server_ts = time.time()
            log_data(server_ts, t_cam, cam_extra, t_em_corrected, em_extra, delay)

            time.sleep(CYCLE_INTERVAL)

        except (socket.error, ValueError) as e:
            print(f"Error during cycle: {e}")
            break

def main():
    log_header()
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    # Accept both clients
    accept_clients(server_sock)

    # Start synchronized cycle in the main thread.
    try:
        synchronized_cycle()
    except KeyboardInterrupt:
        print("Server shutting down due to keyboard interrupt.")
    finally:
        # Close all client sockets
        with clients_lock:
            for client_type, sock in clients.items():
                if sock:
                    sock.close()
        server_sock.close()

if __name__ == "__main__":
    main()
