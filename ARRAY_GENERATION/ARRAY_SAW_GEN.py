# Ian Cassidy - AUTO GENERATED STEPPED SAW LAYOUT
# 2026 AUG 29

# GDS Libraries
import gdstk as gd
lib = gd.Library()

# Operating system / file libraries
from pathlib import Path
import os

import numpy as np

def ITERATE(ITERATION, c, IDT_PARAMS):
    global L, MR, W, APO, BBH, NF, INPUT_OUTPUT_SPACING, STEPPED, M
    globals().update(IDT_PARAMS)

    F_WIDTH = MR*(L/2)  # Finger width
    GAP = L/2 - F_WIDTH # Finger Gap
    BBL = L             # Bus bar length per finger pair
    PITCH = L/2         # Pos center to neg center

    x_i = 0   
    # INPUT IDT - Will always be stepped if stepped is defined above
    for ii in range(NF):
        x_i = x_i + BBL                 # Adjust start

        # OUTPUT IDT
        if ii == int(NF/2):
            x_i = x_i + INPUT_OUTPUT_SPACING    # Shift start by IO spacing
            STEPPED = False                     # Will never be stepped even if defined

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
                    (RIGHT_EDGE, VERT_STRT + w + APO * (1 + (apo_check(i, M)))),    # (TOP RIGT) Horz start point + pitch (EXTEND if by APO for BB connection on last step)
                    layer=1))

                # Create negative finger
                c.add(gd.rectangle((LEFT_EDGE + PITCH, VERT_STRT + APO * (1 - (apo_check(i - 1, M)))),      # (BOT LEFT) Shift horz by pitch, extend first (bottom) step to BB
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
    return


def apo_check(x, M):
    return 1 if x == (M - 1) or x < 0 else 0            # Conditions for BB conection
