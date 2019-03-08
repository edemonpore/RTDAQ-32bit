"""EDL.py
Class structure for Elements PCA's
Acquire USB data:
    Elements    PCA (current, multi-channel)
Set USB data:
    Elements    PCA (Potential, sample rate, etc.)
E.Yafuso
Feb 2019
"""


#import edl_py
from PyQt5 import QtWidgets, uic
import pyqtgraph
import collections, struct
import threading, time

class PCA(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_EDL = uic.loadUiType("EDLui.ui")[0]
        pyqtgraph.setConfigOption('background', 'k')
        self.ui = Ui_EDL()
        self.ui.setupUi(self)
        self.bAcquiring = False

        # Default PCA Settings
        self.ui.rb200pA.setChecked(True)
        self.ui.rb1_25KHz.setChecked(True)
        self.ui.rbSRby2.setChecked(True)

        # Signals to slots
        self.ui.rb200pA.clicked.connect(lambda: self.setRange(.20))
        self.ui.rb2nA.clicked.connect(lambda: self.setRange(2))
        self.ui.rb20nA.clicked.connect(lambda: self.setRange(20))
        self.ui.rb200nA.clicked.connect(lambda: self.setRange(200))
        self.ui.rb1_25KHz.clicked.connect(lambda: self.setSampleRate(1.25))
        self.ui.rb5KHz.clicked.connect(lambda: self.setSampleRate(5))
        self.ui.rb10KHz.clicked.connect(lambda: self.setSampleRate(10))
        self.ui.rb20KHz.clicked.connect(lambda: self.setSampleRate(20))
        self.ui.rb50KHz.clicked.connect(lambda: self.setSampleRate(50))
        self.ui.rb100KHz.clicked.connect(lambda: self.setSampleRate(100))
        self.ui.rb200KHz.clicked.connect(lambda: self.setSampleRate(200))
        self.ui.rbSRby2.clicked.connect(lambda: self.setFinalBandwidth(2))
        self.ui.rbSRby8.clicked.connect(lambda: self.setFinalBandwidth(8))
        self.ui.rbSRby10.clicked.connect(lambda: self.setFinalBandwidth(10))
        self.ui.rbSRby20.clicked.connect(lambda: self.setFinalBandwidth(20))

        # Class attributes
        self.maxLen = 10

        self.iset = 0
        self.isetdata = collections.deque([0], self.maxLen)

        self.fData  = bytearray(2)
        self.idata  = collections.deque([0], self.maxLen)
        self.t      = collections.deque([0], self.maxLen)

        self.px = self.ui.IData.plot()
        self.ui.IData.setYRange(-200, 200)

        self.bShow = True
        self.bCanClose = False
        self.MoveToStart()

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()

        vidwingeo = self.geometry()
        x = 200  # ag.width() - vidwingeo.width()
        y = 100  # 2 * ag.height() - sg.height() - vidwingeo.height()
        self.move(x, y)

    def setRange(self, value):
        temp = value

    def setSampleRate(self, value):
        temp = value

    def setFinalBandwidth(self, value):
        temp = value