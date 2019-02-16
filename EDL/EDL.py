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
import threading, time



class PCA():
    def __init__(self):
        self.EDL = ctypes.CDLL("e4")
        self.devices = []

        self.EDL.init()
        print(self.devices)

PCA = PCA()

