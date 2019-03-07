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

        # Class attributes
        self.maxLen = 10

        self.iset = 0
        self.isetdata = collections.deque([0], self.maxLen)

        self.fData  = bytearray(2)
        self.idata  = collections.deque([0], self.maxLen)
        self.t      = collections.deque([0], self.maxLen)

        self.px = self.ui.IData.plot()
        self.ui.IData.setYRange(0, 100)

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