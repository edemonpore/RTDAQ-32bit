# ...for class debugging

from EDL import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ACCES()
    sys.exit(app.exec_())