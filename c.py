import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
import plotly.express as px

# ------------------------------
# Konstanta dan Setup Awal
# ------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------------
# Fungsi Utilitas
# ------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_filepath(file, username):
    return os.path.join(DATA_DIR, f"{username}_{file}")

def load_data(file, username=None):
    filepath = get_user_filepath(file, username) if username else os.path.join(DATA_DIR, file)
    return pd.read_csv(filepath) if os.path.exists(filepath) else pd.DataFrame()

def save_data(df, file, username=None):
    filepath = get_user_filepath(file, username) if username else os.path.join(DATA_DIR, file)
    df.to_csv(filepath, index=False)

def append_data(data, file, username=None):
    df_new = pd.DataFrame([data])
    df = load_data(file, username)
    df = pd.concat([df, df_new], ignore_index=True)
    save_data(df, file, username)

# ------------------------------
# Autentikasi
# ------------------------------
def login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    st.title("🔐 Login / Daftar Akun")

    akun_file = os.path.join(DATA_DIR, "akun.csv")
    akun_df = pd.read_csv(akun_file) if os.path.exists(akun_file) else pd.DataFrame(columns=["Username", "Password"])

    mode = st.selectbox("Pilih Aksi", ["Login", "Daftar"])
    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Sandi", type="password")

    if mode == "Login":
        if st.button("Masuk"):
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
                return False
            hashed_pw = hash_password(password)
            if not akun_df.empty and ((akun_df['Username'] == username) & (akun_df['Password'] == hashed_pw)).any():
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Login berhasil!")
                st.rerun()
            else:
                st.error("Username atau password salah.")
                return False

    elif mode == "Daftar":
        if st.button("Daftar"):
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
                return False
            if not akun_df.empty and (akun_df['Username'] == username).any():
                st.error("Username sudah digunakan.")
                return False
            new_user = {"Username": username, "Password": hash_password(password)}
            akun_df = pd.concat([akun_df, pd.DataFrame([new_user])], ignore_index=True)
            akun_df.to_csv(akun_file, index=False)
            for f in ["pemasukan.csv", "pengeluaran.csv", "jurnal.csv"]:
                pd.DataFrame().to_csv(get_user_filepath(f, username), index=False)
            st.success("Akun berhasil dibuat. Silakan login.")
            st.rerun()
        return False

# ------------------------------
# Pemasukan
# ------------------------------
def pemasukan():
    st.subheader("Tambah Pemasukan")
    tanggal = st.date_input("Tanggal")
    kategori = st.selectbox("Kategori", ["Penjualan Gabah", "Penjualan Beras", "Pelunasan Piutang", "Lainnya"])
    jumlah = st.number_input("Jumlah", min_value=0.0)
    keterangan = st.text_input("Keterangan")

    if st.button("✅ Simpan Pemasukan"):
        data = {
            "Tanggal": tanggal,
            "Kategori": kategori,
            "Jumlah": jumlah,
            "Keterangan": keterangan
        }
        append_data(data, "pemasukan.csv", st.session_state['username'])
        st.success("Data pemasukan berhasil disimpan.")

        jurnal = {
            "Tanggal": tanggal,
            "Keterangan": f"Pemasukan - {kategori}",
            "Debit": jumlah,
            "Kredit": 0
        }
        append_data(jurnal, "jurnal.csv", st.session_state['username'])

# ------------------------------
# Pengeluaran
# ------------------------------
def pengeluaran():
    st.subheader("Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal")
    kategori = st.selectbox("Kategori", ["Bibit", "Pupuk", "Pestisida", "Gaji", "Peralatan", "Sewa Traktor", "Penyusutan", "Lainnya"])
    jumlah = st.number_input("Jumlah", min_value=0.0)
    keterangan = st.text_input("Keterangan")

    if st.button("✅ Simpan Pengeluaran"):
        data = {
            "Tanggal": tanggal,
            "Kategori": kategori,
            "Jumlah": jumlah,
            "Keterangan": keterangan
        }
        append_data(data, "pengeluaran.csv", st.session_state['username'])
        st.success("Data pengeluaran berhasil disimpan.")

        jurnal = {
            "Tanggal": tanggal,
            "Keterangan": f"Pengeluaran - {kategori}",
            "Debit": 0,
            "Kredit": jumlah
        }
        append_data(jurnal, "jurnal.csv", st.session_state['username'])

# ------------------------------
# Laporan
# ------------------------------
def laporan():
    st.subheader("📊 Laporan Keuangan")

    pemasukan_df = load_data("pemasukan.csv", st.session_state['username'])
    pengeluaran_df = load_data("pengeluaran.csv", st.session_state['username'])
    jurnal_df = load_data("jurnal.csv", st.session_state['username'])

    total_pemasukan = pemasukan_df['Jumlah'].sum() if not pemasukan_df.empty else 0
    total_pengeluaran = pengeluaran_df['Jumlah'].sum() if not pengeluaran_df.empty else 0
    saldo = total_pemasukan - total_pengeluaran

    st.metric("Total Pemasukan", f"Rp {total_pemasukan:,.0f}")
    st.metric("Total Pengeluaran", f"Rp {total_pengeluaran:,.0f}")
    st.metric("Saldo Akhir", f"Rp {saldo:,.0f}")

    st.markdown("---")
    st.subheader("📅 Grafik Bulanan")

    if not jurnal_df.empty:
        jurnal_df['Tanggal'] = pd.to_datetime(jurnal_df['Tanggal'])
        jurnal_df['Bulan'] = jurnal_df['Tanggal'].dt.to_period('M').astype(str)
        df_agg = jurnal_df.groupby('Bulan').agg({"Debit": "sum", "Kredit": "sum"}).reset_index()

        fig = px.bar(df_agg, x='Bulan', y=['Debit', 'Kredit'], barmode='group',
                     labels={'value': 'Jumlah (Rp)', 'variable': 'Jenis'})
        st.plotly_chart(fig)

# ------------------------------
# Main App
# ------------------------------
if __name__ == "__main__":
    if not st.session_state.get("logged_in"):
        login()
    else:
        st.sidebar.title(f"👤 {st.session_state['username']}")
        menu = st.sidebar.radio("Navigasi", ["Pemasukan", "Pengeluaran", "Laporan", "Logout"])

        if menu == "Pemasukan":
            pemasukan()
        elif menu == "Pengeluaran":
            pengeluaran()
        elif menu == "Laporan":
            laporan()
        elif menu == "Logout":
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.rerun()
