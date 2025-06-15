[Setup]
AppName=ComputerStudies
AppVersion=1.1
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
Source: "dist\Main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "thesis_copy\*"; DestDir: "{app}\thesis_copy"; Flags: ignoreversion recursesubdirs createallsubdirs

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

[Code]
function IsDotNet40Installed: Boolean;
var
  Key: string;
  InstallValue: Cardinal;
begin
  Key := 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full';
  Result := RegQueryDWordValue(HKEY_LOCAL_MACHINE, Key, 'Install', InstallValue) and (InstallValue = 1);
end;

function InitializeSetup(): Boolean;
begin
  if not IsDotNet40Installed then
  begin
    MsgBox('ComputerStudies requires .NET Framework 4.0 or higher. Please install it and try again.' + #13#10 +
           'You can download it from: https://dotnet.microsoft.com/download/dotnet-framework', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
