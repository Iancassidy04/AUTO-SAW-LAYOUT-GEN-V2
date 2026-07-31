# Ian Cassidy
# GENERATED SAW LAYOUT FROM DESIGN PARAMETERS
# 2026 AUG 29

# GDS Libraries
import gdstk as gd
lib = gd.Library()

# Operating system / file libraries
from pathlib import Path
import os
import numpy as np
global L, MR, W, APO, BBH, NF, INPUT_OUTPUT_SPACING, STEPPED, M, PW, PH, SEP, TYPE
def ITERATE(c, IDT_PARAMS):
    globals().update(IDT_PARAMS) # Pull global params from CTRL through LAYOUT DESIGN
    global STEPPED

    GEN_GSG(c, 1)
    GEN_GSG(c, 0 - 1)

    F_WIDTH = MR*(L/2)      # Finger width
    GAP = L/2 - F_WIDTH     # Finger Gap
    BBL = L                 # Bus bar length per finger pair
    PITCH = L/2             # Pos center to neg center

    x_i = 0
    # INPUT IDT - Will be stepped if stepped is defined above
    for ii in range(NF):
        x_i = x_i + BBL     # Adjust start

        # OUTPUT IDT - NEVER STEPPED even if defined
        if ii == int(NF/2):
            x_i = x_i + INPUT_OUTPUT_SPACING    # Shift start by IO spacing
            STEPPED = False

        if STEPPED == True:
            w = (W - APO) / M   # Length of steps (discludes bus bar connection)

            for i in range(M):
                D = i * (L / M)                 # Step Displacement
                FINGER_CNTR = x_i + L/8 + D     # Shift center step horz (L/8 for MR != 0.5)
                VERT_STRT = BBH + w*i           # New step start

                # Set horz bounds variable to finger width without altering PITCH
                LEFT_EDGE = FINGER_CNTR - (F_WIDTH / 2)
                RIGHT_EDGE = FINGER_CNTR + (F_WIDTH / 2)

                # Positive Finger (Connect Top BB)
                c.add(gd.rectangle((LEFT_EDGE, VERT_STRT + APO),                    # (BOT LEFT) Vert start dist(apodization) above BB add steps taken
                    (RIGHT_EDGE, VERT_STRT + w + APO * (1 + (apo_check(i, M)))),    # (TOP RIGT) Horz start point + pitch (EXTEND if by APO for BB connection on last step)
                    layer=1))

                # Negative Finger (Connect BOT BB)
                c.add(gd.rectangle((LEFT_EDGE + PITCH, VERT_STRT + APO * (1 - (apo_check(i - 1, M)))),      # (BOT LEFT) Shift horz by PITCH, extend first (bottom) step to BB
                                    (RIGHT_EDGE + PITCH, VERT_STRT + w + APO),                              # (TOP RIGT) Shift PITCH horz from right edge and up by finger step length (w)
                                    layer=1))

        # STANDARD IDT (ALWAYS OUTPUT)
        else:
            FINGER_CNTR = x_i + L/8                     # Center of first finger
            LEFT_EDGE = FINGER_CNTR - (F_WIDTH / 2)     # Edge relative to center variable with MR

            # Create pos finger
            c.add(gd.rectangle((LEFT_EDGE, BBH + APO),                  # (BOT LEFT) Start at HORZ LEFT EDGE, and VERT apodization above bus bar
                            (LEFT_EDGE + F_WIDTH, BBH + W + APO),       # (TOP RGHT) Right edge is a finger width left edge, extend vert by finger length (W)
                            layer=1))

            # Create neg finger
            c.add(gd.rectangle((LEFT_EDGE + PITCH, BBH),                # Shift by 1/2 Lambda, start VERT on BB
                            (LEFT_EDGE + PITCH + F_WIDTH, BBH + W),     # Shift HORZ additional width of finger, extend VERT length of finger (W)
                            layer=1))

        if ii == 0 and STEPPED:
            extender = (L*((M-1)/M)) - (L/8) + (F_WIDTH/2)      # Extends bus bar total displacement after all steps are taken for first finger and made variable with MR
        else:
            extender = 0

        # Create bottom bus bar
        c.add(gd.rectangle((LEFT_EDGE - extender, 0),           # Start bus bar at edge of pos finger
                        (LEFT_EDGE + BBL, BBH), 
                        layer=1))

        # Create upper bus bar
        c.add(gd.rectangle((LEFT_EDGE - extender, W + APO + BBH),            
                        (LEFT_EDGE + BBL, W + APO + 2*BBH),         # Create Top BB identical to, and fingerlenth + apodization above Bot BB 
                        layer=1))
        

def apo_check(x, M):
    return 1 if x == (M - 1) or x < 0 else 0    # Conditions for extension to BB conection

def offset(p, dx=0, dy=0):
    return (p[0] + dx, p[1] + dy)

def GEN_GSG(c, INV):
    PW_INV = PW * INV # INVERSION FOR MIRRORING
    TOTAL_BBL = L * NF
    HEIGHT = 2 * BBH + W + APO
    CORNER = (L + ((TOTAL_BBL) + INPUT_OUTPUT_SPACING) * (INV < 0),
        HEIGHT * (INV > 0))

    GRND_DIST = 1500
    CORNER_INV = offset(CORNER, 0, -INV * HEIGHT)
    CORNER_EXT = offset(CORNER_INV, -INV * GRND_DIST, PW_INV)
    print(CORNER)
    print(CORNER_EXT)
    print(CORNER_INV)
    print(INV)
    c.add(gd.rectangle(CORNER_INV, CORNER_EXT))

    for i in range(3):
        GRND_EXT = offset(CORNER, 0 - ((GRND_DIST) * INV * (i == 0)), 0)
        c.add(gd.rectangle(GRND_EXT, 
                           offset(CORNER, PW_INV, PW_INV))
            .translate(INV * i * SEP, PW_INV))


    a = offset(CORNER_EXT, PW_INV, 0)
    b =offset(a, 0 - PW_INV, HEIGHT * INV)

    c.add(gd.rectangle(a ,b ))