"""
Global Variables and Objects

@author:    David Schote
@reworked by: Sula Mueller
@contact:   david.schote@ovgu.de
@version:   1.0.2
@change:    02/11/2020

@summary:   Global variables
"""

# instances for handy importing
class globals:
    
    class Sequences:
        # class with predefined sequences as file locations

        class SequenceFile:
            def __init__(self, name, path):
                self.str = name
                self.path = path
                self.get_Tname()

            def get_Tname(self):
                self.T_name = 'TE'
                if self.str == 'Inversion Recovery' or self.str == 'Saturation Inversion Recovery':
                    self.T_name = 'TI'

        FID = SequenceFile('Free Induction Decay', 'sequence/FID.txt')
        SE = SequenceFile('Spin Echo', 'sequence/SE_te.txt')
        IR = SequenceFile('Inversion Recovery', 'sequence/IR_ti.txt')
        SIR = SequenceFile('Saturation Inversion Recovery', 'sequence/SIR_ti.txt')
        imgSE = SequenceFile('Spin Echo for Imaging', 'sequence/img/2DSE.txt')

    class ScanParameters:
        f_Ex = 'f_Ex'
        numSamples = 'numSamples'

    class GradientDims:
        X = 0
        Y = 1
        Z = 2
        Z2 = 3

    class RelaxationTypes:
        T1 = 'T1'
        T2 = 'T2'

    class ProjectionAxes:
        x = 0
        y = 1
        z = 2

    class StyleSheets:
        breezeDark = "view/stylesheets/breeze-dark.qss"
        breezeLight = "view/stylesheets/breeze-light.qss"

    class GlobalNamespace:
        f_Ex = "Excitation Frequency"
        f_range = "Frequency Range"
        T_sampling = "Sampling Time"
        numSamples = "Number of Samples"
        G_x = "X Gradient"
        G_y = "Y Gradient"
        G_z = "Z Gradient"
        G_z2 = "Z² Gradient"
        sequencefile = "sequencefile"
        sequencebytestream = "sequencebytestream"
        sequenceType = "Type of Sequence"
        T_val = "Time Value"
        TE = "TE"
        TI = "TI"
        gradwaveform = "Gradient Waveform"
        attenuation = "Attenuation"
        shim = "Gradient Shim Values"

        # for relaxometry
        numTimeValues = 'number of time values'
        numSamplesPerTimeValue = 'number of samples per measurement'
        numAveragesPerTimeValue ='number of averages per time value'
        TI_min = 'TI_min'
        TI_max = 'TI_max'
        TE_min = 'TE_min'
        TE_max = 'TE_max'

    class ReconstructionTypes:
        spectrum = "1D FFT"
        kspace = "2D FFT"
