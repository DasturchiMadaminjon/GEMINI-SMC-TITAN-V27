# clean_caches.ps1
# This script cleans common cache and temporary file locations on Windows.

$ProgressPreference = 'SilentlyContinue'

function Get-Size($path) {
    if (Test-Path $path) {
        try {
            $size = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            if ($size -eq $null) { return 0 }
            return $size
        } catch {
            return 0
        }
    }
    return 0
}

function Format-Bytes($bytes) {
    if ($bytes -ge 1GB) { "{0:N2} GB" -f ($bytes / 1GB) }
    elseif ($bytes -ge 1MB) { "{0:N2} MB" -f ($bytes / 1MB) }
    elseif ($bytes -ge 1KB) { "{0:N2} KB" -f ($bytes / 1KB) }
    else { "$bytes Bytes" }
}

$TotalCleaned = 0

$Locations = @(
    @{Name = "User Temp"; Path = $env:TEMP },
    @{Name = "Windows Temp"; Path = "$env:SystemRoot\Temp" },
    @{Name = "Windows Prefetch"; Path = "$env:SystemRoot\Prefetch" },
    @{Name = "Windows Update Cache"; Path = "$env:SystemRoot\SoftwareDistribution\Download" },
    @{Name = "Recent Items"; Path = "$env:APPDATA\Microsoft\Windows\Recent" },
    @{Name = "Pip Cache"; Path = "$env:LOCALAPPDATA\pip\cache" },
    @{Name = "NPM Cache"; Path = "$env:APPDATA\npm-cache" }
)

Write-Host "--- Disk Cleaning Started ---" -ForegroundColor Cyan

foreach ($Loc in $Locations) {
    if (Test-Path $Loc.Path) {
        $Before = Get-Size $Loc.Path
        Write-Host "Cleaning $($Loc.Name)... " -NoNewline
        try {
            Get-ChildItem $Loc.Path -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            $After = Get-Size $Loc.Path
            $Cleaned = $Before - $After
            if ($Cleaned -lt 0) { $Cleaned = 0 }
            $TotalCleaned += $Cleaned
            Write-Host "Done (Cleaned $(Format-Bytes $Cleaned))" -ForegroundColor Green
        } catch {
            Write-Host "Failed" -ForegroundColor Red
        }
    }
}

# Clean __pycache__ in current project
Write-Host "Cleaning __pycache__ folders... " -NoNewline
$PyCacheSize = Get-Size (Get-Location)
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
$TotalCleaned += $PyCacheSize
Write-Host "Done" -ForegroundColor Green

Write-Host "`n--- Cleaning Finished ---" -ForegroundColor Cyan
Write-Host "Total space recovered: $(Format-Bytes $TotalCleaned)" -ForegroundColor Yellow
Write-Host "Current Free Space on C: $(Format-Bytes (Get-PSDrive C).Free)" -ForegroundColor Cyan
