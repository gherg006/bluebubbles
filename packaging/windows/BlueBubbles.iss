#define MyAppName "BlueBubbles"
#define MyAppPublisher "BlueBubbles"
#define MyAppExeName "BlueBubbles.exe"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#ifndef SourceDirectory
  #define SourceDirectory "..\..\dist\BlueBubbles"
#endif

[Setup]
AppId={{B9274E54-57A6-4C55-AE1C-C40F23EF96C8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\BlueBubbles
DefaultGroupName=BlueBubbles
OutputBaseFilename=BlueBubbles-{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
WizardStyle=modern

[Files]
Source: "{#SourceDirectory}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BlueBubbles"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\BlueBubbles"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch BlueBubbles"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; User profiles under LocalAppData are deliberately preserved to prevent data loss.
Type: filesandordirs; Name: "{app}"
