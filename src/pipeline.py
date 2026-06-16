import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine

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
    df_saham_ri = ambil_data_live("BBCA.JK", "Saham BBCA")
    
    if df_kurs is not None and df_emas_usd is not None and df_saham_ri is not None:
        df_emas_idr = pd.merge(df_emas_usd, df_kurs[['tanggal', 'harga_tutup']], on='tanggal', suffixes=('', '_kurs'))
        
        df_emas_idr['harga_buka'] = (df_emas_idr['harga_buka'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        df_emas_idr['harga_tertinggi'] = (df_emas_idr['harga_tertinggi'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        df_emas_idr['harga_tutup'] = (df_emas_idr['harga_tutup'] * df_emas_idr['harga_tutup_kurs']) / 31.1034768
        
        df_emas_idr = df_emas_idr.drop(columns=['harga_tutup_kurs'])
        tabel_kombinasi = pd.concat([df_emas_idr, df_saham_ri], ignore_index=True)
        
        ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
        
        engine = create_engine(ALAMAT_DATABASE)
        tabel_kombinasi.to_sql('kpi_data', con=engine, if_exists='append', index=False)
        
        print("Sukses! Data 1 tahun berhasil diunggah ke Supabase.")

if __name__ == "__main__":
    jalankan_pipeline()