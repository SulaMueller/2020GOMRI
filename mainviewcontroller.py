"""
Main View Controller

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   2.0.2
@change:    02/11/2020
"""

# system includes
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.uic import loadUiType, loadUi
from PyQt5.QtCore import pyqtSignal, pyqtSlot

# project includes
from acquisitionmanager import AcquisitionManager
from operationmanager import OperationManager
from controller.connectiondialog import ConnectionDialog
from controller.outputparametercontroller import Output
from globalvars import globals
from communicationmanager import ComMngr

style = globals.StyleSheets
MainWindow_Form, MainWindow_Base = loadUiType('view/mainview.ui')

class MainViewController(MainWindow_Base, MainWindow_Form):
    """
    MainViewController Class
    """
    onOperationChanged = pyqtSignal(str)   

    def __init__(self):
        super(MainViewController, self).__init__()
        self.ui = loadUi('view/mainview.ui')
        self.setupUi(self)
        self.styleSheet = style.breezeDark
        self.setupStylesheet(self.styleSheet)
        self.ui.setWindowTitle("GOmri")

        # get a connection to the server
        self.connectiondialog = ConnectionDialog(self)

        # Initialisation of operation list
        self.OpMngr = OperationManager(self)
        self.OpMngr.itemClicked.connect(self.operationChangedSlot)
        self.layout_operations.addWidget(self.OpMngr)

        # Initialisation of acquisition manager
        outputsection = Output(self)
        self.AcqMngr = AcquisitionManager(self, outputsection)
        # if "acquire"-button is pressed in mainview, AcqMngr will start acquisition

        # Select for each button what happens on button click
        self.action_connect.triggered.connect(self.connectiondialog.show)
        self.action_changeappearance.triggered.connect(self.changeAppearanceSlot)
        # self.action_focusfrequency.triggered.connect(AcqMngr.focusFrequency())
        self.action_acquire.setEnabled(False)  # disable acquire button by default (will enable if operation selected)
        
    @pyqtSlot(QListWidgetItem)
    def operationChangedSlot(self, item: QListWidgetItem = None):
        """
        Operation changed slot function
        @param item:    Selected Operation Item
        @return:        None
        """
        operation = item.text()
        self.onOperationChanged.emit(operation)
        self.action_acquire.setEnabled(True)

    @pyqtSlot(bool)
    def connectionDialogSlot(self):
        dialog = ConnectionDialog(self)
        dialog.show()
        dialog.connected.connect(self.start_com)

    def clearPlotviewLayout(self):
        for i in reversed(range(self.plotview_layout.count())):
            self.plotview_layout.itemAt(i).widget().setParent(None)

    # Setup application stylesheet
    def setupStylesheet(self, style):
        # @param style:   Stylesheet to be set

        self.styleSheet = style
        file = QFile(style)
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        self.setStyleSheet(stylesheet)

    # Slot function to switch application appearance
    @pyqtSlot(bool)
    def changeAppearanceSlot(self):
        if self.styleSheet is style.breezeDark:
            self.setupStylesheet(style.breezeLight)
        else:
            self.setupStylesheet(style.breezeDark)

    @staticmethod
    def closeEvent(event):
        """
        Overloaded close function
        @param event:   Close event
        """
        # Disconnect server connection on closed before accepting the event
        ComMngr.disconnectClient()
        event.accept()
