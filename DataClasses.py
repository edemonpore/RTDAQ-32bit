"""DataClasses.py
Definition to integrate Demonpore data acquisition
EYafuso
Feb 2019
"""

class RTDAQData:
    def __init__(self):
        self.DAQData()
        self.PCAData()
        self.t = time.time

class DAQData:
    def __init__(self):
        self.x-set = []
        self.y-set = []
        self.z-set = []
        self.x = []
        self.y = []
        self.z = []

class PCAData:
    def __init__(self):
        self.range = 0
        self.SampFreq = 0
        self.mV-set = []
        self.pA = []