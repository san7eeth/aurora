#ifndef AppVersion
  #define AppVersion "0.3.0"
#endif

#define AppName "Aurora Assistant"
#define AppExe "Aurora.exe"

[Setup]
AppId={{2C4724CC-57E1-4E06-9E9E-A0947D42E6CE}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Aurora
DefaultDirName={localappdata}\Programs\Aurora
DefaultGroupName=Aurora Assistant
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\release\installer
OutputBaseFilename=Aurora-Setup-{#AppVersion}-x64
SetupIconFile=..\assets\aurora.ico
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\..\release\Aurora\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Aurora Assistant"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"
Name: "{autodesktop}\Aurora Assistant"; Filename: "{app}\{#AppExe}"; IconFilename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\Start-Aurora.ps1"""; Description: "Start Aurora Assistant"; Flags: postinstall runasoriginaluser skipifsilent

[UninstallRun]
Filename: "{app}\{#AppExe}"; Parameters: "--shutdown"; Flags: runhidden waituntilterminated; RunOnceId: "StopAurora"
