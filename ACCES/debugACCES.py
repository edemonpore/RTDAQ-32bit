# ...for ACCES class debugging

from ACCES import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ACCES()
    window.show()
    sys.exit(app.exec_())