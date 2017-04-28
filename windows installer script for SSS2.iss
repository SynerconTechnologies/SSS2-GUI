; -- Example1.iss --
; Demonstrates copying 3 files and creating an icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=SSS2-Interface
AppVersion=0.9b
DefaultDirName={pf}\SSS2
DefaultGroupName=SSS2
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:SSS2
OutputBaseFilename=SetupSSS2Interface

[Files]
Source: "dist\*"; DestDir: "{app}"
Source: "dist\tcl\*"; DestDir: "{app}\tcl"
Source: "*.ico"; DestDir: "{app}"
Source: "*.gif"; DestDir: "{app}"
Source: "*.SSS2"; DestDir: "{app}"
Source: "serial_install.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\SSS2"; Filename: "{app}\SSS2-Interface.exe" ; WorkingDir: "{app}"

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; 
Name: quicklaunchicon; Description: "Create a &Quick Launch icon";

[Run]
Filename: "{app}\serial_install.exe"; Description: "Install Serial Drivers";
Filename: "{app}\SSS2-Interface.exe"; Description: "Launch application"; Flags: postinstall nowait skipifsilent unchecked