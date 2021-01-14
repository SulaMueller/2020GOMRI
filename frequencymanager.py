"""
Frequency Manager

@author:    Sula Mueller
@version:   1.0.0
@change:    12/11/2020

@summary:   Class to center frequency (to current Larmor frequency)
"""

# system imports
import numpy as np

# project imports
from communicationmanager import ComMngr
from datamanager import DataManager
from operationmodes import Spectrum, defaultoperations
from globalvars import globals
nmspc = globals.GlobalNamespace

class FrequencyManager:
    def __init__(self, AcqMngr = None, operation = None):
        self.AcqMngr = AcqMngr
        self.operation = operation
        self.f_Larmor = None

        if AcqMngr is not None:
            if hasattr(AcqMngr, 'dataobject'):
                [_, _, self.f_Larmor, _] = self.AcqMngr.dataobject.get_peakparameters()
        
        if self.f_Larmor is None:
            self.getLarmor()
    
    def getLarmor(self):
        print('Centering frequency by additional acquisition.')
        # make sure there is an operation and an f_Ex
        # f_Ex = frequency of excitation; f_Larmor = maximum of response
        if self.AcqMngr is not None:
            if hasattr(self.AcqMngr, 'operation'):
                if self.AcqMngr.operation is not None:
                    self.f_Ex = self.AcqMngr.operation.scanparameters[nmspc.f_Ex][0]
                    if self.operation is None:
                        self.operation = self.AcqMngr.operation
        if not hasattr(self, 'f_Ex') and self.operation is not None:
            self.f_Ex = self.operation.scanparameters[nmspc.f_Ex][0]
        if self.operation is None:
            self.operation = defaultoperations['FID Spectrum']
            self.f_Ex = self.operation.scanparameters[nmspc.f_Ex][0]

        # do an acquisition
        packetIdx: int = 0
        command: int = 0  # 0 equals request a packet
        version = (1 << 16) | (1 << 8) | 1  # needs a version to work
        self.numSamples = self.operation.numSamplesPerTimeValue

        tmp_sequence_pack = ComMngr.constructSequencePacket(self.operation)  # uses self.operation.sequencebytestream
        tmp_scanparam_pack = ComMngr.constructScanParameterPacket(self.operation)  # uses self.operation.scanparameters.f_Ex
        tmp_package = {**tmp_sequence_pack, **tmp_sequence_pack, **tmp_scanparam_pack}
        fields = [command, packetIdx, 0, version, tmp_package]

        response = ComMngr.sendPacket(fields)
        if response is None:
            print("Nothing received. Frequency centering abandoned.")
            return

        # get the actual data
        tmp_data = np.frombuffer(response[4]['acq'], np.complex64)
        print("Size of received data: {}".format(len(tmp_data)))
        dataobject: DataManager = DataManager(tmp_data, self.f_Ex, self.numSamples)
        [_, _, self.f_Larmor, _] = dataobject.get_peakparameters()
        
        self.setLarmor()
    
    def setLarmor(self):
        if self.AcqMngr is not None:
            self.AcqMngr.f_Ex = self.f_Larmor
            if hasattr(self.AcqMngr, 'operation'):
                if self.AcqMngr.operation is not None:
                    self.AcqMngr.operation.scanparameters[nmspc.f_Ex][0] = self.f_Larmor
        if self.operation is not None and self.f_Larmor is not None:
            self.operation.scanparameters[nmspc.f_Ex][0] = self.f_Larmor
