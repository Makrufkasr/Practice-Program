import hashlib
import secrets
from sqlalchemy import create_engine, text

ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(ALAMAT_DATABASE)

def hash_password(password: str, salt: str = None) -> str:
    """Hash password menggunakan PBKDF2-HMAC-SHA256 dengan salt."""
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
    """Verifikasi password dengan mencocokkan hash yang disimpan dengan input."""
    try:
        salt, _ = stored_password.split(':')
        return hash_password(provided_password, salt) == stored_password
    except Exception:
        return False

def init_db_auth():
    """Membuat tabel pengguna jika belum ada dan menyisipkan akun admin default jika kosong."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS pengguna (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        nama_lengkap VARCHAR(100),
        role VARCHAR(20) DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_query))
        
        # Tambah kolom username ke tabel portofolio jika belum ada untuk isolasi user
        alter_portofolio_query = """
        ALTER TABLE portofolio ADD COLUMN IF NOT EXISTS username VARCHAR(50) DEFAULT 'admin';
        """
        conn.execute(text(alter_portofolio_query))
        conn.commit()
        
        # Cek apakah ada pengguna di database
        check_query = "SELECT COUNT(*) FROM pengguna;"
        result = conn.execute(text(check_query)).scalar()
        
        if result == 0:
            # Buat pengguna admin default
            default_username = "admin"
            default_password = "admin123"
            hash_pwd = hash_password(default_password)
            
            insert_query = """
            INSERT INTO pengguna (username, password_hash, nama_lengkap, role)
            VALUES (:username, :password_hash, :nama_lengkap, :role);
            """
            conn.execute(
                text(insert_query),
                {
                    "username": default_username,
                    "password_hash": hash_pwd,
                    "nama_lengkap": "Administrator Utama",
                    "role": "admin"
                }
            )
            conn.commit()
            print("Database diinisialisasi: Akun admin default berhasil dibuat.")
        else:
            print("Database auth sudah siap.")

def autentikasi_pengguna(username, password):
    """Mengecek kredensial pengguna dari database."""
    query = "SELECT password_hash, nama_lengkap, role FROM pengguna WHERE username = :username;"
    with engine.connect() as conn:
        result = conn.execute(text(query), {"username": username}).fetchone()
        if result:
            stored_hash, nama_lengkap, role = result
            if verify_password(stored_hash, password):
                return {
                    "authenticated": True, 
                    "username": username, 
                    "nama_lengkap": nama_lengkap, 
                    "role": role
                }
    return {"authenticated": False}

def tambah_pengguna(username, password, nama_lengkap, role="user"):
    """Menambahkan pengguna baru ke database."""
    # Cek apakah username sudah ada
    check_query = "SELECT COUNT(*) FROM pengguna WHERE username = :username;"
    insert_query = """
    INSERT INTO pengguna (username, password_hash, nama_lengkap, role)
    VALUES (:username, :password_hash, :nama_lengkap, :role);
    """
    try:
        with engine.connect() as conn:
            exists = conn.execute(text(check_query), {"username": username}).scalar()
            if exists > 0:
                return {"status": "gagal", "pesan": "Username sudah terdaftar."}
            
            hash_pwd = hash_password(password)
            conn.execute(
                text(insert_query),
                {
                    "username": username,
                    "password_hash": hash_pwd,
                    "nama_lengkap": nama_lengkap,
                    "role": role
                }
            )
            conn.commit()
            return {"status": "sukses", "pesan": f"Pengguna {username} berhasil didaftarkan."}
    except Exception as e:
        return {"status": "gagal", "pesan": f"Kesalahan database: {str(e)}"}

def ganti_password(username, password_baru):
    """Mengubah password pengguna di database."""
    update_query = """
    UPDATE pengguna 
    SET password_hash = :password_hash 
    WHERE username = :username;
    """
    try:
        with engine.connect() as conn:
            hash_pwd = hash_password(password_baru)
            result = conn.execute(
                text(update_query),
                {
                    "username": username,
                    "password_hash": hash_pwd
                }
            )
            conn.commit()
            return {"status": "sukses", "pesan": "Password berhasil diubah."}
    except Exception as e:
        return {"status": "gagal", "pesan": f"Kesalahan database: {str(e)}"}

def ambil_semua_pengguna():
    """Mengambil semua daftar pengguna dari database."""
    query = "SELECT username, nama_lengkap, role, created_at FROM pengguna ORDER BY created_at DESC;"
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            return [{"username": row[0], "nama_lengkap": row[1], "role": row[2], "created_at": row[3]} for row in result]
    except Exception as e:
        print(f"Error ambil_semua_pengguna: {e}")
        return []

def ubah_role_pengguna(username, role_baru):
    """Mengubah role pengguna di database."""
    query = "UPDATE pengguna SET role = :role WHERE username = :username;"
    try:
        with engine.connect() as conn:
            conn.execute(text(query), {"role": role_baru, "username": username})
            conn.commit()
            return {"status": "sukses", "pesan": f"Role pengguna {username} berhasil diubah menjadi {role_baru}."}
    except Exception as e:
        return {"status": "gagal", "pesan": f"Kesalahan database: {str(e)}"}

def hapus_pengguna(username):
    """Menghapus pengguna dari database."""
    if username == "admin":
        return {"status": "gagal", "pesan": "Akun admin utama tidak dapat dihapus."}
        
    query = "DELETE FROM pengguna WHERE username = :username;"
    try:
        with engine.connect() as conn:
            conn.execute(text(query), {"username": username})
            conn.commit()
            return {"status": "sukses", "pesan": f"Pengguna {username} berhasil dihapus dari sistem."}
    except Exception as e:
        return {"status": "gagal", "pesan": f"Kesalahan database: {str(e)}"}

