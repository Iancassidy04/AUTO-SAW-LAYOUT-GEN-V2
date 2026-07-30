
VAR = 'Wavelength'          # Changing variable
LOW = 2
HIGH = 8
STEP_SIZE = 0.25

'''

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
    ITS = int((HIGH - LOW) / STEP_SIZE) + 1
    print(ITS)
    return ITS

def range_cal(LOW, HIGH):
    ITS = 24
    if LOW:
        HIGH = LOW + (STEP_SIZE * ITS)
    else:
        LOW = HIGH - (STEP_SIZE * ITS)
    return LOW, HIGH


# LOW, HIGH = range_cal(2, None)
VAR_RANGE = [LOW, HIGH]
DEVICES = ITS_cal(LOW, HIGH)
NAME = '2026_AUG_7'         # Name of ARRAY

print(f'Iterations: {DEVICES}')
print(f'Step Size: {STEP_SIZE}')
print(f'Range : {LOW} - {HIGH}\n')
print('=========================\n')

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
from ARRAY_LAYOUT_DES import REMOTE_VAR_CTRL
REMOTE_VAR_CTRL(VAR, VAR_RANGE, IDT_PARAMS)
