import streamlit as st
import requests
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(page_title="Dashboard KPI Finansial", layout="wide")

st.title("📊 Dashboard KPI Live: Emas & Saham")
st.write("Mengonsumsi data secara langsung dari Supabase atau Backend API FastAPI")

# Tautan koneksi database Anda
ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_data(ttl=3600)  # Menghemat kuota, data disimpan di memori selama 1 jam
def ambil_data():
    try:
        # Pilihan Utama: Langsung tembak ke Supabase
        engine = create_engine(ALAMAT_DATABASE)
        query = "SELECT * FROM kpi_data ORDER BY tanggal DESC LIMIT 100;"
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as db_err:
        # Cadangan: Jika koneksi langsung gagal, coba ketuk API lokal
        try:
            response = requests.get("http://127.0.0.1:8000/api/data")
            if response.status_code == 200:
                payload = response.json()
                return pd.DataFrame(payload["data"])
            else:
                raise Exception(f"API returned status code {response.status_code}")
        except Exception as api_err:
            raise Exception(f"Database error: {db_err} | API error: {api_err}")

try:
    df = ambil_data()
    if df.empty:
        st.warning("⚠️ Tidak ada data ditemukan di database.")
    else:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        
        st.metric(label="Total Baris Data Terbaca", value=f"{len(df)} Baris")
        
        aset_pilihan = st.selectbox("Pilih Aset untuk Dilihat Trennya:", df["nama_aset"].unique())
        df_filter = df[df["nama_aset"] == aset_pilihan].sort_values("tanggal")
        
        kolom1, kolom2 = st.columns(2)
        
        with kolom1:
            st.subheader(f"📈 Grafik Harga Penutupan - {aset_pilihan}")
            st.line_chart(data=df_filter, x="tanggal", y="harga_tutup")
            
        with kolom2:
            st.subheader("📋 Data Tabel Terbaru")
            st.dataframe(df_filter.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"❌ Gagal memuat data dari semua jalur. Detail: {e}")