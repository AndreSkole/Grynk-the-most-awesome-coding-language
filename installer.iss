[Setup]
AppName=Grynk Programming Language
AppVersion=1.0.0
AppPublisher=Grynk
DefaultDirName={autopf}\Grynk
DefaultGroupName=Grynk
OutputDir=dist
OutputBaseFilename=Grynk_Windows_Installer
Compression=lzma2
SolidCompression=yes
ChangesEnvironment=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\grynk.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "vscode-extension\grynk-lang-1.0.0.vsix"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "addtopath"; Description: "Add Grynk to system PATH (lets you run 'grynk' in any terminal)"; GroupDescription: "Additional tasks:"; Flags: checkablealone
Name: "vscodesync"; Description: "Install VS Code Extension (Syntax highlighting and icon)"; GroupDescription: "Additional tasks:"; Flags: checkablealone

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{cmd}"; Parameters: "/c """"code"" --install-extension ""{app}\grynk-lang-1.0.0.vsix"""""; Description: "Installing VS Code Extension..."; Flags: runhidden; Tasks: vscodesync; Check: IsVSCodeInstalled

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

function IsVSCodeInstalled: Boolean;
var
  ErrorCode: Integer;
begin
  Result := Exec(ExpandConstant('{cmd}'), '/c code --version', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode) and (ErrorCode = 0);
end;
