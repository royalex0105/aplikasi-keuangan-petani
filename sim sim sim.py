import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# ---------- Helper Functions ----------
def load_data(file):
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame()

def save_data(df, file):
    df.to_csv(file, index=False)

def append_data(data, file):
    df_new = pd.DataFrame([data])
    df = pd.concat([load_data(file), df_new], ignore_index=True)
    save_data(df, file)

def buat_jurnal(tanggal, akun_debit, akun_kredit, jumlah, keterangan):
    return [
        {"Tanggal": tanggal, "Akun": akun_debit, "Debit": jumlah, "Kredit": 0, "Keterangan": keterangan},
        {"Tanggal": tanggal, "Akun": akun_kredit, "Debit": 0, "Kredit": jumlah, "Keterangan": keterangan},
    ]

# ---------- Login ----------
def login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        return True

    st.title("🔐 Login / Daftar Akun")

    akun_file = "akun.csv"
    akun_df = load_data(akun_file)

    mode = st.selectbox("Pilih Aksi", ["Login", "Daftar"])

    username = st.text_input("Nama Pengguna")
    password = st.text_input("Kata Sandi", type="password")

    if mode == "Login":
        if st.button("Masuk"):
            if username.strip() == "" or password.strip() == "":
                st.error("Harap isi semua kolom.")
                return False
            if not akun_df.empty and ((akun_df['Username'] == username) & (akun_df['Password'] == password)).any():
                st.session_state['logged_in'] = True
                st.success("Login berhasil!")
                return True
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
            new_user = {"Username": username, "Password": password}
            append_data(new_user, akun_file)
            st.success("Akun berhasil dibuat. Silakan login.")
            return False

    return False

# ---------- Dropdown Sub Kategori ----------
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

# ---------- Pemasukan ----------
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
        data = {
            "Tanggal": waktu,
            "Sumber": sumber,
            "Jumlah": jumlah,
            "Metode": metode
        }
        append_data(data, "pemasukan.csv")
        akun_debit = {
            "Tunai": "Kas",
            "Transfer": "Bank",
            "Piutang": "Piutang Dagang",
            "Pelunasan Piutang": "Kas"
        }[metode]
        akun_kredit = "Pendapatan" if metode != "Pelunasan Piutang" else "Piutang Dagang"
        jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, sumber)
        for j in jurnal:
            append_data(j, "jurnal.csv")
        st.success("✅ Pemasukan berhasil disimpan.")

# ---------- Pengeluaran ----------
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
        data = {
            "Tanggal": waktu,
            "Kategori": kategori,
            "Sub Kategori": sub_kategori,
            "Jumlah": jumlah,
            "Keterangan": deskripsi,
            "Metode": metode
        }
        append_data(data, "pengeluaran.csv")
        akun_kredit = {
            "Tunai": "Kas",
            "Transfer": "Bank",
            "Utang": "Utang Dagang",
            "Pelunasan Utang": "Kas"
        }[metode]
        akun_debit = sub_kategori if metode != "Pelunasan Utang" else "Utang Dagang"
        jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, deskripsi)
        for j in jurnal:
            append_data(j, "jurnal.csv")
        st.success("✅ Pengeluaran berhasil disimpan.")

# ---------- Laporan ----------
def laporan():
    st.subheader("📊 Laporan Keuangan")
    jurnal_df = load_data("jurnal.csv")
    pemasukan_df = load_data("pemasukan.csv")
    pengeluaran_df = load_data("pengeluaran.csv")
    mulai = st.date_input("Tanggal Mulai", datetime.now().replace(day=1))
    akhir = st.date_input("Tanggal Akhir", datetime.now())

    # Konversi kolom Tanggal jika ada
    for df in [jurnal_df, pemasukan_df, pengeluaran_df]:
        if not df.empty and "Tanggal" in df.columns:
            df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

    # Filter tanggal
    if not jurnal_df.empty and "Tanggal" in jurnal_df.columns:
        jurnal_df = jurnal_df[
            (jurnal_df["Tanggal"] >= pd.to_datetime(mulai)) &
            (jurnal_df["Tanggal"] <= pd.to_datetime(akhir))
        ]
    if not pemasukan_df.empty and "Tanggal" in pemasukan_df.columns:
        pemasukan_df = pemasukan_df[
            (pemasukan_df["Tanggal"] >= pd.to_datetime(mulai)) &
            (pemasukan_df["Tanggal"] <= pd.to_datetime(akhir))
        ]
    if not pengeluaran_df.empty and "Tanggal" in pengeluaran_df.columns:
        pengeluaran_df = pengeluaran_df[
            (pengeluaran_df["Tanggal"] >= pd.to_datetime(mulai)) &
            (pengeluaran_df["Tanggal"] <= pd.to_datetime(akhir))
        ]

    tabs = st.tabs(["Ringkasan", "Jurnal Umum", "Buku Besar", "Laba Rugi", "Neraca"])

    with tabs[0]:
        pemasukan_total = pemasukan_df["Jumlah"].sum() if "Jumlah" in pemasukan_df else 0
        pengeluaran_total = pengeluaran_df["Jumlah"].sum() if "Jumlah" in pengeluaran_df else 0
        st.metric("Total Pemasukan", f"Rp {pemasukan_total:,.0f}")
        st.metric("Total Pengeluaran", f"Rp {pengeluaran_total:,.0f}")
        if pemasukan_total > 0 or pengeluaran_total > 0:
            ringkasan_df = pd.DataFrame({
                "Kategori": ["Pemasukan", "Pengeluaran"],
                "Jumlah": [pemasukan_total, pengeluaran_total]
            })
            fig = px.pie(ringkasan_df, values="Jumlah", names="Kategori")
            st.plotly_chart(fig)

    with tabs[1]:
        st.markdown("### Jurnal Umum")
        st.dataframe(jurnal_df if not jurnal_df.empty else pd.DataFrame())

    with tabs[2]:
        if not jurnal_df.empty:
            for akun in jurnal_df["Akun"].unique():
                df_akun = jurnal_df[jurnal_df["Akun"] == akun].copy()
                df_akun = df_akun.sort_values("Tanggal")
                df_akun["Saldo"] = (df_akun["Debit"] - df_akun["Kredit"]).cumsum()
                st.subheader(f"Akun: {akun}")
                st.dataframe(df_akun)

    with tabs[3]:
        pendapatan = jurnal_df[jurnal_df["Akun"].str.contains("Pendapatan")]["Kredit"].sum()
        beban = jurnal_df[
            ~jurnal_df["Akun"].isin(["Kas", "Bank", "Piutang Dagang", "Utang Dagang", "Pendapatan"])
        ]["Debit"].sum()
        st.metric("Pendapatan", f"Rp {pendapatan:,.0f}")
        st.metric("Beban", f"Rp {beban:,.0f}")
        st.metric("Laba/Rugi", f"Rp {pendapatan - beban:,.0f}")

    with tabs[4]:
        if jurnal_df.empty or "Akun" not in jurnal_df:
            st.warning("Data jurnal tidak tersedia.")
            return
        aset = jurnal_df[jurnal_df["Akun"].isin(["Kas", "Bank", "Piutang Dagang"])]["Debit"].sum() - \
               jurnal_df[jurnal_df["Akun"].isin(["Kas", "Bank", "Piutang Dagang"])]["Kredit"].sum()
        kewajiban = jurnal_df[jurnal_df["Akun"] == "Utang Dagang"]["Kredit"].sum() - \
                    jurnal_df[jurnal_df["Akun"] == "Utang Dagang"]["Debit"].sum()
        ekuitas = jurnal_df["Kredit"].sum() - jurnal_df["Debit"].sum()
        st.write(f"**Aset**: Rp {aset:,.0f}")
        st.write(f"**Kewajiban**: Rp {kewajiban:,.0f}")
        st.write(f"**Ekuitas**: Rp {ekuitas:,.0f}")

# ---------- Main ----------
def main():
    st.set_page_config(page_title="🌾 SiPadi", layout="centered")
    init_files()
    st.markdown("<h1 style='color:#BAC095;'>🌱 SiPadi</h1>", unsafe_allow_html=True)
    if login():
        menu = st.sidebar.radio("Menu Utama", ["Pemasukan", "Pengeluaran", "Laporan"])
        if menu == "Pemasukan":
            pemasukan()
        elif menu == "Pengeluaran":
            pengeluaran()
        elif menu == "Laporan":
            laporan()

if __name__ == "__main__":
    main()
