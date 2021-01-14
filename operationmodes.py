"""
Operation Modes

@author:    David Schote
@reworked and extended by : Sula Mueller
@contact:   david.schote@ovgu.de
@version:   2.0.2
@change:    02/11/2020
"""

# system imports
from warnings import warn

# project imports
from globalvars import globals
from assembler import Assembler
from communicationmanager import Commands as cmd

nmspc = globals.GlobalNamespace
seq = globals.Sequences
relaxtyp = globals.RelaxationTypes

class Spectrum:
    def __init__(self,
                 sequencefile: seq.SequenceFile = None,
                 f_Ex: float = None,
                 T_val: int = None,
                 numSamples: int = 2000,
                 shim: list = None):
        """
        Initialization of spectrum operation class
        @param sequencefile:    given sequence
        @param f_Ex:            excitation frequency
        @param T_val:           time value (TE, TI...)
        @param numSamples:      number of samples to be acquired
        @param shim:            Shim values for operation
        @return:                None
        """
        # make sure, shim is a len=4 array
        if shim is None:
            shim = [0, 0, 0, 0]
        while len(shim) < 4:
            shim += [0]

        # set class variables
        self.f_Ex: float = f_Ex
        self.T_val: int = T_val
        self.numSamples: int = numSamples
        self.sequencefile = sequencefile
        self.sequencebytestream = Assembler().assemble(self.sequencefile.path)
        self.shim_x: int = shim[0]
        self.shim_y: int = shim[1]
        self.shim_z: int = shim[2]
        self.shim_z2: int = shim[3]

    # scanparameters will be shown and can be modified on the GUI
    @property
    def scanparameters(self) -> dict:
        d =  {
            nmspc.f_Ex: [float(self.f_Ex), nmspc.f_Ex, cmd.localOscillatorFrequency],
            nmspc.numSamples: [int(self.numSamples), nmspc.numSamples, cmd.runAcquisition]
        }
        if self.T_val is not None:
            d[self.sequencefile.T_name] = [int(self.T_val), self.sequencefile.T_name]
        return d
    
    def changeScanparameter(self, key, value=None):
        if key == nmspc.f_Ex:
            self.f_Ex = value
        elif key == nmspc.numSamples:
            self.numSamples = value
        elif key == self.sequencefile.T_name:
            self.T_val = value
        elif key == nmspc.sequencebytestream:
            self.sequencebytestream = Assembler().assemble(self.sequencefile.path)
            print("Updated assembler.")
    
    @property
    def sequence(self):
        return{
            nmspc.sequencefile: [self.sequencefile, nmspc.sequencefile, cmd.sequenceData],
            nmspc.sequencebytestream: [self.sequencebytestream, nmspc.sequencebytestream, cmd.sequenceData]
        }

    @property
    def gradientshims(self):
        return {
            nmspc.G_x: [self.shim_x, 'shim_x', cmd.gradientOffsetX],
            nmspc.G_y: [self.shim_y, 'shim_y', cmd.gradientOffsetY],
            nmspc.G_z: [self.shim_z, 'shim_z', cmd.gradientOffsetZ]
        }

class Relaxometer:
    def __init__(self,
                 sequencefile: seq.SequenceFile = None,
                 relaxationtype: relaxtyp = None,
                 f_Ex: float = None,
                 Tval_min: int = None,
                 Tval_max: int = None,
                 numTimeValues = 20,
                 numSamplesPerTimeValue: int = 2000,
                 numAveragesPerTimeValue: int = 5):
        """
        Initialization of spectrum operation class
        @param sequencefile:    given sequence
        @param relaxationtype:  type of relaxation to be measured (T1, T2)
        @param f_Ex:            excitation frequency
        @param Tval_min:        lowest time value (TI, TE)
        @param Tval_max:        max time value (logarithmic scaling between Tval_min/max)
        @param numTimeValues:   number of time values (TI, TE) to be measured
        @param numSamplesPTV:   sample size for each T_val
        @param numAveragesPTV:  number of measurements for each T_val (get averaged)
        @return:                None
        """

        # set class variables
        self.sequencefile = sequencefile
        self.sequencebytestream = Assembler().assemble(self.sequencefile.path)
        self.relaxationtype = relaxationtype
        self.f_Ex: float = f_Ex
        self.numTimeValues: int = numTimeValues
        self.numSamplesPerTimeValue: int = numSamplesPerTimeValue
        self.numAveragesPerTimeValue: int = numAveragesPerTimeValue
        self.tval_min: int = Tval_min
        self.tval_max: int = Tval_max

    @property
    def scanparameters(self) -> dict:
        return {
            nmspc.f_Ex: [float(self.f_Ex), nmspc.f_Ex, cmd.localOscillatorFrequency],
            nmspc.numTimeValues: [int(self.numTimeValues), nmspc.numTimeValues],
            nmspc.numAveragesPerTimeValue: [int(self.numAveragesPerTimeValue), nmspc.numAveragesPerTimeValue],
            nmspc.numSamplesPerTimeValue: [int(self.numSamplesPerTimeValue), nmspc.numSamples, cmd.runAcquisition],
            self.sequencefile.T_name + '_min': [int(self.tval_min), self.sequencefile.T_name + '_min'],
            self.sequencefile.T_name + '_max': [int(self.tval_max), self.sequencefile.T_name + '_max']
        }

    def changeScanparameter(self, key, value=None):
        if key == nmspc.f_Ex:
            self.f_Ex = value
        elif key == nmspc.numTimeValues:
            self.numTimeValues = value
        elif key == nmspc.numAveragesPerTimeValue:
            self.numAveragesPerTimeValue = value
        elif key == nmspc.numSamplesPerTimeValue:
            self.numSamplesPerTimeValue = value
        elif key == self.sequencefile.T_name + '_min':
            self.tval_min = value
        elif key == self.sequencefile.T_name + '_max':
            self.tval_max = value
        elif key == nmspc.sequencebytestream:
            self.sequencebytestream = Assembler().assemble(self.sequencefile.path)
            print("Updated assembler.")
    
    @property
    def sequence(self):
        return{
            nmspc.sequencefile: [self.sequencefile, nmspc.sequencefile, cmd.sequenceData],
            nmspc.sequencebytestream: [self.sequencebytestream, nmspc.sequencebytestream, cmd.sequenceData]
        }


# Definition of default operations
f_Ex_default = 5.8882
T_val_default = 5
T_min_default = 2
T_max_default = 200

defaultoperations = {
    'FID Spectrum': Spectrum(seq.FID, f_Ex_default),
    'SE Spectrum': Spectrum(seq.SE, f_Ex_default, T_val_default), 
    'T1 Relaxometry': Relaxometer(seq.IR, relaxtyp.T1, f_Ex_default, T_min_default, T_max_default),
    'T2 Relaxometry': Relaxometer(seq.SE, relaxtyp.T2, f_Ex_default, T_min_default, T_max_default)
}
