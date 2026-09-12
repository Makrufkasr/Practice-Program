import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

SCHEMA_AUTH = "APP_AUTH"
SCHEMA_ASSET_TRACKER = "APP_ASSET_TRACKER"
SCHEMA_FINANCIAL = "APP_FINANCIAL_PLANNING"
SCHEMA_VENDOR_TRACKER = "Vendor_tracker"


def init_db():
    """Membuat schema APP_AUTH dan tabel users jika belum ada, serta sinkronisasi awal akun Aan."""
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA_AUTH}";'))
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS "{SCHEMA_AUTH}".users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    nama_lengkap VARCHAR(150) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    telegram_chat_id VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # Periksa apakah user Aan sudah ada di APP_AUTH.users
            res = conn.execute(text(f'SELECT count(*) FROM "{SCHEMA_AUTH}".users WHERE LOWER(username) = \'aan\';')).scalar()
            if res == 0:
                # Ambil data Aan dari APP_ASSET_TRACKER.pengguna jika tersedia
                p_row = conn.execute(text(f'SELECT password_hash, nama_lengkap, role FROM "{SCHEMA_ASSET_TRACKER}".pengguna WHERE username = \'Aan\';')).fetchone()
                if p_row:
                    pwd_hash, nama_l, rle = p_row
                else:
                    # Fallback ke hash admin123
                    from src.auth import hash_password
                    pwd_hash = hash_password("admin123")
                    nama_l, rle = "Aan", "admin"

                conn.execute(text(f"""
                    INSERT INTO "{SCHEMA_AUTH}".users (username, password_hash, nama_lengkap, role, is_active)
                    VALUES ('Aan', :pwd, :nama, :rle, TRUE)
                    ON CONFLICT (username) DO NOTHING;
                """), {"pwd": pwd_hash, "nama": nama_l or "Aan", "rle": rle or "admin"})
                logging.info("Akun Aan berhasil disinkronkan ke APP_AUTH.users.")
            
            logging.info("Schema APP_AUTH dan tabel users siap digunakan.")
            return True
    except Exception as e:
        logging.error(f"Error init_db: {e}")
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fetch_quick_metrics(username: str = "Aan") -> dict:
    """Mengambil metrik ringkas terintegrasi untuk ditampilkan pada widget dashboard One Gate."""
    metrics = {
        "tabungan": 0.0,
        "investasi": 0.0,
        "hutang_vendor": 0.0,
        "total_asset": 0.0,
        "vendor_orders_pending": 0,
        "status_bot": "Aktif & Berjalan"
    }
    try:
        with engine.connect() as conn:
            # 1. Total Tabungan
            try:
                res_tab = conn.execute(text(f"""
                    SELECT COALESCE(SUM(saldo), 0) 
                    FROM "{SCHEMA_ASSET_TRACKER}".tabungan 
                    WHERE username = :u;
                """), {"u": username}).scalar()
                metrics["tabungan"] = float(res_tab or 0.0)
            except Exception:
                pass

            # 2. Total Investasi Portofolio
            try:
                # Ambil harga kpi_data terakhir
                p_rows = conn.execute(text(f"""
                    SELECT p.nama_aset, p.jumlah, p.harga_beli,
                           COALESCE((
                               SELECT k.harga_tutup 
                               FROM "{SCHEMA_ASSET_TRACKER}".kpi_data k 
                               WHERE k.nama_aset = p.nama_aset 
                               ORDER BY k.tanggal DESC LIMIT 1
                           ), p.harga_beli) as harga_pasar
                    FROM "{SCHEMA_ASSET_TRACKER}".portofolio p
                    WHERE p.username = :u;
                """), {"u": username}).fetchall()
                total_inv = sum(float(r[1] or 0.0) * float(r[3] or r[2] or 0.0) for r in p_rows)
                metrics["investasi"] = round(total_inv, 2)
            except Exception:
                pass

            # 3. Kekurangan Bayar Vendor
            try:
                res_vendor = conn.execute(text(f"""
                    SELECT 
                        COUNT(o.id) as pending_orders,
                        COALESCE(SUM(o.vendor_cost - COALESCE(p.total_paid, 0)), 0) as total_debt
                    FROM "{SCHEMA_VENDOR_TRACKER}".orders o
                    LEFT JOIN (
                        SELECT order_id, SUM(amount) as total_paid 
                        FROM "{SCHEMA_VENDOR_TRACKER}".vendor_payments 
                        GROUP BY order_id
                    ) p ON o.id = p.order_id
                    WHERE COALESCE(o.vendor_cost, 0) - COALESCE(p.total_paid, 0) > 0;
                """)).fetchone()
                if res_vendor:
                    metrics["vendor_orders_pending"] = int(res_vendor[0] or 0)
                    metrics["hutang_vendor"] = float(res_vendor[1] or 0.0)
            except Exception:
                pass

            metrics["total_asset"] = round(metrics["tabungan"] + metrics["investasi"], 2)
    except Exception as e:
        logging.error(f"Error fetching quick metrics: {e}")

    return metrics
