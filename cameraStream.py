import io
import picamera  # Camera
import os

#### THIS IS IMPORTANT FOR LIFE STREAMING ####
import logging
import socketserver
from threading import Condition
from http import server

#### THIS IS IMPORTANT FOR IMAGE PROCESSING ####
import numpy as np
import cv2

### Imports for pose detector
from pycoral.adapters import common
from pycoral.utils.edgetpu import make_interpreter

### other imports
from datetime import datetime
from datetime import timedelta
from copy import deepcopy

PAGE = """\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480"/>
</body>
</html>
"""

# Initialize face detector
det = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

# Initialize pose detector
interpreter = make_interpreter('coral/movenet_single_pose_thunder_ptq_edgetpu.tflite')
interpreter.allocate_tensors()

# Set constants
BORDER = 10             # Border size [px] of detected faces on stream 
_NUM_KEYPOINTS = 17     # Number of detection points for pose detection

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    frame_i = 0
    # Initialize variable that stores time of last saved image (3 seconds ago to immediately start saving faces
    second = datetime.now() - timedelta(seconds=3)

    # Look up the currently highest file name number and use it as the first file number to avoid overwriting
    fnames = os.listdir("../faces")
    face_i = np.max(np.array([int(f[5:8]) for f in fnames]))+1

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame

                        ### The image is encoded in bytes,
                        ### needs to be converted to e.g. numpy array
                        frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8),
                                             cv2.IMREAD_COLOR)

                        ###############
                        ## HERE CAN GO ALL IMAGE PROCESSING
                        ###############

                        ###############
                        ## POSE DETECTION
                        ###############

                        # This resizes the RGB image
                        resized_img = cv2.resize(frame, common.input_size(interpreter))
                        # Send resized image to Coral
                        common.set_input(interpreter, resized_img)

                        # Do the job
                        interpreter.invoke()

                        # Get the pose
                        pose = common.output_tensor(interpreter, 0).copy().reshape(_NUM_KEYPOINTS, 3)

                        ###############
                        ## FACE DETECTION
                        ###############

                        # Convert frame into greyscale for image processing
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # Use face detector to find all faces in the current frame
                        # Output rects will be a list of tuples with x/y coordinates of the top-left corner of the
                        # detected face rectangle and the width and height of the rectangle
                        rects = det.detectMultiScale(gray, 
                            scaleFactor=1.1,        # How much the image should be scaled down per processing layer
                            minNeighbors=8,         # Detection threshold (higher -> more certain faces are detected)
                            minSize=(170, 170),     # Minimum size of a detected face, depends on face-camera distance
                            flags=cv2.CASCADE_SCALE_IMAGE)

                        ### Save detected faces
                        # Only start the saving process if the last face was saved more than 3 seconds ago
                        current_second = datetime.now()
                        if (current_second - self.second).seconds >= 3:

                            for (x,y,w,h) in rects:
                                if self.face_i > 999:       # Stop at 999 face images to avoid overwriting
                                    break

                                # Crop out face from frame and resize it to a common size (128x128)
                                crop = frame[y + BORDER:y + h - BORDER, x + BORDER:x + w - BORDER]
                                cropscale = cv2.resize(crop, (128,128))

                                # Compute variance of Laplacian convolution as measure of blurriness, with threshold
                                blurry = cv2.Laplacian(cropscale, cv2.CV_64F).var() < 180
                                if not blurry:
                                    #print("BLURRY")
                                    #cv2.imwrite("../faces_blurry/face_%03i.png" % self.face_i, cropscale)
                                #else:

                                    # If variance is above threshold, save face with current face counter in filename
                                    cv2.imwrite("../faces/face_%03i.png" % self.face_i, cropscale)
                                    self.second = datetime.now()   # Remember time of saving to avoid saving too quickly
                                    self.face_i += 1               # Increment face counter
                                    print("saved face %i" % (self.face_i-1))
                        
                        ##################################################
                        ### DRAW DETECTIONS ON THE FRAME BEFORE STREAMING
                        ##################################################

                        ### DRAW RECTANGLE AROUND FACES
                        # Go through all detected faces in the frame and draw a rectangle around it
                        for (x, y, w, h) in rects:
                            # x: x location
                            # y: y location
                            # w: width of the rectangle 
                            # h: height of the rectangle
                            # Remember, order in images: [y, x, channel]
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), BORDER)

                        # Put face counter on top of the streamed frame
                        cv2.putText(frame, "%i" % (self.face_i-1), (100,100), cv2.FONT_HERSHEY_SIMPLEX, 2, 255)


                        ### DRAW DOTS ON POSE KEYPOINTS
                        height, width, ch = frame.shape

                        # Draw the pose onto the image using blue dots
                        for i in range(0, _NUM_KEYPOINTS):
                            cv2.circle(frame,
                                    [int(pose[i][1] * width), int(pose[i][0] * height)],
                                    5,  # radius
                                    (255, 0, 0),  # color in RGB
                                    -1)  # fill the circle

                        ### and now we convert it back to JPEG to stream it
                        _, frame = cv2.imencode('.JPEG', frame)

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# Open the camera and stream a low-res image (width 640, height 480 px)
with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    camera.vflip = True  # Flips image vertically, depends on your camera mounting
    camera.awb_mode = "auto"
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)  # port 8000
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
