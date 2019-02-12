"""EDL.py
Class structure for Elements PCA's
Acquire USB data:
    Elements    PCA (current, multi-channel)
Set USB data:
    Elements    PCA (Potential, sample rate, etc.)
E.Yafuso
Feb 2019
"""
# ToDo:
# Find PCA and connect
# Get PCA version
# Initialize PCA
# Set up acquisition thread
# Display data
# GUI control
import ctypes
import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import collections, struct
import threading, time

class EDL(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_EDL = uic.loadUiType("EDL.ui")[0]
        self.ui = Ui_EDL()
        self.ui.setupUi(self)
        EDL = ctypes.CDLL("edl")