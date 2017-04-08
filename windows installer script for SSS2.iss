; -- Example1.iss --
; Demonstrates copying 3 files and creating an icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=SSS2-GUI
AppVersion=1.0
DefaultDirName={pf}\SSS2-GUI
DefaultGroupName=SSS2-GUI
UninstallDisplayIcon={app}\SSS2-GUI.exe
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:SSS2 Control Program

[Files]
Source: "dist\*"; DestDir: "{app}"
Source: "dist\SSS2-Interface\*"; DestDir: "{app}\SSS2-Interface"
Source: "dist\tcl\*"; DestDir: "{app}\tcl"

[Icons]
Name: "{group}\SSS2"; Filename: "{app}\SSS2-GUI.exe"
