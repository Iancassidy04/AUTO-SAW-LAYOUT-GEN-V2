# Ian Cassidy - AUTO GENERATED MULTEPLE SAW LAYOUTS
# 2026 AUG 29
import numpy as np

# GDS LAYOUT LIBRARIES
import gdstk as gd
from ARRAY_SAW_GEN import ITERATE # Python file

# Operating system / file libraries
from pathlib import Path
import os

lib = gd.Library()

def REMOTE_VAR_CTRL(VAR, VAL, IDT_PARAMS):
    global L, W, APO, BBH, NF, INPUT_OUTPUT_SPACING, STEPPED, HSPACE, VSPACE, NAME, STEP, ITS
    var_map = {
    'Wavelength': 'L',
    'Metalization Ratio': 'MR',
    'Finger Length': 'W',
    'Apodization': 'APO',
    'Bus Bar Height': 'BBH',
    'Number of Fingers': 'NF',
    'Input Output Spacing': 'INPUT_OUTPUT_SPACING',
    'Harmonic Mode': 'M',
    }

    IDT_PARAMS[var_map[VAR]] = max(VAL)
    globals().update(IDT_PARAMS)

    # Device area for seperation
    TOTAL_SAW_WIDTH = ((L * NF) + INPUT_OUTPUT_SPACING) * 2 * HSPACE
    TOTAL_SAW_HEIGHT = ((2 * BBH) + APO + W) * 2 * VSPACE

    IDT_PARAMS[var_map[VAR]] = VAL

    for i in IDT_PARAMS:
        print(i)

    # Global Label
    if STEPPED:
        GL = 'STEPPED_ARRAY'
    else:
        GL = 'STANDARD_ARRAY'

    # Name folder, file and GDS cell
    folder_name = f"AUTO_ARRAY_V2_{GL}"
    layout_name = f"{VAR}{min(VAL)}_to_{max(VAL)}{GL}.gds"

    ROWS = int(np.sqrt(ITS))  # Variable length
    COLS = int(ITS / ROWS)
    REM = ITS - (ROWS * COLS)

    matrix = [[(TOTAL_SAW_WIDTH * i, TOTAL_SAW_HEIGHT * j) 
            for j in range(COLS)] 
            for i in range(ROWS + 1)]

    top = lib.new_cell("TOP")

    START = min(VAL)

    ii = 0
    for row in range(ROWS + 1):
        for col in range(COLS):
            if row == ROWS and col < REM or row < ROWS:
                VAL = START + (ii * STEP)
                IDT_PARAMS[var_map[VAR]] = VAL
                print(IDT_PARAMS[var_map[VAR]])
                c = lib.new_cell(f'{VAL}_{VAR}_{NAME}')
                
                ITERATE(i, c, IDT_PARAMS)
                x, y = matrix[row][col]
                top.add(gd.Reference(c, (x, y)))
                ii +=1

    script_dir = Path(__file__).parent                  # Find active directory
    folder_path = script_dir / folder_name 

    os.makedirs(folder_path, exist_ok=True)             # Create folder if it doesn't exist
    filename = os.path.join(folder_path, layout_name)   # Create path
    lib.write_gds(filename)
    return filename

