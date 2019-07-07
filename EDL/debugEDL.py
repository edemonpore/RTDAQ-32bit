# ...for class debugging

from EDL import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = EDL()
    window.DAQThread = threading.Thread(target=window.DataAcquisitionThread)
    window.DAQThread.start()
    window.show()
    sys.exit(app.exec_())