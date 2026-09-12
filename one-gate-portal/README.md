# One Gate Portal & Single Sign-On (SSO) — Mas Aan Executive Suite

Portal Satu Pintu & Sistem Autentikasi Tunggal Terintegrasi untuk seluruh aplikasi:
1. **Financial Management & Cash Flow** (Port 8003)
2. **Fashion Vendor Tracker** (Port 8002)
3. **Asset Tracker Analytics** (Port 8501)
4. **Senior Investor & BI Bot** (Telegram AI Assistant)

---

## 🚀 Fitur Utama
- **Autentikasi Terpusat:** Menggunakan skema `APP_AUTH` di Supabase PostgreSQL dengan hashing aman (PBKDF2) dan signed JWT Tokens.
- **Akun Tunggal:** Username `Aan` (Role: `admin`) berlaku serentak di semua aplikasi.
- **Master App Launcher:** Satu dashboard eksekutif untuk membuka aplikasi tanpa perlu memasukkan password berulang kali.
- **Live Multi-App KPI Bar:** Menampilkan akumulasi total aset, kas tabungan bank, portofolio saham/emas, dan sisa kewajiban vendor konveksi secara *real-time*.

---

## 🛠️ Cara Menjalankan Secara Lokal
```bash
cd "d:\Practice Program\one-gate-portal"
pip install -r requirements.txt
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
Buka browser di: `http://localhost:8000`

---

## 🌐 Cara Deploy ke VPS
```bash
# Dari folder one-gate-portal di VPS
chmod +x deploy-vps.sh
./deploy-vps.sh
```
Aplikasi akan berjalan otomatis di latar belakang (*background*) pada **Port 8000**.
