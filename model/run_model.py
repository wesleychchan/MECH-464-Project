import os
import time
import subprocess
import torch
import cv2

cad_path = "/workspace/USdata/ultrasound-probe.ply"
camera_path = "/workspace/USdata/camera.json"
output_base = "/workspace/USdata/output2"
rgb_base = "/workspace/USdata/rgb"
depth_base = "/workspace/USdata/depth"
num_frames = 122 
resize_dims =(512, 512) # (320, 320)

for i in range(num_frames):
    print(f"\n[INFO] Processing frame {i}...")

    rgb_path = f"{rgb_base}/image{i}.png"
    depth_path = f"{depth_base}/depth{i}.png"
    output_dir = f"{output_base}/frame_{i}"

    if not os.path.exists(rgb_path) or not os.path.exists(depth_path):
        print(f"[WARNING] Skipping frame {i} due to missing RGB or depth image.")
        continue

    try:
        depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
        if depth is not None:
            depth_resized = cv2.resize(depth, resize_dims, interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(depth_path, depth_resized)
        else:
            print(f"[WARNING] Could not read {depth_path}")
    except Exception as e:
        print(f"[ERROR] Resizing depth image failed: {e}")

    resize_dims = (512, 512)
    try:
        img = cv2.imread(rgb_path)
        if img is not None:
            img_resized = cv2.resize(img, resize_dims)
            cv2.imwrite(rgb_path, img_resized)
        else:
            print(f"[WARNING] Could not read {rgb_path}")
    except Exception as e:
        print(f"[ERROR] Resizing RGB image failed: {e}")
    
    env = os.environ.copy()
    env["CAD_PATH"] = cad_path
    env["RGB_PATH"] = rgb_path
    env["DEPTH_PATH"] = depth_path
    env["CAMERA_PATH"] = camera_path
    env["OUTPUT_DIR"] = output_dir
    env["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:32"
    env["FRAME_IDX"] = str(i)

    torch.cuda.empty_cache()

    try:
        subprocess.run(["sh", "demo.sh"], env=env, check=True)
    except Exception as e:
        print(f"[ERROR] Frame {i} failed: {e}")
        continue
    time.sleep(2)

