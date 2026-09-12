#!/bin/bash
# Skrip otomatisasi deploy One Gate Portal di server Ubuntu VPS

set -e

echo "🚀 Memulai Deployment One Gate Portal Mas Aan..."

# 1. Pastikan Docker dan docker-compose tersedia
if ! command -v docker &> /dev/null; then
    echo "❌ Docker belum terpasang. Menginstall docker.io..."
    sudo apt-get update && sudo apt-get install -y docker.io docker-compose
fi

# 2. Build dan jalankan container
echo "📦 Membangun Docker Image & Mengaktifkan Service di Port 8000..."
docker-compose down || true
docker-compose up --build -d

echo "⏳ Menunggu service stabil (5 detik)..."
sleep 5

# 3. Tes Health Check
if curl -s http://localhost:8000/api/health | grep -q '"status":"ok"'; then
    echo "✅ One Gate Portal Berhasil Aktif!"
    echo "🌐 Akses Portal di: http://<IP_VPS_ANDA>:8000"
else
    echo "⚠️ Peringatan: Health check belum merespon status 'ok', cek log dengan:"
    echo "   docker logs one_gate_portal"
fi
