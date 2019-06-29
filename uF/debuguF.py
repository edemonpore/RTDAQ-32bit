# ...for class debugging

from uF import *
import sys

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = uF()
    window.show()
    sys.exit(app.exec_())