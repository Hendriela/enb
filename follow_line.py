import curses
import serial
import time
import picamera
import io
from threading import Condition
import numpy as np
import cv2

# Color of the line that the robot should follow
COLOR = (255, 0, 0)

# Configure serial port
ser = serial.Serial()
ser.baudrate = 19200
ser.port = '/dev/ttyUSB0'

# Open serial port
ser.open()
time.sleep(2.00)  # Wait for connection before sending any data

# List stores feedback from the Arduino
arduino = []


class StreamingOutput(object):
    """Buffer object where the camera writes frames into and the script can read them out again."""

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


# Open the camera and stream a low-res image (width 640, height 480 px)
with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    camera.vflip = True  # Flips image vertically, depends on your camera mounting
    camera.awb_mode = "auto"
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')

try:
    while True:
        with output.condition:
            output.condition.wait()
            # Read current frame from buffer
            frame = output.frame
            # Decode from bytes to numpy array
            frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8),
                                 cv2.IMREAD_COLOR)

            print(np.mean(frame))

            # # char is the unicode integer of the key, so transform it back into the string character before formatting
            # var_char = '{}0;'.format(chr(char))
            # ser.write(var_char.encode('utf-8'))  # Arduino expects a byte instead of a string, encode before sending it
            # time.sleep(0.05)
            # arduino.append(ser.readline())
            # arduino.append(ser.readline())

# Happens when the script is stopped, e.g. through KeyboardInterrupt
finally:
    # Send "t" for terminate to halt the robot
    ser.write(b't0;')
    arduino.append(ser.readline())
    arduino.append(ser.readline())
    # Close serial port
    ser.close()
