# ==============================================================================
# Automated 1-Click Deployment for One Gate Portal to VPS
# ==============================================================================

$VPS_HOST = "203.194.112.223"
$VPS_USER = "root"
$REMOTE_DIR = "/var/www/one-gate-portal"
$DOMAIN = "basecampmeera.cloud"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host " 🚀 Memulai Deploy One Gate Portal ke VPS ($VPS_HOST)" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Transfer file terbaru ke VPS
Write-Host "[1/3] Mengirim file terbaru (src, static) ke VPS..." -ForegroundColor Yellow
scp -r "$PSScriptRoot\src" "$PSScriptRoot\static" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Gagal mentransfer file ke VPS." -ForegroundColor Red
    exit 1
}

# 2. Rebuild dan restart docker container di VPS
Write-Host "[2/3] Membangun ulang & me-restart container Docker di VPS..." -ForegroundColor Yellow
ssh -o BatchMode=yes "${VPS_USER}@${VPS_HOST}" "cd ${REMOTE_DIR} && docker compose up -d --build --remove-orphans && sudo systemctl reload nginx"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Gagal me-restart container di VPS." -ForegroundColor Red
    exit 1
}

# 3. Verifikasi HTTP Endpoint dengan retry
Write-Host "[3/3] Memverifikasi status endpoint live..." -ForegroundColor Yellow
$maxRetries = 6
$statusCode = ""
for ($i = 1; $i -le $maxRetries; $i++) {
    Start-Sleep -Seconds 3
    $statusCode = (ssh -o BatchMode=yes "${VPS_USER}@${VPS_HOST}" "curl -s -o /dev/null -w '%{http_code}' https://${DOMAIN}/").Trim()
    if ($statusCode -eq "200") {
        break
    }
    Write-Host "   Menunggu aplikasi siap (Percobaan $i/$maxRetries, status: $statusCode)..." -ForegroundColor Gray
}

if ($statusCode -eq "200") {
    Write-Host "=========================================================" -ForegroundColor Green
    Write-Host " ✅ Deployment Berhasil!" -ForegroundColor Green
    Write-Host " 🌐 Akses Portal: https://${DOMAIN}" -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Green
} else {
    Write-Host "⚠️ Respon HTTP: $statusCode. Silakan periksa log container dengan:" -ForegroundColor Yellow
    Write-Host "   ssh root@$VPS_HOST 'docker logs one_gate_portal'" -ForegroundColor Yellow
}
