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
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton
from PyQt5.uic import loadUi




# lets the GUI know which camera to use - camera = 0 is built in webcam, camera = 1 is FPV
camera = 0

# variables to control GUI initial size and placement on screen
winLeft = 400
winTop = 300
winWidth = 1900
winHeight = 900

# serial object to connect to ground station
ser = serial.Serial()

# determines if GS port is open/connected or not
portOpen = False

# datalogging file name
dataloggerName = r"testFlight_" + str(datetime.now().isoformat())[:19].replace("-", "_").replace(":", "_").replace("T", "_") + r".txt"




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
    changePixmap = pyqtSignal(QImage)

    def run(self):
        try:
            # get a new frame from the camera
            cap = cv2.VideoCapture(camera)

            # infinite loop
            while True:
                ret, frame = cap.read()
                if ret:
                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    convertToQtFormat = QImage(rgbImage.data, rgbImage.shape[1], rgbImage.shape[0],
                                               QImage.Format_RGB888)
                    p = convertToQtFormat.scaled(640 * 2, 480 * 2, Qt.KeepAspectRatio)
                    self.changePixmap.emit(p)

        except Exception:
            print(traceback.format_exc())




class radioThread(QThread):
    # create a pySignal to tell GUI when new data has arrived
    updateVals = pyqtSignal(str)

    def run(self):
        # run forever
        while(True):
            try:
                # open and append telemetry to logging .txt
                with open(dataloggerName, 'a') as f:
                    # run forever
                    while (True):
                        # test if serial port is open
                        if (ser.is_open):
                            # get the data
                            data = str(ser.readline())
                            data = data.replace("b'", "")
                            data = data.replace("'", "")
                            data = data.replace(r"\r\n", "\n")

                            # write the data to the datalogging file
                            f.write(data)

                            if(data != '\n'):
                                # optinal debugging print
                                self.updateVals.emit(data)

            except Exception:
                print(traceback.format_exc())


# noinspection SpellCheckingInspection
class App(QDialog):
    def __init__(self):
        # initialize the GUI
        super().__init__()
        loadUi('GS_GUI.ui', self)

        #echo AT commands on by default
        self.echo = True

        #set GUI window geometry
        self.left = winLeft
        self.top = winTop
        self.width = winWidth
        self.height = winHeight

        #find all available serial ports
        self.refreshPorts()

        #connect signals
        self.Refresh_Ports.clicked.connect(self.refreshPorts)
        self.Send_Commands.clicked.connect(self.processAT)
        self.Connect_Radio.clicked.connect(self.connectPort)

        #initialize threads and show GUI
        self.initUI()




    @pyqtSlot(QImage)
    def setImage(self, image):
        self.FPV_Feed.setPixmap(QPixmap.fromImage(image))




    def initUI(self):
        # set window shape and size
        self.setGeometry(self.left, self.top, self.width, self.height)

        # do video processing on a separate thread (parallel processing for speed)
        vidThead = CVThread(self)
        vidThead.changePixmap.connect(self.setImage)
        vidThead.start()

        # take care of serial port/data handling
        dataThread = radioThread(self)
        dataThread.updateVals.connect(self.updateTelem)
        dataThread.start()

        # display the GUI
        self.show()




    def updateTelem(self, data):
        # get rid of newline chars
        data.replace("\n", "")

        # get the name
        dataName = data.split(" ")[0]

        # get the numerical data
        dataValue = data.split(" ")[1]

        if(dataName == "Alt:"):
            self.Altitude.display(float(dataValue))
        elif(dataName == "Roll:"):
            pass
        elif (dataName == "Pitch:"):
            pass
        elif (dataName == "Vel:"):
            self.Airspeed.display(float(dataValue))
        elif (dataName == "Lat:"):
            self.Latitude.display(float(dataValue))
        elif (dataName == "Lon:"):
            self.Longitude.display(float(dataValue))
        elif (dataName == "UTC_y:"):
            pass
        elif (dataName == "UTC_M:"):
            pass
        elif (dataName == "UTC_d:"):
            pass
        elif (dataName == "UTC_h:"):
            pass
        elif (dataName == "UTC_m:"):
            pass
        elif (dataName == "UTC_s:"):
            pass
        elif (dataName == "SOG:"):
            pass
        elif (dataName == "COG:"):
            pass




    @pyqtSlot()
    def processAT(self):
        """
        Type "Echo on" or "Echo Off" to toggle whether or not the typed commands show up in the output
        """
        if (self.UAV_AT_Command_Line.text().lower().split(" ")[0] == "echo" and
                self.UAV_AT_Command_Line.text().lower().split(" ")[1] == "off"):
            self.echo = False
        elif (self.UAV_AT_Command_Line.text().lower().split(" ")[0] == "echo" and
              self.UAV_AT_Command_Line.text().lower().split(" ")[1] == "on"):
            self.echo = False

        commands = "Echo: " + self.UAV_AT_Command_Line.text() + "\n";

        #test if GS is connected
        if(portOpen):
            if(self.echo):
                #echo command
                self.Command_Output.append(commands)
        else:
            #print error
            self.Command_Output.append("GS NOT CONNECTED")

        #clear user input
        self.UAV_AT_Command_Line.clear()




    def refreshPorts(self):
        try:
            portList = []
            ports = serial_ports()

            #only execute if you don't already have a connection to the GS
            if(not ser.is_open):
                if (len(ports) > 0):
                    for port in range(len(ports)):
                        portList.append(self.tr(str(ports[port])))

                self.COM_Select.clear()

                if (len(ports) > 0):
                    self.COM_Select.addItems(portList)
                else:
                    self.COM_Select.addItem("None Available")
        except Exception:
            print(traceback.format_exc())




    def connectPort(self):
        port = self.COM_Select.currentText()

        if (not (port == "None Available")):
            try:
                if(ser.port != str(port) or not ser.is_open):
                    ser.baudrate = 115200
                    ser.port = str(port)
                    ser.open()
                    self.Command_Output.setText("Connected to radio on %s\n" % port)

            except:
                self.Command_Output.append("ERROR - CANNOT CONNECT TO COM PORT\n")
        else:
            self.Command_Output.append("No Radio COM Port Available - Check Device Manager and/or Wiring\n")




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
