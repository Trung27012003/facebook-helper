#ifndef AppVersion
  #define AppVersion "0.11.0"
#endif
[Setup]
AppId=FacebookHelperHR
AppName=Facebook Helper
AppVersion={#AppVersion}
AppPublisher=Trung27012003
AppPublisherURL=https://github.com/Trung27012003/facebook-helper
AppUpdatesURL=https://github.com/Trung27012003/facebook-helper/releases/latest
DefaultDirName={localappdata}\Programs\FacebookHelper
DefaultGroupName=Facebook Helper
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=FacebookHelper-Setup-x64
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\FacebookHelper.exe
WizardStyle=modern
SetupLogging=yes
[Tasks]
Name: desktopicon; Description: "Tạo lối tắt trên màn hình"; Flags: unchecked
[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal\playwright\driver\package\.local-browsers"
[Files]
Source: "..\dist\FacebookHelper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Facebook Helper"; Filename: "{app}\FacebookHelper.exe"
Name: "{autodesktop}\Facebook Helper"; Filename: "{app}\FacebookHelper.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\FacebookHelper.exe"; Description: "Mở Facebook Helper"; Flags: nowait postinstall skipifsilent

[Messages]
ButtonNext=&Tiếp tục >
ButtonBack=< &Quay lại
ButtonInstall=&Cài đặt
ButtonFinish=&Hoàn tất
ButtonCancel=&Hủy
