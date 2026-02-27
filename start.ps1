param(
    [switch]$Dev,
    [switch]$MockTts,
    [switch]$MockVideo,
    [string]$MaskVideo
)

$ErrorActionPreference = "Stop"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$script = Join-Path $PSScriptRoot "app.py"
$argsList = @()

if ($Dev) { $argsList += "--dev" }
if ($MockTts) { $argsList += "--mock-tts" }
if ($MockVideo) { $argsList += "--mock-video" }
if ($MaskVideo) { $argsList += "--mask-video"; $argsList += $MaskVideo }

& $python $script @argsList
