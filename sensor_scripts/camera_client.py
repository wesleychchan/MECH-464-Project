import socket
import time
import pyrealsense2 as rs
import numpy as np
import cv2
import os
import csv

SERVER_IP = "128.189.146.71"  # Replace with actual server IP
PORT = 4999

# Output directories for local storage
depth_dir = "depth_frames"
color_dir = "color_frames"
log_file = "timestamps.csv"

# Create directories if they don’t exist
os.makedirs(depth_dir, exist_ok=True)
os.makedirs(color_dir, exist_ok=True)

def send_realsense_data():
    # Initialize socket client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    client.send(b"RealSense")  # Identify as RealSense client

    # Configure RealSense pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)  # Depth stream
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # Color stream
    pipeline.start(config)

    # Open CSV file for logging timestamps
    with open(log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Depth File", "Color File"])  # CSV header

        frame_count = 0
        try:
            while True:
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                timestamp = time.time()  # Capture system timestamp

                if not depth_frame or not color_frame:
                    continue

                # Convert frames to numpy arrays
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                # Define file names
                depth_filename = os.path.join(depth_dir, f"depth_{frame_count}.npy")
                depth_png_filename = os.path.join(depth_dir, f"depth_{frame_count}.png")
                color_filename = os.path.join(color_dir, f"color_{frame_count}.png")

                # Save depth as numpy array & PNG
                np.save(depth_filename, depth_image)
                cv2.imwrite(depth_png_filename, cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET))

                # Save color frame
                cv2.imwrite(color_filename, color_image)

                # Log timestamps & filenames
                writer.writerow([timestamp, depth_filename, color_filename])

                # Send data to server
                client.send(f"{timestamp}, {depth_filename}, {color_filename}".encode())

                print(f"Sent frame {frame_count}: {depth_filename}, {color_filename}, Timestamp: {timestamp}")
                frame_count += 1

                # Display images for verification
                cv2.imshow("Depth", cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET))
                cv2.imshow("Color", color_image)

                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                    break

        finally:
            pipeline.stop()
            cv2.destroyAllWindows()
            client.close()

send_realsense_data()
