# Kill process using port 8501
Write-Host "Checking for processes using port 8501..." -ForegroundColor Yellow

$connection = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue

if ($connection) {
    $processId = $connection.OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "Found process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Red
        Write-Host "Killing process..." -ForegroundColor Yellow
        Stop-Process -Id $processId -Force
        Write-Host "Process killed successfully!" -ForegroundColor Green
    } else {
        Write-Host "No process found using port 8501" -ForegroundColor Green
    }
} else {
    Write-Host "Port 8501 is free!" -ForegroundColor Green
}

Write-Host "`nYou can now run: streamlit run app.py" -ForegroundColor Cyan

