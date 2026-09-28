#!/usr/bin/env python3
"""
Aplicación de escritorio para consultar los planes de gestión.

Uso:
    python ejecutar.py          (Windows)
    python3 ejecutar.py         (macOS / Linux)

Requisitos: Python 3.8 o superior. No necesita instalar ninguna librería:
usa solo la biblioteca estándar (tkinter viene incluido en Python para Windows
y macOS).
"""
import sys

if sys.version_info < (3, 8):
    sys.exit('Se requiere Python 3.8 o superior.')

try:
    import tkinter  # noqa: F401
except ImportError:
    sys.exit(
        'No se encontró tkinter.\n'
        '  - Windows/macOS: reinstale Python desde python.org marcando "tcl/tk and IDLE".\n'
        '  - Ubuntu/Debian: sudo apt install python3-tk'
    )

from planes.ventana import Aplicacion

if __name__ == '__main__':
    app = Aplicacion()
    try:
        app.mainloop()
    except tkinter.TclError:
        pass
