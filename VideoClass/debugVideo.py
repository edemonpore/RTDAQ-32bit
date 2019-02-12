# ...for class debugging

from Video import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = VidWin()
    sys.exit(app.exec_())