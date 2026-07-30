# Ian Cassidy
# 2026 AUG 29
# Choose/Alter Variable Parameters for Iterative Device Design (ARRAY_LAYOUT_DES.py)

NAME = '2026_AUG_30'         # Name of ARRAY

# Variable Designation
VAR = 'Wavelength'      # Var_map Label
LOW = 2                 # Start Value (Disable LOW or HIGH with "None" for range_cal)
HIGH = 8                # Stop Value
STEP_SIZE = 0.25
# ITS = 24              # ONLY SET FOR range_cal

'''
LIST OF DESIGN PARAMETERS FOR LAYOUT DESIGN VARIABLE MAP
=======================================================

'Wavelength'
'Metalization Ratio'
'Finger Length'
'Apodization'
'Bus Bar Height'
'Number of Fingers'
'Input Output Spacing'
'Harmonic Mode'

'''


def ITS_cal(LOW, HIGH):
    ITS = int((HIGH - LOW) / STEP_SIZE) + 1 # Rounding can cause layout errors
    return ITS

def range_cal(LOW, HIGH):
    if LOW:
        HIGH = LOW + (STEP_SIZE * ITS)
    else:
        LOW = HIGH - (STEP_SIZE * ITS) # Avoid choosing upperbound, possible negative # errors
    return LOW, HIGH

# Calculate bound if missing
if LOW == None or HIGH == None:
    LOW, HIGH = range_cal(LOW, HIGH)

else:
    DEVICES = ITS_cal(LOW, HIGH)

VAR_RANGE = [LOW, HIGH] # Save bounds

# Print iterative data
print(f'Iterations: {DEVICES - 1}')
print(f'Step Size: {STEP_SIZE}')
print(f'Range : {LOW} - {HIGH}\n')
print('=========================\n')

# Standard params will be overwritten by VAR
IDT_PARAMS = {
    "L": 8,
    "MR": 0.5,
    "W": 200,
    "APO": 2,
    "BBH": 80,
    "NF": 100,
    "INPUT_OUTPUT_SPACING": 80,
    "STEPPED": True,
    "M": 5,
    "HSPACE": 1,
    "VSPACE": 1,
    "NAME" : "PARAM_TEST",
    "STEP" : STEP_SIZE,
    "ITS" : DEVICES
}

# Pass variable information to layout design
from ARRAY_LAYOUT_DES import REMOTE_VAR_CTRL
REMOTE_VAR_CTRL(VAR, VAR_RANGE, IDT_PARAMS)
