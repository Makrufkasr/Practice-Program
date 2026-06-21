import streamlit as st
import requests
import pandas as pd
import altair as alt
from sqlalchemy import create_engine, text
try:
    from src.auth import init_db_auth, autentikasi_pengguna, tambah_pengguna, ganti_password, ambil_semua_pengguna, ubah_role_pengguna, hapus_pengguna
except ModuleNotFoundError:
    from auth import init_db_auth, autentikasi_pengguna, tambah_pengguna, ganti_password, ambil_semua_pengguna, ubah_role_pengguna, hapus_pengguna

# Inisialisasi DB auth saat pertama kali dijalankan (jika diperlukan)
init_db_auth()

st.set_page_config(page_title="Asset Tracker", layout="wide")

# Setup session state untuk status login dan halaman aktif
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "nama_lengkap" not in st.session_state:
    st.session_state.nama_lengkap = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "page" not in st.session_state:
    st.session_state.page = "login"

# Halaman Login / Registrasi jika belum login
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .login-container {
            max-width: 450px;
            margin: 60px auto;
            padding: 30px;
            border-radius: 15px;
            background-color: #1E1E2F;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #FFFFFF;
        }
        .login-title {
            text-align: center;
            font-family: 'Outfit', 'Inter', sans-serif;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 25px;
            background: linear-gradient(45deg, #FF8a00, #E52e71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-footer {
            text-align: center;
            font-size: 12px;
            color: #888888;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.page == "login":
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">🔐 Asset Tracker</div>', unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=False):
                username_input = st.text_input("Username", placeholder="Masukkan username Anda...", key="login_user")
                password_input = st.text_input("Password", type="password", placeholder="Masukkan password Anda...", key="login_pass")
                submit_button = st.form_submit_button("Masuk", use_container_width=True)
                
                if submit_button:
                    if not username_input or not password_input:
                        st.error("⚠️ Username dan password tidak boleh kosong.")
                    else:
                        auth_result = autentikasi_pengguna(username_input, password_input)
                        if auth_result.get("authenticated"):
                            st.session_state.authenticated = True
                            st.session_state.username = auth_result["username"]
                            st.session_state.nama_lengkap = auth_result["nama_lengkap"]
                            st.session_state.role = auth_result["role"]
                            st.success("🎉 Login Berhasil! Memuat data...")
                            st.rerun()
                        else:
                            st.error("❌ Username atau password salah.")
            
            # Action di bawah password/login button untuk pindah ke page daftar
            st.write("")
            if st.button("Belum punya akun? Daftar di sini", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
                
            st.markdown('<div class="login-footer">Dilindungi oleh Lapisan Keamanan Database</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        elif st.session_state.page == "register":
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.markdown('<div class="login-title">📝 Daftar Akun Baru</div>', unsafe_allow_html=True)
            
            with st.form("register_form", clear_on_submit=True):
                reg_username = st.text_input("Username Baru:", placeholder="Pilih username...", key="reg_user")
                reg_nama = st.text_input("Nama Lengkap:", placeholder="Masukkan nama lengkap...", key="reg_name")
                reg_pwd = st.text_input("Password Baru:", type="password", placeholder="Masukkan password...", key="reg_pass")
                reg_pwd_confirm = st.text_input("Konfirmasi Password Baru:", type="password", placeholder="Ketik ulang password...", key="reg_pass_confirm")
                submit_reg = st.form_submit_button("Daftarkan Akun Baru", use_container_width=True)
                
                if submit_reg:
                    if not reg_username or not reg_nama or not reg_pwd:
                        st.error("⚠️ Semua field harus diisi!")
                    elif reg_pwd != reg_pwd_confirm:
                        st.error("⚠️ Konfirmasi password tidak cocok.")
                    else:
                        hasil = tambah_pengguna(reg_username, reg_pwd, reg_nama, role="user")
                        if hasil["status"] == "sukses":
                            st.success(f"🎉 {hasil['pesan']}!")
                            st.info("Silakan klik 'Kembali ke Login' di bawah untuk masuk.")
                        else:
                            st.error(f"❌ {hasil['pesan']}")
            
            # Button untuk kembali ke login page
            st.write("")
            if st.button("Sudah punya akun? Kembali ke Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
                
            st.markdown('<div class="login-footer">Dilindungi oleh Lapisan Keamanan Database</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.stop()

# --- SIDEBAR UNTUK PROFIL & LOGOUT ---
st.sidebar.image("https://img.icons8.com/color/96/dashboard.png", width=80)
st.sidebar.markdown("### 📊 Menu Navigasi")
st.sidebar.markdown(f"Selamat Datang,\n**{st.session_state.nama_lengkap}**")
st.sidebar.caption(f"Role: {st.session_state.role.upper()} | User: {st.session_state.username}")

# Ganti Password
with st.sidebar.expander("🔑 Ganti Password"):
    with st.form("form_ganti_password", clear_on_submit=True):
        pwd_baru = st.text_input("Password Baru:", type="password", key="pwd_baru")
        pwd_konfirmasi = st.text_input("Konfirmasi Password Baru:", type="password", key="pwd_konfirmasi")
        tombol_ganti = st.form_submit_button("Simpan Password", use_container_width=True)
        if tombol_ganti:
            if not pwd_baru:
                st.error("⚠️ Password baru tidak boleh kosong.")
            elif pwd_baru != pwd_konfirmasi:
                st.error("⚠️ Konfirmasi password tidak cocok.")
            else:
                hasil = ganti_password(st.session_state.username, pwd_baru)
                if hasil["status"] == "sukses":
                    st.success("🎉 Password berhasil diubah!")
                else:
                    st.error(f"❌ {hasil['pesan']}")

# Panel Admin (hanya tampil jika role = admin)
if st.session_state.role == "admin":
    with st.sidebar.expander("⚙️ Panel Admin"):
        list_users = ambil_semua_pengguna()
        if list_users:
            df_users_sidebar = pd.DataFrame(list_users)
            df_users_sidebar = df_users_sidebar.rename(columns={
                "username": "Username",
                "nama_lengkap": "Nama Lengkap",
                "role": "Role"
            })
            st.dataframe(df_users_sidebar[["Username", "Nama Lengkap", "Role"]], use_container_width=True)

            st.markdown("**Ubah Peran Pengguna**")
            with st.form("form_ubah_role_sidebar", clear_on_submit=False):
                target_user_role_sb = st.selectbox("Pilih Pengguna:", options=[u["username"] for u in list_users if u["username"] != "admin"], key="target_user_role_sb")
                new_role_sb = st.selectbox("Peran Baru:", options=["user", "admin"], key="new_role_sb")
                submit_role_sb = st.form_submit_button("Simpan Peran", use_container_width=True)
                if submit_role_sb:
                    res = ubah_role_pengguna(target_user_role_sb, new_role_sb)
                    if res["status"] == "sukses":
                        st.success(res["pesan"])
                        st.rerun()
                    else:
                        st.error(res["pesan"])

            st.markdown("**Reset Password Pengguna**")
            with st.form("form_reset_pwd_sidebar", clear_on_submit=True):
                target_user_pwd_sb = st.selectbox("Pilih Pengguna:", options=[u["username"] for u in list_users], key="target_user_pwd_sb")
                reset_pwd_sb = st.text_input("Password Baru:", type="password", key="reset_pwd_sb")
                submit_reset_sb = st.form_submit_button("Reset Password", use_container_width=True)
                if submit_reset_sb:
                    if not reset_pwd_sb:
                        st.error("Password tidak boleh kosong.")
                    else:
                        res = ganti_password(target_user_pwd_sb, reset_pwd_sb)
                        if res["status"] == "sukses":
                            st.success(f"🎉 Password '{target_user_pwd_sb}' berhasil direset!")
                        else:
                            st.error(res["pesan"])

            st.markdown("**🗑️ Hapus Pengguna**")
            with st.form("form_hapus_user_sidebar", clear_on_submit=False):
                non_admin_users = [u["username"] for u in list_users if u["username"] != "admin"]
                if non_admin_users:
                    target_user_del_sb = st.selectbox("Pilih Pengguna:", options=non_admin_users, key="target_user_del_sb")
                    submit_del_sb = st.form_submit_button("Hapus Pengguna", use_container_width=True, type="primary")
                    if submit_del_sb:
                        res = hapus_pengguna(target_user_del_sb)
                        if res["status"] == "sukses":
                            st.success(res["pesan"])
                            st.rerun()
                        else:
                            st.error(res["pesan"])
                else:
                    st.info("Tidak ada pengguna lain untuk dihapus.")
        else:
            st.info("Tidak ada pengguna terdaftar.")


st.sidebar.markdown("---")

if st.sidebar.button("🚪 Keluar / Logout", use_container_width=True, type="primary"):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.nama_lengkap = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.markdown("---")

st.title("📊 Asset Tracker: Emas & Saham")
st.write("Mengonsumsi data secara langsung dari Supabase atau Backend API FastAPI")

# Tautan koneksi database Anda
ALAMAT_DATABASE = "postgresql://postgres.zaqxdmhofnbmusemwaxl:Makrufkausar26@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_data(ttl=3600)  # Menghemat kuota, data disimpan di memori selama 1 jam
def ambil_data():
    try:
        # Pilihan Utama: Langsung tembak ke Supabase
        engine = create_engine(ALAMAT_DATABASE)
        query = "SELECT * FROM kpi_data ORDER BY tanggal DESC;"
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

def ambil_data_portofolio(username):
    try:
        engine = create_engine(ALAMAT_DATABASE)
        query = text("SELECT * FROM portofolio WHERE username = :username ORDER BY tanggal_beli DESC;")
        df_port = pd.read_sql(query, con=engine, params={"username": username})
        return df_port
    except Exception as e:
        st.error(f"Gagal mengambil data portofolio: {e}")
        return pd.DataFrame()

def hitung_tren_portofolio_aset(df_historis_aset, df_transaksi_aset):
    df_trend = df_historis_aset.sort_values("tanggal").copy()
    
    list_modal = []
    list_nilai = []
    
    for idx, row in df_trend.iterrows():
        tgl = row["tanggal"].date() if hasattr(row["tanggal"], "date") else pd.to_datetime(row["tanggal"]).date()
        
        tx_aktif = df_transaksi_aset[pd.to_datetime(df_transaksi_aset["tanggal_beli"]).dt.date <= tgl]
        
        if tx_aktif.empty:
            modal_kumulatif = 0.0
            nilai_pasar_kumulatif = 0.0
        else:
            jumlah_kumulatif = tx_aktif["jumlah"].sum()
            modal_kumulatif = (tx_aktif["jumlah"] * tx_aktif["harga_beli"]).sum()
            nilai_pasar_kumulatif = jumlah_kumulatif * row["harga_tutup"]
            
        list_modal.append(modal_kumulatif)
        list_nilai.append(nilai_pasar_kumulatif)
        
    df_trend["Modal (Investasi)"] = list_modal
    df_trend["Nilai Pasar Saat Ini"] = list_nilai
    
    if not df_transaksi_aset.empty:
        tgl_beli_pertama = pd.to_datetime(df_transaksi_aset["tanggal_beli"]).min().date()
        df_trend = df_trend[df_trend["tanggal"].dt.date >= tgl_beli_pertama]
        
    return df_trend

def hitung_tren_total_portofolio(df_pasar, df_port):
    df_sorted_pasar = df_pasar.sort_values("tanggal")
    df_pivot = df_sorted_pasar.pivot_table(index="tanggal", columns="nama_aset", values="harga_tutup").ffill().bfill()
    df_pivot.index = pd.to_datetime(df_pivot.index)
    
    first_purchase = pd.to_datetime(df_port["tanggal_beli"]).min()
    df_pivot_filtered = df_pivot[df_pivot.index >= first_purchase]
    
    dates_list = []
    modal_list = []
    nilai_list = []
    
    for tgl, prices in df_pivot_filtered.iterrows():
        tgl_date = tgl.date()
        
        tx_aktif = df_port[pd.to_datetime(df_port["tanggal_beli"]).dt.date <= tgl_date]
        
        if tx_aktif.empty:
            total_modal = 0.0
            total_nilai = 0.0
        else:
            total_modal = (tx_aktif["jumlah"] * tx_aktif["harga_beli"]).sum()
            total_nilai = 0.0
            grouped_holdings = tx_aktif.groupby("nama_aset")["jumlah"].sum()
            for aset, qty in grouped_holdings.items():
                price = prices[aset] if aset in prices else 0.0
                total_nilai += qty * price
                
        dates_list.append(tgl)
        modal_list.append(total_modal)
        nilai_list.append(total_nilai)
        
    df_trend_total = pd.DataFrame({
        "tanggal": dates_list,
        "Total Modal (Investasi)": modal_list,
        "Total Nilai Pasar Saat Ini": nilai_list
    })
    return df_trend_total


try:
    df = ambil_data()
    if df.empty:
        st.warning("⚠️ Tidak ada data ditemukan di database.")
    else:
        df["tanggal"] = pd.to_datetime(df["tanggal"])
        
        tab_pasar, tab_portofolio = st.tabs(["📈 Tren Pasar Aset", "💼 Portofolio & Monitoring Saya"])
        
        with tab_pasar:
            if "updated_at" in df.columns and not df["updated_at"].isnull().all():
                terakhir_update = pd.to_datetime(df["updated_at"]).max()
                if terakhir_update.tzinfo is not None:
                    terakhir_update = terakhir_update.tz_convert("Asia/Jakarta")
                format_update = terakhir_update.strftime("%d %b %Y, %H:%M WIB")
            else:
                format_update = "Tidak tersedia"
            st.metric(label="Data Terakhir Diperbarui", value=format_update)

            aset_pilihan = st.selectbox("Pilih Aset untuk Dilihat Trennya:", df["nama_aset"].unique())
            df_filter = df[df["nama_aset"] == aset_pilihan].sort_values("tanggal")

            # --- Filter Periode Waktu ---
            kol_periode, _ = st.columns([3, 5])
            with kol_periode:
                pilihan_periode = st.radio(
                    "Periode:",
                    options=["1M", "1B", "3B", "1T"],
                    format_func=lambda x: {"1M": "1 Minggu", "1B": "1 Bulan", "3B": "3 Bulan", "1T": "1 Tahun"}[x],
                    horizontal=True,
                    index=1,
                    key="periode_grafik"
                )

            delta_hari = {"1M": 7, "1B": 30, "3B": 90, "1T": 365}[pilihan_periode]
            df_filter_all = df[df["nama_aset"] == aset_pilihan].copy()
            df_filter_all["tanggal"] = pd.to_datetime(df_filter_all["tanggal"])
            tanggal_maks = df_filter_all["tanggal"].max()
            tanggal_mulai = tanggal_maks - pd.Timedelta(days=delta_hari)
            df_filter_periode = df_filter_all[df_filter_all["tanggal"] >= tanggal_mulai].sort_values("tanggal")

            kolom1, kolom2 = st.columns(2)

            with kolom1:
                st.subheader(f"📈 Grafik Harga Penutupan - {aset_pilihan}")
                df_chart = df_filter_periode[["tanggal", "harga_tutup"]].copy()
                if df_chart.empty:
                    st.info("Tidak ada data untuk periode yang dipilih.")
                else:
                    y_min = df_chart["harga_tutup"].min() * 0.995
                    y_max = df_chart["harga_tutup"].max() * 1.005
                    grafik_aset = alt.Chart(df_chart).mark_line(point=True, color="#4f8ef7").encode(
                        x=alt.X("tanggal:T", title="Tanggal"),
                        y=alt.Y("harga_tutup:Q", title="Harga Penutupan", scale=alt.Scale(domain=[y_min, y_max])),
                        tooltip=[alt.Tooltip("tanggal:T", title="Tanggal", format="%Y-%m-%d"), alt.Tooltip("harga_tutup:Q", title="Harga", format=",.0f")]
                    ).properties(height=300).interactive()
                    st.altair_chart(grafik_aset, use_container_width=True)

            with kolom2:
                st.subheader("📋 Data Transaksi Terakhir")
                kolom_tabel = [c for c in df_filter_periode.columns if c not in ["updated_at", "id", "nama_aset"]]
                df_tabel_baru = df_filter_periode[kolom_tabel].copy()
                if "tanggal" in df_tabel_baru.columns:
                    df_tabel_baru["tanggal"] = df_tabel_baru["tanggal"].dt.strftime("%Y-%m-%d")
                df_tabel_baru = df_tabel_baru.sort_values("tanggal", ascending=False).head(10)
                df_tabel_baru = df_tabel_baru.rename(columns={
                    "tanggal": "Tanggal",
                    "harga_buka": "Harga Buka (Rp)",
                    "harga_tertinggi": "Harga Tertinggi (Rp)",
                    "harga_tutup": "Harga Tutup (Rp)"
                })
                kolom_harga = [c for c in df_tabel_baru.columns if "harga" in c.lower() or "volume" in c.lower()]
                st.dataframe(
                    df_tabel_baru.style.format({k: lambda v: f"{v:,.0f}".replace(",", ".") for k in kolom_harga}),
                    use_container_width=True,
                    hide_index=True
                )


        with tab_portofolio:
            st.subheader("💼 Portofolio Investasi")
            
            # Ambil data portofolio dari DB
            df_port = ambil_data_portofolio(st.session_state.username)
            
            # Hitung harga terkini setiap aset
            df_terbaru = df.sort_values("tanggal", ascending=False).groupby("nama_aset").first().reset_index()
            
            # --- FORM INPUT TRANSAKSI (Expander) ---
            with st.expander("➕ Tambah Pembelian Aset Baru", expanded=False):
                st.write("Masukkan rincian aset yang baru Anda beli, atau catat saldo tabungan Anda.")

                # Susun opsi: Tabungan + Emas dipecah + Saham
                aset_db = list(df["nama_aset"].unique())
                opsi_aset = ["💰 Tabungan"]
                for a in aset_db:
                    if "Emas" in a and "Saham" not in a:
                        opsi_aset += ["🥇 Emas Logam Mulia", "💍 Emas Perhiasan"]
                    else:
                        opsi_aset.append(a)
                # Hilangkan duplikat sambil pertahankan urutan
                opsi_aset_unik = list(dict.fromkeys(opsi_aset))

                form_nama_aset = st.selectbox("Pilih Kategori / Aset:", opsi_aset_unik, key="form_nama")

                if form_nama_aset == "💰 Tabungan":
                    # === Form Tabungan ===
                    tb_bank = st.text_input("Nama Bank / Lembaga:", placeholder="Contoh: BCA, Mandiri, BSI", key="tb_bank_input")
                    kol_tb1, kol_tb2 = st.columns(2)
                    with kol_tb1:
                        tb_saldo = st.number_input("Jumlah Saldo (Rp):", min_value=0.0, step=10000.0, format="%.0f", key="tb_saldo_input")
                    with kol_tb2:
                        tb_tanggal = st.date_input("Tanggal Pencatatan:", key="tb_tanggal_input")
                    tb_catatan = st.text_area("Catatan (opsional):", placeholder="Contoh: Tabungan darurat, gaji bulan ini, dst.", height=68, key="tb_catatan_input")

                    tombol_simpan = st.button("💾 Simpan Tabungan", key="btn_simpan_tabungan")
                    if tombol_simpan:
                        if not tb_bank.strip():
                            st.error("⚠️ Nama bank tidak boleh kosong.")
                        elif tb_saldo <= 0:
                            st.error("⚠️ Saldo harus lebih dari 0.")
                        else:
                            try:
                                engine = create_engine(ALAMAT_DATABASE)
                                with engine.connect() as conn:
                                    conn.execute(text("""
                                        INSERT INTO tabungan (username, nama_bank, saldo, tanggal, catatan)
                                        VALUES (:u, :bank, :saldo, :tgl, :cat)
                                    """), {"u": st.session_state.username, "bank": tb_bank.strip(), "saldo": tb_saldo, "tgl": tb_tanggal, "cat": tb_catatan.strip() or None})
                                    conn.commit()
                                st.success(f"✅ Tabungan '{tb_bank}' berhasil disimpan!")
                                st.rerun()
                            except Exception as tb_err:
                                st.error(f"Gagal menyimpan tabungan: {tb_err}")

                else:
                    # === Form Investasi ===
                    apakah_saham = "Saham" in form_nama_aset
                    apakah_emas_lm = form_nama_aset == "🥇 Emas Logam Mulia"
                    apakah_emas_perhiasan = form_nama_aset == "💍 Emas Perhiasan"
                    apakah_emas = apakah_emas_lm or apakah_emas_perhiasan

                    # Nama aset untuk disimpan ke DB (selalu "Emas (IDR/gram)" agar cocok dengan data pasar)
                    nama_simpan = "Emas (IDR/gram)" if apakah_emas else form_nama_aset

                    label_jumlah = "Jumlah Lot" if apakah_saham else "Jumlah Gram"
                    label_harga = "Harga Beli per Lembar (Rupiah)" if apakah_saham else "Harga Beli per Gram (Rupiah)"

                    # Cari harga pasar emas LM terkini
                    nama_pasar = "Emas (IDR/gram)" if apakah_emas else form_nama_aset
                    harga_lm = df_terbaru[df_terbaru["nama_aset"] == nama_pasar]["harga_tutup"].values[0] if not df_terbaru[df_terbaru["nama_aset"] == nama_pasar].empty else 0.0

                    if apakah_emas_lm:
                        # Logam Mulia = 24K, langsung pakai harga LM
                        st.info(f"🥇 Harga Emas Logam Mulia (24K) saat ini: **Rp {harga_lm:,.0f} / gram**".replace(",", "."))
                        harga_default = float(harga_lm)

                    elif apakah_emas_perhiasan:
                        # Perhiasan: pilih kadar, hitung otomatis
                        KADAR_EMAS = {
                            "22K — Perhiasan (91,67%)": 22/24,
                            "18K — Perhiasan (75,00%)": 18/24,
                            "17K — Perhiasan (70,83%)": 17/24,
                            "16K — Perhiasan (66,67%)": 16/24,
                            "14K — Perhiasan (58,33%)": 14/24,
                            "9K  — Perhiasan (37,50%)":  9/24,
                            "✏️ Kustom (masukkan sendiri)": None,
                        }
                        pilihan_kadar = st.selectbox("Kadar Emas Perhiasan:", options=list(KADAR_EMAS.keys()), key="form_kadar")
                        faktor_kadar = KADAR_EMAS[pilihan_kadar]

                        if faktor_kadar is None:
                            kustom_persen = st.number_input("Kemurnian Kustom (%):", min_value=1.0, max_value=99.9, value=75.0, step=0.5, key="form_kadar_kustom")
                            faktor_kadar = kustom_persen / 100.0

                        harga_default = round(harga_lm * faktor_kadar, 0)
                        st.info(f"💡 Harga LM (24K): **Rp {harga_lm:,.0f}** / gram  →  Estimasi harga perhiasan: **Rp {harga_default:,.0f}** / gram".replace(",", "."))

                    else:
                        harga_default = float(harga_lm)

                    kol_input1, kol_input2 = st.columns(2)
                    with kol_input1:
                        input_jumlah = st.number_input(f"{label_jumlah}:", min_value=0.01, step=1.0 if apakah_saham else 0.1, key="form_jumlah")
                    with kol_input2:
                        input_harga = st.number_input(f"{label_harga}:", min_value=1.0, value=float(harga_default) if harga_default >= 1.0 else 1.0, step=100.0 if apakah_saham else 1000.0, key="form_harga")

                    input_tanggal = st.date_input("Tanggal Pembelian:", key="form_tanggal")

                    tombol_simpan = st.button("Simpan ke Portofolio", key="btn_simpan_portofolio")
                    if tombol_simpan:
                        jumlah_simpan = input_jumlah * 100 if apakah_saham else input_jumlah
                        try:
                            engine = create_engine(ALAMAT_DATABASE)
                            with engine.connect() as conn:
                                conn.execute(
                                    text("""
                                        INSERT INTO portofolio (nama_aset, jumlah, harga_beli, tanggal_beli, username)
                                        VALUES (:nama, :jumlah, :harga, :tanggal, :username)
                                    """),
                                    {
                                        "nama": nama_simpan,
                                        "jumlah": jumlah_simpan,
                                        "harga": input_harga,
                                        "tanggal": input_tanggal,
                                        "username": st.session_state.username
                                    }
                                )
                                conn.commit()
                            st.success(f"✅ Sukses menambahkan {form_nama_aset}!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as ins_err:
                            st.error(f"Gagal menyimpan transaksi: {ins_err}")


            # --- TAMPILKAN PORTFOLIO SUMMARY & DATA ---
            if df_port.empty:
                st.info("ℹ️ Portofolio Anda masih kosong. Gunakan form di atas untuk menambahkan aset pertama Anda.")
            else:
                # --- FITUR EDIT/HAPUS TRANSAKSI (Expander) ---
                with st.expander("✏️ Edit / 🗑️ Hapus Transaksi", expanded=False):
                    st.write("Pilih transaksi yang ingin diubah atau dihapus:")
                    
                    pilihan_riwayat = []
                    for _, row in df_port.iterrows():
                        jumlah_disp = f"{row['jumlah']/100:.2f} Lot" if "Saham" in row["nama_aset"] else f"{row['jumlah']:.2f} Gram"
                        nama_disp = "Emas" if row["nama_aset"] == "Emas (IDR/gram)" else row["nama_aset"]
                        desc = f"ID {row['id']} | {row['tanggal_beli']} | {nama_disp} - {jumlah_disp} @ Rp {row['harga_beli']:,.2f}"
                        pilihan_riwayat.append((row['id'], desc))
                    
                    if pilihan_riwayat:
                        dict_pilihan = dict(pilihan_riwayat)
                        tx_id_pilihan = st.selectbox(
                            "Pilih Transaksi:", 
                            options=list(dict_pilihan.keys()), 
                            format_func=lambda x: dict_pilihan[x],
                            key="edit_tx_select"
                        )
                        
                        tx_detail = df_port[df_port["id"] == tx_id_pilihan].iloc[0]
                        apakah_saham_edit = "Saham" in tx_detail["nama_aset"]
                        jumlah_edit_default = float(tx_detail["jumlah"] / 100 if apakah_saham_edit else tx_detail["jumlah"])
                        
                        kol_edit1, kol_edit2 = st.columns(2)
                        with kol_edit1:
                            label_jumlah_edit = "Jumlah Lot" if apakah_saham_edit else "Jumlah Gram"
                            new_jumlah = st.number_input(f"{label_jumlah_edit}:", min_value=0.01, value=jumlah_edit_default, step=1.0 if apakah_saham_edit else 0.1, key="edit_jumlah")
                        with kol_edit2:
                            label_harga_edit = "Harga Beli per Lembar (Rupiah)" if apakah_saham_edit else "Harga Beli per Gram (Rupiah)"
                            new_harga = st.number_input(f"{label_harga_edit}:", min_value=1.0, value=float(tx_detail["harga_beli"]), step=100.0 if apakah_saham_edit else 1000.0, key="edit_harga")
                        
                        new_tanggal = st.date_input("Tanggal Pembelian:", value=pd.to_datetime(tx_detail["tanggal_beli"]).date(), key="edit_tanggal")
                        
                        kol_tombol1, kol_tombol2 = st.columns(2)
                        with kol_tombol1:
                            tombol_update = st.button("💾 Simpan Perubahan", use_container_width=True)
                            if tombol_update:
                                jumlah_simpan_edit = new_jumlah * 100 if apakah_saham_edit else new_jumlah
                                try:
                                    engine = create_engine(ALAMAT_DATABASE)
                                    with engine.connect() as conn:
                                        conn.execute(
                                            text("""
                                                UPDATE portofolio 
                                                SET jumlah = :jumlah, harga_beli = :harga, tanggal_beli = :tanggal, updated_at = CURRENT_TIMESTAMP
                                                WHERE id = :id AND username = :username
                                            """),
                                            {
                                                "jumlah": jumlah_simpan_edit,
                                                "harga": new_harga,
                                                "tanggal": new_tanggal,
                                                "id": tx_id_pilihan,
                                                "username": st.session_state.username
                                            }
                                        )
                                        conn.commit()
                                    st.success("Transaksi berhasil diperbarui!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as upd_err:
                                    st.error(f"Gagal memperbarui transaksi: {upd_err}")
                                    
                        with kol_tombol2:
                            tombol_delete = st.button("🗑️ Hapus Transaksi", use_container_width=True, type="primary")
                            if tombol_delete:
                                try:
                                    engine = create_engine(ALAMAT_DATABASE)
                                    with engine.connect() as conn:
                                        conn.execute(
                                            text("DELETE FROM portofolio WHERE id = :id AND username = :username"),
                                            {"id": tx_id_pilihan, "username": st.session_state.username}
                                        )
                                        conn.commit()
                                    st.warning("Transaksi berhasil dihapus!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as del_err:
                                    st.error(f"Gagal menghapus transaksi: {del_err}")
                    else:
                        st.info("Tidak ada transaksi untuk diubah.")
                
                df_port_summary = df_port.copy()

                # Ambil data tabungan
                try:
                    eng_tb = create_engine(ALAMAT_DATABASE)
                    with eng_tb.connect() as c_tb:
                        rows_tb = c_tb.execute(text(
                            "SELECT nama_bank, saldo, tanggal FROM tabungan WHERE username = :u ORDER BY tanggal DESC"
                        ), {"u": st.session_state.username}).fetchall()
                    df_tabungan = pd.DataFrame(rows_tb, columns=["nama_bank", "saldo", "tanggal"]) if rows_tb else pd.DataFrame(columns=["nama_bank", "saldo", "tanggal"])
                except:
                    df_tabungan = pd.DataFrame(columns=["nama_bank", "saldo", "tanggal"])

                total_tabungan = float(df_tabungan["saldo"].sum()) if not df_tabungan.empty else 0.0

                dict_harga_terbaru = dict(zip(df_terbaru["nama_aset"], df_terbaru["harga_tutup"]))
                df_port_summary["harga_sekarang"] = df_port_summary["nama_aset"].map(dict_harga_terbaru).fillna(0.0)

                df_port_summary["total_investasi"] = df_port_summary["jumlah"] * df_port_summary["harga_beli"]
                df_port_summary["nilai_sekarang"] = df_port_summary["jumlah"] * df_port_summary["harga_sekarang"]
                df_port_summary["profit_loss"] = df_port_summary["nilai_sekarang"] - df_port_summary["total_investasi"]

                total_investasi_port = float(df_port_summary["total_investasi"].sum()) + total_tabungan
                nilai_sekarang_port = float(df_port_summary["nilai_sekarang"].sum()) + total_tabungan
                profit_loss_port = nilai_sekarang_port - total_investasi_port
                profit_loss_persen_port = (profit_loss_port / total_investasi_port * 100) if total_investasi_port > 0 else 0.0

                # Metrik: 3 kolom (karena tabungan sudah digabung)
                metric_port1, metric_port2, metric_port3 = st.columns(3)
                with metric_port1:
                    st.metric(label="Total Modal Investasi", value=f"Rp {total_investasi_port:,.0f}".replace(",", "."))
                with metric_port2:
                    st.metric(label="Nilai Portofolio Saat Ini", value=f"Rp {nilai_sekarang_port:,.0f}".replace(",", "."))
                with metric_port3:
                    tanda = "+" if profit_loss_port >= 0 else ""
                    st.metric(
                        label="Total Keuntungan / Kerugian",
                        value=f"Rp {profit_loss_port:,.0f}".replace(",", "."),
                        delta=f"{tanda}{profit_loss_persen_port:.2f}%"
                    )


                st.subheader("📋 Rincian Aset yang Dimiliki")

                df_grouped = df_port_summary.groupby("nama_aset").agg({
                    "jumlah": "sum",
                    "total_investasi": "sum",
                    "nilai_sekarang": "sum",
                    "profit_loss": "sum"
                }).reset_index()

                df_grouped["harga_beli_rata2"] = df_grouped["total_investasi"] / df_grouped["jumlah"]
                df_grouped["harga_pasar_sekarang"] = df_grouped["nama_aset"].map(dict_harga_terbaru).fillna(0.0)
                df_grouped["profit_loss_persen"] = (df_grouped["profit_loss"] / df_grouped["total_investasi"]) * 100

                tabel_tampilan = df_grouped.copy()
                tabel_tampilan["nama_aset"] = tabel_tampilan["nama_aset"].replace("Emas (IDR/gram)", "Emas")

                def format_jumlah(row):
                    if "Saham" in row["nama_aset"]:
                        return f"{row['jumlah'] / 100:.2f} Lot ({row['jumlah']:,.0f} Lbr)"
                    else:
                        return f"{row['jumlah']:.2f} Gram"

                tabel_tampilan["Jumlah Kepemilikan"] = tabel_tampilan.apply(format_jumlah, axis=1)

                tabel_tampilan = tabel_tampilan.rename(columns={
                    "nama_aset": "Nama Aset",
                    "harga_beli_rata2": "Harga Rata-Rata Beli (Unit)",
                    "harga_pasar_sekarang": "Harga Pasar Saat Ini (Unit)",
                    "total_investasi": "Total Modal",
                    "nilai_sekarang": "Nilai Pasar Saat Ini",
                    "profit_loss": "Profit / Loss (Rp)",
                    "profit_loss_persen": "Profit / Loss (%)"
                })

                kolom_diurutkan = [
                    "Nama Aset", "Jumlah Kepemilikan", "Harga Rata-Rata Beli (Unit)",
                    "Harga Pasar Saat Ini (Unit)", "Total Modal", "Nilai Pasar Saat Ini",
                    "Profit / Loss (Rp)", "Profit / Loss (%)"
                ]

                tabel_final = tabel_tampilan[kolom_diurutkan].copy()

                # Tambahkan baris Tabungan (per bank) jika ada
                if not df_tabungan.empty:
                    for _, tb_row in df_tabungan.iterrows():
                        baris_tb = {
                            "Nama Aset": f"🏦 Tabungan — {tb_row['nama_bank']}",
                            "Jumlah Kepemilikan": "—",
                            "Harga Rata-Rata Beli (Unit)": 0.0,
                            "Harga Pasar Saat Ini (Unit)": 0.0,
                            "Total Modal": float(tb_row["saldo"]),
                            "Nilai Pasar Saat Ini": float(tb_row["saldo"]),
                            "Profit / Loss (Rp)": 0.0,
                            "Profit / Loss (%)": 0.0,
                        }
                        tabel_final = pd.concat([tabel_final, pd.DataFrame([baris_tb])], ignore_index=True)

                st.dataframe(
                    tabel_final.style.format({
                        "Harga Rata-Rata Beli (Unit)": lambda v: f"Rp {v:,.0f}".replace(",", ".") if v != 0 else "—",
                        "Harga Pasar Saat Ini (Unit)": lambda v: f"Rp {v:,.0f}".replace(",", ".") if v != 0 else "—",
                        "Total Modal": lambda v: f"Rp {v:,.0f}".replace(",", "."),
                        "Nilai Pasar Saat Ini": lambda v: f"Rp {v:,.0f}".replace(",", "."),
                        "Profit / Loss (Rp)": lambda v: f"Rp {v:,.0f}".replace(",", ".") if v != 0 else "—",
                        "Profit / Loss (%)": lambda v: f"{v:+.2f}%" if v != 0 else "—",
                    }),
                    use_container_width=True,
                    hide_index=True
                )


                st.subheader("📈 Tren Kinerja Investasi")

                # Baris atas: pilih tampilan + filter periode
                kol_tren1, kol_tren2 = st.columns([3, 4])
                with kol_tren1:
                    opsi_tren = st.radio(
                        "Tampilan:",
                        ["Total Portofolio", "Per Aset Individu"],
                        horizontal=True,
                        key="opsi_tren_kinerja"
                    )
                with kol_tren2:
                    pilihan_periode_tren = st.radio(
                        "Periode:",
                        options=["1M", "1B", "3B", "1T"],
                        format_func=lambda x: {"1M": "1 Minggu", "1B": "1 Bulan", "3B": "3 Bulan", "1T": "1 Tahun"}[x],
                        horizontal=True,
                        index=3,
                        key="periode_tren"
                    )

                delta_tren = {"1M": 7, "1B": 30, "3B": 90, "1T": 365}[pilihan_periode_tren]

                def filter_periode_df(df_input, delta):
                    df_c = df_input.copy()
                    df_c["tanggal"] = pd.to_datetime(df_c["tanggal"])
                    tgl_maks = df_c["tanggal"].max()
                    return df_c[df_c["tanggal"] >= tgl_maks - pd.Timedelta(days=delta)]

                if opsi_tren == "Total Portofolio":
                    with st.spinner("Menghitung tren total portofolio..."):
                        df_trend_total = hitung_tren_total_portofolio(df, df_port)
                        if not df_trend_total.empty:
                            df_trend_total = filter_periode_df(df_trend_total, delta_tren)
                            df_melt_total = df_trend_total.melt(id_vars="tanggal", value_vars=["Total Modal (Investasi)", "Total Nilai Pasar Saat Ini"], var_name="Kategori", value_name="Nilai")
                            if df_melt_total.empty:
                                st.info("Tidak ada data untuk periode yang dipilih.")
                            else:
                                y_min_t = df_melt_total["Nilai"].min() * 0.995
                                y_max_t = df_melt_total["Nilai"].max() * 1.005
                                grafik_total = alt.Chart(df_melt_total).mark_line(point=True).encode(
                                    x=alt.X("tanggal:T", title="Tanggal"),
                                    y=alt.Y("Nilai:Q", title="Nilai (Rp)", scale=alt.Scale(domain=[y_min_t, y_max_t])),
                                    color=alt.Color("Kategori:N"),
                                    tooltip=[alt.Tooltip("tanggal:T", title="Tanggal", format="%Y-%m-%d"), alt.Tooltip("Kategori:N"), alt.Tooltip("Nilai:Q", format=",.0f")]
                                ).properties(height=350).interactive()
                                st.altair_chart(grafik_total, use_container_width=True)
                        else:
                            st.info("Tidak dapat memuat tren portofolio.")
                else:
                    aset_tren_pilihan = st.selectbox(
                        "Pilih Aset untuk Dilihat Trennya:",
                        options=df_grouped["nama_aset"].unique(),
                        format_func=lambda x: "Emas" if x == "Emas (IDR/gram)" else x,
                        key="aset_tren_pilihan"
                    )

                    nama_tren_disp = "Emas" if aset_tren_pilihan == "Emas (IDR/gram)" else aset_tren_pilihan
                    with st.spinner(f"Menghitung tren {nama_tren_disp}..."):
                        df_historis_aset = df[df["nama_aset"] == aset_tren_pilihan]
                        df_transaksi_aset = df_port[df_port["nama_aset"] == aset_tren_pilihan]

                        df_trend_aset = hitung_tren_portofolio_aset(df_historis_aset, df_transaksi_aset)
                        if not df_trend_aset.empty:
                            df_trend_aset = filter_periode_df(df_trend_aset, delta_tren)
                            df_melt_aset = df_trend_aset.melt(id_vars="tanggal", value_vars=["Modal (Investasi)", "Nilai Pasar Saat Ini"], var_name="Kategori", value_name="Nilai")
                            if df_melt_aset.empty:
                                st.info("Tidak ada data untuk periode yang dipilih.")
                            else:
                                y_min_a = df_melt_aset["Nilai"].min() * 0.995
                                y_max_a = df_melt_aset["Nilai"].max() * 1.005
                                grafik_aset_port = alt.Chart(df_melt_aset).mark_line(point=True).encode(
                                    x=alt.X("tanggal:T", title="Tanggal"),
                                    y=alt.Y("Nilai:Q", title="Nilai (Rp)", scale=alt.Scale(domain=[y_min_a, y_max_a])),
                                    color=alt.Color("Kategori:N"),
                                    tooltip=[alt.Tooltip("tanggal:T", title="Tanggal", format="%Y-%m-%d"), alt.Tooltip("Kategori:N"), alt.Tooltip("Nilai:Q", format=",.0f")]
                                ).properties(height=350).interactive()
                                st.altair_chart(grafik_aset_port, use_container_width=True)
                        else:
                            st.info(f"Tidak ada data transaksi untuk {aset_tren_pilihan}.")


                with st.expander("📜 Riwayat Transaksi Lengkap"):
                    df_riwayat = df_port.copy()
                    
                    def format_jumlah_riwayat(row):
                        if "Saham" in row["nama_aset"]:
                            return f"{row['jumlah'] / 100:.2f} Lot"
                        else:
                            return f"{row['jumlah']:.2f} Gram"
                            
                    df_riwayat["Jumlah"] = df_riwayat.apply(format_jumlah_riwayat, axis=1)
                    # Format tanggal YYYY-MM-DD
                    df_riwayat["tanggal_beli"] = pd.to_datetime(df_riwayat["tanggal_beli"]).dt.strftime("%Y-%m-%d")
                    df_riwayat = df_riwayat.rename(columns={
                        "nama_aset": "Nama Aset",
                        "harga_beli": "Harga Beli (Unit)",
                        "tanggal_beli": "Tanggal Beli"
                    })
                    df_riwayat["Nama Aset"] = df_riwayat["Nama Aset"].replace("Emas (IDR/gram)", "Emas")
                    # Urutkan tanggal terbaru di atas
                    df_riwayat = df_riwayat.sort_values("Tanggal Beli", ascending=False)
                    
                    st.dataframe(
                        df_riwayat[["Tanggal Beli", "Nama Aset", "Jumlah", "Harga Beli (Unit)"]].style.format({
                            "Harga Beli (Unit)": lambda v: f"Rp {v:,.0f}".replace(",", ".")
                        }),
                        use_container_width=True,
                        hide_index=True
                    )

except Exception as e:
    st.error(f"❌ Gagal memuat data dari semua jalur. Detail: {e}")