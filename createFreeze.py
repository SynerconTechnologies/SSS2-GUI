import sys
import os

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","tkinter"],
                         "include_files": ["sss2angle.gif",
                                           "SynerconLogoWithName300.gif",
                                           "SynerconLogoWithName.gif",
                                           "SynerconLogo.gif",
                                           "SSS2Pins.gif"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "SSS2 Interface App",
        version = "1.0.5",
        description = "A graphical user interface for the Smart Sensor Simulator 2 from Synercon Technologies.",
        options = {"build_exe": build_exe_options},
        executables = [Executable("SSS2-Interface.py", base=base)])
