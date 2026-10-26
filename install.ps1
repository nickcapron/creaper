# creaper installer for Windows.
#
# Run this in PowerShell:
#     irm https://raw.githubusercontent.com/nickcapron/creaper/main/install.ps1 | iex
#
# It installs Python if you don't have it (from winget or python.org), puts creaper in
# its own folder (%LOCALAPPDATA%\creaper), offers to install Claude Code (Anthropic's
# official installer), then runs `creaper setup`: ReaImGui for the chat panel (from its
# official GitHub release), creaper's scripts in REAPER, and the Claude connections.
# It never asks for or stores a Claude password or key: you sign in to Claude yourself.
# Running it again upgrades creaper.

$ErrorActionPreference = 'Stop'
# The creaper release this installs (a tag, so what's installed is what was released).
$Release = 'v0.50.1'

$ProgressPreference = 'SilentlyContinue'

function Say($text) { Write-Host $text -ForegroundColor Cyan }
function Warn($text) { Write-Host $text -ForegroundColor Yellow }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'Machine')
}
function Add-UserPath($dir) {
    # The registry value as stored, so entries like %USERPROFILE%\bin stay variables:
    # Environment.SetEnvironmentVariable would write every entry back expanded.
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    try {
        $raw = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $parts = @($raw -split ';' | Where-Object { $_ })
        $expanded = @($parts | ForEach-Object { [Environment]::ExpandEnvironmentVariables($_) })
        if (($parts -notcontains $dir) -and ($expanded -notcontains $dir)) {
            $key.SetValue('Path', (@($parts) + $dir) -join ';', [Microsoft.Win32.RegistryValueKind]::ExpandString)
            # Writing the registry doesn't tell Windows the environment changed; setting
            # (and clearing) a variable this way does, so new windows see the new PATH.
            [Environment]::SetEnvironmentVariable('CREAPER_INSTALL', '1', 'User')
            [Environment]::SetEnvironmentVariable('CREAPER_INSTALL', $null, 'User')
        }
    } finally {
        $key.Close()
    }
    Refresh-Path
}

Say "`ncreaper installer`n"

# An administrator window can belong to a different account, and then creaper would
# install for that account instead of yours.
$identity = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Warn "This PowerShell is running as administrator. creaper installs for one user, so a normal"
    Warn "(non-administrator) PowerShell window is better."
    $answer = Read-Host "Continue anyway? [y/N]"
    if ($answer -notmatch '^[yY]') { return }
}

# REAPER has to have been opened once, so its settings folder exists.
$reaper = Join-Path $env:APPDATA 'REAPER'
if (-not (Test-Path $reaper)) {
    Warn "REAPER's settings folder wasn't found ($reaper)."
    Warn "Install REAPER from https://www.reaper.fm, open it once, then run this again."
    return
}

# Python 3.10 or newer.
function Find-Python {
    foreach ($candidate in @(@('py', '-3'), @('python'))) {
        $exe = $candidate[0]
        $rest = @($candidate | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        try {
            $out = & $exe @rest -c "import sys; print('%d.%d' % sys.version_info[:2]); print(sys.executable)" 2>$null
        } catch { continue }
        if ($out -and $out.Count -ge 2 -and [version]$out[0] -ge [version]'3.10' -and $out[1] -notmatch 'WindowsApps') {
            return $out[1]
        }
    }
    return $null
}

$python = Find-Python
if (-not $python) {
    Say "Installing Python 3.12 (creaper needs it)..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null
    } else {
        $setup = Join-Path $env:TEMP 'python-3.12.7-amd64.exe'
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile $setup
        Start-Process $setup -ArgumentList '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_launcher=1' -Wait
    }
    Refresh-Path
    $python = Find-Python
    if (-not $python) {
        Warn "Python didn't install. Install Python 3.10 or newer from https://www.python.org, then run this again."
        return
    }
}
Say "Python: $python"

# creaper in its own environment, so it can't clash with anything else.
$root = Join-Path $env:LOCALAPPDATA 'creaper'
$venv = Join-Path $root 'venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
# An environment from an earlier run only works while the Python it was made from is
# still installed; after that Python is removed or upgraded, rebuild it.
$venvWorks = $false
if (Test-Path $venvPython) {
    try { & $venvPython -c "import sys" 2>$null; $venvWorks = ($LASTEXITCODE -eq 0) } catch { $venvWorks = $false }
    if (-not $venvWorks) {
        Say "creaper's environment no longer works (its Python was removed or upgraded); rebuilding it..."
        Remove-Item -Recurse -Force $venv
    }
}
if (-not $venvWorks) {
    Say "Creating creaper's environment in $venv..."
    & $python -m venv $venv
}
Say "Installing creaper (this takes a minute)..."
& $venvPython -m pip install --upgrade --quiet pip
& $venvPython -m pip install --upgrade --quiet "https://github.com/nickcapron/creaper/archive/refs/tags/$Release.zip"
if ($LASTEXITCODE -ne 0) {
    Warn "pip couldn't install creaper. Check your internet connection and run this again."
    return
}

# Claude Code runs the chat panel on your own Claude account. Its installer puts it in
# ~\.local\bin but doesn't always add that to PATH, and then `claude` isn't recognized.
$claudeBin = Join-Path $env:USERPROFILE '.local\bin'
$haveClaude = (Get-Command claude -ErrorAction SilentlyContinue) -or
              (Test-Path (Join-Path $claudeBin 'claude.exe'))
if (-not $haveClaude) {
    Write-Host ""
    Write-Host "creaper's chat panel runs on Claude Code, signed in with your own Claude account."
    $answer = Read-Host "Install Claude Code now, with Anthropic's official installer? [Y/n]"
    if ($answer -eq '' -or $answer -match '^[yY]') {
        # In its own PowerShell: that installer calls `exit` when something fails, which
        # would close this window, and it turns on strict mode for the whole session.
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
        if ($LASTEXITCODE -ne 0) {
            Warn "Claude Code didn't install. You can install it later from https://claude.com/claude-code, then run this again."
        }
        Refresh-Path
    }
}
if ((Test-Path (Join-Path $claudeBin 'claude.exe')) -and -not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Add-UserPath $claudeBin
}

# A `creaper` command for new terminals (creaper doctor, creaper install-bridge ...),
# without putting the environment's own python.exe on PATH.
$bin = Join-Path $root 'bin'
New-Item -ItemType Directory -Force -Path $bin | Out-Null
# %LOCALAPPDATA% rather than the path itself: a .cmd file is read in the console's code
# page, so a username like "José" written into it came out as "Jos?" and the command
# couldn't find creaper.
Set-Content -Path (Join-Path $bin 'creaper.cmd') -Encoding ASCII -Value '@"%LOCALAPPDATA%\creaper\venv\Scripts\creaper.exe" %*'
Add-UserPath $bin

# Everything else: ReaImGui, creaper's scripts in REAPER, Claude Desktop / Claude Code.
& (Join-Path $venv 'Scripts\creaper.exe') setup

Write-Host ""
Say "Done. Last steps:"
Write-Host "  1. If you haven't signed in to Claude Code yet: open a new terminal and run  claude"
Write-Host "  2. Restart REAPER. The creaper panel opens by itself."
Write-Host "  3. To check the connection, run  creaper doctor  in a new terminal."
Write-Host "To update creaper later, run this installer again."
