# Ian Cassidy - AUTO GENERATED MULTEPLE SAW LAYOUTS
# 2026 AUG 29
import numpy as np

# GDS LAYOUT LIBRARIES
import gdstk as gd
from ITERATE_IDT_GEN import ITERATE # Python file

# Operating system / file libraries
from pathlib import Path
import os

lib = gd.Library()
# IDT Dimensions (ALL in um)
L = 8                           # Lambda
MR = 0.5                        # Metalization Ratio
W = 200                         # Finger length
APO = 2                         # Apodization
BBH = 80                        # Bus bar height
NF = 100                         # Number of Fingers Pairs
INPUT_OUTPUT_SPACING = L * 10   # Last input finger to first finger

STEPPED = True      # IDT Type
M = 5               # Desired Harmonic mode if IDT is stepped
ITS = 11                    # Number of devices

# Vertical and horzontal spacing factor (1 = one full device pair)
HSPACE = 1
VSPACE = 1

    
# Device area for seperation
TOTAL_SAW_WIDTH = ((L * NF) + INPUT_OUTPUT_SPACING) * 2 * HSPACE
TOTAL_SAW_HEIGHT = ((2 * BBH) + APO + W) * 2 * VSPACE

# Global Label
if STEPPED:
    GL = 'STEPPED_ARRAY'
else:
    GL = 'STANDARD_ARRAY'

# Name folder, file and GDS cell
folder_name = f"ITS{NAME}{GL}_GEN"
layout_name = f"{VAR}{ITS}{GL}.gds"

ROWS = int(np.sqrt(ITS))  # Variable length
COLS = int(ITS / ROWS)
REM = ITS - (ROWS * COLS)

matrix = [[(TOTAL_SAW_WIDTH * i, TOTAL_SAW_HEIGHT * j) 
        for j in range(COLS)] 
        for i in range(ROWS + 1)]

top = lib.new_cell("TOP")
for i in range(ITS):
    c = lib.new_cell(f'{VAR}{i}_{NAME}')
    
    ITERATE(STEPPED, NAME, i, c,
            L, MR, W, APO, BBH, NF, 
            INPUT_OUTPUT_SPACING, GL, M)
    
    for row in range(ROWS + 1):
        for col in range(COLS):
            if row == ROWS and col < REM or row < ROWS:
                x, y = matrix[row][col]
                top.add(gd.Reference(c, (x, y)))

script_dir = Path(__file__).parent                  # Find active directory
folder_path = script_dir / folder_name 

os.makedirs(folder_path, exist_ok=True)             # Create folder if it doesn't exist
filename = os.path.join(folder_path, layout_name)   # Create path
lib.write_gds(filename)


