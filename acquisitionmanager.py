"""
Acquisition Manager

@author:    Sula Mueller (based on work of David Schote)
@contact:   david.schote@ovgu.de
@version:   2.0.2
@change:    02/11/2020

@summary:   Class for controlling the acquisition
"""

# system includes
import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QObject
from plotview.spectrumplot import SpectrumPlot
from warnings import warn

# project includes
from globalvars import globals
from config import configvars as config
from operationmodes import Spectrum, Relaxometer
from communicationmanager import ComMngr
from datamanager import DataManager
from timevaluemanager import TimeValueManager 
from frequencymanager import FrequencyManager
from relaxometermanager import RelaxometerManager

nmspc = globals.GlobalNamespace
relaxtyp = globals.RelaxationTypes
seq = globals.Sequences

class AcquisitionManager(QObject):
    def __init__(self, parent=None, outputsection=None):
         # @param parent:  Mainviewcontroller (access to parameter layout)

        super(AcquisitionManager, self).__init__(parent)

        self.parent = parent
        self.outputsection = outputsection
        self.acquisitionData = None
        self.T_val = 0

        self.version = (1 << 16) | (1 << 8) | 1  # needs a version to work

        # if "acquire"-button in parent is pressed, start acquisition
        self.parent.action_acquire.triggered.connect(self.actionOnRunButtonClicked)
        
    @pyqtSlot(bool) 
    def actionOnRunButtonClicked(self):
        self.operation = self.parent.OpMngr.listOfOperations.get(self.parent.OpMngr.currentOperationmode, None)  # get current operation
        print("Current operationmode: " + self.operation.sequence[nmspc.sequencefile][0].str)

        self.prepareAcquisition()
        if isinstance(self.operation, Spectrum):
            self.runAcquisition()
            self.postprocessAcquisition()
        elif isinstance(self.operation, Relaxometer):
            self.focusFrequency()  # set f_Ex to f_Larmor
            self.RelaxMngr = RelaxometerManager(self)
            self.postprocessRelaxometry()
        else:
            warn("unrecognized operationmode")
    
    def needTval(self) -> bool:
        return not (self.operation.sequence[nmspc.sequencefile][0].str == seq.FID.str or isinstance(self.operation, Relaxometer))

    def setTval(self, T_val):
        # change T_val in sequence file only if changed compared to previous value
        if T_val != self.T_val:
            print("set " + self.operation.sequence[nmspc.sequencefile][0].T_name + " = " + str(T_val) + "ms")
            TimeValueManager(self.operation.sequence[nmspc.sequencefile][0], T_val)  # set T_val in sequence file
            self.operation.changeScanparameter(nmspc.sequencebytestream) # run sequence file into assembler
            self.T_val = T_val
        
    def preparationDebug(self):
        if isinstance(self.operation, Spectrum):
            print("PREPARING SEQUENCE")
            print("   Excitation Frequency = " + str(self.f_Ex))
            print("   Number of acquired samples = " + str(self.numSamples))
            if self.needTval():
                print("   " + self.operation.sequence[nmspc.sequencefile][0].T_name + " = " + str(self.T_val))

    def prepareAcquisition(self):
        self.parent.clearPlotviewLayout()
        self.f_Ex = self.operation.scanparameters[nmspc.f_Ex][0]

        if isinstance(self.operation, Spectrum):
            self.numSamples = self.operation.scanparameters[nmspc.numSamples][0]
            if self.needTval():
                T_val = self.operation.scanparameters[self.operation.sequence[nmspc.sequencefile][0].T_name][0]

        elif isinstance(self.operation, Relaxometer):
            self.numSamples = self.operation.scanparameters[nmspc.numSamplesPerTimeValue][0]
            T_val = self.operation.scanparameters[self.operation.sequence[nmspc.sequencefile][0].T_name + '_min'][0]
        
        if self.needTval():
             # set T_val in sequence file
            self.setTval(T_val) 
        
        self.preparationDebug()
        
    def runAcquisition(self, T_val=None):
        packetIdx: int = 0
        command: int = 0  # 0 equals request a packet

        # set time value (TE/TI)
        if T_val is not None:
            self.setTval(T_val)

        # Get/construct package to be send
        tmp_sequence_pack = ComMngr.constructSequencePacket(self.operation)  # uses self.operation.sequencebytestream
        tmp_scanparam_pack = ComMngr.constructScanParameterPacket(self.operation)  # uses self.operation.scanparameters.f_Ex
        tmp_package = {**tmp_sequence_pack, **tmp_sequence_pack, **tmp_scanparam_pack}
        fields = [command, packetIdx, 0, self.version, tmp_package]

        response = ComMngr.sendPacket(fields)
        if response is None:
            self.parent.OpMngr.setOutput("Console not connected. Nothing received.")
            self.haveResult = False
            return
        self.haveResult = True

        # get the actual data
        tmp_data = np.frombuffer(response[4]['acq'], np.complex64)
        print("Size of received data: {}".format(len(tmp_data)))
        self.dataobject: DataManager = DataManager(tmp_data, self.f_Ex, self.numSamples)

    # Function to create a dictionary of output parameters for Spectrum measurement
    def generateSpectrumOutput(self) -> dict:
        outputvalues: dict = {}
        if hasattr(self, 'dataobject') and isinstance(self.operation, Spectrum):
            outputvalues["SNR"] = round(self.dataobject.get_snr(), config.roundToDigits)
            outputvalues["FWHM [Hz]"] = round(self.dataobject.get_fwhm()[1], config.roundToDigits)
            outputvalues["FWHM [ppm]"] = round(self.dataobject.get_fwhm()[2], config.roundToDigits)
            outputvalues["Center Frequency [MHz]"] = round(self.dataobject.get_peakparameters()[2], config.roundToDigits)
            outputvalues["Signal Maximum [V]"] = round(self.dataobject.get_peakparameters()[3], config.roundToDigits)
        return outputvalues

    # Function to create a dictionary of output parameters for Relaxometry
    def generateRelaxometerOutput(self) -> dict:
        outputvalues: dict = {}
        if hasattr(self, 'dataobject') and isinstance(self.operation, Relaxometer):
            outputvalues["Center Frequency [MHz]"] = round(self.dataobject.get_peakparameters()[2], config.roundToDigits)
        if self.RelaxMngr is not None:
            T_res = round(self.RelaxMngr.relaxationTime, config.roundToDigits)
            outputvalues[self.RelaxMngr.relaxationtype + " [ms]"] = T_res
            outputvalues["Fit-Parameters [A]"] = self.RelaxMngr.fitParameters[0]
            outputvalues["Fit-Parameters [B]"] = self.RelaxMngr.fitParameters[1]
            outputvalues["Fit-Parameters [C] "] = self.RelaxMngr.fitParameters[2]
            outputvalues["r2-metric"] = self.RelaxMngr.r2Metric
            if self.RelaxMngr.relaxationtype is relaxtyp.T1: 
                outputvalues["fit-function"] = "A - B * exp(-C * t)"
            if self.RelaxMngr.relaxationtype is relaxtyp.T2: 
                outputvalues["fit-function"] = "A + B * exp(-C * t)"
        return outputvalues

    def postprocessAcquisition(self):
        if self.haveResult is False:
            return

        # put some results on the UI
        outputvalues = self.generateSpectrumOutput()
        self.outputsection.set_parameters(outputvalues)  # put output parameters on UI

        # manage plot on UI
        f_plotview = SpectrumPlot(self.dataobject.f_axis, self.dataobject.f_fftMagnitude, "frequency", "signal intensity")
        t_plotview = SpectrumPlot(self.dataobject.t_axis, self.dataobject.t_magnitude, "time", "signal intensity")
        self.parent.plotview_layout.addWidget(f_plotview)
        self.parent.plotview_layout.addWidget(t_plotview)

        self.parent.OpMngr.setOutput("Acquisition done.")

    def postprocessRelaxometry(self):
        # put some results on the UI
        outputvalues = self.generateRelaxometerOutput()
        self.outputsection.set_parameters(outputvalues)  # put output parameters on UI

        # manage plot on UI
        if self.RelaxMngr is not None:
            xaxisname = self.operation.sequence[nmspc.sequencefile][0].T_name
            fitted_plotview = SpectrumPlot(self.RelaxMngr.fitXAxis, self.RelaxMngr.fitYAxis, xaxisname, "fitted curve")
            self.parent.plotview_layout.addWidget(fitted_plotview)

            fitted_plotview.addData(self.RelaxMngr.T_vals, self.RelaxMngr.datavals)

        if not self.RelaxMngr.fakeData:
            self.parent.OpMngr.setOutput("Relaxometry done.")
        else:
            self.parent.OpMngr.setOutput("Relaxometry simulated using randomized example data.")

    @pyqtSlot(bool)
    def focusFrequency(self) -> None:  # set f_Ex to f_Larmor
        FrequencyManager(self)
