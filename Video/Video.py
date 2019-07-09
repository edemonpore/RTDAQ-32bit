"""Video.py
VidCam: Video Camera Data Class
EYafuso
Feb 2019
"""

import os
import cv2
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import threading, time

class VidWin(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        path = os.path.abspath("") + '\\Video\\VidWindow.ui'
        try:
            Ui_VW = uic.loadUiType(path)[0]
        except:
            Ui_VW = uic.loadUiType('VidWindow.ui')[0]

        self.fps = 30   #sample frames at 33 millisecond intervals
        self.ui = Ui_VW()
        self.ui.setupUi(self)
        self.ui.vsIntegrate.setMinimum(0)
        self.ui.vsIntegrate.setMaximum(100)
        self.exposure = 33 #exposure setting in milliseconds
        self.ui.vsIntegrate.setValue(self.exposure)
        self.ui.lTs.setText(str(self.exposure))

        self.ui.vsIntegrate.valueChanged.connect(self.setExposure)
        self.PixMap = QtGui.QPixmap()

        self.CamNum = 0
        self.CamThread = None
        self.bAcquiring = False
        self.doLiveVideo()

        self.bShow = True

        self.MoveToStart()

    def setExposure(self):
        temp = self.ui.vsIntegrate.value()
        self.ui.lTs.setText(str(temp))

    def doLiveVideo(self):
        if self.CamThread == None:
            self.CamThread = threading.Thread(target=self.LiveVideoThread)
            self.bAcquiring = True
            self.CamThread.start()

    def UpdateData(self):
        pass

    def LiveVideoThread(self):
        self.cam = cv2.VideoCapture(self.CamNum)
        width = self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cam.get(cv2.CAP_PROP_FPS)
        if self.fps == 0: self.fps = 33
        self.ui.lVideo.setMinimumSize(1, 1)
        self.ui.lVideo.installEventFilter(self)

        while self.bAcquiring:
            ret, frame = self.cam.read()
            if ret == True and frame is not None:
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

    def MoveToStart(self):
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()

        vidwingeo = self.geometry()
        x = 0 # ag.width() - vidwingeo.width()
        y = 0 # 2 * ag.height() - sg.height() - vidwingeo.height()
        self.move(x, y)

    def eventFilter(self, source, event):
        if (source is self.ui.lVideo and event.type() == QtCore.QEvent.Paint):
            self.ui.lVideo.setAlignment(QtCore.Qt.AlignCenter)
            self.ui.lVideo.setPixmap(self.PixMap.scaled(self.ui.lVideo.size(),
                                                        QtCore.Qt.KeepAspectRatio,
                                                        QtCore.Qt.SmoothTransformation))
        return super(VidWin, self).eventFilter(source, event)

    def closeEvent(self, event):
        self.bAcquiring = False
        if self.CamThread != None:
            self.CamThread.join()
            event.accept()
        else:
            self.bShow = False
            self.hide()
            event.ignore()