# A Graphical User Interface for the Smart Sensor Simulator 2
A Python tkinter GUI for the SSS2 that sends and recieves serial commands to the SSS2 over USB

## Building a Windows Executable
1. Install Python 3.4 ```https://www.python.org/downloads/release/python-343/```
   1. Open a command prompt by typing `cmd` in the Windows start menu.
   2. Upgrade pip: ```py -3.4 -m pip install --upgrade pip```
   3. Install PySerial: ```py -3.4 -m pip install pyserial```
   4. Install py2exe: ```py -3.4 -m pip install py2exe```
2. Install the Teensy USB drivers from https://www.pjrc.com/teensy/serial_install.exe
3. Download Github Desktop from https://desktop.github.com/
4. Clone this repository in Github Desktop to work on it.
5. Change the Universal Save Flag to false.
5. Package the Python sources into an executable using ```py -3.4 createExecutable.py py2exe```
6. Copy all graphics files into the newly created dist and build directories.
7. Use Inno windows installer to create a single executable file. http://www.jrsoftware.org/isdl.php#qsp
   1. Open the `windows installer script for SSS2.iss` file.
   2. Compile it.
   3. Find the executable in Documents/SSS2
   4. Rename the executable with the version number and post it to the web.
