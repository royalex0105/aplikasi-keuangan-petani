import streamlit as st
from datetime import datetime
import os
import hashlib
import pandas as pd
import plotly.express as px

# ----------- Helper Functions ------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_file(base_filename, username):
    name, ext = os.path.splitext(base_filename)
    return f"{name}_{username}{ext}"

def load_data(base_filename, username):
    filename = get_user_file(base_filename, username)
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            return df
        except pd.errors.EmptyDataError:
            return empty_df_by_file(base_filename)
    else:
        return empty_df_by_file(base_filename)

def empty_df_by_file(base_filename):
    if "pemasukan" in base_filename:
        return pd.DataFrame(columns=["Tanggal", "Sumber", "Jumlah", "Metode", "Keterangan", "Username"])
    elif "pengeluaran" in base_filename:
        return pd.DataFrame(columns=["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan", "Metode", "Username"])
    elif "jurnal" in base_filename:
        return pd.DataFrame(columns=["Tanggal", "Akun", "Debit", "Kredit", "Keterangan", "Username"])
    elif "akun" in base_filename:
        return pd.DataFrame(columns=["Username", "Password"])
    else:
        return pd.DataFrame()

def save_data(df, base_filename, username):
    filename = get_user_file(base_filename, username)
    df.to_csv(filename, index=False)

def append_data(data, base_filename, username):
    df = load_data(base_filename, username)
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    save_data(df, base_filename, username)

def buat_jurnal(tanggal, akun_debit, akun_kredit, jumlah, keterangan, username):
    return [
        {"Tanggal": tanggal, "Akun": akun_debit, "Debit": jumlah, "Kredit": 0, "Keterangan": keterangan, "Username": username},
        {"Tanggal": tanggal, "Akun": akun_kredit, "Debit": 0, "Kredit": jumlah, "Keterangan": keterangan, "Username": username},
    ]

def load_user_accounts():
    if os.path.exists("akun.csv"):
        return pd.read_csv("akun.csv")
    else:
        return pd.DataFrame(columns=["Username", "Password"])

def save_user_accounts(df):
    df.to_csv("akun.csv", index=False)

def register_user(username, password):
    akun_df = load_user_accounts()
    if (akun_df['Username'] == username).any():
        return False  # Username sudah ada
    akun_df = pd.concat([akun_df, pd.DataFrame([{"Username": username, "Password": hash_password(password)}])], ignore_index=True)
    save_user_accounts(akun_df)
    return True

def validate_login(username, password):
    akun_df = load_user_accounts()
    hashed_pw = hash_password(password)
    return ((akun_df['Username'] == username) & (akun_df['Password'] == hashed_pw)).any()

def load_csv_from_url(url):
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal load data dari {url}: {e}")
        return pd.DataFrame()

# ----------- Data Kategori -------------

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

# ----------- Fungsi Login / Register -------------

def login_register():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        return True

    st.title("🔐 Login / Daftar Akun")

    mode = st.radio("Pilih Mode", ["Login", "Daftar"])
    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Sandi", type="password")

    if mode == "Login":
        if st.button("Masuk"):
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
            elif validate_login(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f"Login berhasil! Selamat datang, {username}.")
                st.experimental_rerun()
            else:
                st.error("Username atau password salah.")

    else:  # Daftar
        if st.button("Daftar"):
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
            elif register_user(username, password):
                st.success("Akun berhasil dibuat. Silakan login.")
            else:
                st.error("Username sudah digunakan.")

    return False

# ----------- Fungsi Pemasukan -------------

def pemasukan():
    st.subheader("Tambah Pemasukan")
    tanggal = st.date_input("Tanggal", datetime.now())
    sumber = st.selectbox("Sumber Pemasukan", kategori_pemasukan["Sumber Pemasukan"])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    deskripsi = st.text_area("Keterangan (opsional)")
    metode = st.radio("Metode Penerimaan", ["Tunai", "Transfer", "Piutang", "Pelunasan Piutang"])

    if st.button("✅ Simpan Pemasukan"):
        if not sumber.strip() or jumlah <= 0:
            st.error("Isi data dengan benar.")
            return
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, sumber, username)
        for j in jurnal:
            append_data(j, "jurnal.csv", username)

        st.success("✅ Pemasukan berhasil disimpan.")

# ----------- Fungsi Pengeluaran -------------

def pengeluaran():
    st.subheader("Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.now())
    kategori = st.selectbox("Kategori Utama", list(kategori_pengeluaran.keys()))
    sub_kategori = st.selectbox("Sub Kategori", kategori_pengeluaran[kategori])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    deskripsi = st.text_area("Keterangan (opsional)")
    metode = st.radio("Metode Pembayaran", ["Tunai", "Transfer", "Utang", "Pelunasan Utang"])

    if st.button("✅ Simpan Pengeluaran"):
        if jumlah <= 0:
            st.error("Jumlah tidak boleh 0.")
            return
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, deskripsi, username)
        for j in jurnal:
            append_data(j, "jurnal.csv", username)

        st.success("✅ Pengeluaran berhasil disimpan.")

# ----------- Fungsi Laporan -------------

def laporan():
    st.header("Laporan Keuangan")
    username = st.session_state['username']

    mulai = st.date_input("Tanggal Mulai", datetime.now().replace(day=1))
    akhir = st.date_input("Tanggal Akhir", datetime.now())

    # Coba load data lokal user, jika kosong, load contoh dari URL
    jurnal_df = load_data("jurnal.csv", username)
    pemasukan_df = load_data("pemasukan.csv", username)
    pengeluaran_df = load_data("pengeluaran.csv", username)

    # Kalau kosong, coba load dari URL contoh data (opsional, bisa dihilangkan kalau hanya mau data lokal)
    if jurnal_df.empty:
        url_jurnal = "https://raw.githubusercontent.com/royalex0105/aplikasi-keuangan-petani/main/jurnal.csv"
        jurnal_df = load_csv_from_url(url_jurnal)
    if pemasukan_df.empty:
        url_pemasukan = "https://raw.githubusercontent.com/royalex0105/aplikasi-keuangan-petani/main/pemasukan.csv"
        pemasukan_df = load_csv_from_url(url_pemasukan)
    if pengeluaran_df.empty:
        url_pengeluaran = "https://raw.githubusercontent.com/royalex0105/aplikasi-keuangan-petani/main/pengeluaran.csv"
        pengeluaran_df = load_csv_from_url(url_pengeluaran)

    for df in [jurnal_df, pemasukan_df, pengeluaran_df]:
        if not df.empty and "Tanggal" in df.columns:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors='coerce')

    jurnal_df = jurnal_df[(jurnal_df["Tanggal"] >= pd.to_datetime(mulai)) & (jurnal_df["Tanggal"] <= pd.to_datetime(akhir))]

    st.subheader("Jurnal Umum")
    st.dataframe(jurnal_df)

    # Buku Besar: total debit dan kredit per akun
    buku_besar = jurnal_df.groupby("Akun").agg(
        Total_Debit=pd.NamedAgg(column="Debit", aggfunc="sum"),
        Total_Kredit=pd.NamedAgg(column="Kredit", aggfunc="sum")
    ).reset_index()
    buku_besar["Saldo"] = buku_besar["Total_Debit"] - buku_besar["Total_Kredit"]

    st.subheader("Buku Besar")
    st.dataframe(buku_besar)

    # Laba Rugi sederhana: Pendapatan - Beban
    pendapatan = jurnal_df[jurnal_df["Akun"].str.lower().str.contains("pendapatan|penjualan")]
    total_pendapatan = pendapatan["Kredit"].sum() - pendapatan["Debit"].sum()

    beban = jurnal_df[jurnal_df["Akun"].str.lower().str.contains("beban|pengeluaran|gaji|pajak")]
    total_beban = beban["Debit"].sum() - beban["Kredit"].sum()

    laba_rugi = total_pendapatan - total_beban

    st.subheader("Laporan Laba Rugi Sederhana")
    st.write(f"Total Pendapatan: Rp {total_pendapatan:,.0f}")
    st.write(f"Total Beban: Rp {total_beban:,.0f}")
    st.write(f"Laba / Rugi Bersih: Rp {laba_rugi:,.0f}")

    # Grafik pendapatan dan beban per tanggal
    pendapatan_per_tgl = pendapatan.groupby("Tanggal")["Kredit"].sum()
    beban_per_tgl = beban.groupby("Tanggal")["Debit"].sum()

    df_grafik = pd.DataFrame({
        "Pendapatan": pendapatan_per_tgl,
        "Beban": beban_per_tgl
    }).fillna(0)

    if not df_grafik.empty:
        fig = px.line(df_grafik, x=df_grafik.index, y=["Pendapatan", "Beban"], title="Grafik Pendapatan & Beban")
        st.plotly_chart(fig)

# ----------- Main Application -------------

def main():
    st.set_page_config(page_title="Aplikasi Keuangan Petani", layout="wide")

    if not login_register():
        return

    st.sidebar.title(f"Selamat Datang, {st.session_state['username']}!")
    menu = st.sidebar.selectbox("Menu", ["Pemasukan", "Pengeluaran", "Laporan", "Logout"])

    if menu == "Pemasukan":
        pemasukan()
    elif menu == "Pengeluaran":
        pengeluaran()
    elif menu == "Laporan":
        laporan()
    elif menu == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['username'] = ""
        st.experimental_rerun()

if __name__ == "__main__":
    main()
