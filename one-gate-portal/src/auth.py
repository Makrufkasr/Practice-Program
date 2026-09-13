import sys
import os
import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, Tuple, List
import jwt
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "one-gate-portal-sso-secret-key-aan-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "14"))

SCHEMA_AUTH = "APP_AUTH"
SCHEMA_ASSET_TRACKER = "APP_ASSET_TRACKER"
SCHEMA_FINANCIAL = "APP_FINANCIAL_PLANNING"


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hash password menggunakan PBKDF2-HMAC-SHA256 dengan salt 16-byte."""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return f"{salt}:{pwd_hash}"


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifikasi password dengan mencocokkan hash tersimpan."""
    try:
        if not stored_password or ":" not in stored_password:
            return False
        salt, _ = stored_password.split(':', 1)
        return hash_password(provided_password, salt) == stored_password
    except Exception:
        return False


def create_access_token(data: dict, expires_days: int = JWT_EXPIRATION_DAYS) -> str:
    """Membuat JSON Web Token (JWT) yang ditandatangani dengan rahasia terpusat."""
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_days)
    to_encode.update({
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "iss": "one-gate-portal"
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> Optional[dict]:
    """Mendekode dan memvalidasi JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def authenticate_user(engine, username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Memverifikasi kredensial pengguna.
    Mengembalikan data user atau error approval jika akun masih pending.
    """
    clean_u = username.strip()
    with engine.connect() as conn:
        # 1. Cari di APP_AUTH.users
        query = text(f"""
            SELECT id, username, password_hash, nama_lengkap, role, is_active, status 
            FROM "{SCHEMA_AUTH}".users 
            WHERE LOWER(username) = LOWER(:u);
        """)
        row = conn.execute(query, {"u": clean_u}).fetchone()

        # 2. Jika belum ada di APP_AUTH, cari di APP_ASSET_TRACKER.pengguna (legacy sync)
        if not row:
            fb_query = text(f"""
                SELECT id, username, password_hash, nama_lengkap, role 
                FROM "{SCHEMA_ASSET_TRACKER}".pengguna 
                WHERE LOWER(username) = LOWER(:u);
            """)
            fb_row = conn.execute(fb_query, {"u": clean_u}).fetchone()
            if fb_row:
                stored_hash = fb_row[2]
                if verify_password(stored_hash, password):
                    is_aan = (clean_u.lower() == "aan")
                    role_val = "superadmin" if is_aan else "user"
                    conn.execute(text(f"""
                        INSERT INTO "{SCHEMA_AUTH}".users (username, password_hash, nama_lengkap, role, status, is_active)
                        VALUES (:username, :password_hash, :nama, :role, 'approved', TRUE)
                        ON CONFLICT (username) DO UPDATE 
                        SET status = 'approved', is_active = TRUE;
                    """), {
                        "username": fb_row[1],
                        "password_hash": stored_hash,
                        "nama": fb_row[3],
                        "role": role_val
                    })
                    conn.commit()
                    return {
                        "id": fb_row[0],
                        "username": fb_row[1],
                        "nama_lengkap": fb_row[3],
                        "role": role_val,
                        "is_superadmin": is_aan,
                        "status": "approved"
                    }
            return None

        uid, uname, stored_hash, nama_l, role, is_active, status_val = row

        if not verify_password(stored_hash, password):
            return None

        # Superadmin Aan selalu diizinkan
        is_aan = (uname.lower() == "aan" or role == "superadmin")
        if is_aan:
            return {
                "id": uid,
                "username": uname,
                "nama_lengkap": nama_l,
                "role": "superadmin",
                "is_superadmin": True,
                "status": "approved"
            }

        # Cek status approval untuk user lain
        current_status = (status_val or "pending").lower()
        if current_status == "pending" or not is_active:
            return {
                "error": "PENDING_APPROVAL",
                "message": "Akun Anda sedang menunggu persetujuan (approval) dari Aan sebelum dapat login."
            }
        elif current_status == "rejected":
            return {
                "error": "REJECTED",
                "message": "Pendaftaran akun Anda tidak disetujui."
            }

        return {
            "id": uid,
            "username": uname,
            "nama_lengkap": nama_l,
            "role": "user",
            "is_superadmin": False,
            "status": "approved"
        }


def register_user(engine, username: str, password: str, nama_lengkap: str, telegram_chat_id: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]], bool]:
    """
    Mendaftarkan pengguna baru dengan status PENDING approval dari Aan.
    Mengembalikan (success, message, user_dict, is_pending).
    """
    clean_u = username.strip()
    clean_n = nama_lengkap.strip()
    clean_p = password.strip()

    if len(clean_u) < 3:
        return False, "Username minimal 3 karakter.", None, False
    if len(clean_p) < 6:
        return False, "Password minimal 6 karakter.", None, False
    if len(clean_n) < 2:
        return False, "Nama lengkap harus diisi dengan benar.", None, False

    with engine.begin() as conn:
        # Cek apakah username sudah ada di APP_AUTH.users
        check_q = text(f"""
            SELECT id, status FROM "{SCHEMA_AUTH}".users 
            WHERE LOWER(username) = LOWER(:u);
        """)
        exists = conn.execute(check_q, {"u": clean_u}).fetchone()
        if exists:
            if exists[1] == "pending":
                return False, f"Pendaftaran dengan username '{clean_u}' sudah masuk dan sedang menunggu persetujuan Aan.", None, True
            return False, f"Username '{clean_u}' sudah digunakan. Silakan gunakan username lain.", None, False

        # Hash password dan simpan dengan status PENDING
        pwd_hash = hash_password(clean_p)
        ins_q = text(f"""
            INSERT INTO "{SCHEMA_AUTH}".users (username, password_hash, nama_lengkap, role, status, telegram_chat_id, is_active)
            VALUES (:u, :p, :n, 'user', 'pending', :tg, FALSE)
            RETURNING id, created_at;
        """)
        row = conn.execute(ins_q, {
            "u": clean_u,
            "p": pwd_hash,
            "n": clean_n,
            "tg": telegram_chat_id
        }).fetchone()
        new_id = row[0]

        user_dict = {
            "id": new_id,
            "username": clean_u,
            "nama_lengkap": clean_n,
            "status": "pending",
            "is_active": False
        }
        return True, "Pendaftaran berhasil! Akun Anda sedang menunggu persetujuan (approval) dari Mas Aan sebelum dapat digunakan.", user_dict, True


def get_pending_registrations(engine) -> List[Dict[str, Any]]:
    """Mengambil daftar seluruh pendaftaran akun yang menunggu persetujuan Aan."""
    results = []
    with engine.connect() as conn:
        query = text(f"""
            SELECT id, username, nama_lengkap, created_at, status 
            FROM "{SCHEMA_AUTH}".users 
            WHERE status = 'pending' 
            ORDER BY created_at DESC;
        """)
        rows = conn.execute(query).fetchall()
        for r in rows:
            created_str = r[3].strftime("%d %b %Y, %H:%M") if r[3] else "-"
            results.append({
                "id": r[0],
                "username": r[1],
                "nama_lengkap": r[2],
                "created_at": created_str,
                "status": r[4]
            })
    return results


def approve_user_registration(engine, user_id: int) -> Tuple[bool, str, Optional[str]]:
    """Aan menyetujui pendaftaran akun pengguna."""
    with engine.begin() as conn:
        q = text(f"""
            SELECT id, username, password_hash, nama_lengkap 
            FROM "{SCHEMA_AUTH}".users 
            WHERE id = :uid AND status = 'pending';
        """)
        row = conn.execute(q, {"uid": user_id}).fetchone()
        if not row:
            return False, "Data pendaftaran tidak ditemukan atau sudah diproses.", None

        uid, uname, pwd_hash, nama_l = row

        # Set ke approved & aktif
        conn.execute(text(f"""
            UPDATE "{SCHEMA_AUTH}".users 
            SET status = 'approved', is_active = TRUE, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :uid;
        """), {"uid": uid})

        # Sinkronkan ke schema portofolio & finansial
        try:
            conn.execute(text(f"""
                INSERT INTO "{SCHEMA_ASSET_TRACKER}".pengguna (username, password_hash, nama_lengkap, role)
                VALUES (:u, :p, :n, 'user')
                ON CONFLICT (username) DO NOTHING;
            """), {"u": uname, "p": pwd_hash, "n": nama_l})
        except Exception:
            pass

        try:
            conn.execute(text(f"""
                INSERT INTO "{SCHEMA_FINANCIAL}".user_profiles (username, display_name, currency)
                VALUES (:u, :n, 'IDR')
                ON CONFLICT (username) DO NOTHING;
            """), {"u": uname, "n": nama_l})
        except Exception:
            pass

        return True, f"Akun '{uname}' ({nama_l}) berhasil disetujui! Pengguna kini dapat masuk ke ekosistem.", uname


def reject_user_registration(engine, user_id: int) -> Tuple[bool, str]:
    """Aan menolak pendaftaran akun pengguna."""
    with engine.begin() as conn:
        q = text(f"""
            UPDATE "{SCHEMA_AUTH}".users 
            SET status = 'rejected', is_active = FALSE, updated_at = CURRENT_TIMESTAMP 
            WHERE id = :uid AND status = 'pending';
        """)
        res = conn.execute(q, {"uid": user_id})
        if res.rowcount == 0:
            return False, "Data pendaftaran tidak ditemukan atau sudah diproses."
        return True, "Pendaftaran akun berhasil ditolak."


def change_user_password(engine, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    """Mengubah password pengguna di database pusat."""
    if len(new_password) < 6:
        return False, "Password baru minimal 6 karakter."

    with engine.begin() as conn:
        query = text(f"""
            SELECT password_hash FROM "{SCHEMA_AUTH}".users 
            WHERE LOWER(username) = LOWER(:u);
        """)
        row = conn.execute(query, {"u": username.strip()}).fetchone()
        if not row or not verify_password(row[0], old_password):
            return False, "Password lama tidak sesuai."

        new_hash = hash_password(new_password)
        conn.execute(text(f"""
            UPDATE "{SCHEMA_AUTH}".users 
            SET password_hash = :p, updated_at = CURRENT_TIMESTAMP 
            WHERE LOWER(username) = LOWER(:u);
        """), {"p": new_hash, "u": username.strip()})

        # Sync juga ke APP_ASSET_TRACKER.pengguna untuk backward compatibility
        try:
            conn.execute(text(f"""
                UPDATE "{SCHEMA_ASSET_TRACKER}".pengguna 
                SET password_hash = :p 
                WHERE LOWER(username) = LOWER(:u);
            """), {"p": new_hash, "u": username.strip()})
        except Exception:
            pass

        return True, "Password berhasil diperbarui."
