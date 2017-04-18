# A Graphical User Interface for the Smart Sensor Simulator 2
A Python tkinter GUI for the SSS2 that sends and recieves serial commands to the SSS2 over USB

## Window Executable
A zip file with the Windows Executable is available here:

https://www.dropbox.com/s/1xc5nckzy8wxag3/SSS2-GUI-Interface.zip?dl=0


## Developer Requirements
1. Install Python 3.4 ```https://www.python.org/downloads/release/python-343/```
   1. Open a command prompt by typing `cmd` in the Windows start menu.
   2. Upgrade pip: ```py -3.4 -m pip install --upgrade pip```
   3. Install PySerial: ```py -3.4 -m pip install pyserial```
   4. Install py2exe: ```py -3.4 -m pip install py2exe```
2. Install the Teensy USB drivers from https://www.pjrc.com/teensy/serial_install.exe
3. Download Github Desktop from https://desktop.github.com/
4. Clone this repository in Github Desktop to work on it.
5. Package the Python sources using ```py -3.4 -m py2exe SSS2-Interface.py```
6. Copy all graphics files into the newly created dist and build directories
7. Zip the dist directory for distribution. You can double click the SSS2-Interface.exe program in the dist directory to run.
8. TODO: use Inno windows installer to create an installer. http://www.jrsoftware.org/isdl.php#qsp
