"""
Communication Manager

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   1.0.2
@change:    02/11/2020

@summary:   Manages the connection to the server, constructs and sends packages (via msgpack)
"""
# system includes
from PyQt5.QtNetwork import QAbstractSocket, QTcpSocket
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from warnings import warn
import numpy as np
import struct
import msgpack

# project includes
from config import configvars
from globalvars import globals

nmspc = globals.GlobalNamespace

# define possible states of the console
states = {
    QAbstractSocket.UnconnectedState: "Unconnected",
    QAbstractSocket.HostLookupState: "Host Lookup",
    QAbstractSocket.ConnectingState: "Connecting",
    QAbstractSocket.ConnectedState: "Connected",
    QAbstractSocket.BoundState: "Bound",
    QAbstractSocket.ClosingState: "Closing Connection",
}

# get the current state
status = QAbstractSocket.SocketState

# Commands Class for Marcos-Server
class Commands:
    fpgaClock = 'fpga_clk' # array of 3 values unsigned int (clock words)
    localOscillatorFrequency = 'lo_freq' # unsigned int (local oscillator freq. for TX/RX)
    txClockDivider = 'tx_div' # unsigned int (clock divider for RF TX samples)
    rfAmplitude = 'rf_amp' # unsigned int 16 bit (RF amplitude)
    rxRate = 'rx_rate' # unsigned int 16 bit (tx sample rate???)
    txSampleSize = 'tx_size' # unsigned int 16 bit (number of TX samples to return)
    txSamplesPerPulse = 'tx_samples' # unsigned int (number of TX samples per pulse)
    gradientOffsetX = 'grad_offs_x' # unsigned int (X gradient channel shim)
    gradientOffsetY = 'grad_offs_y' # unsigned int (Y gradient channel shim)
    gradientOffsetZ = 'grad_offs_z' # unsigned int (Z gradient channel shim)
    gradientMemoryX = 'grad_mem_x' # binary byte array (write X gradient channel memory)
    gradientMemoryY = 'grad_mem_y' # binary byte array (write Y gradient channel memory)
    gradientMemoryZ = 'grad_mem_z' # binary byte array (write Z gradient channel memory)
    recomputeTxPulses = 'recomp_pul' # boolean (recompute the TX pulses)
    txRfWaveform = 'raw_tx_data' # binary byte array (write the RF waveform)
    sequenceData = 'seq_data' # binary byte array (sequence instructions)
    runAcquisition = 'acq' # unsigned int [numSamples] (runs 'seq_data' and returns array of 64-bit complex floats, length = numSamples)
    testRxThroughput = 'test_throughput' # unsigned int [arg] (return array map, array-length = arg)
    requestPacket = 0

class CommunicationManager(QTcpSocket, QObject):
    statusChanged = pyqtSignal(str, name='onStatusChanged')

    def __init__(self):
        super(CommunicationManager, self).__init__()
        self.stateChanged.connect(self.getConnectionStatus)

    def connectClient(self, IP: str) -> [bool]:  # this is the function being debugged right now
        """
        Connect server and host through server's IP
        @param IP:  IP address of the server
        @return:    success of connection
        """
        
        self.connectToHost(IP, 1001)
        self.waitForConnected(2000)
        if self.state() == QAbstractSocket.ConnectedState:
            print("Connection to server established.")
            return True
        else:
            print("Connection to server failed.")
            return False

    def disconnectClient(self) -> bool:
        """
        Disconnects server and host
        @return:    success of disconnection
        """
        self.disconnectFromHost()
        if self.state() is QAbstractSocket.UnconnectedState:
            print("Disconnected from server.")
            return True
        else:
            return False

    @pyqtSlot(status)
    def getConnectionStatus(self, state: status = None) -> None:
        if state in states:
            self.statusChanged.emit(states[state])
        else:
            self.statusChanged.emit(str(state))

    def waitForTransmission(self) -> None:
        while True:  # Wait until bytes are written on server 
            if not self.waitForBytesWritten():
                break

    @staticmethod
    def constructScanParameterPacket(operation) -> dict:
        packet: dict = {}

        if hasattr(operation, 'scanparameters'):
            scanparams = operation.scanparameters
            for key in list(scanparams.keys()):
                if key == nmspc.f_Ex:
                    freq = int(np.round(scanparams[key][0] / configvars.fpga_clk_frequency_MHz * (1 << 30)))
                    # third element of scanparams is cmd.localOscillatorFrequency
                    packet[scanparams[key][2]] = freq & 0xfffffff0 | 0xf
                    continue
        return packet

    @staticmethod
    def constructSequencePacket(operation) -> dict:
        package: dict = {}

        if hasattr(operation, 'sequence') and len(operation.sequence) > 1:
            package[Commands.sequenceData] = operation.sequence[nmspc.sequencebytestream]
        else:
            warn("ERROR: No sequence bytestream!")
        return package

    def sendPacket(self, packet):
        if self.state() != QAbstractSocket.ConnectedState:
            print("No connection to server, doing nothing")
            return
        self.write(msgpack.packb(packet))
        unpacker = msgpack.Unpacker()
        self.waitForReadyRead(1000)

        while True:
            buf = self.read(100)
            if not buf:
                break
            unpacker.feed(buf)
            for i in unpacker:
                return i  # quit function after 1st reply

    def setFrequency(self, f_Ex: float) -> None:
        """
        Set excitation frequency on the server
        @param f_Ex:    excitation frequency in MHz
        @return:        None
        """
        self.write(struct.pack('<I', 2 << 28 | int(1.0e6 * f_Ex)))
        print("Set excitation frequency!")

# initialize an instance
ComMngr = CommunicationManager()
