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
        self.title = 'Proba'
        self.left = 200
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
        self.calibrateButton.clicked.connect(self.calibrate)

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

    def calibrate(self):
        # Calibration x button
        self.calibrateButton = QPushButton('Calibrate X', self)
        self.calibrateButton.resize(100, 50)
        self.calibrateButton.move(100, 100)
        self.calibrateButton.clicked.connect(self.calibrate)

        # Calibration y button
        self.calibrateButton = QPushButton('Calibrate Y', self)
        self.calibrateButton.resize(100, 50)
        self.calibrateButton.move(100, 160)
        self.calibrateButton.clicked.connect(self.calibrate)

        # Calibration z button
        self.calibrateButton = QPushButton('Calibrate Z', self)
        self.calibrateButton.resize(100, 50)
        self.calibrateButton.move(100, 220)
        self.calibrateButton.clicked.connect(self.calibrate)


        print("CALIBRATING")
        self.show()
    
    def startFlight(self):
        print("LETIM")

    def off(self):
        print("bye bye...")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
