import curses
import serial
import time

# Configure serial port
ser = serial.Serial()
ser.baudrate = 19200
ser.port = '/dev/ttyUSB0'

# Open serial port
ser.open()
time.sleep(2.00) # Wait for connection before sending any data

# get the curses screen window
screen = curses.initscr()

# turn off input echoing
curses.noecho()

# respond to keys immediately (don't wait for enter)
curses.cbreak()

# map arrow keys to special values
screen.keypad(True)

arduino = []

try:
    while True:
        char = screen.getch()
        if char == ord('x'):
            break
        elif char == ord(' '):
            # Send a character
            ser.write(b't0;')
            time.sleep(0.05)
            arduino.append(ser.readline())
            arduino.append(ser.readline())
        else:
            # Send a character
            ser.write(b'{}0;'.format(char))
            time.sleep(0.05)
            arduino.append(ser.readline())
            arduino.append(ser.readline())
finally:
    # shut down
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()
    # Close serial port
    #s = ser.read(1)
    #print(s)
    print(arduino)
    ser.close()


