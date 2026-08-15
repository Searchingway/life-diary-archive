param(
    [string]$Destination = "E:\diary"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-NormalizedPath([string]$Path) {
    if (-not $Path -or -not $Path.Trim()) {
        throw "路径不能为空"
    }
    return [System.IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Path)).TrimEnd('\')
}

function Get-BootstrapPath {
    $localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\Local" }
    return Join-Path $localAppData "LifeDiary\bootstrap.json"
}

function Get-CurrentDataRoot([string]$RepoRoot, [string]$BootstrapPath) {
    if ($env:LIFE_DIARY_DATA_ROOT -and $env:LIFE_DIARY_DATA_ROOT.Trim()) {
        return Get-NormalizedPath $env:LIFE_DIARY_DATA_ROOT
    }

    if (Test-Path -LiteralPath $BootstrapPath -PathType Leaf) {
        try {
            $config = Get-Content -LiteralPath $BootstrapPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($config.data_root -and ([string]$config.data_root).Trim()) {
                return Get-NormalizedPath ([string]$config.data_root)
            }
        }
        catch {
            Write-Warning "现有 bootstrap.json 无法解析，将按默认数据目录定位当前数据。"
        }
    }

    return Get-NormalizedPath (Join-Path $RepoRoot "diary_v2.0\data\Diary")
}

function Assert-LifeDiaryClosed {
    $running = @()

    try {
        $running += Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle -like "*人生档案*" } |
            ForEach-Object { "PID=$($_.Id) $($_.ProcessName) [$($_.MainWindowTitle)]" }
    }
    catch {
        # Window-title detection is best effort only.
    }

    try {
        $running += Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.CommandLine -and (
                    $_.CommandLine -match 'diary_v2\.0[\\/](launcher|server)\.py' -or
                    $_.CommandLine -match 'run_life_diary_2\.0'
                )
            } |
            ForEach-Object { "PID=$($_.ProcessId) $($_.Name) [$($_.CommandLine)]" }
    }
    catch {
        # Command-line detection is best effort only.
    }

    $running = @($running | Sort-Object -Unique)
    if ($running.Count -gt 0) {
        throw "检测到人生档案仍在运行。为防止复制期间数据继续写入，迁移未开始。请先完全关闭软件，然后重新运行本脚本。`n$($running -join "`n")"
    }
}

function Get-DirectoryManifest([string]$Root) {
    $rootPath = Get-NormalizedPath $Root
    $entries = @()

    foreach ($file in (Get-ChildItem -LiteralPath $rootPath -Recurse -File -Force | Sort-Object FullName)) {
        $relative = $file.FullName.Substring($rootPath.Length).TrimStart('\').Replace('\', '/')
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        $entries += [pscustomobject]@{
            RelativePath = $relative
            Length = [long]$file.Length
            Hash = $hash
        }
    }

    $lines = @($entries | Sort-Object RelativePath | ForEach-Object {
        "$($_.RelativePath)`t$($_.Length)`t$($_.Hash)"
    })
    $bytes = if ($entries.Count -gt 0) { [long](($entries | Measure-Object -Property Length -Sum).Sum) } else { 0L }

    return [pscustomobject]@{
        Text = ($lines -join "`n")
        Count = [int]$entries.Count
        Bytes = $bytes
    }
}

function Copy-DirectoryExact([string]$Source, [string]$Target) {
    if (Test-Path -LiteralPath $Target) {
        throw "目标已存在，为避免覆盖任何文件，拒绝复制：$Target"
    }

    $parent = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    & robocopy $Source $Target /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /XJ /NFL /NDL /NJH /NJS /NP | Out-Null
    $code = $LASTEXITCODE
    if ($code -ge 8) {
        throw "robocopy 复制失败，退出码：$code。源目录未删除，软件路径未修改。"
    }
}

function Assert-ManifestsEqual($Expected, $Actual, [string]$Label) {
    if ($Expected.Text -ne $Actual.Text) {
        throw "$Label 校验失败：文件路径、大小或 SHA-256 不一致。源目录未删除，软件路径未修改。"
    }
}

function Capture-Bootstrap([string]$BootstrapPath) {
    if (Test-Path -LiteralPath $BootstrapPath -PathType Leaf) {
        return [pscustomobject]@{
            Existed = $true
            Bytes = [System.IO.File]::ReadAllBytes($BootstrapPath)
        }
    }
    return [pscustomobject]@{
        Existed = $false
        Bytes = $null
    }
}

function Restore-Bootstrap([string]$BootstrapPath, $Snapshot) {
    if ($Snapshot.Existed) {
        $directory = Split-Path -Parent $BootstrapPath
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        [System.IO.File]::WriteAllBytes($BootstrapPath, [byte[]]$Snapshot.Bytes)
    }
    elseif (Test-Path -LiteralPath $BootstrapPath -PathType Leaf) {
        Remove-Item -LiteralPath $BootstrapPath -Force
    }
}

function Write-BootstrapAtomically([string]$BootstrapPath, [string]$DataRoot, [string]$Stamp) {
    $directory = Split-Path -Parent $BootstrapPath
    New-Item -ItemType Directory -Path $directory -Force | Out-Null

    if (Test-Path -LiteralPath $BootstrapPath -PathType Leaf) {
        Copy-Item -LiteralPath $BootstrapPath -Destination "$BootstrapPath.bak.$Stamp" -Force
    }

    $temporary = "$BootstrapPath.tmp.$PID"
    $json = @{ data_root = $DataRoot } | ConvertTo-Json
    Set-Content -LiteralPath $temporary -Value $json -Encoding UTF8
    Move-Item -LiteralPath $temporary -Destination $BootstrapPath -Force

    $readBack = Get-Content -LiteralPath $BootstrapPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $readBack.data_root -or (Get-NormalizedPath ([string]$readBack.data_root)) -ne (Get-NormalizedPath $DataRoot)) {
        throw "bootstrap 写入后的回读校验失败。"
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$bootstrapPath = Get-BootstrapPath
$source = Get-CurrentDataRoot $repoRoot $bootstrapPath
$destination = Get-NormalizedPath $Destination
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$bootstrapSnapshot = Capture-Bootstrap $bootstrapPath

Write-Host "Life Diary 安全数据迁移" -ForegroundColor Cyan
Write-Host "当前数据目录: $source"
Write-Host "目标数据目录: $destination"
Write-Host "bootstrap:     $bootstrapPath"

Assert-LifeDiaryClosed

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "当前数据目录不存在，未执行任何修改：$source"
}

$sourceFiles = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
if ($sourceFiles.Count -eq 0) {
    throw "当前数据目录没有任何文件。为避免误迁移空目录，操作已停止。"
}

if ($source -eq $destination) {
    throw "当前数据目录已经是目标目录，无需迁移。"
}

$destinationRoot = [System.IO.Path]::GetPathRoot($destination)
if (-not $destinationRoot -or -not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    throw "目标磁盘不存在或不可访问：$destinationRoot"
}

if (Test-Path -LiteralPath $destination) {
    throw "目标目录已存在。为避免覆盖未知文件，本脚本不会继续：$destination"
}

$sourcePrefix = $source.TrimEnd('\') + '\'
if ($destination.StartsWith($sourcePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "目标目录不能位于当前数据目录内部。"
}

$backupRoot = Join-Path (Split-Path -Parent $source) "Diary.before-E-migration.$stamp"
if (Test-Path -LiteralPath $backupRoot) {
    throw "安全备份目标意外已存在：$backupRoot"
}

Write-Host "[1/6] 计算源数据 SHA-256 清单……"
$sourceBefore = Get-DirectoryManifest $source
Write-Host "      $($sourceBefore.Count) 个文件，共 $($sourceBefore.Bytes) 字节"

Write-Host "[2/6] 创建迁移前完整安全副本……"
Copy-DirectoryExact $source $backupRoot
$backupManifest = Get-DirectoryManifest $backupRoot
Assert-ManifestsEqual $sourceBefore $backupManifest "安全副本"
Write-Host "      安全副本已验证：$backupRoot" -ForegroundColor Green

Write-Host "[3/6] 复制到目标目录 $destination ……"
Copy-DirectoryExact $source $destination

Write-Host "[4/6] 重新校验源目录，确认复制期间没有被软件修改……"
$sourceAfter = Get-DirectoryManifest $source
Assert-ManifestsEqual $sourceBefore $sourceAfter "源目录稳定性"

Write-Host "[5/6] 校验 E 盘副本的每一个文件……"
$destinationManifest = Get-DirectoryManifest $destination
Assert-ManifestsEqual $sourceAfter $destinationManifest "目标目录"
Write-Host "      目标副本 SHA-256 全部一致" -ForegroundColor Green

Write-Host "[6/6] 再次确认软件未启动，然后写入软件自定义数据路径……"
Assert-LifeDiaryClosed
try {
    Write-BootstrapAtomically $bootstrapPath $destination $stamp

    $finalSource = Get-DirectoryManifest $source
    if ($finalSource.Text -ne $sourceAfter.Text) {
        throw "写入配置时检测到旧目录又发生了变化。"
    }
}
catch {
    $migrationError = $_
    try {
        Restore-Bootstrap $bootstrapPath $bootstrapSnapshot
    }
    catch {
        throw "迁移校验失败，而且 bootstrap 自动回滚也失败。请不要启动软件。原数据仍在：$source；E 盘副本仍在：$destination；bootstrap：$bootstrapPath。"
    }
    throw "$($migrationError.Exception.Message) 软件路径已自动回滚到迁移前状态；原目录和 E 盘副本均未删除。"
}

Write-Host ""
Write-Host "迁移完成。" -ForegroundColor Green
Write-Host "新数据目录: $destination"
Write-Host "原数据目录: $source  （保留，未删除）"
Write-Host "安全副本:   $backupRoot"
Write-Host "配置文件:   $bootstrapPath"
Write-Host ""
Write-Host "现在可以重新打开人生档案。确认软件显示的数据目录为 $destination 且日记完整后，再考虑以后是否手动清理旧副本；本脚本不会替你删除任何旧数据。" -ForegroundColor Yellow

if ($env:LIFE_DIARY_DATA_ROOT -and (Get-NormalizedPath $env:LIFE_DIARY_DATA_ROOT) -ne $destination) {
    Write-Warning "当前 PowerShell 会话设置了 LIFE_DIARY_DATA_ROOT=$env:LIFE_DIARY_DATA_ROOT，它会覆盖 bootstrap。请从正常快捷方式重新启动软件，或关闭这个终端后再启动。"
}
