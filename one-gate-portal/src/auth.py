import os
import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, Tuple
import jwt
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "one-gate-portal-sso-secret-key-aan-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "14"))

SCHEMA_AUTH = "APP_AUTH"
SCHEMA_ASSET_TRACKER = "APP_ASSET_TRACKER"


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
    Memverifikasi kredensial pengguna ke skema APP_AUTH.users (dengan fallback ke APP_ASSET_TRACKER.pengguna).
    Mengembalikan data user jika valid.
    """
    clean_u = username.strip()
    with engine.connect() as conn:
        # 1. Cari di APP_AUTH.users
        query = text(f"""
            SELECT id, username, password_hash, nama_lengkap, role, is_active 
            FROM "{SCHEMA_AUTH}".users 
            WHERE LOWER(username) = LOWER(:u);
        """)
        row = conn.execute(query, {"u": clean_u}).fetchone()

        # 2. Jika belum ada di APP_AUTH, cari di APP_ASSET_TRACKER.pengguna
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
                    # Auto migrate ke APP_AUTH.users
                    conn.execute(text(f"""
                        INSERT INTO "{SCHEMA_AUTH}".users (username, password_hash, nama_lengkap, role, is_active)
                        VALUES (:username, :password_hash, :nama, :role, TRUE)
                        ON CONFLICT (username) DO NOTHING;
                    """), {
                        "username": fb_row[1],
                        "password_hash": stored_hash,
                        "nama": fb_row[3],
                        "role": fb_row[4]
                    })
                    conn.commit()
                    return {
                        "id": fb_row[0],
                        "username": fb_row[1],
                        "nama_lengkap": fb_row[3],
                        "role": fb_row[4]
                    }
            return None

        # Verifikasi password dari APP_AUTH
        uid, uname, stored_hash, nama_l, role, is_active = row
        if not is_active:
            return None

        if verify_password(stored_hash, password):
            return {
                "id": uid,
                "username": uname,
                "nama_lengkap": nama_l,
                "role": role
            }

    return None


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
