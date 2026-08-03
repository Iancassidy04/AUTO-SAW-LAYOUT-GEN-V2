# Ian Cassidy
# Set array layout and directory structure
# 2026 AUG 29

# GDS LAYOUT LIBRARIES
import gdstk as gd
from PAD_ARRAY_GEN import ITERATE # Python file

# Operating system / file libraries
from pathlib import Path
import os

import numpy as np
lib = gd.Library()

def REMOTE_VAR_CTRL(VAR, VAL, IDT_PARAMS, USE_DECLARATION):
    global L, W, APO, BBH, NF, INPUT_OUTPUT_SPACING, STEPPED, HSPACE, VSPACE, NAME, STEP, ITS

    # Move variable labeling from ARRAY_CTRL
    var_map = {
    'Wavelength': 'L',
    'Metallization Ratio': 'MR',
    'Finger Length': 'W',
    'Apodization': 'APO',
    'Bus Bar Height': 'BBH',
    'Number of Fingers': 'NF',
    'Input Output Spacing': 'INPUT_OUTPUT_SPACING',
    'Harmonic Mode': 'M',
    'STEPPED' : 'STEPPED',
    'Desired Harmonic Mode' : 'M',
    'Relative Horizontal Distance Between Devices' : 'HSPACE',
    'Relative Vertical Distance Between Devices' : 'VSPACE',
    'File Name' : 'NAME',
    'Incremental Step Size' : 'STEP',
    'Number of Devices' : 'ITS'
    }

    IDT_PARAMS[var_map[VAR]] = max(VAL) # Assign max value for device seperation calc
    globals().update(IDT_PARAMS)

    # Device area for seperation
    TOTAL_SAW_WIDTH = ((L * NF) + INPUT_OUTPUT_SPACING) * 2 * HSPACE
    TOTAL_SAW_HEIGHT = ((2 * BBH) + APO + W) * 2 * VSPACE

    IDT_PARAMS[var_map[VAR]] = VAL # Assign range for iteration

    # Global Label
    if STEPPED:
        GL = 'STEPPED_ARRAY'
    else:
        GL = 'STANDARD_ARRAY'

    # Name folder, file and GDS cell
    folder_name = f"{NAME}"
    layout_name = f"{VAR}_{min(VAL)}_to_{max(VAL)}_{GL}.gds"

    if USE_DECLARATION:
        use_folder = 'LAYOUTS'
    else:
        use_folder = 'TEST and JUNK'

    ROWS = int(np.sqrt(ITS))    # Predict ROW count
    COLS = int(ITS / ROWS)      # Set COL count
    REM = ITS - (ROWS * COLS)   # Calculate remainder for ROW count adjustment

    matrix = [[(TOTAL_SAW_WIDTH * i, TOTAL_SAW_HEIGHT * j)  # Device coordinate matrix
            for j in range(COLS)] 
            for i in range(ROWS + 1)] # Temp add row

    top = lib.new_cell("TOP") # Create main cell

    START = min(VAL) # Starting bound for step count
    ii = 0 # Initialize 0 value
    for row in range(ROWS + 1):
        for col in range(COLS):
            if row < ROWS or row == ROWS and col < REM: # Check for remainder
                VAL = START + (ii * STEP)               # Increase step count by runs relative to VAR lower bound
                IDT_PARAMS[var_map[VAR]] = VAL          # Reset value of VAR in params

                c = lib.new_cell(f'{VAL}_{VAR}_{NAME}') # Create cell for increment
                ITERATE(c, IDT_PARAMS)                  # Generate layout in new cell from updated paramters

                x, y = matrix[row][col]             # Find device coordinates in array
                top.add(gd.Reference(c, (x, y)))    # Create cell on top layer

                ii +=1  # Increase run count

    script_dir = Path(__file__).parent                  # Find active directory
    folder_path = script_dir / use_folder / folder_name 

    os.makedirs(folder_path, exist_ok=True)             # Create folder if it doesn't exist
    filename = os.path.join(folder_path, layout_name)   # Create path
    lib.write_gds(filename)

    # Save parameter text file
    txt_path = folder_path / f"{layout_name}_device_info.txt"

    width = max(len(name) for name in var_map)

    with open(txt_path, "w") as f:
        f.write("Device Parameters\n")
        f.write("-" * (width + 20) + "\n\n")

        for display_name, key in var_map.items():
            f.write(f"{display_name:<{width}} : {IDT_PARAMS[key]}\n\n")