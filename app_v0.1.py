import time
from playwright.sync_api import sync_playwright
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
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

# ==================== FIX BUG #4: Playwright install ====================
if os.getenv("INSTALL_PLAYWRIGHT_ON_START", "0") == "1":
    try:
        os.system("playwright install chromium")
    except Exception as e:
        print(f"⚠️  Playwright install skip: {e}")

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
    .payroll-slip { background: white; padding: 20px; border-radius: 10px; border: 2px solid #2a5298; }
    .payroll-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #e0e0e0; }
    .payroll-total { font-weight: bold; border-top: 2px solid #2a5298; border-bottom: none; margin-top: 8px; padding-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

# ==================== FIX BUG #5: Helper anti-NaN ====================
def clean(val, default=""):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except (TypeError, ValueError): pass
    s = str(val).strip()
    if s.lower() in ("nan", "none", "null", "nat", ""): return default
    return s

def clean_date(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except (TypeError, ValueError): pass
    try: return pd.to_datetime(val, errors="coerce").strftime("%Y-%m-%d")
    except Exception: return None

# ==================== Pembuatan Tabel ====================
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, poh TEXT, status_poh TEXT, mine_permit_start TEXT, mine_permit_end TEXT, status_mine_permit TEXT, peringatan_pkwt TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, tipe_interview TEXT, jam_interview TEXT, tahapan TEXT, status_berkas TEXT, catatan_berkas TEXT, tgl_interview TEXT, hasil_interview TEXT, tgl_ground_test TEXT, hasil_ground_test TEXT, tgl_induksi TEXT, hasil_induksi TEXT, tgl_mcu TEXT, hasil_mcu TEXT, tgl_sign_contract TEXT, tmk TEXT, lead_time_hari INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL DEFAULT 0, admin REAL DEFAULT 0, total_bayar REAL DEFAULT 0, metode TEXT, status TEXT DEFAULT 'Lunas', penanggung_jawab TEXT, catatan TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ruko (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tenant (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT, catatan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT, periode_cuti_ke INTEGER, actual_cuti TEXT, status_pengambilan TEXT, saldo_cuti INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL, bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL, bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL, bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT DEFAULT 'Aktif', periode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS arsip_dokumen (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal_upload TEXT, nama_dokumen TEXT, kategori TEXT, keterangan TEXT, file_data BLOB, file_name TEXT, file_type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# ==================== SEEDING DEFAULT ====================
c.execute("SELECT COUNT(*) FROM lowongan")
if c.fetchone()[0] == 0:
    tgl_buka = date.today().strftime("%Y-%m-%d"); tgl_tutup = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''', ("Mekanik 2 (M2)", "PRODUCT SUPPORT", 5, "Buka", "Pengganti: La Hajar, Ronald, Herdinus, Galant, Kurnia Bangun Samudera", tgl_buka, tgl_tutup))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''', ("Mekanik 3 (M3)", "PRODUCT SUPPORT", 4, "Buka", "Pengganti: Indra S, Mardiansyah, Fahri A, Ikmal", tgl_buka, tgl_tutup))
    conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("hrd", hashlib.sha256("hrd123".encode()).hexdigest(), "HRD Staff", "hrd"))
    conn.commit()

# ==================== FUNGSI SEEDING DARI FILE ====================
def seed_data_from_files():
    base_dir = os.getcwd()
    c.execute("SELECT COUNT(*) FROM karyawan")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'Employee_10670_20261025090235.xlsx')
        if os.path.exists(file_path):
            try:
                df_kar = pd.read_excel(file_path, sheet_name='Worksheet')
                for _, row in df_kar.iterrows():
                    emp_id = clean(row.get('Employee ID'))
                    if not emp_id: continue
                    c.execute('''INSERT OR IGNORE INTO karyawan (employee_id, full_name, organization, job_position, job_level, join_date, resign_date, status_employee, end_date, email, mobile_phone, ptkp_status, bank_name, bank_account, gender, religion, no_ktp, no_kk, bpjs_kesehatan, bpjs_ketenagakerjaan) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (emp_id, clean(row.get('Full Name')), clean(row.get('Organization')), 
                               clean(row.get('Job Position')), clean(row.get('Job Level')), clean_date(row.get('Join Date')), 
                               clean_date(row.get('Resign Date')), clean(row.get('Status Employee')), clean_date(row.get('End Date')), 
                               clean(row.get('Email')), clean(row.get('Mobile Phone')), clean(row.get('PTKP Status')), 
                               clean(row.get('Bank Name')), clean(row.get('Bank Account')), clean(row.get('Gender')), 
                               clean(row.get('Religion')), clean(row.get('NIK (NPWP 16 Digit)')), '', 
                               clean(row.get('BPJS Kesehatan')), clean(row.get('BPJS Ketenagakerjaan'))))
                conn.commit()
                print("✅ Seeding Karyawan Berhasil")
            except Exception as e: print(f"❌ Error Karyawan: {e}")

    c.execute("SELECT COUNT(*) FROM ruko")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'grid_t_ruko.xlsx')
        if os.path.exists(file_path):
            try:
                df_ruko = pd.read_excel(file_path)
                for _, row in df_ruko.iterrows():
                    nama_ruko = clean(row.get('Nama Ruko'))
                    if not nama_ruko or nama_ruko.lower() == 'nama ruko': continue
                    try: nilai = float(row.get('Biaya New') or 0)
                    except (ValueError, TypeError): nilai = 0.0
                    c.execute('''INSERT INTO ruko (nama, alamat, status, penyewa, nilai_sewa, mulai_sewa, akhir_sewa, catatan) 
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (nama_ruko, clean(row.get('Namacabang')), clean(row.get('Status Kepemilikan')),
                               clean(row.get('Name')), nilai, clean_date(row.get('Periode Awal')),
                               clean_date(row.get('Periode Akhir')), clean(row.get('Keterangan'))))
                conn.commit()
                print("✅ Seeding Ruko Berhasil")
            except Exception as e: print(f"❌ Error Ruko: {e}")

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
                                         VALUES (?,?,?,?,?,?,?,?)''',
                                      (clean(row.iloc[2]), clean(row.iloc[3]), '', clean(row.iloc[4]), 
                                       0.0, clean(row.iloc[21]), clean(row.iloc[23]), clean(row.iloc[22])))
                    except: pass
                conn.commit()
                print("✅ Seeding Tenant Berhasil")
            except Exception as e: print(f"❌ Error Tenant: {e}")

    c.execute("SELECT COUNT(*) FROM aset")
    if c.fetchone()[0] == 0:
        file_path = os.path.join(base_dir, 'grid_new_JT.xlsx')
        if os.path.exists(file_path):
            try:
                df_aset = pd.read_excel(file_path)
                for _, row in df_aset.iterrows():
                    kode = clean(row.get('Kdaset'))
                    if not kode: continue
                    c.execute('''INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, penanggung_jawab, status, catatan) 
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (kode, clean(row.get('Nopolisi')), 'Kendaraan', clean(row.get('Namacabang')),
                               clean(row.get('Status')), '', 'Aktif', clean(row.get('Penjelasan'))))
                conn.commit()
                print("✅ Seeding Aset Berhasil")
            except Exception as e: print(f"❌ Error Aset: {e}")

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
                            nama = clean(row.get('Nama', row.get('Nama ', '')))
                            if not nama: continue
                            
                            posisi_dilamar = sheet if sheet not in ['MASTER DATA', 'SUDAH DI INTERVIEW', 'NEW CANDIDATES'] else clean(row.get('Kategori', 'General')) or 'General'
                            telepon = clean(row.get('No HP', row.get('No_HP', '')))
                            hasil = clean(row.get('HASIL', row.get('Hasil', ''))).upper()
                            
                            jadwal_tgl = clean_date(row.get('JADWAL'))
                            jadwal_jam = clean(row.get('WAKTU'))
                            jadwal = jadwal_tgl or '-'
                            
                            tipe_intv = "Offline" if "GMEET" not in clean(row.get('VIA', '')).upper() else "Online"

                            if hasil in ['APPROVE', 'DONE']:
                                status = 'Diterima'; hasil_interview = 'OK'; catatan = f"[SUDAH DIINTERVIEW] Lolos. Potensi sesuai vacant: {posisi_dilamar}."; tahapan = "Selesai"
                            elif hasil == 'REJECT':
                                status = 'Ditolak'; hasil_interview = 'FAIL'; catatan = "[SUDAH DIINTERVIEW] Tidak lolos."; tahapan = "Selesai"
                            elif hasil in ['', 'NAN', 'ON REVIEW', 'REVIEW', 'PROSES INTV /KANDIDAT M3', 'PROSES INTV /KANDIDAT M2']:
                                status = 'Wawancara'; hasil_interview = '-'; catatan = f"[BELUM DIINTERVIEW / SEDANG REVIEW] Memiliki potensi untuk posisi: {posisi_dilamar}."; tahapan = "Interview"
                            else:
                                status = 'Proses'; hasil_interview = '-'; catatan = f"[STATUS: {hasil}] Potensi: {posisi_dilamar}."; tahapan = "Screening"

                            if posisi_dilamar.lower() in list_vacant or any(v in posisi_dilamar.lower() for v in list_vacant):
                                catatan += " [COCOK DENGAN OPEN VACANT]"

                            c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, status, catatan, jadwal_interview, hasil_interview, tipe_interview, jam_interview, tahapan) 
                                         VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                      (nama, telepon, posisi_dilamar, status, catatan, jadwal, hasil_interview, tipe_intv, jadwal_jam, tahapan))
                conn.commit()
                print("✅ Seeding Kandidat (Open Interview) Berhasil")
            except Exception as e: print(f"❌ Error Kandidat OI: {e}")

        file_unt = os.path.join(base_dir, 'Untitled.csv')
        if os.path.exists(file_unt):
            try:
                df = pd.read_csv(file_unt)
                for _, r in df.iterrows():
                    nama = clean(r.get('nama', ''))
                    if nama:
                        c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, email, sumber, tanggal_lamar, status, catatan) VALUES (?,?,?,?,?,?,?,?)''',
                                  (nama, clean(r.get('telepon', '')), clean(r.get('posisi_dilamar', '')), clean(r.get('email', '')), clean(r.get('sumber', '')), clean_date(r.get('tanggal_lamar')), 'Proses', 'Import dari CSV Lamaran'))
                conn.commit()
                print("✅ Seeding Kandidat (Untitled) Berhasil")
            except Exception as e: print(f"❌ Error Kandidat Untitled: {e}")

seed_data_from_files()

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"
def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

def get_image_base64(filenames):
    if isinstance(filenames, str): filenames = [filenames]
    for fn in filenames:
        if os.path.exists(fn):
            try:
                with open(fn, "rb") as f: return base64.b64encode(f.read()).decode()
            except Exception: continue
    return ""

def tarik_data_uniquip(username, password):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://uniquip.co.id/asetuniquip/", timeout=30000)
            try:
                page.fill("input[name='username']", username)
                page.fill("input[name='password']", password)
                page.click("button[type='submit']")
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            rows = []
            try:
                table_rows = page.query_selector_all("table tbody tr")
                for tr in table_rows:
                    cols = [td.inner_text().strip() for td in tr.query_selector_all("td")]
                    if cols: rows.append(cols)
            except Exception: pass
            browser.close()
            if not rows: return "⚠️ Belum ada data / selector perlu disesuaikan."
            return pd.DataFrame(rows)
    except Exception as e: return f"❌ Scraping gagal: {e}"
        # === SAMBUNGAN CHUNK 1 ===

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM, Absensi, Payroll, GA & Utility</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.logged_in = True
                    st.session_state.username = row[0]
                    st.session_state.nama = row[2]
                    st.session_state.role = row[3]
                    log_aksi(u, "LOGIN")
                    st.rerun()
                else: 
                    st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p><p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # MENU LENGKAP (26 menu sesuai aslinya)
    menu = [
        "🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", 
        "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", 
        "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", 
        "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", 
        "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", 
        "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", 
        "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", 
        "📈 Manpower Report", "💾 Import, Export & Backup"
    ]
    
    if st.session_state.role == "admin": 
        menu += ["👤 Manajemen User", "🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]
        
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    tampilkan_flyer = st.checkbox("📢 Tampilkan Flyer Lowongan", value=True)
    st.markdown("---")
    
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: 
            st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================

# --- 1. DASHBOARD HRIS ---
if pilihan == "🏠 Dashboard HRIS":
    # Tampilkan Flyer jika dicentang
    if tampilkan_flyer:
        img_mekanik_b64 = get_image_base64(["flyer_mekanik.png", "flyer_mekanik.png.jpeg", "flyer_mekanik.jpeg", "flyer_mekanik.jpg"])
        img_warehouse_b64 = get_image_base64(["flyer_warehouse.png", "flyer_warehouse.png.jpeg", "flyer_warehouse.jpeg", "flyer_warehouse.jpg"])
        src_mekanik = f"data:image/png;base64,{img_mekanik_b64}" if img_mekanik_b64 else "https://placehold.co/400x600/FFD700/000000.png?text=Flyer+Mekanik"
        src_warehouse = f"data:image/png;base64,{img_warehouse_b64}" if img_warehouse_b64 else "https://placehold.co/400x600/1e3a8a/FFFFFF.png?text=Flyer+Warehouse"
        html_flyers = """
        <style>
            @keyframes floatBounce { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
            .flyer-container { position: fixed; right: 20px; z-index: 999; width: 260px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); animation: floatBounce 4s ease-in-out infinite; transition: transform 0.3s; background-color: #fff; padding: 6px; border: 2px solid #f59e0b; }
            .flyer-container:hover { animation-play-state: paused; transform: scale(1.05); z-index: 1000; }
            .flyer-top { top: 150px; animation-delay: 0s; }
            .flyer-bottom { top: 550px; animation-delay: 2s; }
            @media (max-width: 1024px) { .flyer-container { display: none; } }
        </style>
        """
        html_flyers += f'<div class="flyer-container flyer-top"><img src="{src_mekanik}" style="width:100%; border-radius:8px;"></div>'
        html_flyers += f'<div class="flyer-container flyer-bottom"><img src="{src_warehouse}" style="width:100%; border-radius:8px;"></div>'
        st.markdown(html_flyers, unsafe_allow_html=True)

    st.markdown(f'<div class="main-header"><h1>⚡ HRIS, GA & ASET DASHBOARD</h1><p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime("%d/%m/%Y, %H.%M.%S")}</p></div>', unsafe_allow_html=True)
    
    # KPI Cards
    st.markdown('<div class="section-header"><h3>👥 KPI HRIS & GENERAL AFFAIR</h3></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None'").fetchone()[0]
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    lowongan_buka = c.execute("SELECT SUM(jumlah_dibutuhkan) FROM lowongan WHERE status='Buka'").fetchone()[0] or 0
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses' OR status='Wawancara'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"); tgl_skrg = datetime.now().strftime("%Y-%m-%d")
    kontrak_habis = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date BETWEEN ? AND ?", (tgl_skrg, tgl_30)).fetchone()[0]
    sp_aktif = c.execute("SELECT COUNT(*) FROM disiplin WHERE status='Aktif'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", f"{aktif}", "belum resign", "card-blue")
    html += metric_card("📢 Open Vacant", f"{lowongan_buka}", "kebutuhan", "card-pink")
    html += metric_card("📋 Kandidat CV", f"{kandidat}", "screening", "card-purple")
    html += metric_card("📝 Kontrak Habis", f"{kontrak_habis}", "30 hari", "card-orange")
    html += metric_card("✅ Diterima", f"{diterima}", "lolos", "card-green")
    html += metric_card("❌ Ditolak", f"{ditolak}", "tidak lolos", "card-red")
    html += metric_card("⏳ Proses", f"{proses}", "on going", "card-gold")
    html += metric_card("⚠️ SP Aktif", f"{sp_aktif}", "disiplin", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Detail Vacant
    st.markdown('<div class="section-header"><h3>📢 Detail Kebutuhan (Open Vacant)</h3></div>', unsafe_allow_html=True)
    df_vacant = pd.read_sql_query("SELECT posisi AS 'Posisi / Level', departemen AS 'Departemen', jumlah_dibutuhkan AS 'Jumlah Dibutuhkan', deskripsi AS 'Keterangan' FROM lowongan WHERE status='Buka' ORDER BY id DESC", conn)
    if not df_vacant.empty: 
        st.dataframe(df_vacant, use_container_width=True, hide_index=True)
    else: 
        st.info("✅ Tidak ada posisi yang sedang open vacant saat ini.")
        
    # KPI Utility
    st.markdown('<div class="section-header"><h3>💡 KPI Utility Melak</h3></div>', unsafe_allow_html=True)
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    util_belum = c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'").fetchone()[0]
    util_belum_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status!='Lunas'").fetchone()[0]
    pdam_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='PDAM'").fetchone()[0]
    listrik_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='Listrik'").fetchone()[0]
    internet_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='Internet'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "PDAM+Listrik+Internet", "card-blue")
    html += metric_card("💧 PDAM", format_rp(pdam_rp), "", "card-teal")
    html += metric_card("⚡ Listrik", format_rp(listrik_rp), "", "card-gold")
    html += metric_card("🌐 Internet", format_rp(internet_rp), "", "card-purple")
    html += metric_card("❌ Utility Belum Lunas", f"{util_belum}", format_rp(util_belum_rp), "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Grafik Analitik
    st.markdown('<div class="section-header"><h3>📊 Analitik</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👔 Job Position (Aktif)**")
        df_jab = pd.read_sql_query("SELECT job_position as JABATAN, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND job_position IS NOT NULL GROUP BY job_position ORDER BY JML DESC LIMIT 15", conn)
        if not df_jab.empty:
            chart = alt.Chart(df_jab).mark_bar(cornerRadiusTopRight=10).encode(x=alt.X('JML:Q', title='Jumlah'), y=alt.Y('JABATAN:N', sort='-x', title=''), color=alt.Color('JML:Q', scale=alt.Scale(scheme='blues'), legend=None)).properties(height=max(300, len(df_jab)*35))
            st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("**🏢 Organization (Aktif)**")
        df_div = pd.read_sql_query("SELECT organization as DIVISI, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND organization IS NOT NULL GROUP BY organization ORDER BY JML DESC", conn)
        if not df_div.empty:
            chart = alt.Chart(df_div).mark_arc(innerRadius=60).encode(theta=alt.Theta('JML:Q'), color=alt.Color('DIVISI:N', scale=alt.Scale(scheme='purples')), tooltip=['DIVISI', 'JML']).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

# --- 2. FILING DATA MANPOWER ---
elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1><p>Pencarian Terpusat Data Profil, Interview, Aset & Utilitas</p></div>', unsafe_allow_html=True)
    
    st.info("Ketik nama karyawan atau kandidat untuk melihat seluruh rekam jejak dalam satu layar.")
    search_query = st.text_input("🔍 Masukkan Nama Manpower / Kandidat:")
    
    if search_query:
        q_karyawan = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, status_employee AS Status, mobile_phone AS HP FROM karyawan WHERE full_name LIKE ?", conn, params=(f'%{search_query}%',))
        q_kandidat = pd.read_sql_query("SELECT nama AS Nama, posisi_dilamar AS Posisi, status AS Status, jadwal_interview AS 'Tgl Interview', jam_interview AS 'Jam', tipe_interview AS 'Tipe', tahapan AS 'Tahapan', catatan AS 'Catatan' FROM kandidat WHERE nama LIKE ?", conn, params=(f'%{search_query}%',))
        q_aset = pd.read_sql_query("SELECT nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi, kondisi AS Kondisi FROM aset WHERE penanggung_jawab LIKE ?", conn, params=(f'%{search_query}%',))
        q_utility = pd.read_sql_query("SELECT kategori AS 'Jenis Utility', label AS Label, periode AS Periode, total_bayar AS Nominal, status AS Status FROM utility WHERE penanggung_jawab LIKE ?", conn, params=(f'%{search_query}%',))
        
        if not q_karyawan.empty or not q_kandidat.empty or not q_aset.empty or not q_utility.empty:
            st.success(f"Data ditemukan untuk: **{search_query}**")
            
            tab_profil, tab_rekrut, tab_aset, tab_util = st.tabs(["👤 Profil Karyawan", "📋 Rekam Jejak Rekrutmen", "💻 Aset yang Dipegang", "💡 Riwayat Utilitas"])
            
            with tab_profil:
                if not q_karyawan.empty: 
                    st.dataframe(q_karyawan, use_container_width=True, hide_index=True)
                else: 
                    st.info("Tidak ada data profil karyawan aktif di database.")
                    
            with tab_rekrut:
                if not q_kandidat.empty: 
                    st.dataframe(q_kandidat, use_container_width=True, hide_index=True)
                else: 
                    st.info("Tidak ada data riwayat rekrutmen/interview.")
                    
            with tab_aset:
                if not q_aset.empty: 
                    st.dataframe(q_aset, use_container_width=True, hide_index=True)
                else: 
                    st.info("Manpower ini tidak memegang aset perusahaan.")
            
            with tab_util:
                if not q_utility.empty: 
                    st.dataframe(q_utility, use_container_width=True, hide_index=True)
                else: 
                    st.info("Tidak ada data utilitas terkait manpower ini.")
        else:
            st.warning("Data tidak ditemukan di database Karyawan, Kandidat, Aset, maupun Utilitas. Pastikan ejaan nama sudah benar.")
            # --- 3. REKRUTMEN & CV (DENGAN JADWAL LENGKAP) ---
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Kandidat", "📋 Pipeline & Jadwal", "📢 Open Vacant"])
    
    # TAB 1: INPUT KANDIDAT BARU
    with tab1:
        with st.form("form_kandidat_baru", clear_on_submit=True):
            st.subheader("Formulir Kandidat Baru")
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *")
                posisi = st.text_input("Posisi Dilamar")
                telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email")
                sumber = st.selectbox("Sumber", ["Job Portal", "Referral", "Walk-in", "LinkedIn", "Job Fair", "Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today())
                status = st.selectbox("Status Awal", ["Proses", "Wawancara", "Diterima", "Ditolak"])
                tgl_interview = st.date_input("Tanggal Interview")
                jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time())
                tipe_interview = st.selectbox("Tipe Interview", ["Offline (Kantor)", "Online (Zoom/Meet)"])
                tahapan = st.selectbox("Tahapan", ["Screening", "Interview HR", "Interview User", "MCU", "Offering"])
                status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
            
            catatan = st.text_area("Catatan / Keterangan Tambahan")
            
            if st.form_submit_button("💾 Simpan Kandidat", type="primary"):
                if nama:
                    # === FITUR ALERT DUPLIKAT ===
                    cek_duplikat = c.execute("SELECT id FROM kandidat WHERE LOWER(nama)=LOWER(?) AND LOWER(posisi_dilamar)=LOWER(?)", (nama.strip(), posisi.strip())).fetchone()
                    if cek_duplikat:
                        st.error(f"⚠️ Data Kandidat **{nama}** untuk posisi **{posisi}** sudah ada (ID: {cek_duplikat[0]}). Silakan edit di tab Pipeline & Jadwal.")
                    else:
                        jadwal_str = str(tgl_interview)
                        c.execute('''INSERT INTO kandidat (nama, posisi_dilamar, telepon, email, sumber, tanggal_lamar, status, catatan, jadwal_interview, jam_interview, tipe_interview, tahapan, status_berkas) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                  (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan, jadwal_str, jam_interview.strftime('%H:%M'), tipe_interview, tahapan, status_berkas))
                        conn.commit()
                        st.success(f"✅ Kandidat {nama} berhasil disimpan!")
                        st.rerun()
                else:
                    st.error("⚠️ Nama Kandidat wajib diisi!")

    # TAB 2: PIPELINE & JADWAL (FITUR EDIT & DELETE)
    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        if not df_k.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total Kandidat", str(len(df_k)), "", "card-blue")
            html += metric_card("Diterima", str(len(df_k[df_k['status']=='Diterima'])), "", "card-green")
            html += metric_card("Ditolak", str(len(df_k[df_k['status']=='Ditolak'])), "", "card-red")
            html += metric_card("Proses", str(len(df_k[df_k['status']=='Proses'])), "", "card-gold")
            html += metric_card("Wawancara", str(len(df_k[df_k['status']=='Wawancara'])), "", "card-purple")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            
            filter_status = st.selectbox("🔍 Filter Status:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]
            
            st.markdown("### 📋 Daftar Kandidat & Jadwal")
            st.dataframe(df_filtered[['id','nama','posisi_dilamar','status','jadwal_interview','jam_interview','tipe_interview','tahapan','catatan']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            opsi_kandidat = {f"{row['id']} - {row['nama']} ({row['posisi_dilamar']})": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat untuk Edit/Hapus Pipeline:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]
                    s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(kandidat_id,)).iloc[0]
                    
                    with st.form("form_update_pipeline"):
                        st.markdown(f"**✏️ Edit Data: {s['nama']}**")
                        colA, colB = st.columns(2)
                        with colA:
                            e_nama = st.text_input("Nama Kandidat", value=s['nama'])
                            e_posisi = st.text_input("Posisi", value=s['posisi_dilamar'])
                            e_telepon = st.text_input("Telepon/WA", value=s['telepon'] or "")
                            e_status = st.selectbox("Status Akhir", ["Proses", "Wawancara", "Diterima", "Ditolak"], 
                                                    index=["Proses", "Wawancara", "Diterima", "Ditolak"].index(s['status']) if s['status'] in ["Proses", "Wawancara", "Diterima", "Ditolak"] else 0)
                        with colB:
                            e_tgl_int = st.text_input("Tgl Interview (YYYY-MM-DD)", value=s['jadwal_interview'] or "")
                            e_jam_int = st.text_input("Jam Interview (HH:MM)", value=s['jam_interview'] or "")
                            e_tipe_int = st.selectbox("Tipe Interview", ["Offline (Kantor)", "Online (Zoom/Meet)"], 
                                                      index=0 if s['tipe_interview']=="Offline (Kantor)" else 1)
                            e_tahapan = st.selectbox("Tahapan", ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"], 
                                                     index=["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"].index(s['tahapan']) if s['tahapan'] in ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"] else 0)
                        
                        e_catatan = st.text_area("Catatan / Keterangan", value=s['catatan'] or "")
                        
                        if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                            c.execute('''UPDATE kandidat SET nama=?, posisi_dilamar=?, telepon=?, status=?, jadwal_interview=?, jam_interview=?, tipe_interview=?, tahapan=?, catatan=? WHERE id=?''', 
                                      (e_nama, e_posisi, e_telepon, e_status, e_tgl_int, e_jam_int, e_tipe_int, e_tahapan, e_catatan, kandidat_id))
                            conn.commit()
                            st.success("✅ Data Pipeline berhasil diperbarui!")
                            st.rerun()
                            
                    if st.button(f"🗑️ Hapus Kandidat {s['nama']}", type="primary"):
                        c.execute("DELETE FROM kandidat WHERE id=?", (kandidat_id,))
                        conn.commit()
                        st.success("Kandidat berhasil dihapus!")
                        st.rerun()
        else: 
            st.info("Belum ada data kandidat. Silakan input melalui Tab 'Input Kandidat'.")
            
    # TAB 3: OPEN VACANT
    with tab3:
        st.markdown("### 📢 Daftar Open Vacant (Lowongan)")
        
        with st.expander("➕ Tambah Lowongan Baru"):
            with st.form("form_lowongan_baru", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    vac_posisi = st.text_input("Posisi *")
                    vac_dept = st.selectbox("Departemen", ["PRODUCT SUPPORT", "AFTER MARKET & INVENTORY WAREHOUSE", "PRODUKSI", "PLANT", "ENGINEERING", "LOGISTIC", "HRGA", "FINANCE", "GA", "PARTS", "Adm.PS", "Lainnya"])
                with col2:
                    vac_jumlah = st.number_input("Jumlah Dibutuhkan *", min_value=1, step=1, value=1)
                    vac_status = st.selectbox("Status", ["Buka", "Tutup"])
                with col3:
                    vac_tgl_buka = st.date_input("Tgl Dibuka", date.today())
                    vac_tgl_tutup = st.date_input("Batas Akhir", date.today() + timedelta(days=30))
                vac_deskripsi = st.text_area("Kualifikasi / Deskripsi")
                if st.form_submit_button("💾 Tambah Lowongan", type="primary"):
                    if vac_posisi:
                        c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''', 
                                  (vac_posisi, vac_dept, vac_jumlah, vac_status, vac_deskripsi, str(vac_tgl_buka), str(vac_tgl_tutup)))
                        conn.commit()
                        st.success("✅ Lowongan berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("Posisi wajib diisi!")

        st.markdown("---")
        df_vac = pd.read_sql_query("SELECT * FROM lowongan ORDER BY id DESC", conn)
        if not df_vac.empty:
            for _, r in df_vac.iterrows():
                pelamar = c.execute("SELECT COUNT(*) FROM kandidat WHERE posisi_dilamar LIKE ?", (f"%{r['posisi']}%",)).fetchone()[0]
                
                st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {'#2a5298' if r['status']=='Buka' else '#eb3349'};">
                    <h4 style="margin:0; color:#1e3c72;">{r['posisi']} <span style="font-size:0.6em; background:#e0e7ff; padding:2px 8px; border-radius:10px;">{r['departemen']}</span></h4>
                    <p style="margin:5px 0; font-size:0.9em;">Status: <b>{r['status']}</b> | Batas: {r['tanggal_ditutup']}</p>
                    <div style="display:flex; gap:20px; margin-top:10px;">
                        <div><b>Butuh:</b> {r['jumlah_dibutuhkan']}</div>
                        <div><b>Pelamar:</b> {pelamar}</div>
                        <div style="color:{'#11998e' if pelamar >= r['jumlah_dibutuhkan'] else '#eb3349'};"><b>Sisa:</b> {max(0, r['jumlah_dibutuhkan'] - pelamar)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                colA, colB, colC, _ = st.columns([1, 1, 1, 3])
                with colA:
                    if r['status'] == 'Buka':
                        if st.button(f"🔒 Tutup", key=f"tutup_{r['id']}", use_container_width=True): 
                            c.execute("UPDATE lowongan SET status='Tutup' WHERE id=?", (r['id'],))
                            conn.commit()
                            st.rerun()
                    else:
                        if st.button(f"🔓 Buka", key=f"buka_{r['id']}", use_container_width=True): 
                            c.execute("UPDATE lowongan SET status='Buka' WHERE id=?", (r['id'],))
                            conn.commit()
                            st.rerun()
                with colC:
                    if st.button(f"🗑️ Hapus", key=f"hapus_{r['id']}", use_container_width=True): 
                        c.execute("DELETE FROM lowongan WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()

# --- 4. DATA KARYAWAN ---
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1><p>Master Data Seluruh Karyawan</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Daftar Karyawan", "✏️ Tambah / Edit"])
    
    # TAB 1: DAFTAR KARYAWAN
    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            q_kar = st.text_input("🔍 Cari Nama / NRP / NIK", "")
        with c2:
            df_org_opts = pd.read_sql_query("SELECT DISTINCT organization FROM karyawan WHERE organization IS NOT NULL AND organization != '' ORDER BY organization", conn)
            list_org = ["Semua"] + df_org_opts['organization'].tolist()
            f_org_kar = st.selectbox("🏢 Organisasi", list_org)
        with c3:
            f_status_kar = st.selectbox("📌 Status", ["Aktif", "Resign", "Semua"])
            
        q_kar_sql = "SELECT id, employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, job_level AS Level, gender AS Gender, join_date AS 'Tgl Masuk', status_employee AS Status, end_date AS 'Akhir Kontrak', mobile_phone AS HP, email AS Email, gaji AS 'Gaji Pokok' FROM karyawan WHERE 1=1"
        p_kar = []
        
        if q_kar:
            q_kar_sql += " AND (full_name LIKE ? OR employee_id LIKE ? OR no_ktp LIKE ?)"
            p_kar.extend([f"%{q_kar}%"] * 3)
        if f_org_kar != "Semua":
            q_kar_sql += " AND organization = ?"
            p_kar.append(f_org_kar)
        if f_status_kar == "Aktif":
            q_kar_sql += " AND (resign_date IS NULL OR resign_date='' OR resign_date='None')"
        elif f_status_kar == "Resign":
            q_kar_sql += " AND resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'"
            
        q_kar_sql += " ORDER BY full_name"
        df_kar = pd.read_sql_query(q_kar_sql, conn, params=p_kar)
        
        st.markdown(f"**Total: {len(df_kar)} karyawan ditemukan**")
        st.dataframe(df_kar.drop(columns=['id']), use_container_width=True, hide_index=True)
        
        csv_kar = df_kar.drop(columns=['id']).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Data Karyawan (CSV)", csv_kar, f"data_karyawan_{date.today()}.csv", "text/csv")

    # TAB 2: TAMBAH / EDIT KARYAWAN
    with tab2:
        st.subheader("Formulir Tambah / Edit Karyawan")
        
        list_kar_all = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan ORDER BY full_name", conn)
        opt_kar_all = {"-- Karyawan Baru --": 0}
        for _, r in list_kar_all.iterrows():
            opt_kar_all[f"{r['employee_id']} - {r['full_name']}"] = r['id']
            
        pilih_kar_all = st.selectbox("Pilih Karyawan (Kosongkan jika ingin tambah baru)", list(opt_kar_all.keys()), key="pilih_kar_all")
        edit_kar_id = opt_kar_all[pilih_kar_all]
        
        s_kar = {}
        if edit_kar_id > 0:
            s_kar = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(edit_kar_id,)).iloc[0]
            
        with st.form("form_karyawan"):
            c1, c2, c3 = st.columns(3)
            with c1:
                e_nrp = st.text_input("NRP / Employee ID *", value=str(s_kar.get('employee_id', '')) if edit_kar_id else "")
                e_nama = st.text_input("Nama Lengkap *", value=str(s_kar.get('full_name', '')) if edit_kar_id else "")
                e_org = st.text_input("Organisasi/Dept", value=str(s_kar.get('organization', '') or '') if edit_kar_id else "")
                e_pos = st.text_input("Jabatan", value=str(s_kar.get('job_position', '') or '') if edit_kar_id else "")
                e_lvl = st.text_input("Level", value=str(s_kar.get('job_level', '') or '') if edit_kar_id else "")
            with c2:
                list_gender = ["L", "P"]
                e_gender = st.selectbox("Gender", list_gender, index=list_gender.index(s_kar.get('gender')) if edit_kar_id and s_kar.get('gender') in list_gender else 0)
                e_tgl_masuk = st.text_input("Tanggal Masuk (YYYY-MM-DD)", value=str(s_kar.get('join_date', '') or '') if edit_kar_id else "")
                e_status_kar = st.text_input("Status Karyawan (Kontrak/Tetap)", value=str(s_kar.get('status_employee', '') or '') if edit_kar_id else "")
                e_tgl_akhir = st.text_input("Tanggal Akhir Kontrak (YYYY-MM-DD)", value=str(s_kar.get('end_date', '') or '') if edit_kar_id else "")
                e_tgl_resign = st.text_input("Tanggal Resign (YYYY-MM-DD)", value=str(s_kar.get('resign_date', '') or '') if edit_kar_id else "")
            with c3:
                e_hp = st.text_input("HP / WA", value=str(s_kar.get('mobile_phone', '') or '') if edit_kar_id else "")
                e_email = st.text_input("Email", value=str(s_kar.get('email', '') or '') if edit_kar_id else "")
                e_ktp = st.text_input("No KTP", value=str(s_kar.get('no_ktp', '') or '') if edit_kar_id else "")
                e_ptkp = st.text_input("PTKP Status", value=str(s_kar.get('ptkp_status', '') or 'TK/0') if edit_kar_id else "TK/0")
                e_gaji = st.number_input("Gaji Pokok", min_value=0.0, value=float(s_kar.get('gaji', 0) or 0) if edit_kar_id else 0.0, step=100000.0)
            
            e_aktif = st.checkbox("Status Aktif", value=bool(s_kar.get('aktif', 1)) if edit_kar_id else True)
            
            if st.form_submit_button("💾 Simpan Data Karyawan", type="primary", use_container_width=True):
                if e_nrp and e_nama:
                    if edit_kar_id > 0:
                        c.execute('''UPDATE karyawan SET employee_id=?, full_name=?, organization=?, job_position=?, job_level=?, gender=?, join_date=?, status_employee=?, end_date=?, resign_date=?, mobile_phone=?, email=?, no_ktp=?, ptkp_status=?, gaji=?, aktif=? WHERE id=?''', 
                                  (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ktp, e_ptkp, e_gaji, 1 if e_aktif else 0, edit_kar_id))
                        st.success("✅ Data Karyawan berhasil diperbarui!")
                    else:
                        c.execute('''INSERT INTO karyawan (employee_id, full_name, organization, job_position, job_level, gender, join_date, status_employee, end_date, resign_date, mobile_phone, email, no_ktp, ptkp_status, gaji, aktif) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                  (e_nrp, e_nama, e_org, e_pos, e_lvl, e_gender, e_tgl_masuk, e_status_kar, e_tgl_akhir, e_tgl_resign, e_hp, e_email, e_ktp, e_ptkp, e_gaji, 1 if e_aktif else 0))
                        st.success("✅ Karyawan baru berhasil ditambahkan!")
                    conn.commit()
                    st.rerun()
                else:
                    st.error("⚠️ NRP dan Nama Lengkap wajib diisi!")
                    
        if edit_kar_id > 0:
            st.markdown("---")
            if st.button("🗑️ Hapus Karyawan Ini", type="primary"):
                c.execute("DELETE FROM karyawan WHERE id=?", (edit_kar_id,))
                conn.commit()
                st.success("Karyawan dihapus!")
                st.rerun()

# --- 5. ASET & PROPERTI ---
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1><p>Manajemen Inventaris Perusahaan</p></div>', unsafe_allow_html=True)
    
    # KPI Aset
    total_aset = c.execute("SELECT COUNT(*) FROM aset").fetchone()[0]
    total_nilai = c.execute("SELECT COALESCE(SUM(nilai),0) FROM aset").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("📦 Total Aset", str(total_aset), "unit", "card-blue")
    html += metric_card("💰 Total Nilai", format_rp(total_nilai), "", "card-green")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Daftar Aset", "➕ Tambah Aset"])
    
    with tab1:
        df_aset = pd.read_sql_query("SELECT kode AS Kode, nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi, kondisi AS Kondisi, penanggung_jawab AS 'Penanggung Jawab', status AS Status, catatan AS Catatan FROM aset ORDER BY id DESC", conn)
        if not df_aset.empty:
            st.dataframe(df_aset, use_container_width=True, hide_index=True)
            csv_aset = df_aset.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV Aset", csv_aset, f"data_aset_{date.today()}.csv", "text/csv")
        else:
            st.info("Belum ada data aset.")
            
    with tab2:
        with st.form("form_tambah_aset"):
            col1, col2 = st.columns(2)
            with col1:
                a_kode = st.text_input("Kode Aset *")
                a_nama = st.text_input("Nama Aset *")
                a_kategori = st.selectbox("Kategori", ["Kendaraan", "Elektronik", "Furniture", "Peralatan Kerja", "Bangunan", "Lainnya"])
            with col2:
                a_lokasi = st.text_input("Lokasi")
                a_pj = st.text_input("Penanggung Jawab (Nama Manpower)")
                a_kondisi = st.selectbox("Kondisi", ["Baik", "Rusak Ringan", "Rusak Berat"])
            a_catatan = st.text_area("Catatan Tambahan")
            
            if st.form_submit_button("💾 Simpan Aset", type="primary"):
                if a_kode and a_nama:
                    try:
                        c.execute('''INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, penanggung_jawab, status, catatan) VALUES (?,?,?,?,?,?,?,?)''', 
                                  (a_kode, a_nama, a_kategori, a_lokasi, a_kondisi, a_pj, "Aktif", a_catatan))
                        conn.commit()
                        st.success("✅ Aset berhasil ditambahkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Kode Aset sudah digunakan!")
                else:
                    st.error("⚠️ Kode dan Nama Aset wajib diisi!")
                    # --- 6. UTILITY MELAK ---
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet • Telepon</p></div>', unsafe_allow_html=True)
    
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    util_lunas = c.execute("SELECT COUNT(*) FROM utility WHERE status='Lunas'").fetchone()[0]
    util_belum = c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "semua kategori", "card-blue")
    html += metric_card("✅ Lunas", str(util_lunas), "transaksi", "card-green")
    html += metric_card("❌ Belum Lunas", str(util_belum), "transaksi", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Daftar Utility", "➕ Input Utility"])
    
    with tab1:
        # PERBAIKAN: Menambahkan 'id_pelanggan' ke dalam query SELECT
        df_util = pd.read_sql_query("SELECT kategori AS Kategori, periode AS Periode, id_pelanggan AS 'ID Pelanggan', label AS 'Nama / Lokasi', penanggung_jawab AS 'Penanggung Jawab', total_bayar AS Nominal, status AS Status, tanggal_bayar AS 'Tgl Bayar' FROM utility ORDER BY id DESC", conn)
        if not df_util.empty:
            st.dataframe(df_util, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data utility.")
            
    with tab2:
        with st.form("form_tambah_utility"):
            col1, col2 = st.columns(2)
            with col1:
                u_kategori = st.selectbox("Kategori", ["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"])
                u_id_pel = st.text_input("ID Pelanggan / No. Meter")
                u_label = st.text_input("Nama / Lokasi (Contoh: MELAK - MESS)")
                u_pj = st.text_input("Penanggung Jawab (Nama Manpower)")
                u_periode = st.text_input("Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
            with col2:
                u_tgl = st.date_input("Tanggal Bayar", date.today())
                u_nominal = st.number_input("Nominal Tagihan (Rp)", min_value=0.0, step=10000.0)
                u_admin = st.number_input("Biaya Admin (Rp)", min_value=0.0, step=1000.0)
                u_status = st.selectbox("Status", ["Lunas", "Belum Lunas"])
            
            if st.form_submit_button("💾 Simpan Utility", type="primary"):
                total_bayar = u_nominal + u_admin
                # PERBAIKAN: Memasukkan id_pelanggan ke dalam query INSERT
                c.execute('''INSERT INTO utility (kategori, id_pelanggan, tanggal_bayar, periode, label, nominal, admin, total_bayar, status, penanggung_jawab, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                          (u_kategori, u_id_pel, str(u_tgl), u_periode, u_label, u_nominal, u_admin, total_bayar, u_status, u_pj, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("✅ Data Utility berhasil disimpan!")
                st.rerun()

# --- 7. RUKO & TENANT ---
elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1><p>Manajemen Properti & Penyewa</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🏪 Data Ruko", "🏠 Data Tenant"])
    
    with tab1:
        df_ruko = pd.read_sql_query("SELECT nama AS 'Nama Ruko', alamat AS Cabang, status AS 'Status Kepemilikan', penyewa AS 'Nama Penyewa', nilai_sewa AS 'Nilai Sewa', mulai_sewa AS 'Mulai', akhir_sewa AS 'Akhir' FROM ruko ORDER BY id DESC", conn)
        if not df_ruko.empty:
            st.dataframe(df_ruko, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data Ruko.")
            
    with tab2:
        df_tenant = pd.read_sql_query("SELECT nama AS 'Nama Tenant', lokasi AS Lokasi, penghuni AS Penghuni, status_ci AS 'Status CI', mulai AS Mulai FROM tenant ORDER BY id DESC", conn)
        if not df_tenant.empty:
            st.dataframe(df_tenant, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data Tenant.")

# --- 8. ABSENSI & KEHADIRAN ---
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Harian", "📋 Rekap Harian", "📊 Statistik Bulanan"])
    
    list_kar_abs = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
    opt_abs = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_abs.iterrows()}
    
    with tab1:
        with st.form("form_absensi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                tgl_abs = st.date_input("Tanggal", date.today())
                pilih_kar_abs = st.selectbox("Karyawan", list(opt_abs.keys()) if opt_abs else ["-"])
                status_abs = st.selectbox("Status", ["Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpha", "Libur"])
            with c2:
                jam_masuk = st.time_input("Jam Masuk", datetime.strptime("08:00", "%H:%M").time())
                jam_keluar = st.time_input("Jam Keluar", datetime.strptime("17:00", "%H:%M").time())
                ket_abs = st.text_area("Keterangan")
            
            if st.form_submit_button("💾 Simpan Absensi", type="primary"):
                if opt_abs:
                    kid = opt_abs[pilih_kar_abs]
                    std_in = datetime.strptime("08:00", "%H:%M").time()
                    if status_abs in ["Hadir", "Terlambat"] and jam_masuk > std_in:
                        terlambat = (datetime.combine(date.today(), jam_masuk) - datetime.combine(date.today(), std_in)).seconds // 60
                    else:
                        terlambat = 0
                    
                    c.execute('''INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit) VALUES (?,?,?,?,?,?,?)''', 
                              (kid, str(tgl_abs), jam_masuk.strftime("%H:%M"), jam_keluar.strftime("%H:%M"), status_abs, ket_abs, terlambat))
                    conn.commit()
                    st.success("✅ Absensi tersimpan!")
                    st.rerun()

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            filter_tgl_abs = st.date_input("Filter Tanggal", date.today(), key="f_abs_tgl")
        with c2:
            filter_status_abs = st.selectbox("Filter Status", ["Semua", "Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpha", "Libur"])
            
        q_abs = """SELECT a.id, a.tanggal, k.employee_id AS NRP, k.full_name AS Nama, a.jam_masuk AS Masuk, a.jam_keluar AS Keluar, a.status AS Status, a.terlambat_menit AS 'Terlambat (menit)', a.keterangan AS Keterangan FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id WHERE a.tanggal = ?"""
        p_abs = [str(filter_tgl_abs)]
        if filter_status_abs != "Semua":
            q_abs += " AND a.status = ?"
            p_abs.append(filter_status_abs)
        q_abs += " ORDER BY k.full_name"
        
        df_abs = pd.read_sql_query(q_abs, conn, params=p_abs)
        if not df_abs.empty:
            st.dataframe(df_abs.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada data absensi untuk filter ini")

    with tab3:
        st.markdown("### 📊 Statistik Kehadiran Bulanan")
        c1, c2 = st.columns(2)
        with c1:
            stat_bulan = st.selectbox("Pilih Bulan", list(range(1, 13)), index=datetime.now().month - 1, format_func=lambda x: calendar.month_name[x])
        with c2:
            stat_tahun = st.number_input("Pilih Tahun", 2020, 2100, datetime.now().year)
        
        df_stat = pd.read_sql_query("""SELECT a.status AS Status, COUNT(*) AS Jumlah FROM absensi a WHERE strftime('%m', a.tanggal) = ? AND strftime('%Y', a.tanggal) = ? GROUP BY a.status""", 
                                     conn, params=(f"{stat_bulan:02d}", str(stat_tahun)))
        if not df_stat.empty:
            st.altair_chart(alt.Chart(df_stat).mark_bar().encode(x='Status:N', y='Jumlah:Q', color='Status:N', tooltip=['Status','Jumlah']).properties(height=300), use_container_width=True)
            st.dataframe(df_stat, use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada data kehadiran untuk periode ini")

# --- 9. CUTI & IZIN ---
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Ajukan Cuti", "📋 Approval & Rekap"])
    
    list_kar_cuti = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
    opt_cuti = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_cuti.iterrows()}
    
    with tab1:
        with st.form("form_cuti", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_cuti = st.selectbox("Karyawan", list(opt_cuti.keys()) if opt_cuti else ["-"])
                jenis_cuti = st.selectbox("Jenis Cuti", ["Cuti Tahunan", "Cuti Sakit", "Cuti Melahirkan", "Izin", "Cuti Menikah", "Cuti Duka"])
            with c2:
                tgl_mulai_cuti = st.date_input("Mulai", date.today())
                tgl_selesai_cuti = st.date_input("Selesai", date.today())
            alasan_cuti = st.text_area("Alasan / Keterangan")
            
            if st.form_submit_button("💾 Ajukan Cuti", type="primary"):
                if opt_cuti:
                    delta = (tgl_selesai_cuti - tgl_mulai_cuti).days + 1
                    c.execute('''INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, status) VALUES (?,?,?,?,?,?,?)''', 
                              (opt_cuti[pilih_kar_cuti], jenis_cuti, str(tgl_mulai_cuti), str(tgl_selesai_cuti), delta, alasan_cuti, "Menunggu"))
                    conn.commit()
                    st.success(f"✅ Pengajuan {delta} hari tersimpan!")
                    st.rerun()

    with tab2:
        filter_status_cuti = st.selectbox("Filter Status", ["Semua", "Menunggu", "Disetujui", "Ditolak"])
        q_cuti = """SELECT c.id, k.employee_id AS NRP, k.full_name AS Nama, c.jenis_cuti AS Jenis, c.tanggal_mulai AS Mulai, c.tanggal_selesai AS Selesai, c.lama_hari AS 'Lama (hari)', c.status AS Status, c.alasan AS Alasan FROM cuti c JOIN karyawan k ON c.karyawan_id = k.id"""
        p_cuti = []
        if filter_status_cuti != "Semua":
            q_cuti += " WHERE c.status = ?"
            p_cuti.append(filter_status_cuti)
        q_cuti += " ORDER BY c.id DESC"
        
        df_cuti = pd.read_sql_query(q_cuti, conn, params=p_cuti)
        if not df_cuti.empty:
            st.dataframe(df_cuti.drop(columns=['id']), use_container_width=True, hide_index=True)
            pending_df = df_cuti[df_cuti['Status'] == 'Menunggu']
            if not pending_df.empty:
                st.markdown("### ✅ Approval Cuti")
                opt_appr = {f"#{r['id']} - {r['Nama']} ({r['Mulai']})": r['id'] for _, r in pending_df.iterrows()}
                pilih_appr = st.selectbox("Pilih Pengajuan", list(opt_appr.keys()))
                cA, cB = st.columns(2)
                with cA:
                    if st.button("✅ Setujui", type="primary", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Disetujui', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr]))
                        conn.commit()
                        st.success("Disetujui!")
                        st.rerun()
                with cB:
                    if st.button("❌ Tolak", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Ditolak', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr]))
                        conn.commit()
                        st.success("Ditolak!")
                        st.rerun()
        else:
            st.info("Belum ada pengajuan cuti")

# --- 10. PAYROLL & SLIP GAJI ---
elif pilihan == "💰 Payroll & Slip Gaji":
    # === FIX BUG #3: Helper payroll didefinisikan DI DALAM block Payroll ===
    # Sebelumnya di file asli posisinya di antara rantai elif → menyebabkan SyntaxError
    def hitung_bpjs(gaji_pokok, tunjangan_tetap):
        upah = gaji_pokok + tunjangan_tetap
        upah_kes = min(upah, 12000000)
        upah_jp = min(upah, 11086300)
        return {
            'kes_k': round(upah_kes * 0.01, -2),
            'kes_p': round(upah_kes * 0.04, -2), 
            'jht_k': round(upah * 0.02, -2),
            'jht_p': round(upah * 0.037, -2), 
            'jp_k': round(upah_jp * 0.01, -2),
            'jp_p': round(upah_jp * 0.02, -2), 
            'jkk': round(upah * 0.0024, -2),
            'jkm': round(upah * 0.003, -2),
            'jkp': round(upah * 0.0005, -2), 
            'total_k': round(upah_kes*0.01, -2) + round(upah*0.02, -2) + round(upah_jp*0.01, -2), 
            'total_p': round(upah_kes*0.04, -2) + round(upah*0.037, -2) + round(upah_jp*0.02, -2) + round(upah*0.0024, -2) + round(upah*0.003, -2) + round(upah*0.0005, -2)
        }

    def hitung_pph21(bruto_bulanan, ptkp_setahun, iuran_pensiun_bulanan):
        biaya_jabatan = min(bruto_bulanan * 0.05, 500000)
        neto_bulanan = bruto_bulanan - biaya_jabatan - iuran_pensiun_bulanan
        neto_setahun = neto_bulanan * 12
        pkp = max(0, round(neto_setahun - ptkp_setahun, -3))
        
        if pkp <= 60000000:
            pph = pkp * 0.05
        elif pkp <= 250000000:
            pph = 60000000*0.05 + (pkp-60000000)*0.15
        elif pkp <= 500000000:
            pph = 60000000*0.05 + 190000000*0.15 + (pkp-250000000)*0.25
        elif pkp <= 5000000000:
            pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + (pkp-500000000)*0.30
        else:
            pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + 4500000000*0.30 + (pkp-5000000000)*0.35
        return max(0, round(pph / 12, -2))

    PTKP_MAP = {
        "TK/0": 54000000, "TK/1": 58500000, "TK/2": 63000000, "TK/3": 67500000,
        "K/0": 58500000, "K/1": 63000000, "K/2": 67500000, "K/3": 72000000
    }
    # === END FIX BUG #3 ===

    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["⚙️ Generate Payroll", "📋 Data Payroll", "🧾 Slip Gaji"])
    
    with tab1:
        with st.form("form_gen_payroll"):
            c1, c2 = st.columns(2)
            with c1:
                bln_pay = st.selectbox("Bulan Periode", list(range(1, 13)), index=datetime.now().month - 1)
            with c2:
                thn_pay = st.number_input("Tahun", 2020, 2100, datetime.now().year)
            periode_pay = f"{thn_pay}-{bln_pay:02d}"
            
            st.markdown(f"**Periode aktif:** `{periode_pay}`")
            tunj_jab = st.number_input("Default Tunjangan Jabatan (Rp)", 0.0, step=100000.0, value=0.0)
            tunj_trans = st.number_input("Default Tunjangan Transport (Rp)", 0.0, step=50000.0, value=0.0)
            tunj_makan = st.number_input("Default Tunjangan Makan (Rp)", 0.0, step=50000.0, value=0.0)
            
            if st.form_submit_button("🚀 Generate Payroll", type="primary"):
                existing = c.execute("SELECT COUNT(*) FROM payroll WHERE periode=?", (periode_pay,)).fetchone()[0]
                if existing > 0:
                    st.warning(f"⚠️ Payroll periode {periode_pay} sudah ada ({existing} baris). Hapus dulu untuk regenerate.")
                else:
                    kar_list = pd.read_sql_query("SELECT id, full_name, ptkp_status, gaji FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='')", conn)
                    count = 0
                    for _, kr in kar_list.iterrows():
                        gaji_pokok = float(kr['gaji'] or 0)
                        if gaji_pokok <= 0: continue
                        
                        bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                        bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                        ptkp_key = kr['ptkp_status'] if kr['ptkp_status'] in PTKP_MAP else "TK/0"
                        pph = hitung_pph21(bruto, PTKP_MAP[ptkp_key], bpjs['jp_k'])
                        total_pot = bpjs['total_k'] + pph
                        gaji_bersih = bruto - total_pot
                        
                        c.execute('''INSERT INTO payroll (karyawan_id, periode, gaji_pokok, tunjangan_jabatan, tunjangan_transport, tunjangan_makan, bpjs_kesehatan_karyawan, bpjs_kesehatan_perusahaan, bpjs_jht_karyawan, bpjs_jht_perusahaan, bpjs_jp_karyawan, bpjs_jp_perusahaan, bpjs_jkk, bpjs_jkm, bpjs_jkp, pph21, total_penghasilan_bruto, total_potongan, gaji_bersih, status, tanggal_proses) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                                  (kr['id'], periode_pay, gaji_pokok, tunj_jab, tunj_trans, tunj_makan, bpjs['kes_k'], bpjs['kes_p'], bpjs['jht_k'], bpjs['jht_p'], bpjs['jp_k'], bpjs['jp_p'], bpjs['jkk'], bpjs['jkm'], bpjs['jkp'], pph, bruto, total_pot, gaji_bersih, 'Final', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        count += 1
                    conn.commit()
                    st.success(f"✅ Berhasil generate {count} karyawan untuk periode {periode_pay}")
                    st.rerun()

    with tab2:
        periode_filter = st.text_input("Filter Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
        df_pay = pd.read_sql_query("""SELECT p.id, p.periode, k.employee_id AS NRP, k.full_name AS Nama, p.gaji_pokok AS 'Gaji Pokok', p.total_penghasilan_bruto AS Bruto, p.total_potongan AS Potongan, p.gaji_bersih AS 'Gaji Bersih', p.status AS Status FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id WHERE p.periode = ? ORDER BY k.full_name""", conn, params=(periode_filter,))
        if not df_pay.empty:
            html = '<div class="metric-grid">'
            html += metric_card("👥 Karyawan", str(len(df_pay)), "baris", "card-blue")
            html += metric_card("💰 Total Bruto", format_rp(df_pay['Bruto'].sum()), "", "card-purple")
            html += metric_card("✅ Total Bersih", format_rp(df_pay['Gaji Bersih'].sum()), "", "card-green")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            st.dataframe(df_pay.drop(columns=['id']).style.format({'Gaji Pokok': 'Rp {:,.0f}', 'Bruto': 'Rp {:,.0f}', 'Potongan': 'Rp {:,.0f}', 'Gaji Bersih': 'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
        else:
            st.info(f"Belum ada payroll untuk periode {periode_filter}")

    with tab3:
        q_slip_opts = pd.read_sql_query("SELECT p.id, p.periode, k.employee_id, k.full_name FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id ORDER BY p.periode DESC, k.full_name", conn)
        if not q_slip_opts.empty:
            opt_slip = {f"{r['periode']} | {r['employee_id']} - {r['full_name']}": r['id'] for _, r in q_slip_opts.iterrows()}
            pilih_slip = st.selectbox("Pilih Slip Gaji", list(opt_slip.keys()))
            slip = pd.read_sql_query("""SELECT p.*, k.employee_id, k.full_name, k.job_position, k.organization FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id WHERE p.id=?""", conn, params=(opt_slip[pilih_slip],)).iloc[0]
            
            st.markdown(f"""
            <div class="payroll-slip">
                <h3>🧾 SLIP GAJI — PERIODE {slip['periode']}</h3>
                <p><b>NRP:</b> {slip['employee_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Nama:</b> {slip['full_name']}</p>
                <p><b>Jabatan:</b> {slip['job_position'] or '-'} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Dept:</b> {slip['organization'] or '-'}</p>
                <hr>
                <h4>PENGHASILAN</h4>
                <div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(slip['gaji_pokok'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Jabatan</span><span>{format_rp(slip['tunjangan_jabatan'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Transport</span><span>{format_rp(slip['tunjangan_transport'])}</span></div>
                <div class="payroll-row"><span>Tunjangan Makan</span><span>{format_rp(slip['tunjangan_makan'])}</span></div>
                <div class="payroll-row payroll-total"><span>TOTAL BRUTO</span><span>{format_rp(slip['total_penghasilan_bruto'])}</span></div>
                <h4 style="margin-top:20px;">POTONGAN</h4>
                <div class="payroll-row"><span>BPJS Kesehatan (1%)</span><span>{format_rp(slip['bpjs_kesehatan_karyawan'])}</span></div>
                <div class="payroll-row"><span>BPJS JHT (2%)</span><span>{format_rp(slip['bpjs_jht_karyawan'])}</span></div>
                <div class="payroll-row"><span>BPJS JP (1%)</span><span>{format_rp(slip['bpjs_jp_karyawan'])}</span></div>
                <div class="payroll-row"><span>PPh 21</span><span>{format_rp(slip['pph21'])}</span></div>
                <div class="payroll-row payroll-total" style="color:#eb3349;"><span>TOTAL POTONGAN</span><span>-{format_rp(slip['total_potongan'])}</span></div>
                <div class="payroll-row payroll-total" style="font-size:1.4em;"><span>GAJI BERSIH</span><span>{format_rp(slip['gaji_bersih'])}</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Belum ada data payroll untuk ditampilkan")
            # --- 11. JOBDESK ---
elif pilihan == "📋 Jobdesk":
    # === FIX BUG #3 (varian 2): helper didefinisikan di dalam blok Jobdesk ===
    def render_crud_table(table_name, title, original_df):
        st.markdown(f"### 📋 Data {title}")
        edited_df = st.data_editor(original_df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button(f"💾 Simpan Perubahan {title}", type="primary", use_container_width=True):
            cur = conn.cursor()
            edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
            old_ids = set(original_df['id'].dropna().astype(int).tolist()) if not original_df.empty else set()
            new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
            
            for did in (old_ids - new_ids): 
                cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
                
            cols = [col for col in edited_df.columns if col != 'id']
            for _, row in edited_df.iterrows():
                vals = [None if pd.isna(row[col]) else row[col] for col in cols]
                if row['id'] == 0:
                    ph = ", ".join(["?"] * len(cols))
                    cur.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})", tuple(vals))
                else:
                    set_c = ", ".join([f"{col}=?" for col in cols])
                    cur.execute(f"UPDATE {table_name} SET {set_c} WHERE id=?", tuple(vals) + (row['id'],))
            conn.commit()
            st.success(f"✅ Perubahan data {title} berhasil disimpan!")
            st.rerun()

    st.markdown('<div class="main-header"><h1>📋 Jobdesk & KPI</h1></div>', unsafe_allow_html=True)
    df_jd = pd.read_sql_query("SELECT id, posisi, departemen, tugas_utama, kpi FROM jobdesk ORDER BY id", conn)
    render_crud_table("jobdesk", "Jobdesk", df_jd)

# --- 12. CI REPORT ---
elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 Continuous Improvement Report</h1></div>', unsafe_allow_html=True)
    with st.form("form_ci", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            ci_tgl = st.date_input("Tanggal", date.today())
            ci_judul = st.text_input("Judul *")
            ci_dept = st.text_input("Departemen")
        with c2:
            ci_status = st.selectbox("Status", ["Draft", "Proses", "Selesai", "Ditolak"])
        ci_desk = st.text_area("Deskripsi / Detail Perbaikan", height=120)
        if st.form_submit_button("💾 Simpan", type="primary"):
            if ci_judul:
                c.execute("INSERT INTO ci (tanggal, judul, departemen, deskripsi, status) VALUES (?,?,?,?,?)", (str(ci_tgl), ci_judul, ci_dept, ci_desk, ci_status))
                conn.commit()
                st.success("✅ Tersimpan!")
                st.rerun()
    df_ci = pd.read_sql_query("SELECT * FROM ci ORDER BY id DESC", conn)
    if not df_ci.empty:
        for _, r in df_ci.iterrows():
            with st.expander(f"💡 [{r['tanggal']}] {r['judul']} — {r['status']}"):
                st.markdown(f"**Dept:** {r['departemen']}")
                st.markdown(f"**Deskripsi:**\n\n{r['deskripsi']}")
                if st.button(f"🗑️ Hapus", key=f"del_ci_{r['id']}"):
                    c.execute("DELETE FROM ci WHERE id=?", (r['id'],))
                    conn.commit()
                    st.rerun()

# --- 13. SKD ---
elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 Surat Keterangan Dokter (SKD)</h1></div>', unsafe_allow_html=True)
    with st.form("form_skd", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            skd_tgl = st.date_input("Tanggal", date.today())
            skd_no = st.text_input("No. Surat")
            skd_nama = st.text_input("Nama Karyawan *")
        with c2:
            skd_jenis = st.selectbox("Jenis Surat", ["SKD Umum", "SKD Sakit", "SKD Hamil", "SKD Kecelakaan Kerja"])
        skd_ket = st.text_area("Keterangan / Diagnosis")
        if st.form_submit_button("💾 Simpan", type="primary"):
            if skd_nama:
                c.execute("INSERT INTO skd (tanggal, no_surat, nama_karyawan, jenis_surat, keterangan) VALUES (?,?,?,?,?)", (str(skd_tgl), skd_no, skd_nama, skd_jenis, skd_ket))
                conn.commit()
                st.success("✅ Tersimpan!")
                st.rerun()
    df_skd = pd.read_sql_query("SELECT * FROM skd ORDER BY id DESC", conn)
    if not df_skd.empty:
        st.dataframe(df_skd[['id','tanggal','no_surat','nama_karyawan','jenis_surat','keterangan']], use_container_width=True, hide_index=True)

# --- 14. INTERNAL MEMO ---
elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo</h1></div>', unsafe_allow_html=True)
    with st.form("form_im", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            im_tgl = st.date_input("Tanggal", date.today())
            im_no = st.text_input("No. Memo")
            im_perihal = st.text_input("Perihal *")
        with c2:
            im_pengirim = st.text_input("Pengirim")
            im_penerima = st.text_input("Penerima")
        im_isi = st.text_area("Isi Memo", height=150)
        if st.form_submit_button("💾 Simpan Memo", type="primary"):
            if im_perihal:
                c.execute("INSERT INTO im (tanggal, no_memo, perihal, pengirim, penerima, isi) VALUES (?,?,?,?,?,?)", (str(im_tgl), im_no, im_perihal, im_pengirim, im_penerima, im_isi))
                conn.commit()
                st.success("✅ Tersimpan!")
                st.rerun()
    df_im = pd.read_sql_query("SELECT * FROM im ORDER BY id DESC", conn)
    if not df_im.empty:
        for _, r in df_im.iterrows():
            label = f"📝 {r['no_memo'] or 'No. ' + str(r['id'])} — {r['perihal']} ({r['tanggal']})"
            with st.expander(label):
                st.markdown(f"**Dari:** {r['pengirim'] or '-'} &nbsp;➡️&nbsp; **Kepada:** {r['penerima'] or '-'}")
                st.markdown(f"**Isi:**\n\n{r['isi']}")

# --- 15. MUTASI & PKWT ---
elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1><p>Riwayat Mutasi & Kontrak Karyawan</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Mutasi", "📋 Daftar Mutasi", "📅 PKWT Habis (30 Hari)"])
    
    list_kar_mut = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
    opt_mut = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_mut.iterrows()}
    
    with tab1:
        with st.form("form_mutasi", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_mut = st.selectbox("Karyawan", list(opt_mut.keys()) if opt_mut else ["-"])
                tgl_mut = st.date_input("Tanggal Mutasi", date.today())
                dari_div = st.text_input("Dari Divisi")
            with c2:
                ke_div = st.text_input("Ke Divisi")
                alasan_mut = st.text_area("Alasan Mutasi")
            if st.form_submit_button("💾 Simpan Mutasi", type="primary"):
                if opt_mut:
                    c.execute("INSERT INTO mutasi (karyawan_id, tanggal_mutasi, dari_divisi, ke_divisi, alasan) VALUES (?,?,?,?,?)", (opt_mut[pilih_kar_mut], str(tgl_mut), dari_div, ke_div, alasan_mut))
                    if ke_div.strip():
                        c.execute("UPDATE karyawan SET organization=? WHERE id=?", (ke_div.strip(), opt_mut[pilih_kar_mut]))
                    conn.commit()
                    st.success("✅ Mutasi tersimpan!")
                    st.rerun()
                    
    with tab2:
        df_mut = pd.read_sql_query("SELECT m.id, k.employee_id AS NRP, k.full_name AS Nama, m.tanggal_mutasi AS Tanggal, m.dari_divisi AS 'Dari', m.ke_divisi AS 'Ke', m.alasan AS Alasan FROM mutasi m JOIN karyawan k ON m.karyawan_id=k.id ORDER BY m.id DESC", conn)
        if not df_mut.empty:
            st.dataframe(df_mut.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data mutasi.")
            
    with tab3:
        tgl_skrg_m = date.today().strftime("%Y-%m-%d")
        tgl_30_m = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        df_pkwt_m = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Dept, job_position AS Jabatan, end_date AS 'Kontrak Habis', mobile_phone AS HP FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND end_date BETWEEN ? AND ? ORDER BY end_date", conn, params=(tgl_skrg_m, tgl_30_m))
        if not df_pkwt_m.empty:
            st.warning(f"⚠️ {len(df_pkwt_m)} karyawan kontraknya habis dalam 30 hari")
            st.dataframe(df_pkwt_m, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Tidak ada kontrak yang habis dalam 30 hari ke depan")

# --- 16. RESIGN & TURNOVER ---
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Resign", "📋 Daftar Resign"])
    
    list_kar_res = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
    opt_res = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_res.iterrows()}
    
    with tab1:
        with st.form("form_resign", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_res = st.selectbox("Karyawan", list(opt_res.keys()) if opt_res else ["-"])
                tgl_res = st.date_input("Tanggal Resign", date.today())
                jenis_res = st.selectbox("Jenis", ["Resign", "PHK", "Pensiun", "Habis Kontrak", "Meninggal"])
                kategori_res = st.selectbox("Kategori Penyebab", ["Kemauan Sendiri", "Kinerja", "Pelanggaran", "Restrukturisasi", "Kontrak Berakhir", "Lainnya"])
            with c2:
                exit_int = st.text_area("Exit Interview")
                clearance_res = st.selectbox("Clearance Status", ["Belum", "Proses", "Selesai"])
                tgl_sign_in = st.date_input("Sign In", date.today())
                tgl_sign_out = st.date_input("Sign Out", date.today())
            alasan_res = st.text_area("Alasan Resign *")
            if st.form_submit_button("💾 Simpan Resign", type="primary"):
                if opt_res and alasan_res:
                    kid = opt_res[pilih_kar_res]
                    c.execute("INSERT INTO resign (karyawan_id, tanggal_resign, alasan, jenis, exit_interview, clearance_status, kategori_penyebab, tanggal_sign_in, tanggal_sign_out) VALUES (?,?,?,?,?,?,?,?,?)", (kid, str(tgl_res), alasan_res, jenis_res, exit_int, clearance_res, kategori_res, str(tgl_sign_in), str(tgl_sign_out)))
                    c.execute("UPDATE karyawan SET resign_date=?, aktif=0 WHERE id=?", (str(tgl_res), kid))
                    conn.commit()
                    st.success("✅ Data resign tersimpan!")
                    st.rerun()
                    
    with tab2:
        df_res = pd.read_sql_query("SELECT r.id, k.employee_id AS NRP, k.full_name AS Nama, r.tanggal_resign AS Tanggal, r.jenis AS Jenis, r.kategori_penyebab AS Kategori, r.alasan AS Alasan, r.clearance_status AS Clearance FROM resign r JOIN karyawan k ON r.karyawan_id=k.id ORDER BY r.id DESC", conn)
        if not df_res.empty:
            st.dataframe(df_res.drop(columns=['id']), use_container_width=True, hide_index=True)
            stat_kategori = df_res['Kategori'].value_counts().reset_index()
            stat_kategori.columns = ['Kategori', 'Jumlah']
            chart = alt.Chart(stat_kategori).mark_bar(cornerRadiusTopRight=8).encode(x=alt.X('Jumlah:Q'), y=alt.Y('Kategori:N', sort='-x'), color=alt.Color('Jumlah:Q', scale=alt.Scale(scheme='reds'), legend=None)).properties(height=250, title="Turnover per Kategori")
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Belum ada data resign.")

# --- 17. DISIPLIN & SP ---
elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & Surat Peringatan (SP)</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Manual", "📋 Daftar SP"])
    
    with tab1:
        list_kar_sp = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND (resign_date IS NULL OR resign_date='' OR resign_date='None') ORDER BY full_name", conn)
        opt_sp = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in list_kar_sp.iterrows()}
        with st.form("form_sp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pilih_kar_sp = st.selectbox("Karyawan", list(opt_sp.keys()) if opt_sp else ["-"])
                jenis_sp = st.selectbox("Jenis Sanksi", ["Teguran Lisan", "SP1", "SP2", "SP3", "Peringatan Tertulis"])
                tgl_mulai_sp = st.date_input("Tanggal Mulai", date.today())
                periode_sp = st.text_input("Periode", value=datetime.now().strftime("%Y"))
            with c2:
                tgl_akhir_sp = st.date_input("Tanggal Akhir", date.today() + timedelta(days=180))
                status_sp = st.selectbox("Status", ["Aktif", "Berakhir", "Dibatalkan"])
            pelanggaran_sp = st.text_area("Rincian Pelanggaran *", height=100)
            if st.form_submit_button("💾 Simpan SP", type="primary"):
                if opt_sp and pelanggaran_sp:
                    c.execute("INSERT INTO disiplin (karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status, periode) VALUES (?,?,?,?,?,?,?)", (opt_sp[pilih_kar_sp], jenis_sp, str(tgl_mulai_sp), str(tgl_akhir_sp), pelanggaran_sp, status_sp, periode_sp))
                    conn.commit()
                    st.success("✅ SP tersimpan!")
                    st.rerun()

    with tab2:
        filter_sp = st.selectbox("Filter Status", ["Semua", "Aktif", "Berakhir", "Dibatalkan"])
        q_sp = "SELECT d.id, k.employee_id AS NRP, k.full_name AS Nama, d.jenis_sanksi AS Sanksi, d.tanggal_mulai AS Mulai, d.tanggal_akhir AS Akhir, d.rincian_pelanggaran AS Pelanggaran, d.status AS Status FROM disiplin d JOIN karyawan k ON d.karyawan_id=k.id"
        p_sp = []
        if filter_sp != "Semua":
            q_sp += " WHERE d.status = ?"
            p_sp.append(filter_sp)
        q_sp += " ORDER BY d.id DESC"
        df_sp = pd.read_sql_query(q_sp, conn, params=p_sp)
        if not df_sp.empty:
            st.dataframe(df_sp.drop(columns=['id']), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data SP.")

# --- 18. EXIT CLEARANCE ---
elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1><p>Checklist Serah Terima Karyawan Resign</p></div>', unsafe_allow_html=True)
    df_exit = pd.read_sql_query("SELECT r.id, k.employee_id AS NRP, k.full_name AS Nama, r.tanggal_resign AS 'Tanggal Resign', r.jenis AS Jenis, r.clearance_status AS Clearance, r.exit_interview AS 'Exit Interview' FROM resign r JOIN karyawan k ON r.karyawan_id=k.id ORDER BY r.id DESC", conn)
    if not df_exit.empty:
        st.dataframe(df_exit.drop(columns=['id']), use_container_width=True, hide_index=True)
        opt_exit = {f"#{r['id']} - {r['Nama']} ({r['Tanggal Resign']})": r['id'] for _, r in df_exit.iterrows()}
        pilih_exit = st.selectbox("Pilih Resign untuk Update Clearance", ["-- Pilih --"] + list(opt_exit.keys()))
        if pilih_exit != "-- Pilih --":
            rid = opt_exit[pilih_exit]
            cur_row = pd.read_sql_query("SELECT * FROM resign WHERE id=?", conn, params=(rid,)).iloc[0]
            st.markdown("### 📋 Checklist Clearance")
            cA, cB, cC, cD = st.columns(4)
            with cA: st.checkbox("Serah Terima Aset", value=bool(cur_row['clearance_status']=='Selesai'))
            with cB: st.checkbox("Pengembalian Dokumen")
            with cC: st.checkbox("Penyelesaian Keuangan")
            with cD: st.checkbox("Handover Pekerjaan")
            new_status = st.selectbox("Status Clearance", ["Belum", "Proses", "Selesai"], index=["Belum", "Proses", "Selesai"].index(cur_row['clearance_status']) if cur_row['clearance_status'] in ["Belum", "Proses", "Selesai"] else 0)
            if st.button("💾 Update Status Clearance", type="primary"):
                c.execute("UPDATE resign SET clearance_status=? WHERE id=?", (new_status, rid))
                conn.commit()
                st.success("✅ Clearance diperbarui")
                st.rerun()
    else:
        st.info("Belum ada data resign untuk exit clearance.")
        # --- 19. WHATSAPP REMINDER ---
elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1><p>Kirim pengingat via WhatsApp</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📝 PKWT Habis", "💰 Utility Belum Lunas", "✉️ Template Pesan", "👨‍💼 Jadwal Interview"])
    
    tgl_skrg_wa = date.today().strftime("%Y-%m-%d")
    tgl_30_wa = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with tab1:
        df_wa = pd.read_sql_query("SELECT id, employee_id, full_name, mobile_phone, end_date, job_position FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND end_date BETWEEN ? AND ? ORDER BY end_date", conn, params=(tgl_skrg_wa, tgl_30_wa))
        if not df_wa.empty:
            for _, r in df_wa.iterrows():
                pesan = f"Halo {r['full_name']}, kontrak kerja Anda sebagai {r['job_position'] or 'Karyawan'} akan berakhir pada {r['end_date']}. Mohon hubungi HR untuk proses perpanjangan. Terima kasih."
                hp = str(r['mobile_phone'] or '').replace('-', '').replace(' ', '').replace('+', '')
                if hp.startswith('0'): hp = '62' + hp[1:]
                if hp and hp != '62':
                    wa_link = f"https://wa.me/{hp}?text={quote(pesan, safe='')}"
                    st.markdown(f"**{r['full_name']}** ({r['employee_id']}) — Habis: `{r['end_date']}` — [📱 Kirim WA]({wa_link})", unsafe_allow_html=True)
        else:
            st.info("Tidak ada PKWT yang habis dalam 30 hari")
            
    with tab2:
        df_wa_util = pd.read_sql_query("SELECT id, kategori, periode, label, total_bayar, status FROM utility WHERE status!='Lunas' ORDER BY id DESC", conn)
        if not df_wa_util.empty:
            for _, r in df_wa_util.iterrows():
                pesan = f"Pengingat: Tagihan {r['kategori']} periode {r['periode']} sebesar {format_rp(r['total_bayar'])} belum lunas. Mohon segera diselesaikan. Terima kasih."
                st.markdown(f"**{r['kategori']}** — {r['label'] or '-'} — `{format_rp(r['total_bayar'])}` — [📋 Copy Pesan](https://wa.me/?text={quote(pesan, safe='')})", unsafe_allow_html=True)
        else:
            st.success("✅ Semua tagihan utility sudah lunas")
            
    with tab3:
        st.markdown("### ✉️ Template Pesan")
        st.text_area("Template PKWT", value="Halo [Nama], kontrak kerja Anda sebagai [Jabatan] akan berakhir pada [Tanggal]. Mohon hubungi HR untuk proses perpanjangan. Terima kasih.", height=100)
        st.text_area("Template Utility", value="Pengingat: Tagihan [Kategori] periode [Periode] sebesar [Nominal] belum lunas. Mohon segera diselesaikan. Terima kasih.", height=100)
        
    with tab4:
        st.subheader("Kirim Undangan Interview ke Kandidat")
        mode_interview = st.radio("Pilih Mode Interview:", ["Offline (Tatap Muka)", "Online (Zoom/Meet)"], horizontal=True)
        
        if mode_interview == "Offline (Tatap Muka)":
            default_template = """PT UNITED EQUIPMENT INDONESIA 
Dear [Nama],
Melalui pesan ini kami mengundang Anda untuk mengikuti interview user secara *Offline (Tatap Muka)*, sesuai jadwal di bawah ini:
- Hari, Tanggal: [Hari], [Tanggal]
- Waktu: [Jam] WITA - Selesai
- Agenda: Interview User
- Lokasi: PT. UNITED EQUIPMENT INDONESIA – Melak Reps 
  (Komplek Business Centre Tinggi Diraja Sendawar Blok A-04, Jl. Sendawar Raya, Barong Tongkok, Kutai Barat)
- Mohon mengonfirmasi kehadiran dengan membalas pesan ini.
*Notes!*
1. Wajib hadir 15-30 menit sebelum acara dimulai.
2. Berpakaian rapih dan sopan (Kemeja).
3. Wajib membawa CV (Hardcopy/Print) dan fotokopi berkas pendukung.
Good Luck !!!
Thank you & Best regards,
HR Recruitment"""
        else:
            default_template = """PT UNITED EQUIPMENT INDONESIA 
Dear [Nama],
Melalui pesan ini kami mengundang Anda untuk mengikuti interview user secara *Online*, sesuai jadwal di bawah ini:
- Hari, Tanggal: [Hari], [Tanggal]
- Waktu: [Jam] WITA - Selesai
- Agenda: Interview User 
- Link: [Link_Meeting]
- Mohon mengonfirmasi kehadiran dengan membalas pesan ini
Notes!
1. Join setelah instruksi
2. Wajib oncam
3. Berpakaian rapih
4. Siapkan Koneksi & Device (Hp/Laptop)
Good Luck !!!
Thank you & Best regards,
HR Recruitment"""

        with st.expander("⚙️ Lihat/Edit Template Pesan Interview", expanded=False):
            template_pesan = st.text_area("Template Pesan", value=default_template, height=350, key="tpl_interview_dynamic")
            if mode_interview == "Online (Zoom/Meet)":
                link_meeting = st.text_input("Masukkan Link Meeting (Untuk Mode Online):", value="https://meet.google.com/xxx-xxxx-xxx")
            else:
                link_meeting = "-"
        
        st.divider()
        
        df_kandidat_db = pd.read_sql_query("SELECT * FROM kandidat WHERE jadwal_interview IS NOT NULL AND jadwal_interview != '' AND jadwal_interview != '-' ORDER BY jadwal_interview ASC", conn)
        
        if df_kandidat_db.empty:
            st.warning("Belum ada kandidat yang dijadwalkan untuk interview.")
        else:
            for index, row in df_kandidat_db.iterrows():
                try:
                    jadwal_lengkap = f"{row['jadwal_interview']} {row['jam_interview']}"
                    dt = datetime.strptime(jadwal_lengkap.strip(), "%Y-%m-%d %H:%M")
                    hari = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
                    bulan = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
                    hari_str = hari[dt.weekday()]
                    tgl_str = f"{dt.day} {bulan[dt.month]} {dt.year}"
                    jam_str = dt.strftime("%H:%M")
                except:
                    hari_str, tgl_str, jam_str = "Hari", str(row['jadwal_interview']), str(row['jam_interview'])
                    
                pesan_final = template_pesan.replace("[Nama]", str(row['nama']))
                pesan_final = pesan_final.replace("[Hari]", hari_str)
                pesan_final = pesan_final.replace("[Tanggal]", tgl_str)
                pesan_final = pesan_final.replace("[Jam]", jam_str)
                
                if mode_interview == "Online (Zoom/Meet)":
                    pesan_final = pesan_final.replace("[Link_Meeting]", link_meeting)
                
                pesan_url = quote(pesan_final, safe='')
                wa_link = f"https://wa.me/{row['telepon']}?text={pesan_url}"
                
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.write(f"**{row['nama']}**")
                    st.caption(f"Posisi: {row['posisi_dilamar']}")
                with col2:
                    st.write(f"📅 {hari_str}, {tgl_str}")
                    st.write(f"⏰ {jam_str} WITA")
                with col3:
                    st.write(f"📱 +{row['telepon']}")
                    st.write(f"Tipe: {row['tipe_interview']}")
                with col4:
                    st.link_button("Kirim WA 💬", wa_link, type="primary", use_container_width=True)
                st.divider()

# --- 20. ARSIP DOKUMEN (E-FILING) & UNIVERSAL IMPORT ---
elif pilihan == "📁 Arsip Dokumen (E-Filing)":
    def parse_csv(file, delim=None, encoding=None):
        raw = file.read(); file.seek(0)
        if encoding is None:
            for enc in ["utf-8-sig", "utf-8", "latin-1", "iso-8859-1"]:
                try: raw.decode(enc); encoding = enc; break
                except: continue
            encoding = encoding or "utf-8"
        if delim is None:
            try: text = raw.decode(encoding)
            except: text = raw.decode("latin-1")
            first = "\n".join(text.split("\n")[:5])
            counts = {",": first.count(","), ";": first.count(";"), "\t": first.count("\t"), "|": first.count("|")}
            delim = max(counts, key=counts.get)
            if counts[delim] == 0: delim = ","
        return pd.read_csv(io.BytesIO(raw), delimiter=delim, encoding=encoding, on_bad_lines='skip', engine='python')

    def parse_excel(file):
        raw = file.read(); file.seek(0)
        xls = pd.ExcelFile(io.BytesIO(raw))
        dfs = [pd.read_excel(io.BytesIO(raw), sheet_name=s) for s in xls.sheet_names]
        dfs = [d for d in dfs if not d.empty]
        if len(dfs) == 1: return dfs[0]
        elif len(dfs) > 1: return pd.concat(dfs, ignore_index=True)
        return pd.DataFrame()

    st.markdown('<div class="main-header"><h1>📁 Arsip Dokumen (E-Filing)</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📤 Upload Dokumen", "🗂️ Universal Import"])
    
    with tab1:
        with st.form("form_upload_dokumen", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama_dok = st.text_input("Nama Dokumen *", placeholder="Contoh: STNK B 9542 TAW")
                kategori = st.selectbox("Kategori Dokumen", ["Legalitas & Perizinan", "Keuangan & Invoice", "Aset & Kendaraan", "HRD & Karyawan", "SOP & Internal Memo", "Lainnya"])
            with col2:
                keterangan = st.text_area("Keterangan / Catatan")
                file_up = st.file_uploader("Pilih File *", type=["pdf", "jpg", "jpeg", "png", "xlsx", "xls", "docx", "doc"])
            
            if st.form_submit_button("💾 Simpan ke Sistem", type="primary"):
                if nama_dok and file_up is not None:
                    try:
                        file_bytes = file_up.read(); file_name = file_up.name; file_type = file_up.type
                        c.execute('''INSERT INTO arsip_dokumen (tanggal_upload, nama_dokumen, kategori, keterangan, file_data, file_name, file_type) VALUES (?,?,?,?,?,?,?)''', 
                                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nama_dok, kategori, keterangan, file_bytes, file_name, file_type))
                        conn.commit()
                        st.success("✅ Dokumen berhasil disimpan!")
                        st.rerun()
                    except Exception as e: 
                        st.error(f"❌ Gagal: {e}")
                else: 
                    st.warning("⚠️ Nama dan File wajib diisi!")

        st.markdown("---")
        st.markdown("### 📚 Daftar Dokumen Tersimpan")
        df_arsip = pd.read_sql_query("SELECT id, tanggal_upload, nama_dokumen, kategori, keterangan, file_name, file_type FROM arsip_dokumen ORDER BY id DESC", conn)
        if not df_arsip.empty:
            st.dataframe(df_arsip.drop(columns=['id']), use_container_width=True, hide_index=True)
            
            # Download per dokumen
            opt_dl = {f"#{r['id']} - {r['nama_dokumen']} ({r['file_name']})": r['id'] for _, r in df_arsip.iterrows()}
            pilih_dl = st.selectbox("Pilih dokumen untuk diunduh", ["-- Pilih --"] + list(opt_dl.keys()), key="dl_arsip")
            if pilih_dl != "-- Pilih --":
                dok = pd.read_sql_query("SELECT * FROM arsip_dokumen WHERE id=?", conn, params=(opt_dl[pilih_dl],)).iloc[0]
                st.download_button("📥 Download Dokumen", bytes(dok['file_data']), dok['file_name'], mime=dok['file_type'] or "application/octet-stream")
        else:
            st.info("Belum ada dokumen tersimpan.")
            
    with tab2:
        st.markdown("### 📦 Universal Import")
        st.info("""
        1. Pilih Tabel Tujuan (Misal: `disiplin`).
        2. Download Template untuk melihat nama kolom yang benar.
        3. Upload file Excel/CSV. Sistem akan otomatis menyesuaikan NRP menjadi ID Karyawan.
        """)
        
        tabel_list = ["jobdesk", "ci", "skd", "im", "lowongan", "kandidat", "aset", "utility", "disiplin"]
        target_table = st.selectbox("Pilih Tabel Tujuan", tabel_list)
        
        c.execute(f"PRAGMA table_info({target_table})")
        columns = [info[1] for info in c.fetchall() if info[1] != 'id']
        
        df_template = pd.DataFrame(columns=columns)
        csv_template = df_template.to_csv(index=False).encode('utf-8')
        st.download_button(f"📄 Download Template {target_table.upper()} (CSV)", csv_template, f"template_{target_table}.csv", "text/csv")
        
        st.markdown("---")
        file_univ = st.file_uploader(f"Upload file Excel/CSV untuk tabel {target_table.upper()}", type=["xlsx", "csv"])
        
        if file_univ is not None:
            if st.button(f"🚀 Proses Import ke {target_table.upper()}", type="primary"):
                try:
                    if file_univ.name.endswith('.csv'):
                        df_imp = pd.read_csv(file_univ)
                    else:
                        df_imp = pd.read_excel(file_univ)
                    
                    df_imp.columns = [str(col).lower().strip().replace(' ', '_') for col in df_imp.columns]
                    
                    if ('nrp' in df_imp.columns or 'employee_id' in df_imp.columns) and 'karyawan_id' in columns:
                        nrp_col = 'nrp' if 'nrp' in df_imp.columns else 'employee_id'
                        def get_kid(nrp):
                            res = c.execute("SELECT id FROM karyawan WHERE employee_id=?", (str(nrp).strip(),)).fetchone()
                            return res[0] if res else None
                        df_imp['karyawan_id'] = df_imp[nrp_col].apply(get_kid)
                        df_imp = df_imp.drop(columns=['nrp', 'employee_id'], errors='ignore')
                    
                    missing_cols = [col for col in columns if col not in df_imp.columns]
                    if missing_cols:
                        st.error(f"❌ Kolom berikut tidak ditemukan di file Anda: **{', '.join(missing_cols)}**")
                    else:
                        sukses, gagal = 0, 0
                        for _, row in df_imp.iterrows():
                            try:
                                if 'karyawan_id' in columns and pd.isna(row['karyawan_id']):
                                    raise ValueError("NRP tidak ditemukan")
                                vals = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
                                ph = ", ".join(["?"] * len(columns))
                                c.execute(f"INSERT INTO {target_table} ({', '.join(columns)}) VALUES ({ph})", tuple(vals))
                                sukses += 1
                            except Exception:
                                gagal += 1
                        conn.commit()
                        if sukses > 0:
                            st.success(f"✅ Berhasil mengimpor {sukses} baris ke tabel {target_table}!")
                            st.rerun()
                        if gagal > 0:
                            st.warning(f"⚠️ {gagal} baris gagal diimport.")
                except Exception as e:
                    st.error(f"❌ Gagal import: {e}")

# --- 21. LAPORAN & ANALITIK ---
elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["👥 Karyawan", "💰 Payroll", "💡 Utility"])
    
    with tab1:
        aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None')").fetchone()[0]
        resign_c = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'").fetchone()[0]
        html = '<div class="metric-grid">'
        html += metric_card("👥 Karyawan Aktif", str(aktif), "", "card-blue")
        html += metric_card("📉 Total Resign", str(resign_c), "", "card-red")
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        df_gender = pd.read_sql_query("SELECT gender AS Gender, COUNT(*) AS Jumlah FROM karyawan WHERE (resign_date IS NULL OR resign_date='' OR resign_date='None') AND gender IS NOT NULL GROUP BY gender", conn)
        if not df_gender.empty:
            st.altair_chart(alt.Chart(df_gender).mark_arc(innerRadius=50).encode(theta='Jumlah:Q', color='Gender:N', tooltip=['Gender','Jumlah']).properties(height=300, title="Komposisi Gender"), use_container_width=True)
        else:
            st.info("Belum ada data gender.")
            
    with tab2:
        df_pay_sum = pd.read_sql_query("SELECT periode, COUNT(*) AS Karyawan, SUM(total_penghasilan_bruto) AS Bruto, SUM(total_potongan) AS Potongan, SUM(gaji_bersih) AS Bersih FROM payroll GROUP BY periode ORDER BY periode DESC LIMIT 12", conn)
        if not df_pay_sum.empty:
            st.dataframe(df_pay_sum.style.format({'Bruto':'Rp {:,.0f}','Potongan':'Rp {:,.0f}','Bersih':'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data payroll.")
            
    with tab3:
        df_util_sum = pd.read_sql_query("SELECT kategori, COUNT(*) AS Transaksi, SUM(total_bayar) AS Total FROM utility GROUP BY kategori", conn)
        if not df_util_sum.empty:
            st.dataframe(df_util_sum.style.format({'Total':'Rp {:,.0f}'}), use_container_width=True, hide_index=True)
            st.altair_chart(alt.Chart(df_util_sum).mark_bar().encode(x='kategori:N', y='Total:Q', color='kategori:N', tooltip=['kategori','Total']).properties(height=300), use_container_width=True)
        else:
            st.info("Belum ada data utility.")

# --- 22. MANPOWER REPORT ---
elif pilihan == "📈 Manpower Report":
    st.markdown('<div class="main-header"><h1>📈 Manpower Report</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        mp_status = st.selectbox("Status", ["Aktif", "Resign", "Semua"])
    with c2:
        df_org_mp = pd.read_sql_query("SELECT DISTINCT organization FROM karyawan WHERE organization IS NOT NULL AND organization != '' ORDER BY organization", conn)
        mp_org = st.selectbox("Organisasi", ["Semua"] + df_org_mp['organization'].tolist())
        
    q_mp = "SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, job_level AS Level, join_date AS 'Tgl Masuk', status_employee AS Status, end_date AS 'Akhir Kontrak' FROM karyawan WHERE 1=1"
    p_mp = []
    if mp_status == "Aktif":
        q_mp += " AND (resign_date IS NULL OR resign_date='' OR resign_date='None')"
    elif mp_status == "Resign":
        q_mp += " AND resign_date IS NOT NULL AND resign_date != '' AND resign_date != 'None'"
    if mp_org != "Semua":
        q_mp += " AND organization = ?"
        p_mp.append(mp_org)
    q_mp += " ORDER BY organization, full_name"
    df_mp = pd.read_sql_query(q_mp, conn, params=p_mp)
    st.markdown(f"**Total: {len(df_mp)} karyawan**")
    st.dataframe(df_mp, use_container_width=True, hide_index=True)
    st.download_button("📥 Export CSV Manpower", df_mp.to_csv(index=False).encode('utf-8'), f"manpower_{date.today()}.csv", "text/csv")

# --- 23. IMPORT, EXPORT & BACKUP ---
elif pilihan == "💾 Import, Export & Backup":
    # === FIX BUG #3 (varian 4): import_data_manpower_melak dipindah ke dalam blok ===
    def import_data_manpower_melak(file):
        raw = file.read(); file.seek(0)
        xls = pd.ExcelFile(io.BytesIO(raw))
        sheet = 'DATABASE' if 'DATABASE' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
        
        sukses, gagal, errors = 0, 0, []
        
        if 'Employee ID' in df.columns:
            col_map = {
                'Employee ID': 'employee_id', 'Full Name': 'full_name', 'Barcode': 'barcode',
                'Organization': 'organization', 'Job Position': 'job_position', 'Job Level': 'job_level',
                'Join Date': 'join_date', 'Resign Date': 'resign_date', 'Status Employee': 'status_employee',
                'End Date': 'end_date', 'Sign Date': 'sign_date', 'Email': 'email',
                'Birth Date': 'birth_date', 'Age': 'age', 'Birth Place': 'birth_place',
                'Citizen ID Address': 'citizen_id_address', 'Residential Address': 'residential_address',
                'NPWP': 'npwp', 'PTKP Status': 'ptkp_status', 'Employee Tax Status': 'employee_tax_status',
                'Tax Config': 'tax_config', 'Bank Name': 'bank_name', 'Bank Account': 'bank_account',
                'Bank Account Holder': 'bank_account_holder', 'BPJS Ketenagakerjaan': 'bpjs_ketenagakerjaan',
                'BPJS Kesehatan': 'bpjs_kesehatan', 'NIK (NPWP 16 Digit)': 'nik_npwp_16',
                'Mobile Phone': 'mobile_phone', 'Phone': 'phone', 'Branch Name': 'branch_name',
                'Parent Branch Name': 'parent_branch_name', 'Religion': 'religion', 'Gender': 'gender',
                'Marital Status': 'marital_status', 'Blood Type': 'blood_type', 'Nationality Code': 'nationality_code',
                'Currency': 'currency', 'Length Of Service': 'length_of_service', 'Payment Schedule': 'payment_schedule',
                'Approval Line': 'approval_line', 'Manager': 'manager', 'Grade': 'grade',
                'Class': 'class', 'Profile Picture': 'profile_picture', 'Cost Center': 'cost_center',
                'Cost Center Category': 'cost_center_category', 'SBU': 'sbu', 'NPWP 16 digit (new)': 'npwp_16_new',
                'Passport': 'passport', 'Passport Expiration Date': 'passport_expiration_date',
                'Jenis Dok. Referensi Bukti Potong': 'jenis_dok_referensi_bukti_potong',
                'Nomor Dok. Referensi Bukti Potong': 'nomor_dok_referensi_bukti_potong',
                'Tanggal Dok. Referensi Bukti Potong': 'tanggal_dok_referensi_bukti_potong',
                'TIN (Taxpayer Identification Number)': 'tin', 'Divisi': 'divisi', 'Keterangan': 'keterangan'
            }
            for idx, row in df.iterrows():
                try:
                    nrp = str(row.get('Employee ID', '')).strip()
                    if nrp.lower() in ['nan', '', 'none']: continue
                    data = {'employee_id': nrp}
                    for xls_col, db_col in col_map.items():
                        if xls_col in df.columns and db_col not in data:
                            val = row.get(xls_col)
                            if pd.notna(val) and str(val).strip().lower() not in ['nan', 'none', '']:
                                if db_col in ['join_date','sign_date','end_date','resign_date','birth_date','tanggal_dok_referensi_bukti_potong']:
                                    try: data[db_col] = pd.to_datetime(val).strftime('%Y-%m-%d')
                                    except: data[db_col] = str(val).strip()
                                else: data[db_col] = str(val).strip()
                    if not data.get('full_name'): continue
                    
                    c.execute("SELECT id FROM karyawan WHERE employee_id=?", (nrp,))
                    exists = c.fetchone()
                    if exists:
                        set_clause = ", ".join([f"{k}=?" for k in data.keys() if k != 'employee_id'])
                        vals = [v for k, v in data.items() if k != 'employee_id']; vals.append(exists[0])
                        c.execute(f"UPDATE karyawan SET {set_clause} WHERE id=?", vals)
                    else:
                        cols = ", ".join(data.keys()); phs = ", ".join(["?"] * len(data))
                        c.execute(f"INSERT INTO karyawan ({cols}) VALUES ({phs})", list(data.values()))
                    sukses += 1
                except Exception as e:
                    gagal += 1; errors.append(f"Baris {idx+2}: {str(e)[:100]}")
            conn.commit()
            return sukses, gagal, errors
        return 0, 0, ["Format kolom tidak dikenali."]
    # === END FIX ===

    st.markdown('<div class="main-header"><h1>💾 Import, Export & Backup</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 Import Manpower", "💾 Backup Database"])
    
    with tab1:
        st.markdown("### 📥 Import Data Manpower (Format MELAK)")
        file_imp = st.file_uploader("Pilih file Excel Manpower", type=["xlsx", "xls", "xlsm"], key="imp_manpower")
        if file_imp:
            if st.button("🚀 Proses Import Manpower", type="primary"):
                with st.spinner("Mengimpor data..."):
                    try:
                        sukses, gagal, errors = import_data_manpower_melak(file_imp)
                        st.success(f"✅ Sukses: {sukses} baris | Gagal: {gagal} baris")
                        if errors:
                            with st.expander("⚠️ Detail Error"): 
                                for e in errors[:20]: st.text(e)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Import gagal: {e}")
                        
    with tab2:
        st.markdown("### 💾 Backup Database")
        try:
            with open('hris_ga.db', 'rb') as f:
                db_bytes = f.read()
            st.download_button("📥 Download Backup Database (SQLite)", db_bytes, f"backup_hris_{date.today()}.db", "application/octet-stream", type="primary", use_container_width=True)
        except Exception as e:
            st.error(f"Gagal membaca database: {e}")

# --- 24. MANAJEMEN USER ---
elif pilihan == "👤 Manajemen User":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1></div>', unsafe_allow_html=True)
    if st.session_state.role != "admin":
        st.error("⛔ Hanya admin yang dapat mengakses halaman ini")
    else:
        tab1, tab2 = st.tabs(["📋 Daftar User", "➕ Tambah User"])
        with tab1:
            df_users = pd.read_sql_query("SELECT username, nama_lengkap, role, aktif FROM users ORDER BY username", conn)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
        with tab2:
            with st.form("form_user_baru"):
                u_username = st.text_input("Username *")
                u_nama = st.text_input("Nama Lengkap *")
                u_password = st.text_input("Password *", type="password")
                u_role = st.selectbox("Role", ["staff", "hrd", "admin"])
                if st.form_submit_button("💾 Tambah User", type="primary"):
                    try:
                        c.execute("INSERT INTO users (username, password, nama_lengkap, role, aktif) VALUES (?,?,?,?,1)", (u_username, hash_password(u_password), u_nama, u_role))
                        conn.commit()
                        st.success("User ditambahkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username sudah ada!")

# --- 25. SINKRONISASI UNIQUIP ---
elif pilihan == "🔄 Sinkronisasi Uniquip":
    st.markdown('<div class="main-header"><h1>🔄 Sinkronisasi Uniquip</h1></div>', unsafe_allow_html=True)
    with st.form("login_form_uniquip"):
        st.subheader("Login Uniquip")
        user = st.text_input("User Uniquip", value="okana")
        pwd = st.text_input("Password Uniquip", type="password")
        submit = st.form_submit_button("Tarik Data Aset", type="primary")
    if submit:
        if user and pwd:
            with st.spinner("Robot sedang login dan mengambil data dari Uniquip..."):
                try:
                    df = tarik_data_uniquip(user, pwd)
                    if isinstance(df, pd.DataFrame):
                        st.success("✅ Data berhasil ditarik!")
                        st.dataframe(df, use_container_width=True)
                    else: 
                        st.error(f"Gagal: {df}")
                except Exception as e: 
                    st.error(f"Terjadi kesalahan: {e}")
        else: 
            st.warning("Username dan Password harus diisi!")

# --- 26. LOG AKTIVITAS ---
elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
    if st.session_state.role != "admin":
        st.error("⛔ Hanya admin yang dapat mengakses halaman ini")
    else:
        df_log = pd.read_sql_query("SELECT username AS User, aksi AS Aksi, detail AS Detail, waktu AS Waktu FROM log_aktivitas ORDER BY id DESC LIMIT 500", conn)
        if not df_log.empty:
            st.dataframe(df_log, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada log aktivitas")

# ==================== FOOTER (FIX BUG #6: dynamic year) ====================
st.markdown(f"""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © {datetime.now().year} — All Rights Reserved
</div>
""", unsafe_allow_html=True)
