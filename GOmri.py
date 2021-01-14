"""
Startup Code

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   2.0.2
@change:    02/11/2020
"""

# system includes
import sys
from PyQt5.QtWidgets import QApplication

# project includes
from mainviewcontroller import MainViewController

VERSION = "2.0.2"
AUTHOR = "David Schote, Sula Mueller"

if __name__ == '__main__':
    print("Graphical User Interface for Magnetic Resonance Imaging {} by {}".format(VERSION, AUTHOR))
    app = QApplication(sys.argv)
    gui = MainViewController()
    gui.show()
    gui.connectiondialog.show()
    sys.exit(app.exec_())
