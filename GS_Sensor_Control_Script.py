"""
FPV Display: https://stackoverflow.com/questions/44404349/pyqt-showing-video-stream-from-opencv
https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
Sample Python/Pygame Programs
Simpson College Computer Science
http://programarcadegames.com/
http://simpson.edu/computer-science/
http://programarcadegames.com/python_examples/show_file.php?file=joystick_calls.py

Name: TWCS Throttle //throttle--------------------------------------------------------

Axies:
Axis[0]= 	left-right (index finger joystick)	Left= -1		Right= 1
Axis[1]= 	up-down (index finger joystick)		Up= -1		    Down= 1
Axis[2]= 	throttle				            Full= -1		None= 1
Axis[3]= 	paddles					            Left= -1		Right= 1
?= 	        pinky slider				        Forward= ?	    Backward = ?

Butttons (1 = on, 0 = off):
Button[0]= 	thumb button
Button[1]= 	pinky button
Button[2]= 	ring button
Button[3]= 	middle up toggle button
Button[4]= 	middle down toggle button
Button[5]=  index finger joystick down button
Button[6]=  middle hat up button
Button[7]=  middle hat right button
Button[8]=  middle hat down button
Button[9]=  middle hat left button
Button[10]= bottom hat up button
Button[11]= bottom hat right button
Button[12]= bottom hat down button
Button[13]= bottom hat left button

T.16000M //joystick--------------------------------------------------------

Axies:
Axis[0]= 	left-right				            Left= -1	Right= 1
Axis[1]= 	up-down 				            Up= 1   	Down= -1
Axis[2]= 	throttle slider				        Forward= -1 Backward = 1
Axis[3]= 	twist					            Left= -1	Right= 1

Butttons (128d = on, 0d = off):
Button[0]= 	fire button
Button[1]= 	middle stick button
Button[2]= 	left stick button
Button[3]= 	right stick button
Button[4]= 	position 1 button
Button[5]= 	position 2 button
Button[6]= 	position 3 button
Button[7]= 	position 9 button
Button[8]= 	position 8 button
Button[9]= 	position 7 button
Button[10]= position 6 button
Button[11]= position 5 button
Button[12]= position 4 button
Button[13]= position 10 button
Button[14]= position 11 button
Button[15]= position 12 button

T-Rudder //pedals----------------------------------------------------------

Axies:
Axis[0]= 	right brake				            Down= -1	Up= 1
Axis[1]= 	left brake 				            Down= -1	Up= 1
Axis[2]= 	rudder	 				            Nose L= -1	Nose R= 1
"""

import traceback
import sys
from datetime import datetime
import glob
import serial
import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QDialogButtonBox
from GS_GUI import Ui_GroundStationSensorControl


# lets the GUI know which camera to use - camera = 0 is built in webcam, camera = 1 is FPV
camera = 1

# serial object to connect to ground station
ser = serial.Serial()

# determines if GS port is open/connected or not
portOpen = False

# data logging file name
data_logger_name = (r"testFlight_"
                    + str(datetime.now().isoformat())[:19].replace("-", "_").replace(":", "_").replace("T", "_")
                    + r".txt")


def serial_ports():
    """
    Lists serial port names

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)

        except (OSError, serial.SerialException):
            pass

    return result


class CVThread(QThread):
    change_pixel_map = pyqtSignal(QImage)

    def run(self):
        try:
            # get a new frame from the camera
            cap = cv2.VideoCapture(camera)

            # infinite loop
            while True:
                ret, frame = cap.read()
                if ret:
                    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    convert_to_qt_format = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                                                  QImage.Format_RGB888)
                    p = convert_to_qt_format.scaled(640 * 2, 480 * 2, Qt.KeepAspectRatio)
                    self.changePixmap.emit(p)

        except Exception:
            print(traceback.format_exc())


class RadioThread(QThread):
    # create a pySignal to tell GUI when new data has arrived
    update_values = pyqtSignal(str)

    def run(self):
        # run forever
        while True:
            try:
                # open and append telemetry to logging .txt
                with open(data_logger_name, 'a') as f:
                    # run forever
                    while True:
                        # test if serial port is open
                        if ser.is_open:
                            # get the data
                            data = str(ser.readline())
                            data = data.replace("b'", "")
                            data = data.replace("'", "")
                            data = data.replace(r"\r\n", "\n")

                            # write the data to the data logging file
                            f.write(data)

                            if data != '\n':
                                # optional debugging print
                                self.updateVals.emit(data)

            except:
                print(traceback.format_exc())


class AppWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_GroundStationSensorControl()
        self.ui.setupUi(self)
        self.show()


def main():
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
