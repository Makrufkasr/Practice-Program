#!/bin/bash
# ==============================================================================
# PRODUCTION DEPLOYMENT SCRIPT FOR basecamp.meeracloud
# One Gate Portal — Ecosystem Intelligence
# ==============================================================================

set -e

DOMAIN="basecamp.meeracloud"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================================================"
echo "🚀 Memulai Proses Launching Online One Gate Portal ke $DOMAIN"
echo "======================================================================"

# 1. Update dan Pastikan Dependensi Sistem Terpasang
echo "📦 [1/6] Memeriksa paket dependensi sistem (Docker, Nginx, Certbot)..."
sudo apt-get update -qq
sudo apt-get install -y -qq docker.io docker-compose nginx certbot python3-certbot-nginx curl ufw

# 2. Konfigurasi Firewall UFW
echo "🛡️ [2/6] Membuka port firewall yang dibutuhkan (80, 443, 8000, 8002, 8003, 8501)..."
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw allow 8000/tcp || true
sudo ufw allow 8002/tcp || true
sudo ufw allow 8003/tcp || true
sudo ufw allow 8501/tcp || true

# 3. Persiapan File Environment
echo "⚙️ [3/6] Memeriksa file .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.production.example" ]; then
        cp "$APP_DIR/.env.production.example" "$APP_DIR/.env"
        echo "   -> Dibuat dari .env.production.example"
    fi
fi

# 4. Build & Jalankan Container Docker One Gate Portal
echo "🐳 [4/6] Membangun dan menjalankan container One Gate Portal (Port 8000)..."
cd "$APP_DIR"
docker-compose down || true
docker-compose up --build -d

echo "⏳ Menunggu container siap (5 detik)..."
sleep 5

# 5. Konfigurasi Nginx Reverse Proxy
echo "🌐 [5/6] Mengaktifkan konfigurasi Nginx untuk $DOMAIN..."
if [ -f "$APP_DIR/nginx/basecamp.meeracloud.conf" ]; then
    sudo cp "$APP_DIR/nginx/basecamp.meeracloud.conf" "/etc/nginx/sites-available/$DOMAIN.conf"
    sudo ln -sf "/etc/nginx/sites-available/$DOMAIN.conf" "/etc/nginx/sites-enabled/$DOMAIN.conf"
    sudo nginx -t && sudo systemctl reload nginx
    echo "   -> Nginx berhasil direload."
fi

# 6. Verifikasi Healthcheck
echo "🔍 [6/6] Menjalankan pengujian konektivitas..."
if curl -s http://127.0.0.1:8000/api/health | grep -q '"status":"ok"'; then
    echo "======================================================================"
    echo "🎉 DEPLOYMENT SUKSES!"
    echo "🌐 Akses Portal Online:"
    echo "   - Main URL: https://$DOMAIN"
    echo "   - Local Internal: http://127.0.0.1:8000"
    echo "======================================================================"
    echo "💡 Catatan SSL Let's Encrypt:"
    echo "   Jalankan: sudo certbot --nginx -d $DOMAIN"
else
    echo "⚠️ Peringatan: Container belum merespon. Cek log dengan: docker logs one_gate_portal"
fi
