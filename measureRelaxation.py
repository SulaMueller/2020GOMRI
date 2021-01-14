"""
Script to call the relaxometermanager

@author:    Sula Mueller
@contact:   ursula.mueller@ovgu.de
@version:   1.0
@change:    26/10/2020

@summary:   Main-Script to measure T1 of a probe.

@status:    Under testing
@todo:      Improve get functions

"""
import sys
from manager.relaxometermanager import RelaxometerManager
from .sequencemanager import SequenceManager as SeqHndlr

if __name__ == '__main__':
    print("Measuring relaxation...")
    RlxmtrMngr = RelaxometerManager("T1")

    SqncHndlr = ()  # initialize sequence object

    [relaxation, _, _, _, _] = RlxmtrMngr.get_relaxationTime(f_Ex, SqncHndlr, TIs, TR)

    print(["T1 = ", relaxation])
    