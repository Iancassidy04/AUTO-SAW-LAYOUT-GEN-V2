# Ian Cassidy - AUTO GENERATED STEPPED SAW LAYOUT
# 2026 AUG 29

# GDS Libraries
import gdstk as gd
lib = gd.Library()

# Operating system / file libraries
from pathlib import Path
import os

from CTRL_IDT_GEN import saw_param # Table Script
import numpy as np

# Name folder, file and GDS cell
folder_name = "SAW_GEN_V2_OUTPUT"
layout_name = "test1.gds"
cell_name = "2026_Aug_29"

# SAW device parameters

# IDT Dimensions (ALL in um)
L = 8               # Lambda
MR = 0.5            # Metalization Ratio
F_WIDTH = MR*(L/2)  # Finger width
GAP = L/2 - F_WIDTH # Finger Gap
W = 200             # Finger length
APO = 2             # Apodization

INPUT_OUTPUT_SPACING = L * 10   # Dista between the inner most finger on the input (farthest right) and output (farthest left)

# PAD/Bus Bar Dimensions
BBH = 10            # Bus bar height
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

# Frequency
F0 = V / L      # Fundamental Frequency
STEPPED = True  # IDT Type
M = 5           # Desired Harmonic mode if IDT is stepped
MF0 = F0 * M    # Frequency of Mth mode

# Electrical
CS = 30 # pF/cm                             # Capacitance per unit area
C0 = 4 * CS * NF * APER*1e-4                # Electrical Capacitance of IDT
ZC = 1 / (2 * np.pi * F0*1e6 * C0*1e-12)    # Impedance due to capacitance

# Make nice table (CTRL_IDT_GEN.py) using RICH library
saw_param(MAT, V, EPS_R,
          NF, F_WIDTH, GAP, PITCH, L, APER, TH,
          F0, M, MF0,
          C0, ZC, MR)

c = lib.new_cell(cell_name)     # New Cell
x_i = 0                         # Starting point

def creat_saw(ii):

    if STEPPED:
        w = (W - APO) / M   # Length of steps (not including bus bar connection)

        for i in range(M):
            D = i * (L / M)         # Step Displacement
            FINGER_CNTR = x_i + L/8 + D    # Shift center step horz (L/8 for MR != 0.5)
            VERT_STRT = BBH + w*i        # New step start

            # Set horz bounds variable to finger width without altering PITCH
            LEFT_EDGE = FINGER_CNTR - (F_WIDTH / 2)
            RIGHT_EDGE = FINGER_CNTR + (F_WIDTH / 2)

            # Create positive finger
            c.add(gd.rectangle((LEFT_EDGE, VERT_STRT + APO),                 # (BOT LEFT) Vert start dist(apodization) above BB add steps taken
                (RIGHT_EDGE, VERT_STRT + w + APO * (1 + (apo_check(i)))),    # (TOP RIGT) Horz start point + pitch (EXTEND if by APO for BB connection on last step)
                  layer=1))

            # Create negative finger
            c.add(gd.rectangle((LEFT_EDGE + PITCH, VERT_STRT + APO * (1 - (apo_check(i - 1)))),      # (BOT LEFT) Shift horz by pitch, extend first (bottom) step to BB
                                (RIGHT_EDGE + PITCH, VERT_STRT + w + APO),                           # (TOP RIGT) Shift by 
                                layer=1))

    else:

        FINGER_CNTR = x_i + L/8                 # Center of first finger
        LEFT_EDGE = FINGER_CNTR - (F_WIDTH / 2) # Edge relative to center variable with MR

        # Create pos finger
        c.add(gd.rectangle((LEFT_EDGE, BBH + APO),                  # (BOT LEFT) Start at HORZ LEFT EDGE, and VERT apodization above bus bar
                           (LEFT_EDGE + F_WIDTH, BBH + W + APO),    # (TOP RGHT) Right edge is a finger width left edge, extend vert by finger length (W)
                           layer=1))

        # Create neg finger
        c.add(gd.rectangle((LEFT_EDGE + PITCH, BBH),                # Shift by 1/2 Lambda, start VERT on BB
                           (LEFT_EDGE + PITCH + F_WIDTH, BBH + W),  # Shift HORZ additional width of finger, extend VERT length of finger (W)
                           layer=1))

    if ii == 0 and STEPPED:
        extender = (L*((M-1)/M)) - (L/8) + (F_WIDTH/2) # Extends bus bar total displacement after all steps are taken for first finger and made variable with MR
    else:
        extender = 0

    # Create bottom bus bar
    c.add(gd.rectangle((LEFT_EDGE - extender, 0),               # Start bus bar at edge of pos finger
                       (LEFT_EDGE + BBL, BBH), 
                       layer=1))

    # Create upper bus bar
    c.add(gd.rectangle((LEFT_EDGE - extender, W + APO + BBH),            
                       (LEFT_EDGE + BBL, W + APO + 2*BBH),      # Create Top BB identical to, and fingerlenth + apodization above Bot BB 
                       layer=1))


def apo_check(x):
    return 1 if x == (M - 1) or x < 0 else 0            # Conditions for BB conection

def save_file():
    script_dir = Path(__file__).parent                  # Find active directory
    folder_path = script_dir / folder_name 

    os.makedirs(folder_path, exist_ok=True)             # Create folder if it doesn't exist
    filename = os.path.join(folder_path, layout_name)   # Create path
    lib.write_gds(filename)


NF_p = int(NF / 2)   # Number of Finger Pairs in each IDT

# INPUT IDT - Will always be stepped if stepped is defined above
for i in range(NF_p):
    creat_saw(i)
    x_i = x_i + BBL                 # Adjust start

# OUTPUT IDT
x_i = x_i + INPUT_OUTPUT_SPACING    # Shift start by IO spacing
STEPPED = False                     # Will never be stepped even if defined
for i in range(NF_p):
    creat_saw(i)
    x_i = x_i + BBL

save_file()