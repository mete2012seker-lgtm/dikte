; Dikte kurucusu — Inno Setup 6
; Derleme: build.ps1 (önce PyInstaller, sonra bu dosya). Elle: ISCC.exe installer\Dikte.iss
; Çıktı: installer\Output\Dikte-Setup-<sürüm>.exe
; Sürüm: installer\version.iss (build.ps1 config.APP_VERSION'dan üretir) — tek kaynak config.py

#ifexist "version.iss"
  #include "version.iss"
#endif
#ifndef AppVersion
  #define AppVersion "1.6.0"
#endif

#define AppName "Dikte"
#define AppExe "Dikte.exe"
#define MyAppExeName "Dikte.exe"

[Setup]
; AppId sabit olmalı; her sürümde aynı kalır, güncelleme ve kaldırma bu kimlikle eşleşir.
AppId={{FAACF175-562C-4213-8E04-3A90AEA600AA}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Dikte
; Kurulum yeri Program Files; yönetici izni gerekir (karar 2026-11-07).
DefaultDirName={autopf}\Dikte
DefaultGroupName={#AppName}
PrivilegesRequired=admin
OutputDir=Output
OutputBaseFilename=Dikte-Setup-{#AppVersion}
SetupIconFile=Dikte.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\{#AppExe}
DisableProgramGroupPage=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; \
  GroupDescription: "Ek kısayollar:"
Name: "autostart"; Description: "Windows açıldığında Dikte'yi sistem tepsisinde başlat"; \
  GroupDescription: "Başlatma seçenekleri:"; Flags: unchecked

[Files]
; dist\Dikte PyInstaller çıktısının tamamı (veri içermez; veri %LOCALAPPDATA%\Dikte'de)
Source: "..\dist\Dikte\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\{#AppName} Kaldır"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Otomatik başlatma: Kurulumda seçilirse veya Ayarlar'dan açılırsa --tray ile sessiz başlar.
; Kaldırmada her durumda temizlenir.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#MyAppExeName}"" --tray"; \
  Flags: uninsdeletevalue; Tasks: autostart
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: none; ValueName: "{#AppName}"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExe}"; Description: "{#AppName} uygulamasını başlat"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Kullanıcı verisi: ayarlar, geçmiş, sırlar, günlükler, geçici ses.
; Modeller [Code] bölümünde ele alınır (kullanıcı "Modelleri koru" seçtiyse silinmez).
Type: filesandordirs; Name: "{localappdata}\Dikte\data"
Type: filesandordirs; Name: "{localappdata}\Dikte\logs"
Type: filesandordirs; Name: "{tmp}\dikte"

[Code]
// Uygulama, kaldırıcıyı başlatmadan önce {localappdata}\Dikte\keep_models.flag yazar.
// Bayrak varsa modeller korunur; yoksa models klasörü silinir.

function DiktePath(): String;
begin
  Result := ExpandConstant('{localappdata}\Dikte');
end;

function ModelsKept(): Boolean;
begin
  Result := FileExists(DiktePath() + '\keep_models.flag');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if not ModelsKept() then
      DelTree(DiktePath() + '\models', True, True, True);
    DeleteFile(DiktePath() + '\keep_models.flag');
    // Klasör yalnız boşsa kaldırılır (modeller korunduysa kalır).
    RemoveDir(DiktePath());
  end;
end;
