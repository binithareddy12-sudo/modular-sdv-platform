
# =====================================================
# SOFTWARE DEFINED VEHICLE - STARTUP SCRIPT
# =====================================================

$ProjectPath = "C:\Users\91778\SDV_Project"

Write-Host "========================================="
Write-Host " Starting Software Defined Vehicle"
Write-Host "========================================="

# Move to project directory
Set-Location $ProjectPath

# 1. Check Docker
Write-Host "`n[1/4] Checking Docker..."

docker info | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop."
    Read-Host "Press Enter to exit"
    exit
}

# 2. Start KUKSA Databroker
Write-Host "`n[2/4] Starting KUKSA Databroker..."

docker start kuksa-databroker

Start-Sleep -Seconds 3

# 3. Start Virtual Vehicle Simulator
Write-Host "`n[3/4] Starting Virtual Vehicle Simulator..."

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectPath'; .\venv\Scripts\python.exe virtual_vehicle.py"

Start-Sleep -Seconds 2

# 4. Start Streamlit Dashboard
Write-Host "`n[4/4] Starting Dashboard..."

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectPath'; .\venv\Scripts\python.exe -m streamlit run dashboard.py"

Start-Sleep -Seconds 5

# Open dashboard
Start-Process "http://localhost:8501"

Write-Host "`n========================================="
Write-Host " SDV PLATFORM STARTED!"
Write-Host "========================================="

Read-Host "Press Enter to close this window"
