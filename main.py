#!/usr/bin/python
import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api
import open3d as o3d

# Initialize the depth device
openni2.initialize()
dev = openni2.Device.open_any()
info = dev.get_sensor_info(openni2.SENSOR_DEPTH)
print(info)

width = 640
height = 480

# Start the RGB stream
rgb_stream = dev.create_color_stream()
rgb_stream.start()
rgb_stream.set_video_mode(c_api.OniVideoMode(pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888, resolutionX=width, resolutionY=height, fps=30))

# Start the depth stream
depth_stream = dev.create_depth_stream()
depth_stream.start()
depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM, resolutionX=width, resolutionY=height, fps = 30))

# Intrinsics (https://3dclub.orbbec3d.com/t/access-intrinsic-camera-parameters/2784)
hfov = rgb_stream.get_horizontal_fov()
vfov = rgb_stream.get_vertical_fov()

intrinsics = o3d.camera.PinholeCameraIntrinsic(
    width=width,
    height=height,
    fx = width / (2 * np.tan(hfov / 2)),
    fy = height / (2 * np.tan(vfov / 2)),
    cx = width / 2,
    cy = height / 2
)

point_cloud = o3d.geometry.PointCloud()
point_cloud_window = o3d.visualization.Visualizer()
point_cloud_window.create_window("Point Cloud")
point_cloud_window.add_geometry(point_cloud)
origin = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1, origin=[0, 0, 0])
point_cloud_window.add_geometry(origin)
point_cloud_window.get_view_control().set_constant_z_far(15)

while True:
    key = cv2.waitKey(1)
    # Get the RGB frame
    bgr = np.fromstring(rgb_stream.read_frame().get_buffer_as_uint8(), dtype=np.uint8).reshape(height, width, 3)
    rgb_frame = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Grab a new depth frame
    frame = depth_stream.read_frame()
    frame_data = frame.get_buffer_as_uint16()
    # Put the depth frame into a numpy array and reshape it
    depth: np.ndarray = np.frombuffer(frame_data, dtype=np.uint16).reshape(height, width)

    depth_visualization_frame = cv2.normalize(depth, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
    depth_visualization_frame = cv2.equalizeHist(depth_visualization_frame)
    depth_visualization_frame = cv2.applyColorMap(depth_visualization_frame, cv2.COLORMAP_HOT)

    # create a point cloud
    depth_o3d = o3d.geometry.Image(depth)
    color_o3d = o3d.geometry.Image(cv2.cvtColor(depth_visualization_frame, cv2.COLOR_BGR2RGB))
    color_o3d = o3d.geometry.Image(bgr)
    rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(color_o3d, depth_o3d, convert_rgb_to_intensity=False)
    pcl = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsics)
    # Flip it, otherwise the pointcloud will be upside down
    pcl.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

    point_cloud.points = pcl.points
    point_cloud.colors = pcl.colors

    # Visualize the point cloud
    point_cloud_window.update_geometry(point_cloud)
    point_cloud_window.poll_events()
    point_cloud_window.update_renderer()

    # Display the reshaped depth frame using OpenCV
    cv2.imshow("Depth Image", depth_visualization_frame)
    cv2.imshow("RGB Image", rgb_frame)

    # If the 'c' key is pressed, break the while loop
    if key == ord("q"):
        break

# Close all windows and unload the depth device
openni2.unload()
cv2.destroyAllWindows()