import streamlit as st
import requests
import pandas as pd
from sqlalchemy import create_engine, text
try:
    from src.auth import init_db_auth, autentikasi_pengguna, tambah_pengguna, ganti_password, ambil_semua_pengguna, ubah_role_pengguna, hapus_pengguna
except ModuleNotFoundError:
    from auth import init_db_auth, autentikasi_pengguna, tambah_pengguna, ganti_password, ambil_semua_pengguna, ubah_role_pengguna, hapus_pengguna

# Inisialisasi DB auth saat pertama kali dijalankan (jika diperlukan)
init_db_auth()

st.set_page_config(page_title="Dashboard KPI Finansial", layout="wide")

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
            st.markdown('<div class="login-title">🔐 KPI Dashboard</div>', unsafe_allow_html=True)
            
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

st.title("📊 Dashboard KPI Live: Emas & Saham")
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
            col_metrik1, col_metrik2 = st.columns(2)
            with col_metrik1:
                st.metric(label="Total Baris Data Terbaca", value=f"{len(df)} Baris")
            with col_metrik2:
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
            
            kolom1, kolom2 = st.columns(2)
            
            with kolom1:
                st.subheader(f"📈 Grafik Harga Penutupan - {aset_pilihan}")
                st.line_chart(data=df_filter, x="tanggal", y="harga_tutup")
                
            with kolom2:
                st.subheader("📋 Data Tabel Terbaru")
                st.dataframe(df_filter.tail(10), use_container_width=True)
                
        with tab_portofolio:
            st.subheader("💼 Portofolio Investasi")
            
            # Ambil data portofolio dari DB
            df_port = ambil_data_portofolio(st.session_state.username)
            
            # Hitung harga terkini setiap aset
            df_terbaru = df.sort_values("tanggal", ascending=False).groupby("nama_aset").first().reset_index()
            
            # --- FORM INPUT TRANSAKSI (Expander) ---
            with st.expander("➕ Tambah Pembelian Aset Baru", expanded=False):
                st.write("Masukkan rincian aset yang baru Anda beli untuk ditambahkan ke portofolio.")
                
                form_nama_aset = st.selectbox("Pilih Aset:", df["nama_aset"].unique(), key="form_nama")
                apakah_saham = "Saham" in form_nama_aset
                label_jumlah = "Jumlah Lot" if apakah_saham else "Jumlah Gram"
                label_harga = "Harga Beli per Lembar (Rupiah)" if apakah_saham else "Harga Beli per Gram (Rupiah)"
                
                kol_input1, kol_input2 = st.columns(2)
                with kol_input1:
                    input_jumlah = st.number_input(f"{label_jumlah}:", min_value=0.01, step=1.0 if apakah_saham else 0.1, key="form_jumlah")
                with kol_input2:
                    harga_sekarang = df_terbaru[df_terbaru["nama_aset"] == form_nama_aset]["harga_tutup"].values[0] if not df_terbaru[df_terbaru["nama_aset"] == form_nama_aset].empty else 0.0
                    input_harga = st.number_input(f"{label_harga}:", min_value=1.0, value=float(harga_sekarang), step=100.0 if apakah_saham else 1000.0, key="form_harga")
                
                input_tanggal = st.date_input("Tanggal Pembelian:", key="form_tanggal")
                
                tombol_simpan = st.button("Simpan ke Portofolio")
                if tombol_simpan:
                    # Konversi Lot ke Lembar untuk penyimpanan database saham
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
                                    "nama": form_nama_aset,
                                    "jumlah": jumlah_simpan,
                                    "harga": input_harga,
                                    "tanggal": input_tanggal,
                                    "username": st.session_state.username
                                }
                            )
                            conn.commit()
                        st.success(f"Sukses menambahkan pembelian {form_nama_aset}!")
                        st.cache_data.clear() # Invalidate cache
                        st.rerun() # Refresh page
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
                        desc = f"ID {row['id']} | {row['tanggal_beli']} | {row['nama_aset']} - {jumlah_disp} @ Rp {row['harga_beli']:,.2f}"
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
                
                dict_harga_terbaru = dict(zip(df_terbaru["nama_aset"], df_terbaru["harga_tutup"]))
                df_port_summary["harga_sekarang"] = df_port_summary["nama_aset"].map(dict_harga_terbaru).fillna(0.0)
                
                df_port_summary["total_investasi"] = df_port_summary["jumlah"] * df_port_summary["harga_beli"]
                df_port_summary["nilai_sekarang"] = df_port_summary["jumlah"] * df_port_summary["harga_sekarang"]
                df_port_summary["profit_loss"] = df_port_summary["nilai_sekarang"] - df_port_summary["total_investasi"]
                
                total_investasi_port = df_port_summary["total_investasi"].sum()
                nilai_sekarang_port = df_port_summary["nilai_sekarang"].sum()
                profit_loss_port = nilai_sekarang_port - total_investasi_port
                profit_loss_persen_port = (profit_loss_port / total_investasi_port * 100) if total_investasi_port > 0 else 0.0
                
                metric_port1, metric_port2, metric_port3 = st.columns(3)
                with metric_port1:
                    st.metric(label="Total Nilai Investasi (Modal)", value=f"Rp {total_investasi_port:,.2f}")
                with metric_port2:
                    st.metric(label="Nilai Portofolio Saat Ini", value=f"Rp {nilai_sekarang_port:,.2f}")
                with metric_port3:
                    tanda = "+" if profit_loss_port >= 0 else ""
                    st.metric(
                        label="Total Keuntungan / Kerugian", 
                        value=f"Rp {profit_loss_port:,.2f}", 
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
                
                st.dataframe(
                    tabel_tampilan[kolom_diurutkan].style.format({
                        "Harga Rata-Rata Beli (Unit)": "Rp {:,.2f}",
                        "Harga Pasar Saat Ini (Unit)": "Rp {:,.2f}",
                        "Total Modal": "Rp {:,.2f}",
                        "Nilai Pasar Saat Ini": "Rp {:,.2f}",
                        "Profit / Loss (Rp)": "Rp {:,.2f}",
                        "Profit / Loss (%)": "{:+.2f}%"
                    }),
                    use_container_width=True
                )
                

                st.subheader("📈 Tren Kinerja Investasi")
                opsi_tren = st.radio(
                    "Pilih Tampilan Tren:", 
                    ["Total Portofolio", "Per Aset Individu"], 
                    horizontal=True, 
                    key="opsi_tren_kinerja"
                )
                
                if opsi_tren == "Total Portofolio":
                    with st.spinner("Menghitung tren total portofolio..."):
                        df_trend_total = hitung_tren_total_portofolio(df, df_port)
                        if not df_trend_total.empty:
                            df_trend_total = df_trend_total.set_index("tanggal")
                            st.line_chart(df_trend_total[["Total Modal (Investasi)", "Total Nilai Pasar Saat Ini"]])
                        else:
                            st.info("Tidak dapat memuat tren portofolio.")
                else:
                    aset_tren_pilihan = st.selectbox(
                        "Pilih Aset untuk Dilihat Trennya:", 
                        df_grouped["nama_aset"].unique(),
                        key="aset_tren_pilihan"
                    )
                    
                    with st.spinner(f"Menghitung tren {aset_tren_pilihan}..."):
                        df_historis_aset = df[df["nama_aset"] == aset_tren_pilihan]
                        df_transaksi_aset = df_port[df_port["nama_aset"] == aset_tren_pilihan]
                        
                        df_trend_aset = hitung_tren_portofolio_aset(df_historis_aset, df_transaksi_aset)
                        if not df_trend_aset.empty:
                            df_trend_aset = df_trend_aset.set_index("tanggal")
                            st.line_chart(df_trend_aset[["Modal (Investasi)", "Nilai Pasar Saat Ini"]])
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
                    df_riwayat = df_riwayat.rename(columns={
                        "nama_aset": "Nama Aset",
                        "harga_beli": "Harga Beli (Unit)",
                        "tanggal_beli": "Tanggal Beli"
                    })
                    
                    st.dataframe(
                        df_riwayat[["Tanggal Beli", "Nama Aset", "Jumlah", "Harga Beli (Unit)"]].style.format({
                            "Harga Beli (Unit)": "Rp {:,.2f}"
                        }),
                        use_container_width=True
                    )
        


except Exception as e:
    st.error(f"❌ Gagal memuat data dari semua jalur. Detail: {e}")