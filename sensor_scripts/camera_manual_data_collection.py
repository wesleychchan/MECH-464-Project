import time
import pyrealsense2 as rs
import numpy as np
import cv2
import os
import csv

# Determine the script's directory and set paths relative to it
base_dir = os.path.dirname(os.path.abspath(__file__))
depth_dir = os.path.join(base_dir, "depth_frames")
color_dir = os.path.join(base_dir, "color_frames")
log_file = os.path.join(base_dir, "camera_timestamps.csv")

# Create folders if they don't exist
os.makedirs(depth_dir, exist_ok=True)
os.makedirs(color_dir, exist_ok=True)

def main():
    frame_count = 0

    # Initialize RealSense pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
    pipeline.start(config)

    # Open CSV log file
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        # Write header only if file is empty
        if os.stat(log_file).st_size == 0:
            writer.writerow(["Timestamp", "Depth File", "Color File"])

        print("Recording started. Press 'q' to quit.")
        try:
            while True:
                # Wait for a new frame
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                timestamp = time.time()

                if not depth_frame or not color_frame:
                    print("Invalid frame, skipping.")
                    continue

                # Convert to NumPy arrays
                depth_image = np.asanyarray(depth_frame.get_data())
                color_image = np.asanyarray(color_frame.get_data())

                # Create filenames
                depth_filename = os.path.join(depth_dir, f"depth_{frame_count}.npy")
                color_filename = os.path.join(color_dir, f"color_{frame_count}.png")

                # Save data
                np.save(depth_filename, depth_image)
                cv2.imwrite(color_filename, color_image)

                # Log the data
                writer.writerow([timestamp, depth_filename, color_filename])
                f.flush()

                # Show frames
                depth_display = cv2.applyColorMap(
                    cv2.convertScaleAbs(depth_image, alpha=0.03),
                    cv2.COLORMAP_JET)
                cv2.imshow("Depth", depth_display)
                cv2.imshow("Color", color_image)

                # Quit on key press 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("User requested exit.")
                    break

                print(f"Captured frame {frame_count}")
                frame_count += 1

        finally:
            pipeline.stop()
            cv2.destroyAllWindows()
            print("Capture stopped.")

if __name__ == "__main__":
    main()
