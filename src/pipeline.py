import os
import logging
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 1. Daftar Saham Unggulan BEI (LQ45 & Big Caps Lintas Sektor)
SAHAM_MAP = {
    # Perbankan Utama (Big Caps & Digital)
    "BBCA.JK": "Saham BBCA",
    "BBRI.JK": "Saham BBRI",
    "BMRI.JK": "Saham BMRI",
    "BBNI.JK": "Saham BBNI",
    "BRIS.JK": "Saham BRIS",
    "ARTO.JK": "Saham ARTO",
    # Consumer Goods & Retail Bluechip
    "AMRT.JK": "Saham AMRT",
    "ICBP.JK": "Saham ICBP",
    "INDF.JK": "Saham INDF",
    "KLBF.JK": "Saham KLBF",
    "UNVR.JK": "Saham UNVR",
    "MYOR.JK": "Saham MYOR",
    "ACES.JK": "Saham ACES",
    "MAPI.JK": "Saham MAPI",
    "SIDO.JK": "Saham SIDO",
    "CPIN.JK": "Saham CPIN",
    # Energi, Tambang & Komoditas Utama
    "ADRO.JK": "Saham ADRO",
    "ANTM.JK": "Saham ANTM",
    "AKRA.JK": "Saham AKRA",
    "ASII.JK": "Saham ASII",
    "BRPT.JK": "Saham BRPT",
    "PGAS.JK": "Saham PGAS",
    "PTBA.JK": "Saham PTBA",
    "ITMG.JK": "Saham ITMG",
    "MDKA.JK": "Saham MDKA",
    "MEDC.JK": "Saham MEDC",
    "INCO.JK": "Saham INCO",
    "PGEO.JK": "Saham PGEO",
    "UNTR.JK": "Saham UNTR",
    "MBMA.JK": "Saham MBMA",
    # Telekomunikasi & Infrastruktur
    "TLKM.JK": "Saham TLKM",
    "ISAT.JK": "Saham ISAT",
    "EXCL.JK": "Saham EXCL",
    "TOWR.JK": "Saham TOWR",
    "TBIG.JK": "Saham TBIG",
    # Industri Dasar, Semen, Konglomerasi & Properti
    "INKP.JK": "Saham INKP",
    "INTP.JK": "Saham INTP",
    "SMGR.JK": "Saham SMGR",
    "TPIA.JK": "Saham TPIA",
    "SRTG.JK": "Saham SRTG",
    "MNCN.JK": "Saham MNCN",
    "PANI.JK": "Saham PANI",
    "BSDE.JK": "Saham BSDE",
    "CTRA.JK": "Saham CTRA"
}

# 2. Daftar Komoditas Acuan & Kurs Valuta Asing
KOMODITAS_MAP = {
    "CL=F": "Minyak Mentah WTI (USD/barel)",
    "BZ=F": "Minyak Brent (USD/barel)",
    "NG=F": "Gas Alam (USD/MMBtu)",
    "HG=F": "Tembaga (USD/lb)",
    "IDR=X": "Kurs USD ke IDR"
}


def extract_ticker_df(df_batch, ticker: str, nama_aset: str) -> pd.DataFrame:
    """Ekstraksi dan standarisasi dataframe dari hasil batch download yfinance."""
    try:
        if ticker not in df_batch.columns.levels[0]:
            return None
        df_t = df_batch[ticker].dropna(how='all').copy()
        if df_t.empty:
            return None

        df_t = df_t.reset_index()

        col_map = {}
        for c in df_t.columns:
            c_low = str(c).lower()
            if 'date' in c_low:
                col_map[c] = 'tanggal'
            elif 'open' in c_low:
                col_map[c] = 'harga_buka'
            elif 'high' in c_low:
                col_map[c] = 'harga_tertinggi'
            elif 'close' in c_low:
                col_map[c] = 'harga_tutup'

        df_clean = df_t[list(col_map.keys())].rename(columns=col_map).copy()
        df_clean['nama_aset'] = nama_aset
        df_clean['tanggal'] = pd.to_datetime(df_clean['tanggal']).dt.date
        df_clean['updated_at'] = pd.Timestamp.now(tz='Asia/Jakarta')

        return df_clean[['tanggal', 'harga_buka', 'harga_tertinggi', 'harga_tutup', 'nama_aset', 'updated_at']]
    except Exception as e:
        logging.error(f"Error extracting ticker {ticker} ({nama_aset}): {e}")
        return None


def jalankan_pipeline():
    logging.info("🚀 Memulai Pipeline Sinkronisasi Data Saham & Komoditas...")

    all_tickers = list(SAHAM_MAP.keys()) + list(KOMODITAS_MAP.keys()) + ["GC=F", "SI=F"]

    logging.info(f"Mengunduh data batch untuk {len(all_tickers)} instrumen dari Yahoo Finance...")
    df_batch = yf.download(
        all_tickers,
        period="1y",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True
    )

    list_df = []

    # 1. Kurs USD ke IDR
    df_kurs = extract_ticker_df(df_batch, "IDR=X", "Kurs USD ke IDR")
    if df_kurs is not None:
        list_df.append(df_kurs)

    troy_oz = 31.1034768  # 1 Troy Ounce = 31.1034768 Gram

    # 2. Emas ke Rupiah per gram (GC=F * IDR=X / troy_oz)
    df_emas_raw = extract_ticker_df(df_batch, "GC=F", "Emas (IDR/gram)")
    if df_kurs is not None and df_emas_raw is not None:
        df_emas = pd.merge(df_emas_raw, df_kurs[['tanggal', 'harga_tutup']], on='tanggal', suffixes=('', '_kurs'))
        df_emas['harga_buka'] = (df_emas['harga_buka'] * df_emas['harga_tutup_kurs']) / troy_oz
        df_emas['harga_tertinggi'] = (df_emas['harga_tertinggi'] * df_emas['harga_tutup_kurs']) / troy_oz
        df_emas['harga_tutup'] = (df_emas['harga_tutup'] * df_emas['harga_tutup_kurs']) / troy_oz
        df_emas = df_emas.drop(columns=['harga_tutup_kurs'])
        list_df.append(df_emas)

    # 3. Perak ke Rupiah per gram (SI=F * IDR=X / troy_oz)
    df_perak_raw = extract_ticker_df(df_batch, "SI=F", "Perak (IDR/gram)")
    if df_kurs is not None and df_perak_raw is not None:
        df_perak = pd.merge(df_perak_raw, df_kurs[['tanggal', 'harga_tutup']], on='tanggal', suffixes=('', '_kurs'))
        df_perak['harga_buka'] = (df_perak['harga_buka'] * df_perak['harga_tutup_kurs']) / troy_oz
        df_perak['harga_tertinggi'] = (df_perak['harga_tertinggi'] * df_perak['harga_tutup_kurs']) / troy_oz
        df_perak['harga_tutup'] = (df_perak['harga_tutup'] * df_perak['harga_tutup_kurs']) / troy_oz
        df_perak = df_perak.drop(columns=['harga_tutup_kurs'])
        list_df.append(df_perak)

    # 4. Komoditas Lainnya (WTI Crude Oil, Brent, Natural Gas, Tembaga)
    for ticker, nama in KOMODITAS_MAP.items():
        if ticker == "IDR=X":
            continue
        df_kom = extract_ticker_df(df_batch, ticker, nama)
        if df_kom is not None:
            list_df.append(df_kom)

    # 5. Seluruh Saham-saham Unggulan BEI
    for ticker, nama in SAHAM_MAP.items():
        df_s = extract_ticker_df(df_batch, ticker, nama)
        if df_s is not None:
            list_df.append(df_s)

    if not list_df:
        logging.error("Tidak ada data yang berhasil diunduh. Pipeline dibatalkan.")
        return

    tabel_kombinasi = pd.concat(list_df, ignore_index=True)
    total_aset = tabel_kombinasi['nama_aset'].nunique()
    logging.info(f"Berhasil mengolah {len(tabel_kombinasi)} baris data untuk {total_aset} aset.")

    ALAMAT_DATABASE = os.getenv(
        "ALAMAT_DATABASE",
        "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    )
    engine = create_engine(ALAMAT_DATABASE)

    # 6. Bersihkan data lama untuk aset yang akan diperbarui
    aset_list = list(tabel_kombinasi['nama_aset'].unique())
    logging.info(f"Menghapus data lama untuk {len(aset_list)} aset di database Supabase...")
    with engine.connect() as conn:
        for nama in aset_list:
            conn.execute(
                text('DELETE FROM "APP_ASSET_TRACKER".kpi_data WHERE nama_aset = :nama'),
                {"nama": nama}
            )
        conn.commit()

    # 7. Unggah data 1 tahun terbaru ke Supabase
    logging.info("Mengunggah data terbaru ke tabel APP_ASSET_TRACKER.kpi_data...")
    tabel_kombinasi.to_sql(
        'kpi_data',
        con=engine,
        if_exists='append',
        index=False,
        schema='APP_ASSET_TRACKER',
        chunksize=1000
    )

    logging.info(f"✅ Sukses! {len(tabel_kombinasi)} baris data untuk {total_aset} saham & komoditas berhasil diunggah ke Supabase.")


if __name__ == "__main__":
    jalankan_pipeline()