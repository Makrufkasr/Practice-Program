import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Dashboard KPI Finansial", layout="wide")

st.title("📊 Dashboard KPI Live: Emas & Saham")
st.write("Mengonsumsi data secara langsung dari Backend API FastAPI")

try:
    response = requests.get("http://127.0.0.1:8000/api/data")
    if response.status_code == 200:
        payload = response.json()
        data_mentah = payload["data"]
        
        df = pd.DataFrame(data_mentah)
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        
        st.metric(label="Total Baris Data Terbaca", value=f"{payload['total_data']} Baris")
        
        aset_pilihan = st.selectbox("Pilih Aset untuk Dilihat Trennya:", df["nama_aset"].unique())
        df_filter = df[df["nama_aset"] == aset_pilihan].sort_values("tanggal")
        
        kolom1, kolom2 = st.columns(2)
        
        with kolom1:
            st.subheader(f"📈 Grafik Harga Penutupan - {aset_pilihan}")
            st.line_chart(data=df_filter, x="tanggal", y="harga_tutup")
            
        with kolom2:
            st.subheader("📋 Data Tabel Terbaru")
            st.dataframe(df_filter.tail(10), use_container_width=True)
    else:
        st.error(f"❌ Gagal mengambil data dari Backend API (Status Code: {response.status_code})")
except requests.exceptions.ConnectionError:
    st.error("❌ Tidak dapat terhubung ke Backend API. Pastikan server Uvicorn (FastAPI) sudah dijalankan di port 8000!")