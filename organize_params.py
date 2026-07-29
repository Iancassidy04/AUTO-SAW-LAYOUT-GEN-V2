# Ian Cassidy - PARAMETER TABLE FOR AUTO GENERATED STEPPED SAW LAYOUT
# 2026 AUG 29

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def print_saw_parameters(params):
    console = Console()

    table = Table(
        title="SAW Device Design Parameters",
        show_header=True,
        header_style="bold cyan",
        title_style="bold magenta"
    )

    table.add_column("Category", style="bold yellow")
    table.add_column("Parameter")
    table.add_column("Value", justify="right")
    table.add_column("Units", style="green")

    for category, values in params.items():
        first = True

        for param, data in values.items():
            value, units = data

            table.add_row(
                category if first else "",
                param,
                str(value),
                units
            )

            first = False

    return console.print(Panel(table, expand=False))

def saw_param(MAT, V, Eps_R,
          NF, F_WIDTH, GAP, PITCH, L, APER, TH,
          F0, M, MF0,
          C0, Z, MR):
    
    saw_device = {

        "Substrate": {
            "Material": (MAT, ""),
            "SAW Velocity": (V, "m/s"),
            "Dielectric Constant": (Eps_R, "\n"),
        },

        "IDT Geometry": {
            "Finger Pairs": (NF, ""),
            "Finger Width": (F_WIDTH, "µm"),
            "Finger Gap": (GAP, "µm"),
            "Pitch": (PITCH, "µm"),
            "Wavelength": (L, "µm"),
            "Aperture": (APER, "µm"),
            "Metal Thickness": (TH, "nm\n"),
        },

        "Frequency": {
            "Fundamental Frequency": (F0, "MHz"),
            "Target Harmonic": (M, ""),
            "Harmonic Frequency": (MF0, "GHz\n"),
        },

        "Electrical": {
            "IDT Capacitance": (C0, "pF"),
            "Input Impedance": (round(Z, 3), "jΩ"),
            "Metallization Ratio": (MR, ""),
        }
    }
    return print_saw_parameters(saw_device)
