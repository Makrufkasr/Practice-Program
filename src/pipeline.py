import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

def ambil_data_live(simbol, nama_aset):
    ticker = yf.Ticker(simbol)
    df_historis = ticker.history(period="1y", interval="1d")
    
    if df_historis.empty:
        return None
        
    df_historis = df_historis.reset_index()
    df_bersih = df_historis[['Date', 'Open', 'High', 'Close']].copy()
    df_bersih.columns = ['tanggal', 'harga_buka', 'harga_tertinggi', 'harga_tutup']
    df_bersih['nama_aset'] = nama_aset
    df_bersih['tanggal'] = pd.to_datetime(df_bersih['tanggal']).dt.date
    
    return df_bersih

def jalankan_pipeline():
    df_kurs = ambil_data_live("IDR=X", "Kurs USD ke IDR")
    df_emas_usd = ambil_data_live("GC=F", "Emas (IDR/gram)")
    
    list_df = []
    
    # 1. Proses data Emas ke Rupiah per Gram
    if df_kurs is not None and df_emas_usd is not None:
        df_emas_idr = pd.merge(df_emas_usd, df_kurs[['tanggal', 'harga_tutup']], on='tanggal', suffixes=('', '_kurs'))
        
        df_emas_idr['harga_buka'] = (df_emas_idr['harga_buka'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        df_emas_idr['harga_tertinggi'] = (df_emas_idr['harga_tertinggi'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        df_emas_idr['harga_tutup'] = (df_emas_idr['harga_tutup'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        
        df_emas_idr = df_emas_idr.drop(columns=['harga_tutup_kurs'])
        list_df.append(df_emas_idr)
        
    # 2. Ambil data Saham-Saham Bluechip Indonesia
    saham_bluechip = {
        "BBCA.JK": "Saham BBCA",
        "BBRI.JK": "Saham BBRI",
        "BMRI.JK": "Saham BMRI",
        "BBNI.JK": "Saham BBNI",
        "TLKM.JK": "Saham TLKM",
        "ASII.JK": "Saham ASII",
        "UNVR.JK": "Saham UNVR"
    }
    
    for simbol, nama in saham_bluechip.items():
        df_saham = ambil_data_live(simbol, nama)
        if df_saham is not None:
            list_df.append(df_saham)
            
    if list_df:
        tabel_kombinasi = pd.concat(list_df, ignore_index=True)
        
        ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
        engine = create_engine(ALAMAT_DATABASE)
        
        # 1. Hapus data lama untuk aset yang ada di list hari ini agar hanya tersisa data 1 tahun terbaru
        with engine.connect() as conn:
            for nama in tabel_kombinasi['nama_aset'].unique():
                conn.execute(
                    text("DELETE FROM kpi_data WHERE nama_aset = :nama"),
                    {"nama": nama}
                )
            conn.commit()
            
        # 2. Unggah data 1 tahun terbaru yang bersih
        tabel_kombinasi.to_sql('kpi_data', con=engine, if_exists='append', index=False)
        
        print("Sukses! Data 1 tahun berhasil diunggah ke Supabase.")

if __name__ == "__main__":
    jalankan_pipeline()