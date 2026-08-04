# SAWGEN2 - Surface Acoustic Wave Device Layout Generator

## Overview

SAWGEN2 is a Python-based Surface Acoustic Wave (SAW) device layout generation tool.

The generator is designed for the generation of:

- Single SAW devices
- SAW device arrays
- Parameter sweeps over device dimensions

Generated layouts are compatible with standard IC layout tools such as KLayout.



# Repository Structure

```
├── SAWGEN2_FULL.py
│   └── Main Python layout generation script
│
├── SINGLE DEVICE
│   └── Generated single-device layouts
│
├── SINGLE DEVICE W PADS
│   └── Single devices including GSG pads
│
├── SAW ARRAY NO PADS
│   └── Array layouts without pads
│
├── SAW ARRAY W PADS
│   └── Array layouts with GSG pads
│
├── LAYOUTS
│   └── Final/exported GDS files
│
├── Example
│   └── Example generated layouts
│
└── OLD FILES FOR REFERENCE
    └── Previous versions and archived files
```

---

# Installation

## Requirements

Python version:

```
Python >= 3.10
```

Required packages:

```
numpy
gdstk
tkinter
```

---

# Usage

Run the generator with:

```
python SAWGEN2_FULL.py
```

A GUI will open for the user to:

1. Modify geometry values
2. Select sweep variable
3. Set step size and number of iterations
4. Save and run

---

# Features

## Parameterized Device Generation

The device geometry can be controlled through a parameter dictionary:

```python
IDT_PARAMS = {
    "L": 8,
    "MR": 0.5,
    "W": 200,
    "APO": 2,
    "BBH": 80,
    "NF": 100,
    ...
}
```

---

---

# Parameter Sweeps

Supported sweep variables:

- Wavelength
- Metallization Ratio
- Finger Length
- Apodization
- Bus Bar Height
- Number of Fingers
- Input/Output spacing

---

# Generated Layouts

The generator creates:

- IDT
- Bus bars
- GSG pads
- txt file with important layout information

Output format:

```
GDSII (.gds)
```

---

# Example Device

<img width="905" height="957" alt="image" src="https://github.com/user-attachments/assets/f84dc191-0f9e-470f-8496-9440f5495dca" />

---

# Author

**Ian Cassidy**

Electrical Engineering Masters Student  
University of Vermont

Research focus:

- Surface Acoustic Wave devices
- Wireless sensing
- Piezoelectric resonator fabrication
