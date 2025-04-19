import pandas as pd
import os

pose_csv_path = "data/Parsed_Pose_Data.csv"  
image_folder = "data/MECH464-Color/"    
output_csv_path = "data/pose_with_image_matches.csv" 

pose_df = pd.read_csv(pose_csv_path)
pose_df['image_ts'] = 0  # default = unassigned
pose_df['image_filename'] = ""  

def extract_ts(filename):
    try:
        return int(float(filename.split("_")[-1].replace(".png", "")))
    except:
        return None

image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]
image_data = [(f, extract_ts(f)) for f in image_files]
image_data = [(f, ts) for f, ts in image_data if ts is not None]
image_data.sort(key=lambda x: x[1]) 
pose_df['time'] = (pose_df['time'] * 1000).astype(int) 

pose_times = pose_df['time'].values

for fname, img_ts in image_data:
    abs_diffs = abs(pose_times - img_ts)
    closest_idx = abs_diffs.argmin()

    pose_df.at[closest_idx, 'image_ts'] = img_ts
    pose_df.at[closest_idx, 'image_filename'] = fname

pose_df = pose_df[pose_df['image_ts'] != 0].reset_index(drop=True)
pose_df.to_csv(output_csv_path, index=False)