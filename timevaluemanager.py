"""
Time Value Manager

@author:    Sula Mueller
@version:   1.0.0
@change:    06/11/2020

@summary:   Class to set time values in sequence files
"""

# system includes
from PyQt5.QtCore import QObject, pyqtSignal
from warnings import warn

# project includes
from globalvars import globals
from assembler import Assembler

seq = globals.Sequences

class TimeValueManager:
    # is called from AcquisitionManger.runAcquisition or RelaxometerManager
    def __init__(self,
                 sequencefile: seq.SequenceFile,
                 T_val: int):  # time value in ms

        self.sequence = sequencefile
        self.sequencepath = sequencefile.path

        self.setTimeVal(T_val)

    # Function to set time value of a sequence (TE/TI)
    def setTimeVal(self, T_val: int = 15) -> None:
        f = open(self.sequencepath, 'r+')  # Open sequence and read lines
        lines = f.readlines()
        # Modify T_val time in correct line
        if self.sequence is seq.SE:
            lines[-10] = 'PR 3, ' + str(int(T_val / 2 * 1000 - 112)) + '\t// wait&r\n'
            lines[-6] = 'PR 3, ' + str(int(T_val / 2 * 1000 - 975)) + '\t// wait&r\n'
        elif self.sequence is seq.IR:
            lines[-14] = 'PR 3, ' + str(int(T_val * 1000 - 198)) + '\t// wait&r\n'
        elif self.sequence is seq.SIR:
            lines[-9] = 'PR 3, ' + str(int(T_val * 1000 - 198)) + '\t// wait&r\n'
            lines[-13] = 'PR 3, ' + str(int(T_val * 1000 - 198)) + '\t// wait&r\n'
        else:
            warn("SetTimeValue is not implemented for this sequence type.")
            f.close()  # Close and write/save modified sequence
            return
        with open(self.sequencepath, "w") as out_file:
            for line in lines:
                out_file.write(line)
        f.close()  # Close and write/save modified sequence
                

