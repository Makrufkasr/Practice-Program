import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.database import init_db, engine, fetch_quick_metrics
from src.auth import (
    authenticate_user, 
    register_user, 
    create_access_token, 
    verify_access_token, 
    change_user_password,
    get_pending_registrations,
    approve_user_registration,
    reject_user_registration
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="Ecosystem Intelligence — One Gate Portal",
    description="Pintu Gerbang Utama & Autentikasi Tunggal Terintegrasi Ekosistem",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    nama_lengkap: str
    telegram_chat_id: Optional[str] = None

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


def require_superadmin(user: dict = Depends(get_current_user)):
    uname = (user.get("username") or "").lower()
    is_super = user.get("is_superadmin") or (uname == "aan")
    if not is_super:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Akses khusus Superadmin (Aan)."
        )
    return user


# --- Auth Endpoints ---

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """Mendaftarkan akun baru dengan status PENDING approval Aan."""
    success, msg, user_data, is_pending = register_user(
        engine,
        username=req.username,
        password=req.password,
        nama_lengkap=req.nama_lengkap,
        telegram_chat_id=req.telegram_chat_id
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return {
        "status": "pending_approval",
        "message": msg,
        "user": user_data
    }


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Endpoint login tunggal. Memeriksa status persetujuan akun."""
    auth_result = authenticate_user(engine, req.username, req.password)
    if not auth_result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username atau password tidak sesuai.")

    # Cek jika status pending atau rejected
    if "error" in auth_result:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=auth_result["message"])

    is_super = bool(auth_result.get("is_superadmin"))

    token = create_access_token({
        "sub": str(auth_result["id"]),
        "username": auth_result["username"],
        "nama_lengkap": auth_result["nama_lengkap"],
        "role": auth_result.get("role", "user"),
        "is_superadmin": is_super
    })

    user_data = {
        "id": auth_result["id"],
        "username": auth_result["username"],
        "nama_lengkap": auth_result["nama_lengkap"],
        "role": auth_result.get("role", "user"),
        "is_superadmin": is_super,
        "role_display": "Superadmin (Owner)" if is_super else "Member"
    }

    return {
        "status": "success",
        "message": f"Selamat datang kembali, {auth_result['nama_lengkap']}!",
        "token": token,
        "user": user_data
    }


@app.get("/api/auth/verify")
def verify_token(token: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    """Verifikasi token JWT dan kembalikan profil serta status Superadmin."""
    raw_token = token
    if not raw_token and authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token tidak disertakan.")

    payload = verify_access_token(raw_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak valid atau telah kedaluwarsa.")

    uname = payload.get("username", "")
    is_super = payload.get("is_superadmin") or (uname.lower() == "aan")

    return {
        "valid": True,
        "user": {
            "id": payload.get("sub"),
            "username": uname,
            "nama_lengkap": payload.get("nama_lengkap"),
            "role": payload.get("role", "user"),
            "is_superadmin": is_super,
            "role_display": "Superadmin (Owner)" if is_super else "Member"
        }
    }


@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    uname = user.get("username", "")
    is_super = user.get("is_superadmin") or (uname.lower() == "aan")
    return {
        "user": {
            "id": user.get("sub"),
            "username": uname,
            "nama_lengkap": user.get("nama_lengkap"),
            "role": user.get("role", "user"),
            "is_superadmin": is_super,
            "role_display": "Superadmin (Owner)" if is_super else "Member"
        }
    }


@app.post("/api/auth/change-password")
def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    username = user.get("username")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identitas pengguna tidak valid.")
    success, msg = change_user_password(engine, username, req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg}


# --- Superadmin Approval Endpoints (Aan Exclusive) ---

@app.get("/api/admin/pending-users")
def list_pending_registrations(admin: dict = Depends(require_superadmin)):
    """Mengambil daftar seluruh permintaan registrasi akun yang menunggu persetujuan Aan."""
    pending_list = get_pending_registrations(engine)
    return {
        "count": len(pending_list),
        "pending_users": pending_list
    }


@app.post("/api/admin/approve-user/{user_id}")
def approve_user(user_id: int, admin: dict = Depends(require_superadmin)):
    """Aan menyetujui akun baru."""
    success, msg, uname = approve_user_registration(engine, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg, "approved_username": uname}


@app.post("/api/admin/reject-user/{user_id}")
def reject_user(user_id: int, admin: dict = Depends(require_superadmin)):
    """Aan menolak akun baru."""
    success, msg = reject_user_registration(engine, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return {"status": "success", "message": msg}


# --- App Directory & Dashboard (User Isolated) ---

@app.get("/api/apps")
def get_registered_apps(user: dict = Depends(get_current_user)):
    """Daftar seluruh modul aplikasi terintegrasi untuk pengguna yang telah login."""
    portal_host = os.getenv("PORTAL_DOMAIN", os.getenv("VPS_HOST", "localhost"))
    is_prod_domain = "meeracloud" in portal_host or portal_host not in ["localhost", "127.0.0.1"]
    default_protocol = "https" if is_prod_domain else "http"

    # Dynamic URLs with fallback
    nexat_url = os.getenv("NEXAT_URL", f"https://{portal_host}:8002" if is_prod_domain else f"http://{portal_host}:8002")
    aspiran_url = os.getenv("ASPIRAN_URL", "https://t.me/SeniorInvestorBot")
    finance_url = os.getenv("FINANCE_URL", f"https://finance.{portal_host.replace('www.', '').replace('basecamp.', '')}" if is_prod_domain else f"http://{portal_host}:8003")
    asset_url = os.getenv("ASSET_TRACKER_URL", "https://practice-program-fb3wd5vvoslgltdyf9fwzq.streamlit.app/")

    all_apps = [
        {
            "id": "nexat",
            "key": "nexat",
            "name": "NEXAT Project Apparel",
            "subtitle": "Order Konveksi, HPP & Tracking Vendor",
            "category": "Operasional Bisnis",
            "port": 8002,
            "url": nexat_url,
            "icon": "t-shirt",
            "accent_color": "#0284C7",
            "status": "Online",
            "badge": "Port 8002",
            "description": "Kelola order batch pakaian, kontrol HPP per item, dan jadwal pembayaran termin vendor konveksi.",
            "is_allowed": True
        },
        {
            "id": "aspiran",
            "key": "aspiran",
            "name": "ASPIRAN! AI Assistant",
            "subtitle": "Telegram Bot & Intelligence Screener",
            "category": "Artificial Intelligence",
            "port": None,
            "url": aspiran_url,
            "icon": "robot",
            "accent_color": "#6366F1",
            "status": "Active 24/7",
            "badge": "Telegram Bot",
            "description": "Asisten bertenaga Gemini Flash untuk monitoring bisnis, screener saham IHSG, dan konsultasi interaktif.",
            "is_allowed": True
        },
        {
            "id": "finance",
            "key": "finance",
            "name": "Financial Management",
            "subtitle": "12-Month Cash Flow & Forecasting",
            "category": "Arus Kas & Beban",
            "port": 8003,
            "url": finance_url,
            "icon": "currency-circle-dollar",
            "accent_color": "#10B981",
            "status": "Online",
            "badge": "Port 8003",
            "description": "Monitoring cash flow 12 bulan, evaluasi pos pengeluaran rutin, forecast horizon, dan target dana darurat.",
            "is_allowed": True
        },
        {
            "id": "asset-tracker",
            "key": "asset-tracker",
            "name": "Asset Tracker Analytics",
            "subtitle": "Valuasi Portofolio & Roadmap 2030",
            "category": "Net Worth & Aset",
            "port": 8501,
            "url": asset_url,
            "icon": "chart-donut",
            "accent_color": "#F59E0B",
            "status": "Online",
            "badge": "Port 8501",
            "description": "Visualisasi multi-aset (properti, saham IHSG, emas, kas likuid) dan pemantauan target kekayaan bersih jangka panjang.",
            "is_allowed": True
        }
    ]

    return {
        "apps": all_apps,
        "username": user.get("username")
    }


@app.get("/api/quick-stats")
def get_quick_stats(user: dict = Depends(get_current_user)):
    """Mengambil metrik ringkas terintegrasi yang terisolasi secara privat khusus untuk username yang sedang login."""
    uname = user.get("username", "")
    metrics = fetch_quick_metrics(uname)

    return {
        "username": uname,
        "nama_lengkap": user.get("nama_lengkap", uname),
        "metrics": metrics
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
    return {"message": "One Gate Portal API siap."}
