# Ian Cassidy - AUTO GENERATED STEPPED SAW LAYOUT
# 2026 AUG 29

# GDS Libraries
import gdstk as gd
lib = gd.Library()

# Operating system / file libraries
from pathlib import Path
import os

from organize_params import saw_param # Table making
import numpy as np

GL = 'STANDARD'

# Name folder, file and GDS cell
folder_name = f"{GL}_LAYOUT_SAWGEN2"
layout_name = f"{GL}_TEST.gds"
cell_name = "2026_Aug_30"

# SAW device parameters

# IDT Dimensions (ALL in um)
L = 80              # Lambda
MR = 0.5            # Metalization Ratio
F_WIDTH = MR*(L/2)  # Finger width
GAP = L/2 - F_WIDTH # Finger Gap
W = 2000             # Finger length
APO = 2             # Apodization

INPUT_OUTPUT_SPACING = L * 10   # Dista between the inner most finger on the input (farthest right) and output (farthest left)

# PAD/Bus Bar Dimensions
BBH = 80            # Bus bar height
BBL = L             # Bus bar length per finger pair

# Material Properties
MAT = "128° YX LiNbO3"  # Crystal Cut
V = 3990                # Velocity (m/s)
EPS_R = 46              # Relative Permativity

# IDT Geometry
NF = 30             # Number of Fingers Pairs
PITCH = L/2         # Pos center to neg center
APER = W - 2*APO    # Total finger overlap
TH = 100            # Metal thickness (nm)

# Pad Geometry
PW = 80     # Width of pad
PH = PW
SEP = 100   # Separation between pad centers

while PW > BBH + APO:
    print("Ground connection shorts to signal finger, increase bus bar height or enter '0' to change pad height.")
    new_val = input(f"BBH must be greater than {PW}.\nOld BBH: {BBH}\nNew BBH:")
    if new_val == "0":
        new_val = input(f"\nOld Pad Height: {PW}\nNew PH:")
        PH = int(new_val)
    else:
        BBH = int(new_val)

# Frequency
F0 = V / L      # Fundamental Frequency

# Electrical
CS = 30 # pF/cm                             # Capacitance per unit area
C0 = 4 * CS * NF * APER*1e-4                # Electrical Capacitance of IDT
ZC = 1 / (2 * np.pi * F0*1e6 * C0*1e-12)    # Impedance due to capacitance

# Make table (CTRL_IDT_GEN.py) using RICH library
saw_param(MAT, V, EPS_R,
          NF, F_WIDTH, GAP, PITCH, L, APER, TH,
          F0, None, None,
          C0, ZC, MR)

c = lib.new_cell(cell_name)     # New Cell
x_i = 0                         # Starting point

def creat_saw():

    FINGER_CNTR = x_i + L/8                 # Center of first finger
    LEFT_EDGE = FINGER_CNTR - (F_WIDTH / 2) # Edge relative to center variable with MR

    # Create pos finger
    c.add(gd.rectangle((LEFT_EDGE, BBH + APO),                  # (BOT LEFT) Start at HORZ LEFT EDGE, and VERT apodization above bus bar
                        (LEFT_EDGE + F_WIDTH, BBH + W + APO),   # (TOP RGHT) Right edge is a finger width left edge, extend vert by finger length (W)
                        layer=1))

    # Create neg finger
    c.add(gd.rectangle((LEFT_EDGE + PITCH, BBH),                # Shift by 1/2 Lambda, start VERT on BB
                        (LEFT_EDGE + PITCH + F_WIDTH, BBH + W), # Shift HORZ additional width of finger, extend VERT length of finger (W)
                        layer=1))

    # Create bottom bus bar
    c.add(gd.rectangle((LEFT_EDGE, 0),                          # Start bus bar at edge of pos finger
                        (LEFT_EDGE + BBL, BBH), 
                        layer=1))

    # Create upper bus bar
    c.add(gd.rectangle((LEFT_EDGE, W + APO + BBH),            
                        (LEFT_EDGE + BBL, W + APO + 2*BBH),     # Create Top BB identical to, and fingerlenth + apodization above Bot BB 
                        layer=1))


def save_file():
    script_dir = Path(__file__).parent                  # Find active directory
    folder_path = script_dir / folder_name 

    os.makedirs(folder_path, exist_ok=True)             # Create folder if it doesn't exist
    filename = os.path.join(folder_path, layout_name)   # Create path
    lib.write_gds(filename)


def offset(p, dx=0, dy=0):
    return (p[0] + dx, p[1] + dy)

GND_DIST = 1500                                             # Distance GND connect moves (HORZ) away from SAW
PAD_BB_SEP = 80                                             # Distance from pads to nearest BB
def GEN_GSG(INV):
    PW_M = PW * INV # INVERSION FOR MIRRORING
    PH_M = PH * INV
    SEP_M = SEP * INV
    PAD_BB_M = PAD_BB_SEP * INV

    TOTAL_BBL = L * NF
    HEIGHT = 2 * BBH + W + APO
    CORNER = (((TOTAL_BBL) + INPUT_OUTPUT_SPACING) * (INV < 0),     # Starting Point for Pads
        HEIGHT * (INV > 0))                                         # Top left for Input, bottom right for output



    CORNER_EXT = offset(CORNER, -INV * GND_DIST, PW_M)                            # Point that BB extends to (HORZ) for GND connect
    c.add(gd.rectangle(CORNER, CORNER_EXT).translate(0, PAD_BB_M))          # Create PAD Extension for GND connect
    c.add(gd.rectangle(CORNER, CORNER_EXT).translate(0, -INV * HEIGHT))             # Create BB Extension for GND connect

    for i in range(3):
        PH_M = PH_M * (1 + (i != 1))

        c.add(gd.rectangle(CORNER, offset(CORNER, PW_M, PH_M))
                                        .translate(i * SEP_M, PAD_BB_M))

        PH_M = PH * INV
        
    c.add(gd.rectangle(CORNER, offset(CORNER, 2 * SEP * INV + PW_M, PH_M))      # GND - GND Connector
                                        .translate(0, 3 * PH_M))
      
    # Connect both HORZ GND extensions
    GND_VERT_A = offset(CORNER_EXT, PW_M, 0)
    GND_VERT_B = offset(GND_VERT_A, 0 - PW_M, HEIGHT * -INV)
    c.add(gd.rectangle(GND_VERT_A, GND_VERT_B))                 


NF_p = int(NF / 2)   # Number of Finger Pairs in each IDT

# INPUT IDT
for i in range(NF_p):
    GEN_GSG(1)
    creat_saw()
    x_i = x_i + BBL                 # Adjust start


# OUTPUT IDT
x_i = x_i + INPUT_OUTPUT_SPACING    # Shift start by IO spacing
for i in range(NF_p):
    GEN_GSG(-1)
    creat_saw()
    x_i = x_i + BBL

save_file()