[Setup]
AppName=GradesWatch
AppVersion=1.0
DefaultDirName={pf}\GradesWatch
DefaultGroupName=GradesWatch
OutputDir=.
OutputBaseFilename=GradesWatchInstaller
Compression=lzma
SolidCompression=yes
DisableDirPage=no
LicenseFile="license_agreement.txt"
InfoBeforeFile="info_before.txt"
UninstallDisplayIcon={app}\student_grades.exe
UninstallDisplayName=GradesWatch
SetupIconFile="icons\gradeicon.ico"
WizardImageFile="Image\Capiz_State_University 2.bmp"
VersionInfoVersion=1.0.0
VersionInfoCompany=Computer Science Department
VersionInfoDescription=GradesWatch Application

[Files]
Source: "icons\gradeicon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "thesis_copy\dist\student_grades\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Icons]
Name: "{group}\GradesWatch"; Filename: "{app}\student_grades.exe"; IconFilename: "{app}\gradeicon.ico"
Name: "{commondesktop}\GradesWatch"; Filename: "{app}\student_grades.exe"; IconFilename: "{app}\gradeicon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\student_grades.exe"; Description: "Launch GradesWatch"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Welcome to the GradesWatch Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nIt is recommended that you close all other applications before continuing.
FinishedLabel=Setup has finished installing [name/ver] on your computer.