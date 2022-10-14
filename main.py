#!/usr/bin/python
import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api

# Initialize the depth device
openni2.initialize()
dev = openni2.Device.open_any()

# Start the RGB stream
rgb_stream = dev.create_color_stream()
rgb_stream.start()
rgb_stream.set_video_mode(c_api.OniVideoMode(pixelFormat=c_api.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888, resolutionX=640, resolutionY=480, fps=30))


# Start the depth stream
depth_stream = dev.create_depth_stream()
depth_stream.start()
depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM, resolutionX = 640, resolutionY = 480, fps = 30))


# Function to return some pixel information when the OpenCV window is clicked
rect = None
selecting = False

def point_and_shoot(event, x, y, flags, param):
    global rect, selecting
    if selecting:
        rect = (rect[0], (x,y))
    if event == cv2.EVENT_LBUTTONDOWN:
        rect = ((x, y), (x, y))
        selecting = True
    elif event == cv2.EVENT_LBUTTONUP and selecting:
        if abs(rect[0][0] - rect[1][0]) * abs(rect[0][1] - rect[1][1]) <= 1:
            rect = None
        selecting = False

# Initial OpenCV Window Functions
cv2.namedWindow("Depth Image")
cv2.setMouseCallback("Depth Image", point_and_shoot)

# Loop
while True:
    # Get the RGB frame
    bgr = np.fromstring(rgb_stream.read_frame().get_buffer_as_uint8(), dtype=np.uint8).reshape(480, 640, 3)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    # Display the RGB frame
    cv2.imshow("RGB Image", rgb)

    # Grab a new depth frame
    frame = depth_stream.read_frame()
    frame_data = frame.get_buffer_as_uint16()
    # Put the depth frame into a numpy array and reshape it
    depth: np.ndarray = np.frombuffer(frame_data, dtype=np.uint16)
    depth.shape = (480, 640)

    depth_visualization_frame = cv2.normalize(depth, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
    depth_visualization_frame = cv2.equalizeHist(depth_visualization_frame)
    depth_visualization_frame = cv2.applyColorMap(depth_visualization_frame, cv2.COLORMAP_HOT)

    if selecting:
        cv2.rectangle(depth_visualization_frame, rect[0], rect[1], (255, 255, 255), 1)
    elif rect is not None:
        cv2.rectangle(depth_visualization_frame, rect[0], rect[1], (0, 255, 0), 1)
        avg_depth = np.mean(depth[rect[0][1]:rect[1][1], rect[0][0]:rect[1][0]])
        print(f"Depth: {avg_depth} mm")

    # Display the reshaped depth frame using OpenCV
    cv2.imshow("Depth Image", depth_visualization_frame)
    key = cv2.waitKey(1) & 0xFF

    # If the 'c' key is pressed, break the while loop
    if key == ord("c"):
        break

# Close all windows and unload the depth device
openni2.unload()
cv2.destroyAllWindows()