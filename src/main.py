from fastapi import FastAPI
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI()

ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(ALAMAT_DATABASE)

@app.get("/")
def halaman_utama():
    return {"status": "Backend API Berjalan Sukses", "proyek": "Automated KPI Dashboard"}

@app.get("/api/data")
def ambil_data_kpi():
    query = "SELECT * FROM kpi_data ORDER BY tanggal DESC;"
    df = pd.read_sql(query, con=engine)
    
    df['tanggal'] = df['tanggal'].astype(str)
    if 'updated_at' in df.columns:
        df['updated_at'] = df['updated_at'].astype(str)
    
    data_json = df.to_dict(orient="records")
    return {"total_data": len(data_json), "data": data_json}

@app.get("/api/portofolio")
def ambil_portofolio():
    try:
        # 1. Ambil data portofolio
        df_port = pd.read_sql("SELECT * FROM portofolio ORDER BY tanggal_beli DESC;", con=engine)
        
        if df_port.empty:
            return {"status": "sukses", "total_investasi": 0.0, "nilai_sekarang": 0.0, "profit_loss": 0.0, "data": []}
            
        # 2. Ambil data harga terbaru
        df_pasar = pd.read_sql("SELECT * FROM kpi_data ORDER BY tanggal DESC;", con=engine)
        df_terbaru = df_pasar.sort_values("tanggal", ascending=False).groupby("nama_aset").first().reset_index()
        
        # 3. Hitung kalkulasi portofolio
        dict_harga_terbaru = dict(zip(df_terbaru["nama_aset"], df_terbaru["harga_tutup"]))
        df_port["harga_sekarang"] = df_port["nama_aset"].map(dict_harga_terbaru).fillna(0.0)
        
        df_port["total_investasi"] = df_port["jumlah"] * df_port["harga_beli"]
        df_port["nilai_sekarang"] = df_port["jumlah"] * df_port["harga_sekarang"]
        df_port["profit_loss"] = df_port["nilai_sekarang"] - df_port["total_investasi"]
        
        # Konversi objek tanggal/waktu ke string untuk JSON
        df_port["tanggal_beli"] = df_port["tanggal_beli"].astype(str)
        if "updated_at" in df_port.columns:
            df_port["updated_at"] = df_port["updated_at"].astype(str)
            
        total_investasi = float(df_port["total_investasi"].sum())
        nilai_sekarang = float(df_port["nilai_sekarang"].sum())
        profit_loss = nilai_sekarang - total_investasi
        
        data_json = df_port.to_dict(orient="records")
        
        return {
            "status": "sukses",
            "total_investasi": total_investasi,
            "nilai_sekarang": nilai_sekarang,
            "profit_loss": profit_loss,
            "data": data_json
        }
    except Exception as e:
        return {"status": "gagal", "detail": str(e)}