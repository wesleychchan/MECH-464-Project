"""
    Run this on the same computer as the server. 
"""

import socket
import time
import pyrealsense2 as rs
import numpy as np
import cv2
import os
import csv

SERVER_IP = "206.87.234.104"  # Replace with actual server IP
PORT = 4999           # Replace with actual server port
RETRY_DELAY = 5       # Seconds to wait before reconnection

# Directories and log file setup
depth_dir = "../data/depth_frames"
color_dir = "../data/color_frames"
log_file = "../data/camera_timestamps.csv"
os.makedirs(depth_dir, exist_ok=True)
os.makedirs(color_dir, exist_ok=True)

def send_realsense_data():
    frame_count = 0
    try:
        # Create and connect the client socket.
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, PORT))
        print("Connected to server.")
        # Send handshake message to identify client type.
        client.send(b"RealSense")

        # Start the RealSense pipeline.
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        pipeline.start(config)

        # Open CSV file in append mode; write header if starting fresh.
        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if frame_count == 0:
                writer.writerow(["Timestamp", "Depth File", "Color File"])

            while True:
                # Block until the server sends a request.
                server_msg = client.recv(1024)
                if not server_msg:
                    print("Server closed the connection.")
                    break

                request = server_msg.strip()
                print(f"Received request: {request}")

                if request == b"RequestCameraData":
                    # Capture frames upon receiving a data request.
                    frames = pipeline.wait_for_frames()
                    depth_frame = frames.get_depth_frame()
                    color_frame = frames.get_color_frame()
                    timestamp = time.time()

                    if not depth_frame or not color_frame:
                        print("Invalid frame data, skipping this request.")
                        continue

                    # Convert frames to numpy arrays.
                    depth_image = np.asanyarray(depth_frame.get_data())
                    color_image = np.asanyarray(color_frame.get_data())

                    # Define filenames for saving data.
                    depth_filename = os.path.join(depth_dir, f"depth_{frame_count}.npy")
                    depth_png_filename = os.path.join(depth_dir, f"depth_{frame_count}.png")
                    color_filename = os.path.join(color_dir, f"color_{frame_count}.png")

                    # Save the depth data and images.
                    np.save(depth_filename, depth_image)
                    cv2.imwrite(depth_png_filename, cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET))
                    cv2.imwrite(color_filename, color_image)

                    # Log the timestamp and file paths.
                    writer.writerow([timestamp, depth_filename, color_filename])
                    f.flush()  # Ensure data is written promptly

                    # Send the data info back to the server.
                    data_str = f"{timestamp}, {depth_filename}, {color_filename}"
                    client.send(data_str.encode())
                    print(f"Sent frame {frame_count}: {data_str}")
                    frame_count += 1

                    # Optionally, display images for debugging.
                    cv2.imshow("Depth", cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET))
                    cv2.imshow("Color", color_image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Quitting on user request.")
                        return
                else:
                    print("Received unrecognized request; ignoring.")

    except (socket.error, ConnectionRefusedError) as e:
        print(f"Connection error: {e}. Retrying in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
    finally:
        try:
            client.close()
        except Exception:
            pass
        try:
            pipeline.stop()
        except Exception:
            pass
        cv2.destroyAllWindows()
        print("Connection closed. Attempting reconnection...")

if __name__ == "__main__":
    while True:
        send_realsense_data()
