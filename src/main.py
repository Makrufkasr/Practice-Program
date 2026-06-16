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
    query = "SELECT * FROM kpi_data ORDER BY tanggal DESC LIMIT 100;"
    df = pd.read_sql(query, con=engine)
    
    df['tanggal'] = df['tanggal'].astype(str)
    
    data_json = df.to_dict(orient="records")
    return {"total_data": len(data_json), "data": data_json}