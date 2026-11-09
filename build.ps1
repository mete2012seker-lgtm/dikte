# Dikte derleme betiği: PyInstaller (dist\Dikte) -> Inno Setup (installer\Output\Dikte-Setup-<sürüm>.exe)
# Kullanım (proje kökünden):  powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw ".venv bulunamadı. Önce sanal ortamı kur." }

# 1) Sürüm tek kaynaktan (config.APP_VERSION) okunur ve Inno'ya aktarılır.
$version = (& $python -c "from dikte import config; print(config.APP_VERSION)").Trim()
if (-not $version) { throw "Sürüm okunamadı." }
Set-Content -LiteralPath (Join-Path $root "installer\version.iss") -Value "#define AppVersion `"$version`"" -Encoding ASCII
Write-Output "Sürüm: $version"

# 2) PyInstaller
& $python -m PyInstaller Dikte.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller başarısız (kod $LASTEXITCODE)." }
if (-not (Test-Path -LiteralPath (Join-Path $root "dist\Dikte\Dikte.exe"))) { throw "dist\Dikte\Dikte.exe üretilmedi." }

# 3) Inno Setup (ISCC.exe)
$candidates = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
)
$iscc = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $iscc) { throw "ISCC.exe bulunamadı. Inno Setup 6 kur." }
& $iscc (Join-Path $root "installer\Dikte.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup başarısız (kod $LASTEXITCODE)." }

# 4) Kurucu boyutu ve SHA-256 (latest.json için)
$setup = Join-Path $root "installer\Output\Dikte-Setup-$version.exe"
if (-not (Test-Path -LiteralPath $setup)) { throw "Kurucu üretilmedi: $setup" }
$hash = (Get-FileHash -LiteralPath $setup -Algorithm SHA256).Hash.ToLower()
$size = (Get-Item -LiteralPath $setup).Length
Write-Output "Kurucu: $setup"
Write-Output "Boyut : $size bayt"
Write-Output "SHA256: $hash"
