param(
    [switch]$SkipDocker,
    [switch]$Install,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$LogsDir = Join-Path $Root "logs"

function Test-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Start-DevWindow($Title, $WorkingDirectory, $Command) {
    $script = @"
`$host.UI.RawUI.WindowTitle = "$Title"
Set-Location -LiteralPath "$WorkingDirectory"
$Command
"@

    if ($DryRun) {
        Write-Host "[$Title] $Command"
        return
    }

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $script
    )
}

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

Write-Host "== DeepReCy one-click startup =="
Write-Host "Project: $Root"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Warning "Root .env not found. Copy .env.example to .env and fill API keys if needed."
}

if ($Install) {
    if (-not (Test-Command "python")) {
        throw "Python was not found in PATH."
    }
    if (-not (Test-Command "npm")) {
        throw "npm was not found in PATH."
    }

    Write-Host "Installing backend Python dependencies..."
    if (-not $DryRun) {
        Push-Location $BackendDir
        python -m pip install -r requirements.txt
        Pop-Location
    }

    Write-Host "Installing backend Prisma dependencies..."
    if (-not $DryRun) {
        Push-Location $BackendDir
        npm install
        Pop-Location
    }

    Write-Host "Installing frontend dependencies..."
    if (-not $DryRun) {
        Push-Location $FrontendDir
        npm install
        Pop-Location
    }
} else {
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Warning "frontend/node_modules not found. Run: .\start.ps1 -Install"
    }
    if (-not (Test-Path (Join-Path $BackendDir "node_modules"))) {
        Write-Warning "backend/node_modules not found. Run: .\start.ps1 -Install"
    }
}

if (-not $SkipDocker) {
    if (Test-Command "docker") {
        Write-Host "Starting Docker services..."
        try {
            if (-not $DryRun) {
                Push-Location $Root
                docker compose up -d
                Pop-Location
            }
        } catch {
            Write-Warning "Docker services were not started. Start Docker Desktop, then run: docker compose up -d"
        }
    } else {
        Write-Warning "Docker was not found. PostgreSQL and Chroma must be started another way."
    }
}

if (-not (Test-Command "python")) {
    throw "Python was not found in PATH."
}
if (-not (Test-Command "npm")) {
    throw "npm was not found in PATH."
}

Start-DevWindow `
    -Title "DeepReCy Backend :8000" `
    -WorkingDirectory $BackendDir `
    -Command "python run.py"

Start-DevWindow `
    -Title "DeepReCy Frontend :3000" `
    -WorkingDirectory $FrontendDir `
    -Command "npm run dev"

Write-Host ""
Write-Host "Startup commands sent."
Write-Host "Backend:  http://localhost:8000/health"
Write-Host "Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Tips:"
Write-Host "  First run with dependency install: .\start.ps1 -Install"
Write-Host "  Skip Docker startup:             .\start.ps1 -SkipDocker"
