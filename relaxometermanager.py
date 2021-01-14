"""
Relaxometer Manager

@author:    Sula Mueller
@version:   1.0.0
@change:    06/11/2020

@summary:   Class for relaxometry
"""

# system includes
import numpy as np
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QObject
from warnings import warn
from scipy.optimize import curve_fit, brentq

# project includes
from globalvars import globals
from config import configvars as config
from communicationmanager import ComMngr
from datamanager import DataManager
from timevaluemanager import TimeValueManager 

nmspc = globals.GlobalNamespace
relaxtyp = globals.RelaxationTypes

class RelaxometerManager(QObject):
    def __init__(self, parent=None):
         # @param parent:  AcquisitionManager

        super(RelaxometerManager, self).__init__(parent)
        self.parent = parent

        # get measurement parameters
        self.relaxationtype = parent.operation.relaxationtype  # T1 or T2
        self.numTimeValues = parent.operation.scanparameters[nmspc.numTimeValues][0] 
        self.numSamplesPerTimeValue = parent.operation.scanparameters[nmspc.numSamplesPerTimeValue][0]
        self.numAveragesPerTimeValue = parent.operation.scanparameters[nmspc.numAveragesPerTimeValue][0]
        self.tval_min = parent.operation.scanparameters[parent.operation.sequencefile.T_name + '_min'][0]
        self.tval_max = parent.operation.scanparameters[parent.operation.sequencefile.T_name + '_max'][0]

        self.parent.parent.OpMngr.setOutput("STARTING " + self.relaxationtype + "-RELAXOMETRY")
        print("   Excitation Frequency = " + str(self.parent.f_Ex))
        print("   Number of acquired " + parent.operation.sequencefile.T_name + "s = " + str(self.numTimeValues))
        print("   Number of averages per " + parent.operation.sequencefile.T_name + " = " + str(self.numAveragesPerTimeValue))
        print("   Number of samples per measurement = " + str(self.numSamplesPerTimeValue))
        print("   "  + parent.operation.sequencefile.T_name + " = [" + str(self.tval_min) + ", " + str(self.tval_max) + "]")

        # functionality
        self.fakeData = False
        self.getTvals()
        self.doAllMeasurements()
        self.getResult()

    def removeRedundancies(self, inlist) -> list:
        res = [] 
        for i in inlist: 
            if i not in res: 
                res.append(i) 
        return res
        
    def getTvals(self):
        log_Tmin : float = np.log10(float(self.tval_min))  # logspace will use power, need to inverse first
        log_Tmax : float = np.log10(float(self.tval_max))
        # get logarithmic spaced T_val axis rounded to whole ms (rint for rounding)
        self.T_vals = np.rint(np.logspace(log_Tmin, log_Tmax, self.numTimeValues))
        # remove redundancies
        self.T_vals = self.removeRedundancies(self.T_vals)
        self.numTimeValues = len(self.T_vals)
        # make sure times are in int
        self.T_vals = [int(t) for t in self.T_vals]

    def doAllMeasurements(self):
        successful = True
        self.datavals = []
        for T_val in self.T_vals:
            self.parent.parent.OpMngr.setOutput("...measuring " + self.parent.operation.sequencefile.T_name + " = " + str(int(T_val)) + "ms")
            av = 0
            for _ in range(0, self.numAveragesPerTimeValue):
                self.parent.runAcquisition(T_val)
                if self.parent.haveResult is False:
                    successful = False
                    continue
                av = av + round(self.parent.dataobject.get_peakparameters()[3], config.roundToDigits)
            av = round(av / self.numAveragesPerTimeValue, config.roundToDigits)
            self.datavals.append(av)
        if not successful:
            self.getExampleData()
    
    def getRandomValue(self, minVal, maxVal):
        valrange = maxVal - minVal
        val = valrange*np.random.random_sample() + minVal
        return val

    def getExampleData(self):
        self.parent.parent.OpMngr.setOutput("GETTING EXAMPLE DATA....")
        self.fakeData = True
        for i in range(0, self.numTimeValues):
            if self.relaxationtype is relaxtyp.T1:
                self.datavals[i] = abs( (np.log10(float(self.T_vals[i]))-1) * self.getRandomValue(1-config.rand_range, 1+config.rand_range))
            elif self.relaxationtype is relaxtyp.T2:      
                self.datavals[i] = (1 - 0.5*np.log10(float(self.T_vals[i]))) * self.getRandomValue(1-config.rand_range, 1+config.rand_range)
            else:
                self.datavals[i] = i

    def getResult(self):
        FF = FitFunction(self.relaxationtype, self.T_vals, self.datavals)
        self.relaxationTime = FF.relaxationTime
        self.fitParameters = FF.fitParameters
        self.r2Metric = FF.r2Metric
        self.fitXAxis = FF.fitXAxis
        self.fitYAxis = FF.fitYAxis

# Class for fitting relaxation curve (partially by David Schote)
class FitFunction:
    def __init__(self, relaxationtype: str, T_vals: list, datapoints: np.ndarray, bounds=None):
        """
        Initialization of FitFunction class
        @param relaxationtype:  Relaxation type (T1/T2)
        @param T_vals:          Time values (TI, TE, ...)
        @param datapoints:      Measured datapoints
        @param bounds:          Boundaries (optional)
        """

        # map input
        self.numDatapoints = len(datapoints)
        self.numFitpoints = self.numDatapoints * config.fitting_precision * config.fitting_overshot
        self.relaxationtype = relaxationtype
        
        # check fitting is possible
        error = False
        if self.relaxationtype is not relaxtyp.T1 and self.relaxationtype is not relaxtyp.T2:
            self.parent.parent.OpMngr.setOutput('Unknown relaxation time requested!')
            error = True
        if self.numDatapoints < config.min_fitpoints:
            self.parent.parent.OpMngr.setOutput('Not enough data to calculate fit!')
            error = True
        if len(T_vals) is not self.numDatapoints:
            self.parent.parent.OpMngr.setOutput('Number of given time values does not match number of given data points!')
            error = True
        if error:
            return

        # functionality
        self.calculateRelaxationTime(T_vals, datapoints, bounds)
        # gives self.fitParameters, self.relaxationTime, self.fitYAxis/ X

    @staticmethod
    def fit_t1RelaxationTime(t, A, B, C):
        return abs(A - B * np.exp(-C * t))

    @staticmethod
    def fit_t2RelaxationTime(t, A, B, C):
        return A + B * np.exp(-C * t)

    def getFunctionValues(self, T_vals, func, fitParameters):
        res = []
        for t in T_vals:
            res.append(func(t, *fitParameters))
        return res
    
    def getListDifference(self, list1, list2):
        res = []
        lenn = min(len(list1), len(list2))
        for i in range(0, lenn):
            res.append(list1[i] - list2[i])
        return res
    
    def getListSquare(self, list1):
        res = []
        for x in list1:
            res.append(x*x)
        return res
    
    # since exponential curve fitted to (absolute of) signal, need to inverse before finding zero-crossing
    def removeAbs(self, datapoints):
        minind = np.argmin(datapoints)
        for i in range(0, minind):
            datapoints[i] = -datapoints[i]
        return datapoints

    def calculateRelaxationTime(self, T_vals: list, datapoints: np.ndarray, bounds=None):
        # Calculate relaxation time and fit data
        # @param T_vals:         Time values in ms (TI, TE)
        # @param datapoints:      Acquired datapoints
        # @param bounds:          Boundaries (optional)

        # X values of fitted function
        self.fitXAxis: np.ndarray = np.linspace(0, int(T_vals[-1] * config.fitting_overshot), int(self.numFitpoints))
        self.fitXAxis = [round(x, config.roundToDigits) for x in self.fitXAxis]

        # Calculate T1 relaxation time
        if self.relaxationtype is relaxtyp.T1:
            if bounds is not None and len(bounds) == 6:
                fitParameters, _ = curve_fit(self.fit_t1RelaxationTime, T_vals, datapoints,
                                         bounds=([bounds[0], bounds[2], bounds[4]],
                                                 [bounds[1], bounds[3], bounds[5]]))
            else:
                fitParameters, _ = curve_fit(self.fit_t1RelaxationTime, T_vals, datapoints)

            def _fit(x: float) -> float:
                return float(fitParameters[0] - fitParameters[1] * np.exp(-fitParameters[2] * x))

            # Calculate relaxation time (brentq gives zero of function)
            self.relaxationTime: float = round(config.one_over_ln2 * brentq(_fit, T_vals[0], T_vals[-1]), config.roundToDigits)
            # Calculate r2 error metric
            f_vals = self.getFunctionValues(T_vals, self.fit_t1RelaxationTime, fitParameters)
            self.r2Metric: float  = round(1 - (np.sum(self.getListSquare(self.getListDifference(datapoints, f_vals)))) / 
                                    np.sum(self.getListSquare(datapoints - np.mean(datapoints))), config.roundToDigits)
            # Y values of fitted function
            self.fitYAxis: np.ndarray = self.getFunctionValues(self.fitXAxis, self.fit_t1RelaxationTime, fitParameters)
            self.fitYAxis = [round(y, config.roundToDigits) for y in self.fitYAxis]

        else:  # Calculate T2 relaxation time
            if bounds is not None and len(bounds) == 6:
                fitParameters, _ = curve_fit(self.fit_t2RelaxationTime, T_vals, datapoints,
                                          bounds=([bounds[0], bounds[2], bounds[4]],
                                                  [bounds[1], bounds[3], bounds[5]]))
            else:
                fitParameters, _ = curve_fit(self.fit_t2RelaxationTime, T_vals, datapoints)
            # Calculate relaxation time
            self.relaxationTime: float = round(-(1 / fitParameters[2]) * np.log(((config.one_over_e * (fitParameters[0] + fitParameters[1]))
                                                                     - fitParameters[0]) / fitParameters[1]), config.roundToDigits)
            # Calculate r2 error metric
            f_vals = self.getFunctionValues(T_vals, self.fit_t2RelaxationTime, fitParameters)
            self.r2Metric: float  = round(1 - (np.sum(self.getListSquare(self.getListDifference(datapoints, f_vals)))) /
                                       np.sum(self.getListSquare(datapoints - np.mean(datapoints))), config.roundToDigits)
            # Y values of fitted function
            self.fitYAxis: np.ndarray  = self.getFunctionValues(self.fitXAxis, self.fit_t2RelaxationTime, fitParameters)
            self.fitYAxis = [round(y, config.roundToDigits) for y in self.fitYAxis]

        self.fitParameters: np.ndarray = fitParameters
        self.fitParameters = [round(p, config.roundToDigits) for p in self.fitParameters]