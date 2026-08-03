# Ian Cassidy
# 2026 AUG 3
# FULL SAWGEN2 With User Interface

import tkinter as tk
from tkinter import ttk
import numpy as np

# GDS Libraries
import gdstk as gd
lib = gd.Library()

# Operating system / file libraries
from pathlib import Path
import os

# Parameters
IDT_PARAMS = {
    "NAME": "Example",
    "L": 80,
    "MR": 0.5,
    "W": 2000,
    "APO": 20,
    "BBH": 80,
    "NF": 100,
    "INPUT_OUTPUT_SPACING": 80,
    "STEPPED": False,
    "M": 5,
    "HSPACE": 1,
    "VSPACE": 1,
    "STEP": 0.25,
    "ITS": 1,
    "PW": 80,
    "PH": 80,
    "SEP": 100,
    "TYPE": "GSG",
    "START": 80,
    "PAD_BB_SEP": 80,
    "GND_DIST": 1500
}

# Display names
var_map = {
    'File Name': 'NAME',
    'Wavelength': 'L',
    'Metallization Ratio': 'MR',
    'Finger Length': 'W',
    'Apodization': 'APO',
    'Bus Bar Height': 'BBH',
    'Number of Fingers': 'NF',
    'Input Output Spacing': 'INPUT_OUTPUT_SPACING',
    'STEPPED': 'STEPPED',
    'Desired Harmonic Mode': 'M',
    'Relative Horizontal Distance Between Devices': 'HSPACE',
    'Relative Vertical Distance Between Devices': 'VSPACE',
    'Incremental Step Size': 'STEP',
    'Number of Devices': 'ITS',
    'Start Value': 'START',
    'Pad Width': 'PW',
    'Pad Height': 'PH',
    'Pad Separation': 'SEP',
    'Pad Type': 'TYPE',
    'Distance from Pads to Bus Bar': 'PAD_BB_SEP',
    "Distance Ground Travels from IDT": "GND_DIST"
}

# Organize GUI
sections = {
    "General": [
        "NAME",
    ],

    "IDT Geometry": [
        "L",
        "MR",
        "W",
        "APO",
        "BBH",
        "NF",
        "INPUT_OUTPUT_SPACING",
    ],

    "Electrical/Layout": [
        "M",
        "STEPPED",
        "PW",
        "PH",
        "SEP",
        "PAD_BB_SEP",
        "GND_DIST",
        "TYPE",
        "HSPACE",
        "VSPACE",
    ]
}

# Parameters that can be swept
sweep_options = {
    "Wavelength": "L",
    "Metallization Ratio": "MR",
    "Finger Length": "W",
    "Apodization": "APO",
    "Bus Bar Height": "BBH",
    "Number of Fingers": "NF",
    "Input Output Spacing": "INPUT_OUTPUT_SPACING",
}

# Create Window
root = tk.Tk()
root.title("SAWGEN2 Parameter Input")

root.geometry("500x800")  
widgets = {}                # Store GUI variables

row = 0
for section_name, params in sections.items():
    section = ttk.LabelFrame(root, text=section_name, padding=10)
    section.grid(row=row, column=0, padx=10, pady=5, sticky="ew")

    row += 1
    section_row = 0

    for param in params:
        display_name = [
            k for k, v in var_map.items()
            if v == param
        ][0]

        ttk.Label(section, text=display_name).grid(row=section_row, column=0, padx=5, pady=3, sticky="w")
        value = IDT_PARAMS[param]

        # Boolean checkbox
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            ttk.Checkbutton(section, variable=var).grid(row=section_row, column=1)

        # Text/numbers
        else:
            var = tk.StringVar(value=str(value))
            ttk.Entry(section, textvariable=var, width=15).grid(row=section_row, column=1)

        widgets[param] = var
        section_row += 1

# Parameter Sweep Section
sweep_frame = ttk.LabelFrame(root, text="Parameter Sweep", padding=10)
sweep_frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
row += 1

# Variable selection
ttk.Label(sweep_frame, text="Variable").grid(row=0, column=0, padx=5, pady=5)
VAR = ttk.Combobox(sweep_frame, values=list(sweep_options.keys()), state="readonly")
VAR.grid(row=0, column=1)
VAR.current(0)

# Step size
ttk.Label(sweep_frame, text="Step Size").grid(row=1, column=0)
step_entry = ttk.Entry(sweep_frame)
step_entry.insert(0, str(IDT_PARAMS["STEP"]))
step_entry.grid(row=1, column=1)

# Iterations
ttk.Label(sweep_frame, text="Iterations").grid(row=2, column=0)
iteration_entry = ttk.Entry(sweep_frame)
iteration_entry.insert(0, str(IDT_PARAMS["ITS"]))
iteration_entry.grid(row=2, column=1)

# Start value
ttk.Label(sweep_frame, text="Start Value").grid(row=3, column=0)
start_entry = ttk.Entry(sweep_frame)
start_entry.insert(0, str(IDT_PARAMS["START"]))
start_entry.grid(row=3, column=1)

def save_parameters():
    # Update normal parameters
    for key, var in widgets.items():
        old_value = IDT_PARAMS[key]

        if isinstance(old_value, bool):
            IDT_PARAMS[key] = var.get()

        elif isinstance(old_value, int):
            IDT_PARAMS[key] = int(var.get())

        elif isinstance(old_value, float):
            IDT_PARAMS[key] = float(var.get())

        else:
            IDT_PARAMS[key] = var.get()

    # Update sweep parameters
    IDT_PARAMS["VAR"] = sweep_options[VAR.get()]
    IDT_PARAMS["STEP"] = float(step_entry.get())
    IDT_PARAMS["ITS"] = int(iteration_entry.get())
    IDT_PARAMS["START"] = int(start_entry.get())

    print("\nUpdated Parameters:")
    for key, value in IDT_PARAMS.items():
        name = next((k for k, v in var_map.items() if v == key), key)
        print(f"{name:40} : {value}")
            
    root.destroy() # Close window

# Save Button
ttk.Button(root, text="Save Parameters", command=save_parameters).grid(row=row, column=0, pady=15)

root.mainloop()

for key, value in IDT_PARAMS.items():
    globals()[key] = value

# Device area for seperation
TOTAL_SAW_WIDTH = ((L * NF) + INPUT_OUTPUT_SPACING) * 2 * HSPACE
TOTAL_SAW_HEIGHT = ((2 * BBH) + APO + W) * 2 * VSPACE

# Global Label
if STEPPED:
    GL = 'STEPPED_ARRAY'
else:
    GL = 'STANDARD_ARRAY'

STOP = START + ITS * STEP           # Stopping bound for sweep

# Name folder, file and GDS cell
folder_name = f"{NAME}"
layout_name = f"{VAR}_{START}_to_{STOP}_{GL}.gds"


ROWS = int(np.sqrt(ITS))    # Predict ROW count
COLS = int(ITS / ROWS)      # Set COL count
REM = ITS - (ROWS * COLS)   # Calculate remainder for ROW count adjustment

matrix = [[(TOTAL_SAW_WIDTH * i, TOTAL_SAW_HEIGHT * j)  # Device coordinate matrix
        for j in range(COLS)] 
        for i in range(ROWS + 1)] # Temp add row

def ITERATE(c):
    GEN_GSG(c, 1)
    GEN_GSG(c, 0 - 1)
    global STEPPED
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
    return 1 if x == (M - 1) or x < 0 else 0            # Conditions for BB conection

def offset(p, dx=0, dy=0):
    return (p[0] + dx, p[1] + dy)

def GEN_GSG(c, INV):
    # INVERSION FOR MIRRORING
    PW_M = PW * INV
    PH_M = PH * INV
    SEP_M = SEP * INV
    PAD_BB_M = PAD_BB_SEP * INV

    TOTAL_BBL = L * NF
    HEIGHT = 2 * BBH + W + APO
    CORNER = (L + ((TOTAL_BBL) + INPUT_OUTPUT_SPACING) * (INV < 0),     # Starting Point for Pads
        HEIGHT * (INV > 0))                                         # Top left for Input, bottom right for output

    CORNER_EXT = offset(CORNER, -INV * GND_DIST, PW_M)                      # Point that BB extends to (HORZ) for GND connect
    c.add(gd.rectangle(CORNER, CORNER_EXT).translate(0, PAD_BB_M))          # Create PAD Extension for GND connect
    c.add(gd.rectangle(CORNER, CORNER_EXT).translate(0, -INV * HEIGHT))     # Create BB Extension for GND connect

    for i in range(3):
        PH_M = PH_M * (1 + (i != 1))        # Extend height for first and third pad

        c.add(gd.rectangle(CORNER, offset(CORNER, PW_M, PH_M))
                                        .translate(i * SEP_M, PAD_BB_M))    # Create PADs

        PH_M = PH * INV # Reset height
        
    c.add(gd.rectangle(CORNER, offset(CORNER, 2 * SEP_M + PW_M, PH_M))      # GND - GND Connector
                                        .translate(0, 3 * PH_M))
      
    # Connect both HORZ GND extensions
    GND_VERT_A = offset(CORNER_EXT, PW_M, 0)
    GND_VERT_B = offset(GND_VERT_A, 0 - PW_M, HEIGHT * -INV)
    c.add(gd.rectangle(GND_VERT_A, GND_VERT_B))    

top = lib.new_cell("TOP") # Create main cell
ii = 0 # Initialize 0 value

for row in range(ROWS + 1):
    for col in range(COLS):
        if row < ROWS or row == ROWS and col < REM: # Check for remainder
            IDT_PARAMS[IDT_PARAMS["VAR"]] =  START + (ii * STEP)   # Assign max value for device seperation calc
            VAL = IDT_PARAMS[IDT_PARAMS["VAR"]]
            globals().update(IDT_PARAMS)
            c = lib.new_cell(f'{VAL}_{VAR}_{NAME}') # Create cell for increment
            ITERATE(c)                  # Generate layout in new cell from updated paramters

            x, y = matrix[row][col]             # Find device coordinates in array
            top.add(gd.Reference(c, (x, y)))    # Create cell on top layer

            ii +=1  # Increase run count

script_dir = Path(__file__).parent                  # Find active directory
folder_path = script_dir  / folder_name 

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