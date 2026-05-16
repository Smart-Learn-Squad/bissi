#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "━━━ BISSI Launcher ━━━"

# ─────────────────────────────────────────────
# 1. Check venv
# ─────────────────────────────────────────────
if (-not (Test-Path ".venv")) {
    Write-Host "X Virtual env not found in .venv" -ForegroundColor Red
    exit 1
}
& ".venv\Scripts\Activate.ps1"

# ─────────────────────────────────────────────
# 2. Kill stale processes
# ─────────────────────────────────────────────
Write-Host "-> Cleaning up old processes..."

function Stop-ProcessByFilter {
    param([string]$Filter)
    Get-WmiObject Win32_Process |
        Where-Object { $_.CommandLine -like "*$Filter*" } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
}

Stop-ProcessByFilter "llama_cpp.server"
Stop-ProcessByFilter "uvicorn"
Start-Sleep -Seconds 1

# ─────────────────────────────────────────────
# 3. Launch llama.cpp server
# ─────────────────────────────────────────────
$LlamaLog = "$env:TEMP\bissi-llama.log"
$LlamaPID = $null

function Test-Port {
    param([int]$Port)
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpClient]::new()
        $task = $listener.ConnectAsync("127.0.0.1", $Port)
        $task.Wait(500) | Out-Null
        return $listener.Connected
    } catch {
        return $false
    } finally {
        if ($listener) { $listener.Close() }
    }
}

function Test-Endpoint {
    param([string]$Url)
    try {
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $resp.StatusCode -eq 200
    } catch {
        return $false
    }
}

$llamaReady = Test-Endpoint "http://127.0.0.1:8001/v1/models"

if ($llamaReady) {
    Write-Host "OK Existing llama.cpp server detected on :8001" -ForegroundColor Green
    $LlamaPID = (Get-WmiObject Win32_Process |
        Where-Object { $_.CommandLine -like "*llama_cpp.server*" } |
        Select-Object -First 1).ProcessId
} else {
    if (Test-Port 8001) {
        Write-Host "X Port 8001 is already in use." -ForegroundColor Red
        Write-Host "  A stale llama.cpp server is blocking startup."
        Write-Host "  Log: $LlamaLog"
        if (Test-Path $LlamaLog) { Get-Content $LlamaLog -Tail 5 }
        exit 1
    }

    Write-Host "-> Starting llama.cpp server on :8001..."
    $LlamaProc = Start-Process -FilePath ".venv\Scripts\python.exe" `
        -ArgumentList "-m", "llama_cpp.server",
                      "--model", "gemma-4-E2B-it-Q4_K_M.gguf",
                      "--host", "127.0.0.1",
                      "--port", "8001",
                      "--n_ctx", "3072",
                      "--n_threads", "6",
                      "--use_mmap", "False" `
        -RedirectStandardOutput $LlamaLog `
        -RedirectStandardError $LlamaLog `
        -NoNewWindow `
        -PassThru
    $LlamaPID = $LlamaProc.Id
}

# Wait for llama.cpp to be ready
Write-Host "-> Waiting for llama.cpp..."
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    if ((Test-Endpoint "http://127.0.0.1:8001/v1/models") -or
        (Test-Endpoint "http://127.0.0.1:8001/health")) {
        Write-Host "OK llama.cpp ready (PID $LlamaPID)" -ForegroundColor Green
        $ready = $true
        break
    }
    if ($i -eq 30) {
        Write-Host "X llama.cpp failed to start after 30s" -ForegroundColor Red
        Write-Host "  Log: $LlamaLog"
        if (Test-Path $LlamaLog) { Get-Content $LlamaLog -Tail 5 }
        if ($LlamaPID) { Stop-Process -Id $LlamaPID -Force -ErrorAction SilentlyContinue }
        exit 1
    }
    Start-Sleep -Seconds 2
}

# ─────────────────────────────────────────────
# 4. Launch FastAPI backend
# ─────────────────────────────────────────────
$ApiLog = "$env:TEMP\bissi-api.log"

Write-Host "-> Starting BISSI backend on :8765..."
$ApiProc = Start-Process -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "api.server:app",
                  "--host", "127.0.0.1",
                  "--port", "8765",
                  "--log-level", "info" `
    -RedirectStandardOutput $ApiLog `
    -RedirectStandardError $ApiLog `
    -NoNewWindow `
    -PassThru
$ApiPID = $ApiProc.Id

# Wait for FastAPI to be ready
Write-Host "-> Waiting for backend..."
for ($i = 1; $i -le 15; $i++) {
    if (Test-Endpoint "http://127.0.0.1:8765/health") {
        Write-Host "OK BISSI backend ready (PID $ApiPID)" -ForegroundColor Green
        break
    }
    if ($i -eq 15) {
        Write-Host "X Backend failed to start after 15s" -ForegroundColor Red
        Write-Host "  Log: $ApiLog"
        if (Test-Path $ApiLog) { Get-Content $ApiLog -Tail 5 }
        Stop-Process -Id $ApiPID  -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $LlamaPID -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Start-Sleep -Seconds 1
}

# ─────────────────────────────────────────────
# 5. Launch Electron
# ─────────────────────────────────────────────
Write-Host "-> Launching Electron app..."
Set-Location "bissi-master-ui"
npm start   # Blocks until Electron closes

# ─────────────────────────────────────────────
# Cleanup on exit
# ─────────────────────────────────────────────
Write-Host "-> Shutting down servers..."
Stop-Process -Id $ApiPID   -Force -ErrorAction SilentlyContinue
Stop-Process -Id $LlamaPID -Force -ErrorAction SilentlyContinue
Write-Host "OK Done" -ForegroundColor Green
