# ============================================================
#  AI Interview Prep — PowerShell convenience scripts
#  Usage:  .\run.ps1 run | test | seed | lint | install
# ============================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("run","test","seed","lint","install","help")]
    [string]$Command = "help"
)

$Root = $PSScriptRoot

function Show-Help {
    Write-Host ""
    Write-Host "  AI Interview Prep Assistant — Dev Scripts" -ForegroundColor Cyan
    Write-Host "  ----------------------------------------" -ForegroundColor DarkGray
    Write-Host "  .\run.ps1 install    Install all Python dependencies" -ForegroundColor White
    Write-Host "  .\run.ps1 run        Launch Streamlit development server" -ForegroundColor White
    Write-Host "  .\run.ps1 test       Run pytest test suite" -ForegroundColor White
    Write-Host "  .\run.ps1 seed       Seed the database with mock data" -ForegroundColor White
    Write-Host "  .\run.ps1 lint       Run flake8 code quality check" -ForegroundColor White
    Write-Host ""
}

switch ($Command) {

    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Cyan
        pip install -r "$Root\requirements.txt"
    }

    "run" {
        Write-Host "Starting Streamlit server at http://localhost:8501 ..." -ForegroundColor Green
        Set-Location $Root
        streamlit run app.py
    }

    "test" {
        Write-Host "Running test suite..." -ForegroundColor Yellow
        Set-Location $Root
        pytest -v --tb=short
    }

    "seed" {
        $email = Read-Host "Enter registered user email to seed data for"
        Write-Host "Seeding database for $email..." -ForegroundColor Cyan
        Set-Location $Root
        $env:PYTHONPATH = $Root
        python src\database\seed_db.py --email $email
    }

    "lint" {
        Write-Host "Running flake8 linter..." -ForegroundColor Magenta
        Set-Location $Root
        flake8 src pages app.py --max-line-length=120 --exclude=__pycache__
    }

    default { Show-Help }
}
