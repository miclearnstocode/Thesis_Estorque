[Setup]
AppName=ComputerStudies
AppVersion=1.1.2
DefaultDirName={pf}\ComputerStudies
DefaultGroupName=ComputerStudies
OutputDir=.
OutputBaseFilename=ComputerStudiesInstaller
Compression=lzma
SolidCompression=yes
DisableDirPage=no
LicenseFile="license_agreement.txt"
InfoBeforeFile="info_before.txt"
UninstallDisplayIcon={app}\Main.exe
UninstallDisplayName=ComputerStudies
SetupIconFile="Image\CSD.ico"
WizardImageFile="Image\Capiz_State_University 2.bmp"
VersionInfoVersion=1.2.2
VersionInfoCompany=Computer Science Department
VersionInfoDescription=ComputerStudies Application

[Files]
Source: "Image\CSD.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "thesis_copy\dist\Main\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Icons]
Name: "{group}\ComputerStudies"; Filename: "{app}\Main.exe"; IconFilename: "{app}\CSD.ico"
Name: "{commondesktop}\ComputerStudies"; Filename: "{app}\Main.exe"; IconFilename: "{app}\CSD.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Main.exe"; Description: "Launch ComputerStudies"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Welcome to the ComputerStudies Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nIt is recommended that you close all other applications before continuing.
FinishedLabel=Setup has finished installing [name/ver] on your computer.