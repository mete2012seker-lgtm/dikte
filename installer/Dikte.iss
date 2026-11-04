; Dikte kurucusu — Inno Setup 6
; Derleme: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\Dikte.iss
; Çıktı: installer\Output\Dikte-1.3.0-kurulum.exe
; Kurallar: kullanıcı bazlı, yönetici izni istemez; tek CPU paketi (K4).

#define AppName "Dikte"
#define AppVersion "1.3.0"
#define AppExe "Dikte.exe"

[Setup]
AppId={{8A5D2C61-1D46-4E25-9A0B-DIKTE0000000}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={localappdata}\Programs\Dikte
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Dikte-{#AppVersion}-kurulum
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; \
  GroupDescription: "Ek kısayollar:"

[Files]
; dist\Dikte PyInstaller çıktısının tamamı
Source: "..\dist\Dikte\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; Veri kökü (%LOCALAPPDATA%\Dikte) PyInstaller sürümünde config.py tarafından kullanılır.
; Otomatik başlatma yalnızca kullanıcı isterse (Ayarlar'daki anahtar) yazılır; burada varsayılan yok.

[Run]
Filename: "{app}\{#AppExe}"; Description: "{#AppName} uygulamasını başlat"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Kaldırmada uygulama klasörü tamamen silinir (Inno varsayılanı {app} dosyalarını kaldırır).
; Kullanıcı verisi %LOCALAPPDATA%\Dikte'de kalır; derin silme kaldırıcı kartındaki ikinci onayla yapılır.
