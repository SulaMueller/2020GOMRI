"""
Operations Controller

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   2.0.2
@change:    02/11/2020
"""

# system includes
from PyQt5.QtWidgets import QListWidget, QSizePolicy, QLabel
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUiType
from warnings import warn

# project includes
from globalvars import globals
from communicationmanager import ComMngr
from operationmodes import defaultoperations

nmspc = globals.GlobalNamespace
Parameter_Form, Parameter_Base = loadUiType('view/inputparameter.ui')

# class to define property parameters of sequence (text labels shown on GUI, such as TE)
class OperationParameter(Parameter_Base, Parameter_Form):
    # Get reference to position in operation object
    def __init__(self, parent, key, scanparameter, operationmode):
        # eg OperationParameter(nmspc.f_Ex, [float(self.f_Ex), nmspc.f_Ex, cmd.localOscillatorFrequency], operationmode)
        super(OperationParameter, self).__init__()
        self.setupUi(self)
        self.parent = parent

        # Set input parameter's label and value
        self.operationmode = operationmode
        self.operation = self.parent.listOfOperations[self.operationmode]
        self.scanparameter = scanparameter  # dictionary entry
        if key is nmspc.f_Ex:
            key = key + " [MHz]"
        if "T" in key:
            key = key + " [ms]"
        self.label_name.setText(key)
        self.input_value.setText(str(scanparameter[0]))

        # Connect text changed signal to getValue function
        self.input_value.textChanged.connect(self.get_value)

    # define what happens if value changed
    def get_value(self) -> None:
        # Reset value in operation object through the key in self.scanparameter[1]
        key = self.scanparameter[1]
        if self.input_value.text() == '':
            value = 0
        else:
            value: float = float(self.input_value.text())

        # sanity check to protect assembler file
        if ("TE" in key or "TI" in key) and value > 10000:
            value = 10000
            self.parent.setOutput("Can't set " + key + " > 10000 otherwise assembler file will crash.")
            self.set_value(value)
        if "TE" in key and value < 2:
            value = 2
            self.parent.setOutput("Can't set " + key + " < 2 otherwise assembler file will crash.")
            self.set_value(value)
        
        print("{}: {}".format(key, value))  # print every change in debugger
        self.operation.changeScanparameter(key, value)
        
    def set_value(self, value) -> None:
        self.input_value.setText(str(value))

class OperationManager(QListWidget):
    def __init__(self, parent=None):
        # @param parent:  Mainviewcontroller (access to parameter layout)

        super(OperationManager, self).__init__(parent)

        # Make parent reachable from outside __init__
        self.parent = parent
        self.currentOperationmode = None
        self.listOfOperations = defaultoperations

        # Add operation to UI
        self.addItems(list(self.listOfOperations.keys()))
        self.parent.onOperationChanged.connect(self.triggeredOperationChanged)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    #@staticmethod
    def generateLabelItem(text):
        label = QLabel()
        label.setText(text)
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return label

    # @staticmethod
    def generateWidgetsFromDict(self, obj: dict = None, operationmode: str = None) -> list:
        widgetlist: list = []
        for key in obj:
            widget = OperationParameter(self, key, obj[key], operationmode)
            widgetlist.append(widget)
        return widgetlist

    def get_items(self, struct: dict = None, operationmode: str = None) -> list:
        itemlist: list = []
        for key in list(struct.keys()):
            if type(struct[key]) == dict:
                itemlist.append(self.generateLabelItem(key))
                itemlist += self.get_items(struct[key], operationmode)
            else:
                item = OperationParameter(self, key, struct[key], operationmode)
                itemlist.append(item)
        return itemlist
    
    def addOutlabel(self):
        self.outlabel = QLabel()
        spacelabel = QLabel()
        self.outlabel.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        # self.outlabel.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        # self.outlabel.setStyleSheet("color: red")
        self.parent.layout_parameters.addWidget(spacelabel)
        self.parent.layout_parameters.addWidget(self.outlabel)
        self.outlabel.setText("")
    
    def setOutput(self, text: str = None):
        self.outlabel.setText(text)
        print(text)

    # Set input parameters from operation object
    def setParametersUI(self, operationmode: str = None) -> None:
        # Reset row layout for input parameters
        for i in reversed(range(self.parent.layout_parameters.count())):
            self.parent.layout_parameters.itemAt(i).widget().setParent(None)

        # Add input parameters to row layout
        inputwidgets: list = []

        if hasattr(self.listOfOperations[operationmode], 'scanparameters'):
            scanparams = self.listOfOperations[operationmode].scanparameters
            inputwidgets += self.generateWidgetsFromDict(scanparams, operationmode)

        for item in inputwidgets:
            self.parent.layout_parameters.addWidget(item)
        
        self.addOutlabel()

    def triggeredOperationChanged(self, operationmode: str = None) -> None:
        self.currentOperationmode = operationmode
        self.setParametersUI(operationmode)

        






