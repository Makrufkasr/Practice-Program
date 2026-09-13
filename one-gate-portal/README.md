# Ecosystem Intelligence — One Gate Portal & Single Sign-On (SSO)

Pusat kendali ekosistem digital terintegrasi untuk bisnis apparel **NEXAT**, **ASPIRAN! AI Assistant**, **Financial Management**, dan **Asset Tracker Analytics**.

---

## 🌟 Fitur Utama
- **Single Sign-On (SSO) & JWT Token:** Masuk satu kali untuk mengakses seluruh ekosistem tanpa perlu login ulang.
- **Superadmin (Aan) & Workflow Persetujuan Registrasi:**
  - Registrasi mandiri untuk pengguna baru dengan status *Pending Approval*.
  - Lonceng notifikasi real-time dan modal persetujuan (*Approve/Reject*) eksklusif untuk Aan.
- **Isolasi Data Per Pengguna (*Strict User-Isolated Data Space*):** Setiap pengguna hanya memiliki akses privat ke data portofolio dan keuangan mereka sendiri.
- **Antarmuka Futuristik Command Center:** Dilengkapi jalur sirkuit data cybernetic dinamis (*animated circuit pulse*), kartu aplikasi melayang, dan visualisasi arsitektur live stream.
- **Mobile Friendly:** Desain responsif penuh untuk ponsel/smartphone dengan Quick Navigation Bar.

---

## 🌐 Panduan Launching Online ke `basecamp.meeracloud`

### 1. Konfigurasi DNS (Domain Provider / Cloudflare)
Arahkan DNS Record berikut ke IP VPS Anda:
| Tipe | Nama Host | Target IP | Keterangan |
|---|---|---|---|
| **A** | `basecamp.meeracloud` | `<IP_VPS_ANDA>` | Portal Utama One Gate |
| **A** | `nexat.meeracloud` | `<IP_VPS_ANDA>` | Subdomain NEXAT Apparel |
| **A** | `finance.meeracloud` | `<IP_VPS_ANDA>` | Subdomain Financial Planning |
| **A** | `assets.meeracloud` | `<IP_VPS_ANDA>` | Subdomain Asset Tracker |

---

### 2. Persiapan di Server VPS (Ubuntu / Debian)

Clone atau upload folder `one-gate-portal` ke VPS:
```bash
cd /var/www/one-gate-portal
cp .env.production.example .env
```

Sesuaikan nilai pada file `.env`:
```env
DATABASE_URL=postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
JWT_SECRET=meera-cloud-basecamp-sso-master-key-prod-2026
PORTAL_DOMAIN=basecamp.meeracloud
VPS_HOST=basecamp.meeracloud
```

---

### 3. Eksekusi Skrip Otomatisasi Deploy
Jalankan skrip deployment online:
```bash
chmod +x deploy-online.sh
./deploy-online.sh
```

Skrip ini akan secara otomatis:
1. Memeriksa dan menginstal paket sistem (`Docker`, `docker-compose`, `Nginx`, `Certbot`, `ufw`).
2. Membuka port firewall yang diperlukan (80, 443, 8000, 8002, 8003, 8501).
3. Melakukan build container Docker `one_gate_portal` (Port 8000).
4. Memasang konfigurasi Nginx Reverse Proxy dari `nginx/basecamp.meeracloud.conf`.
5. Memverifikasi healthcheck API.

---

### 4. Konfigurasi SSL / HTTPS Let's Encrypt
Aktifkan sertifikat SSL gratis dari Let's Encrypt:
```bash
sudo certbot --nginx -d basecamp.meeracloud
```

---

### 5. Verifikasi & Pengujian Online
- **Akses Web Portal:** `https://basecamp.meeracloud`
- **Health Check:** `https://basecamp.meeracloud/api/health`
- **Akun Superadmin:** `Aan`

---

## 💻 Menjalankan Secara Lokal (Development)
```bash
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Buka peramban di `http://localhost:8000`.
