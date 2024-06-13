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
    
    def isSet(self):
        return self.flag
    


class Acquisition:
    def __init__(self, queue: Queue, stop: StopFlag):
        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        self.queue = queue
        self.stop = stop
        self.calibrationParams = np.zeros((3,2))
        self.isCalibrated = [False, False, False]

    def parseSerialData(self):
        # x:0.0,y:0.0,z:0.0
        
        # Read data from serial
        data = self.ser.readline()
        if data == None or data == b'': 
            #print("No data")
            return [None, None, None]

        # Split data into x, y and z
        data = data.split(b',')
        floats = np.array(list(map(lambda x: float(x.split(b':')[-1]), data)))
    
        return floats        

    def acquireData(self):
        commandMsg = 'start\n'
        self.ser.write(commandMsg.encode())

        # Continuously acquire data
        while not self.stop.isSet():
            floats = self.parseSerialData()
            print(floats)
            # Check if any of the in the list data are None
            if any([x is None for x in floats]):
                continue

            # Calculate roll and pitch
            gravity = floats * self.calibrationParams[:,0] + self.calibrationParams[:,1]
            roll = np.arctan2(gravity[0], np.sqrt(pow(gravity[1], 2) + pow(gravity[2], 2)))
            pitch = np.arctan2(gravity[1], np.sqrt(pow(gravity[0], 2) + pow(gravity[2], 2)))

            print("Roll: ", roll, "   Pitch: ", pitch)

            dataSerialSend = pitch / (np.pi / 2) * 255
            if dataSerialSend > 255: dataSerialSend = 255
            if dataSerialSend < -255: dataSerialSend = -255

            dataSerialSend = int(dataSerialSend)
            print("Sent on serial: ", dataSerialSend)
            dataSerialSend = str(dataSerialSend) + '\n'

            self.ser.write(dataSerialSend.encode())

            # Put acquired data to the queue
            self.queue.put([roll, pitch])

        self.ser.write("kraj letenja\n".encode())
            
    def calibrate(self, coordinate):
    
        print("Calibrating " + coordinate + "...")
        coordinateNum = 0
        if coordinate == 'Y':
            coordinateNum = 1
        elif coordinate == 'Z':
            coordinateNum = 2

        # Send signal to Arduino to start calibration
        commandMsg = 'calibrate' + coordinate + '\n'
        self.ser.write(commandMsg.encode())
        dataPlus = []
        dataMinus = []
        
        iteration = 0
        # Read data from Arduino TWICE
        for dataArray in [dataPlus, dataMinus]:

            calibrationStartTime = time.time()
            i = 0
            while i < 5:

                # If the OFF button is pressed break
                # if self.stop.isSet():
                #     return

                print("Elapsed time: ", time.time() - calibrationStartTime)
                print("Reading data...")
                if (time.time() - calibrationStartTime >= 18):
                    print("Time is up!")
                    break
                data = self.parseSerialData()
                # Check if any of the in the list data are None
                if not any([x is None for x in data]):
                    dataArray.append(data[coordinateNum])
                    print(dataArray)
                    i += 1
                    if (i == 5):
                        self.isCalibrated[coordinateNum] = True

            time.sleep(1)
            if iteration == 0:
                self.ser.write(commandMsg.encode())
                iteration += 1

        # Calculate k and n
        dataPlus = np.array(dataPlus)
        dataMinus = np.array(dataMinus)
        k = 19.62 / (np.mean(dataPlus) - np.mean(dataMinus))
        n = -9.81 - k * np.mean(dataMinus)

        # Save k and n to calibrationParams
        self.calibrationParams[coordinateNum] = [k, n]
        
    def saveCalibrationParams(self):

        with open('./calibrationParams.txt', 'a') as f:
            for i in range(3):
                f.write(str('k = ' + str(self.calibrationParams[i][0])) + 
                        '  n = ' + str(self.calibrationParams[i][1]) + ':\n')

    def waitForCalibration(self):
        while not self.stop.isSet():
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
        self.acquisition = Acquisition(self.queue, self.stop)

        self.dataPitch = []
        self.dataRoll = []

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

        # Stop Flight button
        self.offButton = QPushButton('Stop Flight', self)
        self.offButton.resize(100, 50)
        self.offButton.move(10, 130)
        self.offButton.clicked.connect(self.stopFlight)

        # OFF button
        self.offButton = QPushButton('OFF', self)
        self.offButton.resize(100, 50)
        self.offButton.move(10, 490)
        self.offButton.clicked.connect(self.off)


        # Add text input field
        self.textInput = QLineEdit('1', self)
        self.textInput.resize(100, 50)
        self.textInput.move(10, 190)


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
        self.calibrationThread = threading.Thread(target=self.acquisition.calibrate, args=(coordinate,))
        self.calibrationThread.start()
        self.calibrationThread.join()
    
    def endCalibration(self):
        # Check if all axies were calibrated
        if not all(self.acquisition.isCalibrated):
            print("Not all axies were calibrated!")
            return

        # Remove X, Y, Z and End Calibration buttons
        self.buttonX.deleteLater()
        self.buttonY.deleteLater()
        self.buttonZ.deleteLater()
        self.buttonEndCalibration.deleteLater()

        if all(self.acquisition.isCalibrated):
            self.savePilotNameAndParams()   
        
    def savePilotNameAndParams(self):
        # Save the name of the pilot to a file
        with open('./calibrationParams.txt', 'a') as f:
            f.write(self.textInput.text() + ' ' + '\n')
        self.acquisition.saveCalibrationParams()

    def startFlight(self):
        # Start acquisition
        print("Starting flight...")
        self.calibrationThread = threading.Thread(target=self.acquisition.acquireData)
        self.calibrationThread.start()     

    def stopFlight(self):
        # Add plot button to the interface
        print("Stopping...")
        self.stop.set()
        self.buttonX = QPushButton('Plot Data', self)
        self.buttonX.resize(100, 50)
        self.buttonX.move(10, 250)
        self.buttonX.clicked.connect(self.plotData)
        self.buttonX.show()

    def plotData(self):
        # Acquire data fro mthe queue
        while not self.queue.empty():
            data = self.queue.get()
            self.dataRoll.append(data[0])
            self.dataPitch.append(data[1])
        
        self.dataPitch = np.array(self.dataPitch)
        self.dataRoll = np.array(self.dataRoll)

        # Plot data as a new element on the interface
        fig = plt.figure()
        ax = fig.add_subplot(111)
        plotData = np.vstack((self.dataRoll, self.dataPitch))
        ax.plot(plotData.T)
        ax.set_title('Roll and Pitch')
        ax.legend(['Roll', 'Pitch'])
        plt.show()

    def off(self):
        # Close serial communication and stop the application
        self.ser.write("kraj letenja\n".encode())
        self.ser.close()
        self.stop.set()
        # End the application
        sys.exit()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
