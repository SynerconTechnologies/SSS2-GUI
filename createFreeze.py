import sys
import os

from cx_Freeze import setup, Executable

os.environ['TCL_LIBRARY'] = r'C:\Users\dailyadmin\AppData\Local\Programs\Python\Python36-32\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\dailyadmin\AppData\Local\Programs\Python\Python36-32\tcl\tk8.6'

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os","tkinter"],
                         "include_files": ["sss2angle.gif",
                                           "SynerconLogoWithName300.gif",
                                           "SynerconLogoWithName.gif",
                                           "SynerconLogo.gif",
                                           "SSS2Pins.gif"]}

if sys.platform == "win32":
    base = "Win32GUI"

target = Executable(
    script="SSS2-Interface.py",
    base="Win32GUI",
    icon="SynerconLogo.ico"
    )

setup(  name = "SSS2 Interface App",
        version = "1.0.9",
        description = "A graphical user interface for the Smart Sensor Simulator 2 from Synercon Technologies.",
        options = {"build_exe": build_exe_options},
        executables = [target])
