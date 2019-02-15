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

class EDL():
    def __init__(self):
        self.EDL = ctypes.CDLL("edl")
        self.devices = []

        self.EDL.init()
        self.EDL.detectDevices(byref(self.devices))
        print(self.devices)

pca = EDL()