"""
Config File

@author:    Sula Mueller
@version:   1.0.0
@change:    02/11/2020

@summary: set some hardcoded variables
"""

class configvars:
    # define clock frequency of connection
    fpga_clk_frequency_MHz = 125

    # sampling time
    timePerSample = 4e-3

    # rounding to how many digits
    roundToDigits = 4

    # for polynomial fitting
    fitting_overshot = 1.2
    fitting_precision = 100  # multiplyer for number of fit points
    min_fitpoints = 5

    # for randomized example data
    rand_range = 0.1
    maxExampleDataval = 0.8  # max Signal
    minExampleDataval = -0.4  # min Signal before absolute

    # natural constants
    one_over_ln2: float = 1.4427
    one_over_e: float = 0.3679