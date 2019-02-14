"""Video.py
VidCam: Video Camera Data Class
EYafuso
Feb 2019
"""

import sys
import cv2
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import threading, time

class VidWin(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_VW = uic.loadUiType("VidWindow.ui")[0]

        self.fps = 30   #sample frames at 33 millisecond intervals
        self.ui = Ui_VW()
        self.ui.setupUi(self)


        self.PixMap = QtGui.QPixmap()
        self.CamNum = 0
        self.CamThread = None
        self.bAcquiring = False
        self.doLiveVideo()
        self.show()

    def doLiveVideo(self):
        if self.CamThread == None:
            self.CamThread = threading.Thread(target=self.LiveVideoThread)
            self.bAcquiring = True
            self.CamThread.start()

    def LiveVideoThread(self):
        self.cam = cv2.VideoCapture(self.CamNum)
        width = self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cam.get(cv2.CAP_PROP_FPS)
        self.ui.lVideo.setMinimumSize(1, 1)
        self.ui.lVideo.installEventFilter(self)

        while self.bAcquiring is True:
            ret, frame = self.cam.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QtGui.QImage(frame,
                                 width,
                                 height,
                                 QtGui.QImage.Format_RGB888)
            self.PixMap = QtGui.QPixmap.fromImage(image)
            self.ui.lVideo.setPixmap(self.PixMap)
            time.sleep(1/self.fps)
        self.cam.release()
        cv2.destroyAllWindows()

    def eventFilter(self, source, event):
        if (source is self.ui.lVideo and event.type() == QtCore.QEvent.Paint):
            self.ui.lVideo.setAlignment(QtCore.Qt.AlignCenter)
            self.ui.lVideo.setPixmap(self.PixMap.scaled(self.ui.lVideo.size(),
                                                        QtCore.Qt.KeepAspectRatio,
                                                        QtCore.Qt.SmoothTransformation))
        return super(VidWin, self).eventFilter(source, event)

    def closeEvent(self,event):
        self.bAcquiring = False
        self.close()