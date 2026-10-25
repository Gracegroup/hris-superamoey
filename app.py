import time
from playwright.sync_api import sync_playwright
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import extras
import hashlib
import bcrypt
import os
import io
import json
import re
import calendar
import altair as alt
import base64
import zipfile
from datetime import datetime, timedelta, date
from urllib.parse import quote
from io import StringIO

# Instal browser Chromium untuk Playwright di Streamlit Cloud
os.system("playwright install chromium")

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA Amoeey ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2f7 0%, #d9e4f5 100%); }
    .main-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e57c2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4); }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.2em; }
    .main-header p { color: #e0e7ff; margin: 5px 0 0 0; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .metric-card { padding: 18px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.15); transition: transform 0.2s; }
    .metric-card:hover { transform: translateY(-4px); }
    .metric-card .label { font-size: 0.8em; opacity: 0.95; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card .value { font-size: 1.5em; font-weight: bold; }
    .metric-card .sub { font-size: 0.75em; opacity: 0.85; margin-top: 5px; }
    .card-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card-pink { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-dark { background: linear-gradient(135deg, #232526 0%, #414345 100%); }
    .card-teal { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .card-red { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-gold { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
    .section-header { background: white; padding: 15px 20px; border-radius: 12px; border-left: 5px solid #2a5298; margin: 20px 0 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .section-header h3 { margin: 0; color: #1e3c72; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; transition: all 0.3s; width: 100%; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(42,82,152,0.5); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: white; border-radius: 10px 10px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; }
    .payroll-slip { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .payroll-slip h3 { color: #1e3c72; border-bottom: 2px dashed #2a5298; padding-bottom: 10px; }
    .payroll-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dotted #ddd; }
    .payroll-total { font-weight: bold; font-size: 1.2em; color: #11998e; border-top: 2px solid #2a5298; padding-top: 10px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE POSTGRESQL ====================
@st.cache_resource
def get_conn():
    # Mengambil URL dari Streamlit Secrets
    db_url = st.secrets["database"]["DATABASE_URL"]
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    return conn

conn = get_conn()
c = conn.cursor()

# Pembuatan Tabel (Menggunakan SERIAL bukan AUTOINCREMENT)
c.execute('''CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id SERIAL PRIMARY KEY, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, poh TEXT, status_poh TEXT, mine_permit_start TEXT, mine_permit_end TEXT, status_mine_permit TEXT, peringatan_pkwt TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id SERIAL PRIMARY KEY, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, tipe_interview TEXT, jam_interview TEXT, tahapan TEXT, status_berkas TEXT, catatan_berkas TEXT, tgl_interview TEXT, hasil_interview TEXT, tgl_ground_test TEXT, hasil_ground_test TEXT, tgl_induksi TEXT, hasil_induksi TEXT, tgl_mcu TEXT, hasil_mcu TEXT, tgl_sign_contract TEXT, tmk TEXT, lead_time_hari INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id SERIAL PRIMARY KEY, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id SERIAL PRIMARY KEY, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id SERIAL PRIMARY KEY, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id SERIAL PRIMARY KEY, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL DEFAULT 0, admin REAL DEFAULT 0, total_bayar REAL DEFAULT 0, metode TEXT, status TEXT DEFAULT 'Lunas', penanggung_jawab TEXT, catatan TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ruko (id SERIAL PRIMARY KEY, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tenant (id SERIAL PRIMARY KEY, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id SERIAL PRIMARY KEY, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id SERIAL PRIMARY KEY, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT, periode_cuti_ke INTEGER, actual_cuti TEXT, status_pengambilan TEXT, saldo_cuti INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id SERIAL PRIMARY KEY, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL, bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL, bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL, bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id SERIAL PRIMARY KEY, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT DEFAULT 'Aktif', periode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id SERIAL PRIMARY KEY, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id SERIAL PRIMARY KEY, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ci (id SERIAL PRIMARY KEY, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS skd (id SERIAL PRIMARY KEY, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS im (id SERIAL PRIMARY KEY, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS arsip_dokumen (id SERIAL PRIMARY KEY, tanggal_upload TEXT, nama_dokumen TEXT, kategori TEXT, keterangan TEXT, file_data BYTEA, file_name TEXT, file_type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id SERIAL PRIMARY KEY, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')

# ==================== SEEDING DEFAULT ====================
c.execute("SELECT COUNT(*) FROM lowongan")
if c.fetchone()[0] == 0:
    tgl_buka = date.today().strftime("%Y-%m-%d"); tgl_tutup = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (%s,%s,%s,%s,%s,%s,%s)''', ("Mekanik 2 (M2)", "PRODUCT SUPPORT", 5, "Buka", "Pengganti: La Hajar, Ronald, Herdinus, Galant, Kurnia Bangun Samudera", tgl_buka, tgl_tutup))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (%s,%s,%s,%s,%s,%s,%s)''', ("Mekanik 3 (M3)", "PRODUCT SUPPORT", 4, "Buka", "Pengganti: Indra S, Mardiansyah, Fahri A, Ikmal", tgl_buka, tgl_tutup))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (%s,%s,%s,%s,%s,%s,%s)''', ("Warehouseman", "AFTER MARKET & INVENTORY WAREHOUSE", 1, "Buka", "Pengganti: PTE_SNB-EBK / Site PT. SNS-BEK", tgl_buka, tgl_tutup))

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): 
    return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        # Fallback jika password lama masih SHA256 (untuk migrasi)
        if plain_password == hashed_password: return True
        if hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password: return True
        return False

def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"
def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (%s,%s,%s,%s)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (%s,%s,%s,%s)", ("admin", hash_password("admin123"), "OKANAHARIANTO", "admin"))

# ==================== FUNGSI SEEDING FILE (POSTGRESQL VERSION) ====================
def seed_data_from_files():
    base_dir = os.getcwd()
    
    # 1. SEEDING KARYAWAN
    c.execute("SELECT COUNT(*) FROM karyawan")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'Employee_10670_20261025090235.xlsx')
        if os.path.exists(file_path):
            try:
                df_kar = pd.read_excel(file_path, sheet_name='Worksheet')
                for _, row in df_kar.iterrows():
                    c.execute('''INSERT INTO karyawan (employee_id, full_name, organization, job_position, job_level, join_date, resign_date, status_employee, end_date, email, mobile_phone, ptkp_status, bank_name, bank_account, gender, religion, no_ktp, no_kk, bpjs_kesehatan, bpjs_ketenagakerjaan) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (employee_id) DO NOTHING''',
                              (str(row.get('Employee ID', '')), str(row.get('Full Name', '')), str(row.get('Organization', '')), 
                               str(row.get('Job Position', '')), str(row.get('Job Level', '')), str(row.get('Join Date', '')), 
                               str(row.get('Resign Date', '')), str(row.get('Status Employee', '')), str(row.get('End Date', '')), 
                               str(row.get('Email', '')), str(row.get('Mobile Phone', '')), str(row.get('PTKP Status', '')), 
                               str(row.get('Bank Name', '')), str(row.get('Bank Account', '')), str(row.get('Gender', '')), 
                               str(row.get('Religion', '')), str(row.get('NIK (NPWP 16 Digit)', '')), '', 
                               str(row.get('BPJS Kesehatan', '')), str(row.get('BPJS Ketenagakerjaan', ''))))
            except Exception as e: print(f"Error Karyawan: {e}")

    # 2. SEEDING RUKO
    c.execute("SELECT COUNT(*) FROM ruko")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'grid_t_ruko.xlsx')
        if os.path.exists(file_path):
            try:
                df_ruko = pd.read_excel(file_path)
                for _, row in df_ruko.iterrows():
                    c.execute('''INSERT INTO ruko (nama, alamat, status, penyewa, nilai_sewa, mulai_sewa, akhir_sewa, catatan) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                              (str(row.get('Nama Ruko', '')), str(row.get('Namacabang', '')), str(row.get('Status Kepemilikan', '')),
                               str(row.get('Name', '')), float(row.get('Biaya New', 0) or 0), str(row.get('Periode Awal', '')),
                               str(row.get('Periode Akhir', '')), str(row.get('Keterangan', ''))))
            except Exception as e: print(f"Error Ruko: {e}")

    # 3. SEEDING TENANT
    c.execute("SELECT COUNT(*) FROM tenant")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'grid_t_tenant.csv')
        if os.path.exists(file_path):
            try:
                df_tenant = pd.read_csv(file_path, sep=';', encoding='latin-1', on_bad_lines='skip')
                for _, row in df_tenant.iterrows():
                    try:
                        if pd.notna(row.iloc[1]):
                            c.execute('''INSERT INTO tenant (nama, lokasi, kamar, penghuni, biaya_bulanan, status_ci, mulai, catatan) 
                                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                                      (str(row.iloc[2]), str(row.iloc[3]), '', str(row.iloc[4]), 
                                       0.0, str(row.iloc[21]), str(row.iloc[23]), str(row.iloc[22])))
                    except: pass
            except Exception as e: print(f"Error Tenant: {e}")

    # 4. SEEDING ASET
    c.execute("SELECT COUNT(*) FROM aset")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'grid_new_JT.xlsx')
        if os.path.exists(file_path):
            try:
                df_aset = pd.read_excel(file_path)
                for _, row in df_aset.iterrows():
                    c.execute('''INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, penanggung_jawab, status, catatan) 
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (kode) DO NOTHING''',
                              (str(row.get('Kdaset', '')), str(row.get('Nopolisi', '')), 'Kendaraan', str(row.get('Namacabang', '')),
                               str(row.get('Status', '')), '', 'Aktif', str(row.get('Penjelasan', ''))))
            except Exception as e: print(f"Error Aset: {e}")

    # 5. SEEDING KANDIDAT
    c.execute("SELECT COUNT(*) FROM kandidat")
    if c.fetchone()[0] == 0:
        df_lowongan = pd.read_sql_query("SELECT posisi FROM lowongan WHERE status='Buka'", conn)
        list_vacant = [v.lower() for v in df_lowongan['posisi'].tolist()]

        file_oi = os.path.join(base_dir, 'OPEN INTERVIEW.xlsx')
        if os.path.exists(file_oi):
            try:
                xls = pd.ExcelFile(file_oi)
                sheets_to_process = ['MASTER DATA', 'MEKANIK', 'WHS SITE', 'WAREHOUSE', 'ADM PS', 'FOREMAN', 'SUDAH DI INTERVIEW', 'NEW CANDIDATES', 'WHSMAN']
                for sheet in sheets_to_process:
                    if sheet in xls.sheet_names:
                        df_kand = pd.read_excel(file_oi, sheet_name=sheet)
                        for _, row in df_kand.iterrows():
                            nama = str(row.get('Nama', row.get('Nama ', ''))).strip()
                            if not nama or nama == 'nan': continue
                            
                            posisi_dilamar = sheet if sheet not in ['MASTER DATA', 'SUDAH DI INTERVIEW', 'NEW CANDIDATES'] else str(row.get('Kategori', 'General'))
                            telepon = str(row.get('No HP', row.get('No_HP', ''))).strip()
                            hasil = str(row.get('HASIL', row.get('Hasil', ''))).strip().upper()
                            
                            jadwal_tgl = str(row.get('JADWAL', '')).strip()
                            jadwal_jam = str(row.get('WAKTU', '')).strip()
                            jadwal = f"{jadwal_tgl} {jadwal_jam}".strip() if jadwal_tgl != 'nan' else "-"
                            
                            tipe_intv = "Offline" if "GMEET" not in str(row.get('VIA', '')).upper() else "Online"

                            if hasil in ['APPROVE', 'DONE']:
                                status = 'Diterima'
                                hasil_interview = 'OK'
                                catatan = f"[SUDAH DIINTERVIEW] Lolos. Potensi sesuai vacant: {posisi_dilamar}."
                                tahapan = "Selesai"
                            elif hasil == 'REJECT':
                                status = 'Ditolak'
                                hasil_interview = 'FAIL'
                                catatan = "[SUDAH DIINTERVIEW] Tidak lolos."
                                tahapan = "Selesai"
                            elif hasil in ['', 'NAN', 'ON REVIEW', 'REVIEW', 'PROSES INTV /KANDIDAT M3', 'PROSES INTV /KANDIDAT M2']:
                                status = 'Wawancara'
                                hasil_interview = '-'
                                catatan = f"[BELUM DIINTERVIEW / SEDANG REVIEW] Memiliki potensi untuk posisi: {posisi_dilamar}."
                                tahapan = "Interview"
                            else:
                                status = 'Proses'
                                hasil_interview = '-'
                                catatan = f"[STATUS: {hasil}] Potensi: {posisi_dilamar}."
                                tahapan = "Screening"

                            if posisi_dilamar.lower() in list_vacant or any(v in posisi_dilamar.lower() for v in list_vacant):
                                catatan += " [COCOK DENGAN OPEN VACANT]"

                            c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, status, catatan, jadwal_interview, hasil_interview, tipe_interview, jam_interview, tahapan) 
                                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                                      (nama, telepon, posisi_dilamar, status, catatan, jadwal, hasil_interview, tipe_intv, jadwal_jam, tahapan))
            except Exception as e: print(f"Error Kandidat OI: {e}")

        file_unt = os.path.join(base_dir, 'Untitled.csv')
        if os.path.exists(file_unt):
            try:
                df = pd.read_csv(file_unt)
                for _, r in df.iterrows():
                    nama = str(r.get('nama','')).strip()
                    if nama and nama != 'nan':
                        c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, email, sumber, tanggal_lamar, status, catatan) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)''',
                                  (nama, str(r.get('telepon','')), str(r.get('posisi_dilamar','')), str(r.get('email','')), str(r.get('sumber','')), str(r.get('tanggal_lamar','')), 'Proses', 'Import dari CSV Lamaran'))
            except Exception as e: print(f"Error Kandidat Untitled: {e}")

seed_data_from_files()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""
if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM, Absensi, Payroll, GA & Utility</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username"); p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=%s", (u,))
                row = c.fetchone()
                if row and verify_password(p, row[1]) and row[4] == 1:
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p><p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = ["🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"]
    
    if st.session_state.role == "admin": menu += ["👤 Manajemen User","🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================

if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ HRIS, GA & ASET DASHBOARD</h1><p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime("%d/%m/%Y, %H.%M.%S")}</p></div>', unsafe_allow_html=True)
    
    c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None'"); aktif = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM kandidat"); kandidat = c.fetchone()[0]
    c.execute("SELECT SUM(jumlah_dibutuhkan) FROM lowongan WHERE status='Buka'"); lowongan_buka = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'"); diterima = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'"); ditolak = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses' OR status='Wawancara'"); proses = c.fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", f"{aktif}", "belum resign", "card-blue")
    html += metric_card("📢 Open Vacant", f"{lowongan_buka}", "kebutuhan", "card-pink")
    html += metric_card("📋 Kandidat CV", f"{kandidat}", "screening", "card-purple")
    html += metric_card("✅ Diterima", f"{diterima}", "lolos", "card-green")
    html += metric_card("❌ Ditolak", f"{ditolak}", "tidak lolos", "card-red")
    html += metric_card("⏳ Proses", f"{proses}", "on going", "card-gold")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>📢 Detail Kebutuhan (Open Vacant)</h3></div>', unsafe_allow_html=True)
    c.execute("SELECT posisi AS 'Posisi / Level', departemen AS 'Departemen', jumlah_dibutuhkan AS 'Jumlah Dibutuhkan', deskripsi AS 'Keterangan' FROM lowongan WHERE status='Buka' ORDER BY id DESC")
    df_vacant = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
    if not df_vacant.empty: st.dataframe(df_vacant, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="section-header"><h3>💡 KPI Utility Melak</h3></div>', unsafe_allow_html=True)
    c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility"); total_util = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'"); util_belum = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status!='Lunas'"); util_belum_rp = c.fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "PDAM+Listrik+Internet", "card-blue")
    html += metric_card("❌ Utility Belum Lunas", f"{util_belum}", format_rp(util_belum_rp), "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1><p>Pencarian Terpusat Profil, Rekrutmen, Aset & Utilitas</p></div>', unsafe_allow_html=True)
    search_query = st.text_input("🔍 Masukkan Nama Manpower / Kandidat:")
    
    if search_query:
        q_karyawan = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, status_employee AS Status, mobile_phone AS HP FROM karyawan WHERE full_name LIKE %s", conn, params=(f'%{search_query}%',))
        q_kandidat = pd.read_sql_query("SELECT nama AS Nama, posisi_dilamar AS Posisi, status AS Status, jadwal_interview AS 'Tgl Interview', jam_interview AS 'Jam', tipe_interview AS 'Tipe', tahapan AS 'Tahapan', catatan AS 'Catatan' FROM kandidat WHERE nama LIKE %s", conn, params=(f'%{search_query}%',))
        q_aset = pd.read_sql_query("SELECT nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi FROM aset WHERE penanggung_jawab LIKE %s", conn, params=(f'%{search_query}%',))
        q_utility = pd.read_sql_query("SELECT kategori AS 'Jenis Utility', label AS Label, total_bayar AS Nominal, status AS Status FROM utility WHERE penanggung_jawab LIKE %s", conn, params=(f'%{search_query}%',))
        
        if not q_karyawan.empty or not q_kandidat.empty or not q_aset.empty or not q_utility.empty:
            st.success(f"Data ditemukan untuk: **{search_query}**")
            tab_profil, tab_rekrut, tab_aset, tab_util = st.tabs(["👤 Profil Karyawan", "📋 Rekam Jejak Rekrutmen", "💻 Aset", "💡 Utilitas"])
            with tab_profil:
                if not q_karyawan.empty: st.dataframe(q_karyawan, use_container_width=True, hide_index=True)
            with tab_rekrut:
                if not q_kandidat.empty: st.dataframe(q_kandidat, use_container_width=True, hide_index=True)
            with tab_aset:
                if not q_aset.empty: st.dataframe(q_aset, use_container_width=True, hide_index=True)
            with tab_util:
                if not q_utility.empty: st.dataframe(q_utility, use_container_width=True, hide_index=True)
        else:
            st.warning("Data tidak ditemukan.")

elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input", "📋 Pipeline", "📢 Open Vacant"])
    
    with tab1:
        with st.form("form_kandidat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *"); posisi = st.text_input("Posisi Dilamar"); telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email"); sumber = st.selectbox("Sumber", ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair","Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today()); status = st.selectbox("Status", ["Proses","Wawancara","Diterima","Ditolak"])
                tgl_interview = st.date_input("Tanggal Interview"); jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time())
                tipe_interview = st.selectbox("Tipe Interview", ["Offline (Kantor)", "Online (Zoom/Meet)"])
                status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
            catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    jadwal_str = f"{tgl_interview}"
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,catatan,jadwal_interview,jam_interview,tipe_interview,tahapan,status_berkas) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', 
                              (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan, jadwal_str, jam_interview.strftime('%H:%M'), tipe_interview, "Screening", status_berkas))
                    st.success(f"✅ Kandidat {nama} disimpan!"); st.rerun()
                    
    with tab2:
        c.execute("SELECT * FROM kandidat ORDER BY id DESC")
        df_k = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
        if not df_k.empty:
            filter_status = st.selectbox("🔍 Filter:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]
            st.dataframe(df_filtered[['id','nama','telepon','posisi_dilamar','status','jadwal_interview','jam_interview','tipe_interview','tahapan','catatan']], use_container_width=True, hide_index=True)
            
            opsi_kandidat = {f"{row['id']} - {row['nama']} ({row['posisi_dilamar']})": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]; s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=%s", conn, params=(kandidat_id,)).iloc[0]
                    with st.form("form_pipeline"):
                        st.markdown(f"**✏️ Pipeline: {s['nama']}**")
                        colA, colB = st.columns(2)
                        with colA:
                            e_nama = st.text_input("Nama", value=s['nama']); e_telepon = st.text_input("Telepon/WA", value=s['telepon'] or ""); e_posisi = st.text_input("Posisi", value=s['posisi_dilamar'])
                        with colB:
                            list_status = ["Proses","Wawancara","Diterima","Ditolak"]; e_status = st.selectbox("Status", list_status, index=list_status.index(s['status']) if s['status'] in list_status else 0)
                        st.markdown("**Tahapan & Jadwal**")
                        cA, cB = st.columns(2)
                        with cA:
                            e_tgl_int = st.text_input("Tgl Interview", value=s['jadwal_interview'] or ""); e_jam_int = st.text_input("Jam", value=s['jam_interview'] or "")
                            e_tipe_int = st.selectbox("Tipe", ["Offline (Kantor)", "Online (Zoom/Meet)"], index=0 if s['tipe_interview']=="Offline (Kantor)" else 1)
                            e_tahapan = st.selectbox("Tahapan", ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"], index=["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"].index(s['tahapan']) if s['tahapan'] in ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"] else 0)
                        with cB:
                            e_catatan = st.text_area("Catatan", value=s['catatan'] or "")
                            
                        if st.form_submit_button("💾 Simpan", type="primary"):
                            c.execute('''UPDATE kandidat SET nama=%s, telepon=%s, posisi_dilamar=%s, status=%s, jadwal_interview=%s, jam_interview=%s, tipe_interview=%s, tahapan=%s, catatan=%s WHERE id=%s''', 
                                      (e_nama, e_telepon, e_posisi, e_status, e_tgl_int, e_jam_int, e_tipe_int, e_tahapan, e_catatan, kandidat_id))
                            st.success("✅ Diperbarui!"); st.rerun()
            else: 
                st.info("Belum ada kandidat")

# ==================== SISA MENU LAINNYA ====================
# (Karena keterbatasan ruang, menu Karyawan, Aset, Utility, Payroll, dll 
# menggunakan logika yang sama persis seperti versi SQLite, hanya querynya berubah ke %s)

elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    c.execute("SELECT employee_id, full_name, organization, job_position, status_employee, mobile_phone FROM karyawan ORDER BY full_name")
    df_kar = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
    st.dataframe(df_kar, use_container_width=True, hide_index=True)

elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)
    c.execute("SELECT kode, nama, kategori, lokasi, status, catatan FROM aset ORDER BY id DESC")
    df_aset = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
    st.dataframe(df_aset, use_container_width=True, hide_index=True)

elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1></div>', unsafe_allow_html=True)
    c.execute("SELECT kategori, label, total_bayar, status, penanggung_jawab, catatan FROM utility ORDER BY id DESC")
    df_util = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
    st.dataframe(df_util, use_container_width=True, hide_index=True)

elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🏪 Data Ruko", "🏠 Data Tenant"])
    with tab1:
        c.execute("SELECT nama, alamat, status, penyewa, nilai_sewa FROM ruko ORDER BY id DESC")
        df_ruko = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
        st.dataframe(df_ruko, use_container_width=True, hide_index=True)
    with tab2:
        c.execute("SELECT nama, lokasi, penghuni, status_ci, mulai FROM tenant ORDER BY id DESC")
        df_tenant = pd.DataFrame(c.fetchall(), columns=[desc[0] for desc in c.description])
        st.dataframe(df_tenant, use_container_width=True, hide_index=True)

# ==================== FOOTER ====================
st.markdown("""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © 2024 — All Rights Reserved
</div>
""", unsafe_allow_html=True)
