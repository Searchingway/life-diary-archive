param(
    [Parameter(Mandatory = $true)]
    [string]$KeystorePath,
    [string]$OutputPath = (Join-Path $PSScriptRoot "..\build-output\LifeDiary-Mobile-2.3.0.apk")
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$androidHome = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$buildTools = Get-ChildItem -LiteralPath (Join-Path $androidHome "build-tools") -Directory |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $buildTools) { throw "Android build-tools are not installed." }
if (-not (Test-Path -LiteralPath $KeystorePath)) { throw "Keystore not found: $KeystorePath" }
if (-not $env:LIFE_DIARY_STORE_PASSWORD -or -not $env:LIFE_DIARY_KEY_PASSWORD -or -not $env:LIFE_DIARY_KEY_ALIAS) {
    throw "Set LIFE_DIARY_STORE_PASSWORD, LIFE_DIARY_KEY_PASSWORD, and LIFE_DIARY_KEY_ALIAS."
}

$env:ANDROID_HOME = $androidHome
$env:ANDROID_SDK_ROOT = $androidHome
$env:NODE_ENV = "production"

Push-Location $projectRoot
try {
    & npx expo prebuild --platform android --clean --no-install
    if ($LASTEXITCODE -ne 0) { throw "Expo prebuild failed." }

    $wrapperProperties = Join-Path $projectRoot "android\gradle\wrapper\gradle-wrapper.properties"
    $wrapperText = Get-Content -LiteralPath $wrapperProperties -Raw
    $wrapperText = $wrapperText.Replace("networkTimeout=10000", "networkTimeout=120000")
    $wrapperText = $wrapperText.Replace("gradle-9.3.1-bin.zip", "gradle-8.14.3-bin.zip")
    Set-Content -LiteralPath $wrapperProperties -Value $wrapperText -Encoding ascii

    $gradleProperties = Join-Path $projectRoot "android\gradle.properties"
    $gradleText = Get-Content -LiteralPath $gradleProperties -Raw
    $gradleText = $gradleText.Replace("org.gradle.parallel=true", "org.gradle.parallel=false")
    $gradleText = $gradleText.Replace(
        "reactNativeArchitectures=armeabi-v7a,arm64-v8a,x86,x86_64",
        "reactNativeArchitectures=arm64-v8a"
    )
    if ($gradleText -notmatch "org.gradle.workers.max=4") {
        $gradleText += "`norg.gradle.workers.max=4`n"
    }
    Set-Content -LiteralPath $gradleProperties -Value $gradleText -Encoding ascii

    $rootBuild = Join-Path $projectRoot "android\build.gradle"
    $rootBuildText = Get-Content -LiteralPath $rootBuild -Raw
    if ($rootBuildText -notmatch 'ndkVersion = "27\.2\.12479018"') {
        $marker = "// Top-level build file where you can add configuration options common to all sub-projects/modules."
        $replacement = "$marker`n`next {`n  ndkVersion = `"27.2.12479018`"`n}"
        $rootBuildText = $rootBuildText.Replace($marker, $replacement)
        Set-Content -LiteralPath $rootBuild -Value $rootBuildText -Encoding ascii
    }

    & (Join-Path $projectRoot "android\gradlew.bat") `
        -p (Join-Path $projectRoot "android") `
        -I (Join-Path $projectRoot "scripts\gradle-init.gradle") `
        :app:assembleRelease `
        --no-daemon
    if ($LASTEXITCODE -ne 0) { throw "Gradle release build failed." }

    $unsigned = Get-ChildItem -LiteralPath (Join-Path $projectRoot "android\app\build\outputs\apk\release") -Filter "*.apk" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $unsigned) { throw "Release APK was not found." }

    $outputDirectory = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
    $aligned = Join-Path $outputDirectory "aligned-unsigned.apk"
    & (Join-Path $buildTools.FullName "zipalign.exe") -f -p 4 $unsigned.FullName $aligned
    if ($LASTEXITCODE -ne 0) { throw "zipalign failed." }

    & (Join-Path $buildTools.FullName "apksigner.bat") sign `
        --ks $KeystorePath `
        --ks-key-alias $env:LIFE_DIARY_KEY_ALIAS `
        --ks-pass "env:LIFE_DIARY_STORE_PASSWORD" `
        --key-pass "env:LIFE_DIARY_KEY_PASSWORD" `
        --out $OutputPath `
        $aligned
    if ($LASTEXITCODE -ne 0) { throw "APK signing failed." }

    & (Join-Path $buildTools.FullName "apksigner.bat") verify --verbose --print-certs $OutputPath
    if ($LASTEXITCODE -ne 0) { throw "APK signature verification failed." }
    Remove-Item -LiteralPath $aligned -Force
    Write-Host "SIGNED_APK=$OutputPath"
}
finally {
    Pop-Location
}
