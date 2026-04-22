$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $root
$buildDir = Join-Path $root "build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

Write-Host "This script builds the native LMU bridge once you add the official LMU shared memory header and implementation details."
Write-Host "Expected output: native\lmu_bridge\build\lmu_bridge.dll"
Write-Host "Use cl.exe from Visual Studio Developer PowerShell, or adapt for CMake if preferred."

$source = Join-Path $root "src\lmu_shared_memory_bridge.c"
$include = Join-Path $root "include"

if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
  throw "cl.exe not found. Open a Visual Studio Developer PowerShell and rerun this script."
}

Push-Location $buildDir
cl.exe /LD /I $include $source /Fe:lmu_bridge.dll
Pop-Location
