import cv2
import numpy as np
from scipy.spatial.transform import Rotation as R
import csv
import os
import json


"""
image_file = "test_img.png"


# === EM tracker data: pose of probe in base frame ===
x, y, z = 5.977*0.0254, -2.439*0.0254, 0.396*0.0254  # meters?
azimuth, elevation, roll = 145.984, 1.959, -175.165  # degrees
"""


# === Camera Intrinsics (replace with actual values) ===
fx, fy = 621.94506836, 621.4609375
cx, cy = 317.80065918, 246.69602966
camera_matrix = np.array([[fx, 0, cx],
                         [0, fy, cy],
                         [0,  0,  1]], dtype=np.float32)
dist_coeffs = np.zeros((5, 1)) 


def get_T_base_aruco(marker_length):
   # Rotation: ArUco to EM base
   R_base_aruco = np.array([
       [ 0,  0,  1],
       [-1,  0,  0],
       [ 0, -1,  0]
   ])


   # Translation from center to bottom-center in ArUco frame
   offset_aruco = np.array([0, marker_length / 2, 0])  # +Y in ArUco frame
   t_base_aruco = R_base_aruco @ offset_aruco


   # Combine into 4x4 transform
   T_base_aruco = np.eye(4)
   T_base_aruco[:3, :3] = R_base_aruco
   T_base_aruco[:3, 3] = t_base_aruco


   return T_base_aruco


def rvec_tvec_to_matrix(rvec, tvec):
   R, _ = cv2.Rodrigues(rvec)
   T = np.eye(4)
   T[:3, :3] = R
   T[:3, 3] = tvec.flatten()
   return T


def em_values_to_t_matrix(x, y, z, azimuth, elevation, roll):
   r = R.from_euler('ZYX', [azimuth, elevation, roll], degrees=True)
   T = np.eye(4)
   T[:3, :3] = r.as_matrix()
   T[:3, 3] = [x, y, z]
   return T


def transformation(x, y, z, azimuth, elevation, roll, image_filename, input_dir, output_dir):
   image_file = os.path.join(input_dir, image_filename)


   # === Aruco Detection ===


   # ArUco marker size (meters)
   marker_length = 0.05


   # Define 3D coordinates of marker corners in marker frame
   half_len = marker_length / 2
   obj_points = np.array([
       [-half_len,  half_len, 0],  # top-left
       [ half_len,  half_len, 0],  # top-right
       [ half_len, -half_len, 0],  # bottom-right
       [-half_len, -half_len, 0]   # bottom-left
   ], dtype=np.float32)


   # Load image and detect markers
   image = cv2.imread(image_file)
   aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
   parameters = cv2.aruco.DetectorParameters()
   detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)


   corners, ids, _ = detector.detectMarkers(image)


   if ids is not None:
       for i, marker_corners in enumerate(corners):
           image_points = marker_corners[0].astype(np.float32)


           # SolvePnP for pose estimation
           success, rvec, tvec = cv2.solvePnP(obj_points, image_points,
                                           camera_matrix, dist_coeffs)


           if success:
               # print(f"\nMarker ID {ids[i][0]}")
               # print("Rotation vector (rvec):\n", rvec)
               # print("Translation vector (tvec):\n", tvec)


               # Draw marker and axis
               cv2.aruco.drawDetectedMarkers(image, corners)
               cv2.drawFrameAxes(image, camera_matrix, dist_coeffs, rvec, tvec, 0.03)
   else:
       print("No ArUco markers detected.")


   # === transformation matrices ===
   T_base_probe = em_values_to_t_matrix(x, y, z, azimuth, elevation, roll)
   T_base_aruco = get_T_base_aruco(marker_length)
   T_cam_aruco = rvec_tvec_to_matrix(rvec, tvec)


   # Final computation: Probe in camera frame
   T_cam_probe = T_cam_aruco @ np.linalg.inv(T_base_aruco) @ T_base_probe


   # print("T_base_aruco:")
   # print(T_base_aruco)
   # print("T_cam_aruco:")
   # print(T_cam_aruco)
   # print("T_base_probe:")
   # print(T_base_probe)
   # print("T_cam_probe:")
   # print(T_cam_probe)


   # Draw the tracker base frame on image to verify T_base_aruco transformation
   T_cam_base = T_cam_aruco @ np.linalg.inv(T_base_aruco)
   # convert to t and r vectors to draw frame axes
   R_cam_base = T_cam_base[:3, :3]
   t_cam_base = T_cam_base[:3, 3]
   rvec_base, _ = cv2.Rodrigues(R_cam_base)
   tvec_base = t_cam_base.reshape(3, 1)
   cv2.drawFrameAxes(image, camera_matrix, dist_coeffs, rvec_base, tvec_base, 0.03)


   # Draw the probe frame on image to verify T_cam_probe transformation
   # convert to t and r vectors to draw frame axes
   R_cam_probe = T_cam_probe[:3, :3]
   t_cam_probe = T_cam_probe[:3, 3]
   rvec_probe, _ = cv2.Rodrigues(R_cam_probe)
   tvec_probe = t_cam_probe.reshape(3, 1)
   cv2.drawFrameAxes(image, camera_matrix, dist_coeffs, rvec_probe, tvec_probe, 0.03)


   # Show the result
   # cv2.imshow("Pose Estimation", image)
   # cv2.waitKey(0)
   # cv2.destroyAllWindows()


   # save image
   output_file = "ground_truth_" + image_filename
   output_file = os.path.join(output_dir, output_file)
   cv2.imwrite(output_file, image)


   # save R and t
   pose_data = {
       'R': R_cam_probe.tolist(),
       't': t_cam_probe.tolist()
   }
   output_pose_file = "ground_truth" + image_filename.replace("png", "json")
   output_pose_file = os.path.join(output_dir, output_pose_file)
   with open(output_pose_file, 'w') as f:
       json.dump(pose_data, f)




with open('pose_with_image_matches.csv', newline='') as csvfile:
   reader = csv.DictReader(csvfile)
   i = 0
   for row in reader:
       x, y, z = float(row['x'])/1000, float(row['y'])/1000, float(row['z'])/1000
       azimuth, elevation, roll = float(row['azimuth']), float(row['elevation']), float(row['roll'])
       image_filename = row['image_filename']
       transformation(x, y, z, azimuth, elevation, roll, image_filename, "Color", "ground_truth")
