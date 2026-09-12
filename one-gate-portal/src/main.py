import os
import logging
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.database import init_db, engine, fetch_quick_metrics
from src.auth import authenticate_user, create_access_token, verify_access_token, change_user_password

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="One Gate Portal & Single Sign-On (SSO)",
    description="Pintu Gerbang Utama & Autentikasi Tunggal Terintegrasi Aplikasi Mas Aan",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inisialisasi skema & tabel auth saat startup
@app.on_event("startup")
def on_startup():
    init_db()


# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


# --- Dependency Helper: Get Authenticated User ---
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token autentikasi tidak ditemukan.")
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token kedaluwarsa atau tidak valid.")
    return payload


# --- Auth Endpoints ---

@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Endpoint login tunggal. Memvalidasi username & password, mengembalikan token JWT."""
    user = authenticate_user(engine, req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username atau password tidak sesuai.")

    token = create_access_token({
        "sub": str(user["id"]),
        "username": user["username"],
        "nama_lengkap": user["nama_lengkap"],
        "role": user["role"]
    })

    return {
        "status": "success",
        "message": f"Selamat datang kembali, {user['nama_lengkap']}!",
        "token": token,
        "user": user
    }


@app.get("/api/auth/verify")
def verify_token(token: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """
    Endpoint verifikasi token JWT untuk aplikasi eksternal (Financial Management, Vendor Tracker).
    Menerima token via Query Parameter atau Authorization Header.
    """
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token tidak disertakan.")

    payload = verify_access_token(raw_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid atau telah kedaluwarsa.")

    return {
        "valid": True,
        "user": {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "nama_lengkap": payload.get("nama_lengkap"),
            "role": payload.get("role")
        }
    }


@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    return {"user": user}


@app.post("/api/auth/change-password")
def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    success, msg = change_user_password(engine, user["username"], req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg}


# --- App Directory & Dashboard Endpoints ---

@app.get("/api/apps")
def get_registered_apps(user: dict = Depends(get_current_user)):
    """Daftar aplikasi terintegrasi yang tersedia di ekosistem Mas Aan."""
    # Menentukan host dasar sesuai origin atau VPS default
    vps_ip = os.getenv("VPS_HOST", "localhost")
    
    apps = [
        {
            "id": "finance",
            "name": "Financial Management",
            "subtitle": "Perencanaan Keuangan, Cash Flow & Alokasi Beban",
            "category": "Keuangan & Investasi",
            "port": 8003,
            "url": f"http://{vps_ip}:8003",
            "icon": "wallet",
            "accent_color": "#10B981", # Emerald Green
            "status": "Online",
            "badge": "Active",
            "description": "Kelola cash flow 12 bulan, sinkronisasi tabungan live, portofolio aset, dan pelunasan kewajiban vendor."
        },
        {
            "id": "fashion-vendor",
            "name": "Fashion Vendor Tracker",
            "subtitle": "Order Tracking, Pembayaran & Kewajiban Vendor",
            "category": "Operasional Bisnis",
            "port": 8002,
            "url": f"http://{vps_ip}:8002",
            "icon": "tag",
            "accent_color": "#EC4899", # Pink Modern
            "status": "Online",
            "badge": "Active",
            "description": "Pantau status pesanan konveksi/vendor fashion, termin pembayaran, jatuh tempo, serta histori pelunasan."
        },
        {
            "id": "asset-tracker",
            "name": "Asset Tracker Analytics",
            "subtitle": "Monitor Portofolio Saham & Komoditas Riil",
            "category": "Investasi Pasar Modal",
            "port": 8501,
            "url": f"http://{vps_ip}:8501",
            "icon": "trending-up",
            "accent_color": "#6366F1", # Indigo
            "status": "Online",
            "badge": "Active",
            "description": "Dashboard interaktif portofolio multi-aset, visualisasi return IHSG vs Portofolio Mas Aan."
        },
        {
            "id": "ai-assistant",
            "name": "Senior Investor & BI Bot",
            "subtitle": "Telegram Intelligence, Screener & Otomasi Transaksi",
            "category": "Artificial Intelligence",
            "port": None,
            "url": "https://t.me",
            "icon": "cpu",
            "accent_color": "#F59E0B", # Amber
            "status": "Aktif (Background)",
            "badge": "24/7 Service",
            "description": "Asisten cerdas Telegram berbasis Gemini AI Flash untuk mencatat transaksi otomatis, screening swing, dan scalping kilat."
        }
    ]
    return {"apps": apps}


@app.get("/api/quick-stats")
def get_quick_stats(user: dict = Depends(get_current_user)):
    """Mengambil metrik ringkas terintegrasi lintas aplikasi untuk ditampilkan di master portal."""
    uname = user.get("username", "Aan")
    stats = fetch_quick_metrics(uname)
    return {
        "username": uname,
        "nama_lengkap": user.get("nama_lengkap", uname),
        "role": user.get("role", "admin"),
        "metrics": stats
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "one-gate-portal"}


# --- Serve Static UI Files ---
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_portal():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "One Gate Portal API siap. UI frontend sedang disiapkan."}
