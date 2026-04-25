$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Packaging = Join-Path $Root "packaging\windows"
$Release = Join-Path $Root "release\windows"
$Payload = Join-Path $Packaging "payload"

New-Item -ItemType Directory -Force -Path $Release, $Payload | Out-Null

python -m PyInstaller --noconfirm `
    --distpath (Join-Path $Release "app_dist") `
    --workpath (Join-Path $Release "build_app") `
    (Join-Path $Packaging "LifeDiary.spec")

$AppDir = Join-Path $Release "app_dist\LifeDiary"
$AppExe = Join-Path $AppDir "LifeDiary.exe"
$ChineseExe = Join-Path $AppDir "人生档案.exe"
if ((Test-Path -LiteralPath $AppExe) -and -not (Test-Path -LiteralPath $ChineseExe)) {
    Copy-Item -LiteralPath $AppExe -Destination $ChineseExe -Force
}

$PayloadZip = Join-Path $Payload "life_diary_payload.zip"
if (Test-Path -LiteralPath $PayloadZip) {
    Remove-Item -LiteralPath $PayloadZip -Force
}
Compress-Archive -Path (Join-Path $AppDir "*") -DestinationPath $PayloadZip -Force

python -m PyInstaller --noconfirm `
    --distpath (Join-Path $Release "installer_dist") `
    --workpath (Join-Path $Release "build_installer") `
    (Join-Path $Packaging "LifeDiaryInstaller.spec")

Write-Host "Windows installer output:"
Write-Host (Join-Path $Release "installer_dist\LifeDiaryInstaller.exe")
