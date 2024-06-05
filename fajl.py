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
    


class Acquisition:
    def __init__(self, queue: Queue, stop: StopFlag):
        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        self.queue = queue
        self.stop = stop
        self.calibrationParams = np.zeros((3,2))

    def start(self):
        # Write calibration paramaters to a file
        # self.saveCalibrationParams()

        self.acquire_data()

    def parseSerialData(self):
        # x:0.0,y:0.0,z:0.0
        
        # Read data from serial

        data = self.ser.readline()
        if data == None or data == b'': 
            print("No data")
            return None

        # Split data into x, y and z
        data = data.split(b',')
        floats = np.array(list(map(lambda x: float(x.split(b':')[-1]), data)))
    
        print("floats: ", floats)
        return floats        

    def acquire_data(self):
        # Continuously acquire data
        while not self.stop.is_set():
            print('Acquiring data')
            floats = self.parseSerialData()
            if floats is None:
                continue

            # Calculate roll and pitch
            gravity = floats * self.calibrationParams[:,0] + self.calibrationParams[:,1]
            roll = np.arctan2(gravity[0], np.sqrt(pow(gravity[1], 2) + pow(gravity[2], 2)))
            pitch = np.arctan2(gravity[1], np.sqrt(pow(gravity[0], 2) + pow(gravity[2], 2)))

            # Put acquired data to the queue
            self.queue.put([roll, pitch])
    
    def calibrate(self, coordinate):
    

        print("Calibrating " + coordinate + "...")
        coordinate_num = 0
        if coordinate == 'Y':
            coordinate_num = 1
        elif coordinate == 'Z':
            coordinate_num = 2

        # Send signal to Arduino to start calibration
        msg = 'calibrate-' + coordinate + '\n'
        self.ser.write(msg.encode())
        dataPlus = np.array([])
        dataMinus = np.array([])
        
        
        # Read data from Arduino TWICE
        for dataArray in [dataPlus, dataMinus]:
            calibration_start_time = time.time()
            i = 0
            while time.time() - calibration_start_time < 3 and i < 10:
                print("Elapsed time: ", time.time() - calibration_start_time)
                print("Reading data...")
                data = self.parseSerialData()
                if data != None:
                    dataArray.append(data[coordinate_num])
                    i += 1


        # Calculate k and n
        k = 19.62 / (np.mean(dataPlus) - np.mean(dataMinus))
        n = -9.81 - k * np.mean(dataMinus)

        # Save k and n to calibrationParams
        self.calibrationParams[coordinate_num] = [k, n]
        
    def saveCalibrationParams(self):
        with open('./calibrationParams.txt', 'w') as f:
            for i in range(3):
                f.write(str('k = ' + self.calibrationParams[i][0]) + '  n = ' + str(self.calibrationParams[i][1]) + '\n')

    def wait_for_calibration(self):
        while not self.stop.is_set():
            print('Waiting for calibration')
            data = self.ser.readline()
            print(data)
            if data == b'CALIBRATION\n':
                return True
        return False



class App(QWidget):

    def __init__(self):
        super().__init__()
        # TODO: Initialize serial communication
        self.ser = serial.Serial('/dev/ttyACM0', 9600)
        self.title = 'Proba'
        self.left = 200

        self.queue = Queue()
        self.stop = StopFlag()
        self.acquisition = Acquisition(Queue(), StopFlag())
        
        self.acquisition_thread = threading.Thread(target=self.acquisition.start)

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
        self.calibration_thread = threading.Thread(target=self.acquisition.calibrate, args=(coordinate,))
        self.calibration_thread.start()
        self.calibration_thread.join()

    
    def endCalibration(self):
        # Remove X, Y, Z and End Calibration buttons
        self.buttonX.deleteLater()
        self.buttonY.deleteLater()
        self.buttonZ.deleteLater()
        self.buttonEndCalibration.deleteLater()

        self.savePilotNameAndParams()
        
    def savePilotNameAndParams(self):
        # Save the name of the pilot to a file
        with open('./calibrationParams.txt', 'w') as f:
            f.write(self.text_input.text() + ' ' + '\n')
        self.acquisition.saveCalibrationParams()

    def startFlight(self):
        print("LETIM WEEEE")

    def off(self):
        print("bye bye...")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
