# GTK3 runtime'ı kontrol et / otomatik indir
# Output: GTK bin dizini yolu (eğer bulunduysa)
# Exit 0: GTK hazır
# Exit 1: GTK bulunamadı / kurulamadı

$dllName = 'libgobject-2.0-0.dll'

# 1. Sistem PATH'inde kontrol et
try {
    $where = Get-Command $dllName -ErrorAction Stop
    $binDir = Split-Path $where.Source -Parent
    Write-Output $binDir
    exit 0
} catch {
    # PATH'te yok, local kuruluma bak
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$gtkDir = Join-Path $projectRoot '.gtk'
$dllPath = Join-Path $gtkDir 'bin' $dllName

# 2. Local .gtk klasöründe kontrol et
if (Test-Path $dllPath) {
    Write-Output (Join-Path $gtkDir 'bin')
    exit 0
}

# 3. İndir ve kur
Write-Host 'GTK runtime bulunamadi, indiriliyor...'

$version = '2026.4.1'
$zipName = "GTK3_Gvsbuild_${version}_x64.zip"
$zipUrl = "https://github.com/wingtk/gvsbuild/releases/download/$version/$zipName"
$zipPath = Join-Path $gtkDir $zipName

try {
    New-Item -ItemType Directory -Path $gtkDir -Force | Out-Null

    Write-Host '  GTK3 runtime indiriliyor (~300MB)...'
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($zipUrl, $zipPath)

    Write-Host '  Ayiklaniyor...'
    $tmpDir = Join-Path $gtkDir '_tmp'
    Expand-Archive -Path $zipPath -DestinationPath $tmpDir -ErrorAction Stop

    $root = Get-ChildItem -Path $tmpDir -Directory | Select-Object -First 1
    if ($root) {
        Get-ChildItem -Path $root.FullName | Move-Item -Destination $gtkDir -Force
    }
    Remove-Item -Path $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue

    if (-not (Test-Path $dllPath)) {
        throw "$dllPath bulunamadi."
    }

    Write-Host '  GTK kurulumu tamamlandi.'
    Write-Output (Join-Path $gtkDir 'bin')
    exit 0
} catch {
    Write-Host "  GTK KURULUM HATASI: $_"
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force -ErrorAction SilentlyContinue }
    if (Test-Path (Join-Path $gtkDir '_tmp')) { Remove-Item (Join-Path $gtkDir '_tmp') -Recurse -Force -ErrorAction SilentlyContinue }
    exit 1
}
