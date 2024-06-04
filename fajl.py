from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys

import time
# import QSizePolicy
from queue import Queue
import serial # type: ignore
import threading
import numpy as np # type: ignore

class StopFlag:
    def __init__(self):
        self.flag = False
    
    def set(self):
        self.flag = True
    
    def is_set(self):
        return self.flag
    

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial('/dev/ttyACM0', 9600)
        self.title = 'Proba'
        self.left = 200

        self.calibrationParams = {
            'X': [0, 0],
            'Y': [0, 0],
            'Z': [0, 0]
        }

        self.top = 200
        self.width = 730
        self.height = 520
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Calibration button
        self.calibrateButton = QPushButton('Calibrate', self)
        self.calibrateButton.resize(100, 50)
        self.calibrateButton.move(10, 10)
        self.calibrateButton.clicked.connect(self.calibrateInterface)

        # Start Flight button
        self.startFlightButton = QPushButton('Start Flight', self)
        self.startFlightButton.resize(100, 50)
        self.startFlightButton.move(10, 70)
        self.startFlightButton.clicked.connect(self.startFlight)

        # OFF button
        self.offButton = QPushButton('OFF', self)
        self.offButton.resize(100, 50)
        self.offButton.move(10, 130)
        self.offButton.clicked.connect(self.off)

        # Add text input field
        self.text_input = QLineEdit('1', self)
        self.text_input.resize(100, 50)
        self.text_input.move(10, 190)

        self.show()

    def calibrateInterface(self):
        # Calibrate X button
        self.buttonX = QPushButton('X', self)
        self.buttonX.resize(100, 50)
        self.buttonX.move(10, 250)
        self.buttonX.clicked.connect(self.calibrateX)
        self.buttonX.show()
        
        # Calibrate Y button
        self.buttonY = QPushButton('Y', self)
        self.buttonY.resize(100, 50)
        self.buttonY.move(10, 310)
        self.buttonY.clicked.connect(self.calibrateY)
        self.buttonY.show()

        # Calibrate Z button
        self.buttonZ = QPushButton('Z', self)
        self.buttonZ.resize(100, 50)
        self.buttonZ.move(10, 370)
        self.buttonZ.clicked.connect(self.calibrateZ)
        self.buttonZ.show()

        # End Calibration button
        self.buttonEndCalibration = QPushButton('End Calibration', self)
        self.buttonEndCalibration.resize(100, 50)
        self.buttonEndCalibration.move(10, 430)
        self.buttonEndCalibration.clicked.connect(self.endCalibration)
        self.buttonEndCalibration.show()
        self.show()

    def calibrateX(self):
        self.calibrateCoordinate("X")

    def calibrateY(self):
        self.calibrateCoordinate("Y")
    
    def calibrateZ(self):
        self.calibrateCoordinate("Z")        

    def calibrateCoordinate(self, coordinate):
        print("Calibrating " + coordinate + "...")
        # TODO: Implement calibration

        # Send signal to Arduino to start calibration
        self.ser.write(('calibrate-' + coordinate + '\n').encode())
        dataArray = []
        
        # Read data from Arduino TWICE
        for merenje in range(2):
            dataArray.append(np.array([]))
            start_time = time.time()
            i = 0
            while time.time() - start_time < 3 or i < 50:
                data = self.ser.readline()
                data = data.decode('utf-8')
                dataArray[merenje].append(float(data))
                i += 1

            # Calculate mean value of the data
            dataArray[merenje] = np.mean(dataArray)

        # Calculate k and n
        k = 19.62 / (dataArray[0] - dataArray[1])
        n = -9.81 - k * dataArray[1]

        # Save k and n to calibrationParams
        self.calibrationParams[coordinate] = [k, n]

    
    def endCalibration(self):
        # Remove X, Y, Z and End Calibration buttons
        self.buttonX.deleteLater()
        self.buttonY.deleteLater()
        self.buttonZ.deleteLater()
        self.buttonEndCalibration.deleteLater()

        # TODO: Save the name of the pilot and calibration paramaters to a file

    def startFlight(self):
        print("LETIM")

    def off(self):
        print("bye bye...")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
