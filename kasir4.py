import streamlit as st
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

# ---------- Helper Functions ----------
def load_data(file):
    try:
        if os.path.exists(file):
            df = pd.read_csv(file)
            if "Tanggal" in df.columns:
                df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
            return df
        else:
            return pd.DataFrame()
    except pd.errors.ParserError:
        st.error(f"Gagal membaca file {file}. Format CSV tidak valid.")
        return pd.DataFrame()

def save_data(df, file):
    df.to_csv(file, index=False)

def append_data(data, file):
    df_new = pd.DataFrame([data])
    df = load_data(file)
    df = pd.concat([df, df_new], ignore_index=True)
    save_data(df, file)

def buat_jurnal(tanggal, akun_debit, akun_kredit, jumlah, keterangan):
    return [
        {"Tanggal": tanggal, "Akun": akun_debit, "Debit": jumlah, "Kredit": 0, "Keterangan": keterangan},
        {"Tanggal": tanggal, "Akun": akun_kredit, "Debit": 0, "Kredit": jumlah, "Keterangan": keterangan},
    ]

def init_files():
    files_and_headers = {
        "pemasukan.csv": ["Tanggal", "Sumber", "Jumlah", "Metode"],
        "pengeluaran.csv": ["Tanggal", "Kategori", "Sub Kategori", "Jumlah", "Keterangan"],
        "jurnal.csv": ["Tanggal", "Akun", "Debit", "Kredit", "Keterangan"],
        "piutang.csv": ["Tanggal", "Pelanggan", "Jumlah", "Keterangan"]
    }
    for file, headers in files_and_headers.items():
        if not os.path.exists(file):
            df = pd.DataFrame(columns=headers)
            df.to_csv(file, index=False)

def format_rp(value):
    return f"Rp {value:,.0f}".replace(",", ".")

# ---------- Login ----------
def login():
    st.image("C:/Users/user/Pictures/Saved Pictures/logo.jpg", width=120)
    st.markdown("<h2 style='color:#388e3c;'>🔐 Login Petani</h2>", unsafe_allow_html=True)
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if not st.session_state['logged_in']:
        username = st.text_input("👤 Nama Pengguna", placeholder="Masukkan username")
        password = st.text_input("🔒 Kata Sandi", type="password", placeholder="Masukkan password")
        if st.button("Masuk"):
            if username.lower() == "petani" and password == "sawah123":
                st.session_state['logged_in'] = True
                st.success("Login berhasil!")
            else:
                st.error("Username atau password salah.")
        return False
    return True

# ---------- Kategori Pengeluaran ----------
kategori_pengeluaran = {
    "Bibit": ["IR64", "Inpari", "Ciherang"],
    "Pupuk": ["Urea", "NPK", "Organik"],
    "Pestisida": ["Furadan", "BPMC", "Dursban"],
    "Alat Tani": ["Sabit", "Cangkul", "Karung"],
    "Tenaga Kerja": ["Upah Harian", "Borongan"],
    "Lainnya": ["Transportasi", "Listrik", "Air", "Sewa Traktor", "Penyusutan", "Perlengkapan"]
}

# ---------- Pemasukan ----------
def pemasukan():
    st.subheader("💰 Tambah Pemasukan")
    tanggal = st.date_input("Tanggal", datetime.now(), help="Pilih tanggal pemasukan")
    sumber = st.text_input("📝 Sumber Pemasukan (misal: Penjualan Padi)", placeholder="Contoh: Penjualan Padi")
    jumlah = st.number_input("💵 Jumlah (Rp)", min_value=0, step=1000, help="Masukkan jumlah pemasukan")
    metode = st.radio("💳 Metode Penerimaan", ["Tunai", "Transfer"], index=0)
    if st.button("✅ Simpan Pemasukan"):
        if not sumber.strip():
            st.error("Sumber pemasukan tidak boleh kosong.")
            return
        if jumlah <= 0:
            st.error("Jumlah pemasukan harus lebih dari 0.")
            return
        waktu = datetime.combine(tanggal, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
        data = {"Tanggal": waktu, "Sumber": sumber, "Jumlah": jumlah, "Metode": metode}
        append_data(data, "pemasukan.csv")
        akun_debit = "Kas" if metode == "Tunai" else "Bank"
        jurnal = buat_jurnal(waktu, akun_debit, "Pendapatan", jumlah, sumber)
        for j in jurnal:
            append_data(j, "jurnal.csv")
        st.success("✅ Pemasukan berhasil disimpan.")

# ---------- Pengeluaran ----------
def pengeluaran():
    st.subheader("💸 Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.now(), help="Pilih tanggal pengeluaran")
    kategori = st.selectbox("📦 Kategori Utama", list(kategori_pengeluaran.keys()))
    sub_kategori = st.selectbox("🔽 Sub Kategori", kategori_pengeluaran[kategori])
    jumlah = st.number_input("💵 Jumlah (Rp)", min_value=0, step=1000, help="Masukkan jumlah pengeluaran")
    deskripsi = st.text_area("📝 Keterangan (opsional)", placeholder="Deskripsikan pengeluaran")
    if st.button("✅ Simpan Pengeluaran"):
        if jumlah <= 0:
            st.error("Jumlah pengeluaran harus lebih dari 0.")
            return
        waktu = datetime.combine(tanggal, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
        data = {"Tanggal": waktu, "Kategori": kategori, "Sub Kategori": sub_kategori, "Jumlah": jumlah, "Keterangan": deskripsi}
        append_data(data, "pengeluaran.csv")

        # Penentuan akun debit
        if kategori == "Alat Tani":
            akun_debit = "Peralatan Tani"
        elif kategori == "Tenaga Kerja":
            akun_debit = "Beban Gaji"
        elif kategori == "Lainnya":
            if sub_kategori == "Penyusutan":
                akun_debit = "Beban Penyusutan"
            elif sub_kategori == "Perlengkapan":
                akun_debit = "Perlengkapan"
            elif sub_kategori == "Sewa Traktor":
                akun_debit = "Beban Sewa Traktor"
            else:
                akun_debit = f"Biaya - {sub_kategori}"
        else:
            akun_debit = f"Biaya - {sub_kategori}"

        akun_kredit = "Kas"
        jurnal = buat_jurnal(waktu, akun_debit, akun_kredit, jumlah, deskripsi or f"Pengeluaran {sub_kategori}")
        for j in jurnal:
            append_data(j, "jurnal.csv")
        st.success("✅ Pengeluaran berhasil disimpan.")

# ---------- Piutang ----------
def piutang():
    st.subheader("📄 Tambah Piutang")
    tanggal = st.date_input("Tanggal", datetime.now(), help="Pilih tanggal piutang")
    pelanggan = st.text_input("👥 Nama Pelanggan", placeholder="Nama pelanggan")
    jumlah = st.number_input("💵 Jumlah Piutang", min_value=0, step=1000, help="Masukkan jumlah piutang")
    keterangan = st.text_area("📝 Keterangan", placeholder="Deskripsi piutang (opsional)")
    if st.button("✅ Simpan Piutang"):
        if not pelanggan.strip():
            st.error("Nama pelanggan tidak boleh kosong.")
            return
        if jumlah <= 0:
            st.error("Jumlah piutang harus lebih dari 0.")
            return
        waktu = datetime.combine(tanggal, datetime.now().time()).strftime("%Y-%m-%d %H:%M:%S")
        data = {"Tanggal": waktu, "Pelanggan": pelanggan, "Jumlah": jumlah, "Keterangan": keterangan}
        append_data(data, "piutang.csv")

        jurnal = buat_jurnal(waktu, "Piutang Dagang", "Pendapatan", jumlah, keterangan or f"Piutang dari {pelanggan}")
        for j in jurnal:
            append_data(j, "jurnal.csv")
        st.success("✅ Piutang berhasil dicatat.")

# ---------- Laporan ----------
def laporan():
    st.subheader("📊 Laporan Keuangan")
    pemasukan_df = load_data("pemasukan.csv")
    pengeluaran_df = load_data("pengeluaran.csv")
    jurnal_df = load_data("jurnal.csv")
    piutang_df = load_data("piutang.csv")

    mulai = st.date_input("Mulai", datetime.now().replace(day=1), help="Tanggal awal laporan")
    akhir = st.date_input("Sampai", datetime.now(), help="Tanggal akhir laporan")
    if mulai > akhir:
        st.error("Tanggal mulai harus sebelum tanggal sampai.")
        return

    # Filter data berdasarkan tanggal
    pemasukan_df = pemasukan_df[(pemasukan_df['Tanggal'] >= pd.to_datetime(mulai)) & (pemasukan_df['Tanggal'] <= pd.to_datetime(akhir))]
    pengeluaran_df = pengeluaran_df[(pengeluaran_df['Tanggal'] >= pd.to_datetime(mulai)) & (pengeluaran_df['Tanggal'] <= pd.to_datetime(akhir))]
    jurnal_df = jurnal_df[(jurnal_df['Tanggal'] >= pd.to_datetime(mulai)) & (jurnal_df['Tanggal'] <= pd.to_datetime(akhir))]
    piutang_df = piutang_df[(piutang_df['Tanggal'] >= pd.to_datetime(mulai)) & (piutang_df['Tanggal'] <= pd.to_datetime(akhir))]

    tabs = st.tabs(["📈 Grafik Ringkasan", "📥 Pemasukan", "📤 Pengeluaran", "📄 Piutang", "📚 Jurnal", "📘 Buku Besar", "📑 Laporan Laba Rugi", "⬇️ Ekspor Data"])

    with tabs[0]:
        if not pemasukan_df.empty or not pengeluaran_df.empty:
            ringkasan_df = pd.DataFrame({
                "Kategori": ["Pemasukan", "Pengeluaran"],
                "Jumlah": [pemasukan_df['Jumlah'].sum(), pengeluaran_df['Jumlah'].sum()]
            })
            fig = px.pie(ringkasan_df, values='Jumlah', names='Kategori',
                         title="Perbandingan Pemasukan vs Pengeluaran",
                         color_discrete_sequence=px.colors.sequential.Viridis)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data untuk ditampilkan.")

        # Tambahkan saldo kas dan bank
        kas_debit = jurnal_df[(jurnal_df['Akun'] == "Kas")]['Debit'].sum()
        kas_kredit = jurnal_df[(jurnal_df['Akun'] == "Kas")]['Kredit'].sum()
        saldo_kas = kas_debit - kas_kredit

        bank_debit = jurnal_df[(jurnal_df['Akun'] == "Bank")]['Debit'].sum()
        bank_kredit = jurnal_df[(jurnal_df['Akun'] == "Bank")]['Kredit'].sum()
        saldo_bank = bank_debit - bank_kredit

        st.markdown(f"**Saldo Kas:** {format_rp(saldo_kas)}  |  **Saldo Bank:** {format_rp(saldo_bank)}")

    with tabs[1]:
        st.metric("Total Pemasukan", format_rp(pemasukan_df['Jumlah'].sum()))
        st.dataframe(pemasukan_df.style.format({"Jumlah": "{:,.0f}"}))

    with tabs[2]:
        st.metric("Total Pengeluaran", format_rp(pengeluaran_df['Jumlah'].sum()))
        st.dataframe(pengeluaran_df.style.format({"Jumlah": "{:,.0f}"}))

    with tabs[3]:
        st.metric("Total Piutang", format_rp(piutang_df['Jumlah'].sum()))
        st.dataframe(piutang_df.style.format({"Jumlah": "{:,.0f}"}))

    with tabs[4]:
        st.dataframe(jurnal_df.style.format({"Debit": "{:,.0f}", "Kredit": "{:,.0f}"}))

    with tabs[5]:
        if not jurnal_df.empty:
            akun_list = sorted(jurnal_df['Akun'].unique())
            for akun in akun_list:
                df_akun = jurnal_df[jurnal_df['Akun'] == akun].copy()
                df_akun = df_akun.sort_values("Tanggal")
                df_akun["Saldo"] = (df_akun["Debit"] - df_akun["Kredit"]).cumsum()
                st.subheader(f"📘 Buku Besar: {akun}")
                st.dataframe(df_akun.style.format({"Debit": "{:,.0f}", "Kredit": "{:,.0f}", "Saldo": "{:,.0f}"}))
        else:
            st.info("Belum ada data jurnal.")

    with tabs[6]:
        total_pendapatan = jurnal_df[jurnal_df['Akun'] == 'Pendapatan']['Kredit'].sum()
        total_beban = jurnal_df[jurnal_df['Akun'].str.contains('Beban')]['Debit'].sum()
        laba_bersih = total_pendapatan - total_beban
        st.subheader("📑 Laporan Laba Rugi")
        st.markdown(f"- **Pendapatan:** {format_rp(total_pendapatan)}")
        st.markdown(f"- **Total Beban:** {format_rp(total_beban)}")
        st.markdown(f"### Laba Bersih: {format_rp(laba_bersih)}")

    with tabs[7]:
        st.download_button("📤 Unduh Pemasukan (CSV)", data=pemasukan_df.to_csv(index=False).encode(), file_name="pemasukan.csv")
        st.download_button("📤 Unduh Pengeluaran (CSV)", data=pengeluaran_df.to_csv(index=False).encode(), file_name="pengeluaran.csv")
        st.download_button("📤 Unduh Piutang (CSV)", data=piutang_df.to_csv(index=False).encode(), file_name="piutang.csv")
        st.download_button("📤 Unduh Jurnal (CSV)", data=jurnal_df.to_csv(index=False).encode(), file_name="jurnal.csv")

# ---------- Main ----------
def main():
    st.set_page_config(page_title="🌾 Aplikasi Keuangan Petani", layout="centered")
    init_files()

    if login():
        st.markdown("""
            <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                <img src='C:/Users/user/Pictures/Saved Pictures/logo.jpg' width='60' style='border-radius: 12px; box-shadow: 0 0 8px #4caf50;'/>
                <h1 style='color:#2e7d32; margin-left: 15px;'>🌱 Aplikasi Keuangan Petani</h1>
            </div>
        """, unsafe_allow_html=True)

        menu = st.sidebar.radio("📋 Menu Utama", ["Pemasukan", "Pengeluaran", "Piutang", "Laporan"])

        if menu == "Pemasukan":
            pemasukan()
        elif menu == "Pengeluaran":
            pengeluaran()
        elif menu == "Piutang":
            piutang()
        elif menu == "Laporan":
            laporan()

if __name__ == '__main__':
    main()
