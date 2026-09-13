# Standard Operating Procedure (SOP) Deployment ke VPS

Dokumen ini berisi panduan resmi dan alur kerja (*workflow*) untuk melakukan update kode dan deployment aplikasi ke VPS **basecampmeera.cloud** (`203.194.112.223`) secara cepat, aman, dan otomatis.

---

## 🎯 Ringkasan Mekanisme (1-Click Deployment)

Untuk memudahkan deployment tanpa perlu login manual atau mengetik perintah panjang di terminal server, telah disediakan skrip otomatisasi di folder proyek lokal:

| Proyek | Skrip PowerShell | File Shortcut (Double Click) | Domain Live |
|---|---|---|---|
| **Financial Management** | `.\deploy.ps1` | `deploy.bat` | `https://finance.basecampmeera.cloud` |
| **One Gate Portal** | `.\deploy.ps1` | `deploy.bat` | `https://basecampmeera.cloud` |

---

## 📋 Alur Kerja Standar (Standard Workflow)

```
[1. Coding & Modifikasi Lokal]
               │
               ▼
[2. Uji Coba Lokal / Pytest]
               │
               ▼
[3. Commit & Push ke GitHub]
               │
               ▼
[4. Jalankan 1-Click Deploy (deploy.bat / .\deploy.ps1)]
               │
               ▼
[5. Verifikasi Otomatis & Live Check di Browser]
```

---

## 🚀 Langkah-langkah Deployment

### Cara 1: Menggunakan 1-Click Script (Sangat Direkomendasikan)
1. **Lakukan perubahan kode** pada folder proyek Anda di lokal.
2. Buka folder proyek di Windows Explorer / Terminal:
   - **Financial Management**: `D:\Financial Management`
   - **One Gate Portal**: `d:\Practice Program\one-gate-portal`
3. **Jalankan Skrip**:
   - Klik ganda (Double Click) file `deploy.bat` **ATAU**
   - Di PowerShell ketik:
     ```powershell
     .\deploy.ps1
     ```
4. **Apa yang dilakukan skrip secara otomatis?**
   - Mengirim folder `src/`, `static/`, dan konfigurasi terbaru ke VPS via SSH/SCP.
   - Membangun ulang (*build*) container Docker secara zero-downtime.
   - Me-reload reverse proxy Nginx dan SSL certbot.
   - Melakukan polling health check hingga status `HTTP 200 OK`.

---

### Cara 2: Deployment Manual via Terminal VPS (Opsional / Debugging)

Jika Anda sedang terhubung via SSH ke server:

```bash
# 1. Masuk ke direktori aplikasi
cd /home/ubuntu/financial_management
# (atau cd /var/www/one-gate-portal)

# 2. Rebuild dan jalankan container Docker
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

# 3. Reload konfigurasi Nginx
sudo systemctl reload nginx

# 4. Periksa log aplikasi jika diperlukan
docker logs --tail 50 financial-management-app
```

---

## 🔍 Checklist Verifikasi Pasca Deploy

Setelah pesan `✅ Deployment Berhasil!` muncul:
1. Buka browser (rekomendasi mode *Incognito* / *Hard Refresh* `Ctrl + F5` untuk memastikan cache aset CSS/JS bersih).
2. Akses URL:
   - Financial Management: [https://finance.basecampmeera.cloud](https://finance.basecampmeera.cloud)
   - Portal SSO: [https://basecampmeera.cloud](https://basecampmeera.cloud)
3. Pastikan data live, tema (Dark/Light mode), dan kalkulasi berjalan dengan normal.

---

## 🛠️ Troubleshooting & Penanganan Kendala

| Kendala | Penyebab Umum | Solusi |
|---|---|---|
| **HTTP 502 Bad Gateway** | Container uvicorn masih dalam proses booting | Tunggu 5-10 detik atau cek log: `ssh root@203.194.112.223 "docker logs financial-management-app"` |
| **Permission Denied (SSH)** | Kunci SSH lokal belum dikenali server | Pastikan file `~/.ssh/id_rsa` tersedia di komputer Anda |
| **Data di Web Tidak Berubah** | Cache browser lokal masih menyimpan JS/CSS lama | Tekan tombol `Ctrl + Shift + R` atau `Ctrl + F5` di browser |
