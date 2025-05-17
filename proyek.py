import streamlit as st
from datetime import datetime
import os
import hashlib
import pandas as pd
import plotly.express as px 
import base64

# ==================== HELPER FUNCTIONS ====================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_file(base_filename, username):
    # Create data directory if not exists
    os.makedirs("data", exist_ok=True)
    name, ext = os.path.splitext(base_filename)
    return f"data/{name}_{username}{ext}"

def load_data(base_filename, username):
    filename = get_user_file(base_filename, username)
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename)
        except pd.errors.EmptyDataError:
            if "pemasukan" in filename:
                return pd.DataFrame(columns=["Tanggal", "Sumber", "Jumlah", "Metode", "Keterangan", "Username"])
            elif "pengeluaran" in filename:
                return pd.DataFrame(columns=["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan", "Metode", "Username"])
            elif "jurnal" in filename:
                return pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])
            else:
                return pd.DataFrame()
    else:
        if "pemasukan" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Sumber", "Jumlah", "Metode", "Keterangan", "Username"])
        elif "pengeluaran" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan", "Metode", "Username"])
        elif "jurnal" in base_filename:
            return pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"])
        else:
            return pd.DataFrame()

def save_data(df, base_filename, username):
    filename = get_user_file(base_filename, username)
    df.to_csv(filename, index=False)

def append_data(data, base_filename, username):
    df = load_data(base_filename, username)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    save_data(df, base_filename, username)

def buat_jurnal(tanggal, akun_debit, akun_kredit, jumlah, keterangan):
    return [
        {"Tanggal": tanggal, "Akun": akun_debit, "Debit": jumlah, "Kredit": 0, "Keterangan": keterangan},
        {"Tanggal": tanggal, "Akun": akun_kredit, "Debit": 0, "Kredit": jumlah, "Keterangan": keterangan},
    ]

def load_user_accounts():
    if os.path.exists("data/akun.csv"):
        return pd.read_csv("data/akun.csv")
    else:
        return pd.DataFrame(columns=["Username", "Password"])

def save_user_accounts(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/akun.csv", index=False)

def register_user(username, password):
    akun_df = load_user_accounts()
    if (akun_df['Username'] == username).any():
        return False
    akun_df = pd.concat([akun_df, pd.DataFrame([{"Username": username, "Password": hash_password(password)}])], ignore_index=True)
    save_user_accounts(akun_df)
    return True

def validate_login(username, password):
    akun_df = load_user_accounts()
    hashed_pw = hash_password(password)
    return ((akun_df['Username'] == username) & (akun_df['Password'] == hashed_pw)).any()

# ==================== CUSTOM STYLING ====================
def apply_custom_styles():
    st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            padding: 8px 16px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input,
        .stTextArea>div>div>textarea {
            border-radius: 4px;
        }
        .stMetric {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# ==================== LOGIN & REGISTER ====================
def login_register():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        return True

    st.title("Login / Daftar Akun")
    st.write("---")
    
    mode = st.radio("Pilih Mode", ["Login", "Daftar"], horizontal=True)
    
    with st.form(key='auth_form'):
        username = st.text_input("Nama Pengguna", placeholder="Masukkan username")
        password = st.text_input("Kata Sandi", type="password", placeholder="Masukkan password")
        
        if mode == "Login":
            submitted = st.form_submit_button("Masuk")
            if submitted:
                if not username.strip() or not password.strip():
                    st.error("Harap isi semua kolom.")
                elif validate_login(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success(f"Login berhasil! Selamat datang, {username}.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
        else:
            submitted = st.form_submit_button("Daftar")
            if submitted:
                if not username.strip() or not password.strip():
                    st.error("Harap isi semua kolom.")
                elif register_user(username, password):
                    st.success("Akun berhasil dibuat. Silakan login.")
                else:
                    st.error("Username sudah digunakan.")

    return False

# ==================== DATA CATEGORIES ====================
kategori_pengeluaran = {
    "Bibit": ["Intani", "Inpari", "Ciherang"],
    "Pupuk": ["Urea", "NPK", "Organik"],
    "Pestisida": ["Furadan", "BPMC", "Dursban"],
    "Alat Tani": ["Sabit", "Cangkul", "Karung"],
    "Tenaga Kerja": ["Upah Harian", "Borongan"],
    "Lainnya": ["Lain-lain"]
}

kategori_pemasukan = {
    "Sumber Pemasukan": ["Penjualan Padi", "Lain-lain"]
}

# ==================== INCOME FUNCTION ====================
def pemasukan():
    st.subheader("Tambah Pemasukan")
    st.write("---")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.date_input("Tanggal", datetime.now())
            sumber = st.selectbox("Sumber Pemasukan", kategori_pemasukan["Sumber Pemasukan"])
            jumlah = st.number_input("Jumlah (Rp)", min_value=0)
        with col2:
            deskripsi = st.text_area("Keterangan (opsional)") 
            metode = st.radio("Metode Penerimaan", ["Tunai", "Transfer", "Piutang", "Pelunasan Piutang"], horizontal=True)
        
        if st.button("Simpan Pemasukan", use_container_width=True):
            if not sumber.strip() or jumlah <= 0:
                st.error("Isi data dengan benar.")
                return
            waktu = tanggal.strftime("%Y-%m-%d %H:%M:%S")
            username = st.session_state['username']
            data = {
                "Tanggal": waktu,
                "Sumber": sumber,
                "Jumlah": jumlah,
                "Metode": metode,
                "Keterangan": deskripsi,
                "Username": username
            }
            append_data(data, "pemasukan.csv", username)
            akun_debit = {
                "Tunai": "Kas",
                "Transfer": "Bank",
                "Piutang": "Piutang Dagang",
                "Pelunasan Piutang": "Kas"
            }[metode]
            akun_kredit = "Pendapatan" if metode != "Pelunasan Piutang" else "Piutang Dagang"
            jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, sumber)
            for j in jurnal:
                append_data(j, "jurnal.csv", username)
            st.success("Pemasukan berhasil disimpan.")
            st.balloons()

# ==================== EXPENSE FUNCTION ====================
def pengeluaran():
    st.subheader("Tambah Pengeluaran")
    st.write("---")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            tanggal = st.date_input("Tanggal", datetime.now())
            kategori = st.selectbox("Kategori Utama", list(kategori_pengeluaran.keys()))
            sub_kategori = st.selectbox("Sub Kategori", kategori_pengeluaran[kategori])
            jumlah = st.number_input("Jumlah (Rp)", min_value=0)
        with col2:
            deskripsi = st.text_area("Keterangan (opsional)")
            metode = st.radio("Metode Pembayaran", ["Tunai", "Transfer", "Utang", "Pelunasan Utang"], horizontal=True)
        
        if st.button("Simpan Pengeluaran", use_container_width=True):
            if jumlah <= 0:
                st.error("Jumlah tidak boleh 0.")
                return
            waktu = tanggal.strftime("%Y-%m-%d %H:%M:%S")
            username = st.session_state['username']
            data = {
                "Tanggal": waktu,
                "Kategori": kategori,
                "Sub Kategori": sub_kategori,
                "Jumlah": jumlah,
                "Keterangan": deskripsi,
                "Metode": metode,
                "Username": username
            }
            append_data(data, "pengeluaran.csv", username)
            akun_kredit = {
                "Tunai": "Kas",
                "Transfer": "Bank",
                "Utang": "Utang Dagang",
                "Pelunasan Utang": "Kas"
            }[metode]
            akun_debit = sub_kategori if metode != "Pelunasan Utang" else "Utang Dagang"
            jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, deskripsi)
            for j in jurnal:
                append_data(j, "jurnal.csv", username)
            st.success("Pengeluaran berhasil disimpan.")
            st.balloons()

# ==================== REPORT FUNCTION ====================
def laporan():
    st.header("Laporan Keuangan")
    st.write("---")
    
    username = st.session_state['username']

    col1, col2 = st.columns(2)
    with col1:
        mulai = st.date_input("Tanggal Mulai", datetime.now().replace(day=1))
    with col2:
        akhir = st.date_input("Tanggal Akhir", datetime.now())

    pemasukan_df = load_data("pemasukan.csv", username)
    pengeluaran_df = load_data("pengeluaran.csv", username)
    jurnal_df = load_data("jurnal.csv", username)

    for df in [pemasukan_df, pengeluaran_df, jurnal_df]:
        if not df.empty and "Tanggal" in df.columns:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors='coerce')

    jurnal_df = jurnal_df[(jurnal_df['Tanggal'] >= pd.to_datetime(mulai)) & (jurnal_df['Tanggal'] <= pd.to_datetime(akhir))]

    tabs = st.tabs(["Ringkasan", "Jurnal Umum", "Buku Besar", "Laba Rugi", "Neraca"])

    with tabs[0]:
        st.subheader("Ringkasan Keuangan")
        total_pemasukan = pemasukan_df[(pemasukan_df['Tanggal'] >= pd.to_datetime(mulai)) & 
                                      (pemasukan_df['Tanggal'] <= pd.to_datetime(akhir))]['Jumlah'].sum() if not pemasukan_df.empty else 0
        total_pengeluaran = pengeluaran_df[(pengeluaran_df['Tanggal'] >= pd.to_datetime(mulai)) & 
                                         (pengeluaran_df['Tanggal'] <= pd.to_datetime(akhir))]['Jumlah'].sum() if not pengeluaran_df.empty else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
        with col2:
            st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
        with col3:
            saldo = total_pemasukan - total_pengeluaran
            st.metric("Saldo", f"Rp {saldo:,.0f}")

        if total_pemasukan > 0 or total_pengeluaran > 0:
            df_sum = pd.DataFrame({
                'Kategori': ['Pemasukan', 'Pengeluaran'],
                'Jumlah': [total_pemasukan, total_pengeluaran]
            })
            fig = px.pie(df_sum, values='Jumlah', names='Kategori', 
                         title="Persentase Pemasukan dan Pengeluaran")
            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Jurnal Umum")
        if not jurnal_df.empty:
            st.dataframe(jurnal_df.style.format({'Debit': '{:,.0f}', 'Kredit': '{:,.0f}'}), 
                        use_container_width=True)
        else:
            st.warning("Tidak ada data jurnal untuk periode ini.")

    with tabs[2]:
        st.subheader("Buku Besar")
        if not jurnal_df.empty:
            akun_list = jurnal_df['Akun'].unique()
            for akun in akun_list:
                with st.expander(f"Akun: {akun}"):
                    df_akun = jurnal_df[jurnal_df['Akun'] == akun].copy()
                    df_akun = df_akun.sort_values("Tanggal")
                    df_akun['Saldo'] = df_akun['Debit'] - df_akun['Kredit']
                    df_akun['Saldo'] = df_akun['Saldo'].cumsum()
                    st.dataframe(df_akun.style.format({'Debit': '{:,.0f}', 'Kredit': '{:,.0f}', 'Saldo': '{:,.0f}'}))
        else:
            st.warning("Tidak ada data buku besar untuk periode ini.")

    with tabs[3]:
        st.subheader("Laporan Laba Rugi")
        pendapatan = jurnal_df[jurnal_df['Akun'].str.contains("Pendapatan")]['Kredit'].sum() if not jurnal_df.empty else 0
        beban = jurnal_df[~jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang', 'Utang Dagang', 'Pendapatan'])]['Debit'].sum() if not jurnal_df.empty else 0
        laba_rugi = pendapatan - beban
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pendapatan", f"Rp {pendapatan:,.0f}")
        with col2:
            st.metric("Beban", f"Rp {beban:,.0f}")
        with col3:
            st.metric("Laba / Rugi", f"Rp {laba_rugi:,.0f}")
        
        if pendapatan > 0 or beban > 0:
            df_lr = pd.DataFrame({
                'Kategori': ['Pendapatan', 'Beban'],
                'Jumlah': [pendapatan, beban]
            })
            fig = px.bar(df_lr, x='Kategori', y='Jumlah', 
                        title="Perbandingan Pendapatan dan Beban")
            st.plotly_chart(fig, use_container_width=True)

    with tabs[4]:
        st.subheader("Neraca Keuangan")
        aktiva = jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Debit'].sum() - jurnal_df[jurnal_df['Akun'].isin(['Kas', 'Bank', 'Piutang Dagang'])]['Kredit'].sum() if not jurnal_df.empty else 0
        kewajiban = jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Kredit'].sum() - jurnal_df[jurnal_df['Akun'].isin(['Utang Dagang'])]['Debit'].sum() if not jurnal_df.empty else 0
        ekuitas = laba_rugi
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Aktiva", f"Rp {aktiva:,.0f}")
        with col2:
            st.metric("Kewajiban", f"Rp {kewajiban:,.0f}")
        with col3:
            st.metric("Ekuitas", f"Rp {ekuitas:,.0f}")
        
        if aktiva > 0 or kewajiban > 0 or ekuitas > 0:
            df_neraca = pd.DataFrame({
                'Kategori': ['Aktiva', 'Kewajiban', 'Ekuitas'],
                'Jumlah': [aktiva, kewajiban, ekuitas]
            })
            fig = px.pie(df_neraca, values='Jumlah', names='Kategori',
                        title="Komposisi Neraca Keuangan")
            st.plotly_chart(fig, use_container_width=True)

# ==================== MAIN APP ====================
def main():
    st.set_page_config(
        page_title="SiPadi",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom styles
    apply_custom_styles()
    
    # Sidebar with logo
    with st.sidebar:
        st.image("logo.jpg", width=80)
        st.title("SiPadi")
        st.title("Petani Makmur")
        st.write("---")
        
    logged_in = login_register()
    if not logged_in:
        return
    
    # Main menu
    with st.sidebar:
        menu = st.radio(
            "Menu Navigasi",
            ["Beranda", "Pemasukan", "Pengeluaran", "Laporan", "Logout"],
            index=0
        )
    
    if menu == "Beranda":
        st.title(f"Selamat datang, {st.session_state['username']}!")
        st.write("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Aplikasi Keuangan untuk Petani")
            st.write("Kelola keuangan usaha tani Anda dengan lebih mudah dan efisien.")
            
            st.subheader("Fitur Utama:")
            st.write("- Catat pemasukan dari hasil panen")
            st.write("- Lacak pengeluaran usaha tani")
            st.write("- Laporan keuangan lengkap")
            st.write("- Analisis laba rugi")
            st.write("- Neraca keuangan")
            
        with col2:
            st.subheader("Aktivitas Terakhir")
            st.write("Berikut ringkasan aktivitas terakhir Anda:")
            
            # Show recent transactions
            username = st.session_state['username']
            pemasukan_df = load_data("pemasukan.csv", username)
            pengeluaran_df = load_data("pengeluaran.csv", username)
            
            if not pemasukan_df.empty:
                pemasukan_df["Tanggal"] = pd.to_datetime(pemasukan_df["Tanggal"])
                st.write("5 Pemasukan Terakhir")
                st.dataframe(pemasukan_df.sort_values("Tanggal", ascending=False).head(5)[["Tanggal", "Sumber", "Jumlah"]].style.format({'Jumlah': 'Rp {:,.0f}'}))
            
            if not pengeluaran_df.empty:
                pengeluaran_df["Tanggal"] = pd.to_datetime(pengeluaran_df["Tanggal"])
                st.write("5 Pengeluaran Terakhir")
                st.dataframe(pengeluaran_df.sort_values("Tanggal", ascending=False).head(5)[["Tanggal", "Kategori", "Jumlah"]].style.format({'Jumlah': 'Rp {:,.0f}'}))

    elif menu == "Pemasukan":
        pemasukan()

    elif menu == "Pengeluaran":
        pengeluaran()

    elif menu == "Laporan":
        laporan()

    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.success("Anda telah berhasil logout.")
        st.rerun()

if __name__ == "__main__":
    main()
