"""
Data Manager

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   1.0.2
@change:    02/11/2020

@summary:   Class for managing the data procession of acquired data.
            Processes data in time (t_) and frequency (f_) domain.
"""

# system includes
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
from dataclasses import dataclass
import numpy as np

# project includes
from config import configvars

@dataclass(repr=False, eq=False)
class DataManager(QObject):
    # Init signal that's emitted when readout is processed
    t1_finished = pyqtSignal()
    t2_finished = pyqtSignal()
    uploaded = pyqtSignal(bool)

    __slots__ = ['t_magnitude',
                 't_real',
                 't_imag',
                 't_axis',
                 'f_axis',
                 'f_fftData',
                 'f_fftMagnitude']

    def __init__(self, data: np.complex, f_Ex: float, numSamples: int, f_range: int = 250000):
        """
        Initialisation of data manager class
        @param data:        Raw data
        @param numSamples:  number of samples
        @param f_range:     Range of frequency spectrum
        """
        super(DataManager, self).__init__()
        self.data = data
        self.f_Ex = f_Ex
        self.numSamples = numSamples
        self.f_range = f_range
        self.T_sampling = self.numSamples * configvars.timePerSample  # time axis for plotting

        d_cropped = self.data[0:self.numSamples]  # crop datastream to specified number of numSamples
        self.t_axis = np.linspace(0, self.T_sampling, self.numSamples)
        self.t_magnitude = np.abs(d_cropped)
        self.t_magnitudeConvolved = np.convolve(self.t_magnitude, np.ones((50,)) / 50, mode='same')
        self.t_real = np.real(d_cropped)
        self.t_realConvolved = np.convolve(self.t_real, np.ones((50,)) / 50, mode='same')
        self.t_imag = np.imag(d_cropped)
        
        self.f_axis = np.linspace(-self.f_range / 2, self.f_range / 2, self.numSamples)
        self.f_fftData = np.fft.fftshift(np.fft.fft(np.fft.fftshift(d_cropped), n=self.numSamples))
        self.f_fftMagnitude = abs(self.f_fftData)

    def is_evaluateable(self) -> bool:
        """
        Check if acquired data is evaluateable
        @return:    Evaluateable (true/false)
        """
        minValue = min(self.f_fftMagnitude)
        maxValue = max(self.f_fftMagnitude)
        return (maxValue - minValue) > 1

    @property
    def get_sign(self) -> int:
        """
        Get sign of real part signal in time domain
        @return:    Sign
        """
        index: np.ndarray = np.argmin(self.t_realCon[0:self.numSamples])
        return np.sign(self.t_realCon[index])

    def get_peakparameters(self) -> [float, float, int, float]:
        """
        Get peak parameters
        @return:     index of frequency peak, frequency peak value, frequency of peak, time domain peak value
        """
        if not self.is_evaluateable():
            return [float("nan"), float("nan"), 0, float("nan")]

        t_signalValue: float = round(np.max(self.t_magnitudeCon), configvars.roundToDigits)
        f_signalValue: float = round(np.max(self.f_fftMagnitude), configvars.roundToDigits)
        f_signalIdx: int = np.argmax(self.f_fftMagnitude)
        f_signalFrequency: float = round(self.f_Ex + ((f_signalIdx - self.numSamples / 2)
                                                            * self.f_range / self.numSamples) / 1.0e6, configvars.roundToDigits)
        return [f_signalIdx, f_signalValue, f_signalFrequency, t_signalValue]

    def get_fwhm(self, f_fwhmWindow: int = 1000) -> [int, float, float]:
        """
        Get full width at half maximum
        @param f_fwhmWindow:    Frequency window
        @return:                FWHM in datapoint indices, hertz and ppm
        """
        if not self.is_evaluateable():
            return [0, float("nan"), float("nan")]

        [peakIdx, peakValue, peakFreq, _] = self.get_peakparameters()
        fft_window = self.f_fftMagnitude[int(peakIdx - f_fwhmWindow / 2):int(peakIdx + f_fwhmWindow / 2)]
        candidates: np.ndarray = np.abs([x - peakValue / 2 for x in fft_window])
        # Calculate index difference by find indices of minima, calculate fwhm in Hz thereafter
        winC = int(f_fwhmWindow / 2)
        fwhm: int = np.argmin(candidates[winC:-1]) + winC - np.argmin(candidates[0:winC])
        fwhm_hz: float = fwhm * (abs(np.min(self.f_axis)) + abs(np.max(self.f_axis))) / self.numSamples
        fwhm_ppm: float = fwhm_hz / peakFreq

        return [fwhm, fwhm_hz, fwhm_ppm]

    def get_snr(self, f_windowfactor: float = 10) -> float:
        """
        Get signal to noise ratio
        @param f_windowfactor:  Factor for fwhm to define peak window
        @param n:               N datapoints for moving average
        @return:                SNR
        """
        if not self.is_evaluateable():
            return float("nan")

        [fwhm, _, _] = self.get_fwhm()
        [_, peakValue, _, _] = self.get_peakparameters()
        peakWindow = int(fwhm * f_windowfactor)
        winC = int(len(self.f_fftData) / 2)
        noiseBorder = int(len(self.f_fftData) * 0.05)
        noiseFloor = np.concatenate((self.f_fftData[noiseBorder:int(winC - peakWindow / 2)],
                                      self.f_fftData[int(winC + peakWindow / 2):-1 - noiseBorder]))
        noise = np.std(noiseFloor / peakValue)
        snr = round(1 / noise)
        return snr


