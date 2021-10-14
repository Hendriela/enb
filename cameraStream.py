import io
import picamera  # Camera

#### THIS IS IMPORTANT FOR LIFE STREAMING ####
import logging
import socketserver
from threading import Condition
from http import server

#### THIS IS IMPORTANT FOR IMAGE PROCESSING ####
import numpy as np
import cv2

### other imports
from datetime import datetime

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

det = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
bordersize = 10

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
    face_i = 0
    second = datetime.now()

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

                        if frame is None:
                            print("!!!!!!!!!!!!!!!")

                        ###############
                        ## HERE CAN GO ALL IMAGE PROCESSING
                        ###############
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
                        rects = det.detectMultiScale(gray, 
                            scaleFactor=1.1, 
                            minNeighbors=5, 
                            minSize=(150, 150), # adjust to your image size, maybe smaller, maybe larger?
                            flags=cv2.CASCADE_SCALE_IMAGE)

                        for (x, y, w, h) in rects:
                            # x: x location
                            # y: y location
                            # w: width of the rectangle 
                            # h: height of the rectangle
                            # Remember, order in images: [y, x, channel]
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), bordersize)

                        current_second = datetime.now()
                        if (current_second - self.second).seconds >= 3:
                            for (x,y,w,h) in rects:
                                if self.face_i > 99:
                                    break
                                
                                crop = frame[y+bordersize:y+h-bordersize, x+bordersize:x+w-bordersize]
                                cropscale = cv2.resize(crop, (128,128))
                                blurry = cv2.Laplacian(cropscale, cv2.CV_64F).var() < 250
                                if not blurry:
                                    #print("BLURRY")
                                    #cv2.imwrite("../faces_blurry/face_%03i.png" % self.face_i, cropscale)
                                #else:
                                    cv2.imwrite("../faces/face_%03i.png" % self.face_i, cropscale)
                                    self.second = datetime.now()
                                    self.face_i += 1
                                    print("saved face %i" % (self.face_i-1))
                                

                        cv2.putText(frame, "%i" % (self.face_i-1), (100,100), cv2.FONT_HERSHEY_SIMPLEX, 2, 255)
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
    camera.awb_mode= "auto"
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)  # port 8000
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()