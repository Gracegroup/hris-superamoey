import subprocess
import os

if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    subprocess.run(["playwright", "install", "chromium"])

import time
import streamlit as st
import pandas as pd
import sqlite3
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
from fpdf import FPDF
import bcrypt
import scraper_uniquip

st.set_page_config(page_title="HRIS & GA Amoey", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

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

@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

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

c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, poh TEXT, status_poh TEXT, mine_permit_start TEXT, mine_permit_end TEXT, status_mine_permit TEXT, peringatan_pkwt TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT, catatan TEXT, is_deleted INTEGER DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, tipe_interview TEXT, jam_interview TEXT, tahapan TEXT, status_berkas TEXT, catatan_berkas TEXT, tgl_interview TEXT, hasil_interview TEXT, tgl_ground_test TEXT, hasil_ground_test TEXT, tgl_induksi TEXT, hasil_induksi TEXT, tgl_mcu TEXT, hasil_mcu TEXT, tgl_sign_contract TEXT, tmk TEXT, lead_time_hari INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')
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

try: c.execute("ALTER TABLE karyawan ADD COLUMN is_deleted INTEGER DEFAULT 0")
except: pass
try: c.execute("ALTER TABLE aset ADD COLUMN is_deleted INTEGER DEFAULT 0")
except: pass

c.execute("SELECT COUNT(*) FROM lowongan")
if c.fetchone()[0] == 0:
    tgl_buka = date.today().strftime("%Y-%m-%d"); tgl_tutup = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''', ("Mekanik 2 (M2)", "PRODUCT SUPPORT", 5, "Buka", "Pengganti: La Hajar, Ronald, Herdinus, Galant, Kurnia Bangun Samudera", tgl_buka, tgl_tutup))
    conn.commit()

c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    hashed_admin = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    hashed_hrd = bcrypt.hashpw("hrd123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashed_admin, "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("hrd", hashed_hrd, "HRD Staff", "hrd"))
    conn.commit()

def seed_data_from_files():
    base_dir = os.getcwd()
    # SEEDING KARYAWAN
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
            except Exception as e: print(f"❌ Error Karyawan: {e}")
            
    # SEEDING KANDIDAT
    c.execute("SELECT COUNT(*) FROM kandidat")
    if c.fetchone()[0] == 0:
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
                            jadwal = clean_date(row.get('JADWAL')) or '-'
                            jam = clean(row.get('WAKTU'))
                            tipe_intv = "Offline" if "GMEET" not in clean(row.get('VIA', '')).upper() else "Online"

                            if hasil in ['APPROVE', 'DONE']:
                                status, tahapan, hasil_int, catatan = 'Diterima', "Selesai", 'OK', f"[SUDAH DIINTERVIEW] Lolos. Potensi: {posisi_dilamar}."
                            elif hasil == 'REJECT':
                                status, tahapan, hasil_int, catatan = 'Ditolak', "Selesai", 'FAIL', "[SUDAH DIINTERVIEW] Tidak lolos."
                            elif hasil in ['', 'NAN', 'ON REVIEW', 'REVIEW']:
                                status, tahapan, hasil_int, catatan = 'Wawancara', "Interview", '-', f"[REVIEW] Potensi: {posisi_dilamar}."
                            else:
                                status, tahapan, hasil_int, catatan = 'Proses', "Screening", '-', f"[STATUS: {hasil}] Potensi: {posisi_dilamar}."

                            c.execute('''INSERT INTO kandidat (nama, telepon, posisi_dilamar, status, catatan, jadwal_interview, hasil_interview, tipe_interview, jam_interview, tahapan) 
                                         VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                      (nama, telepon, posisi_dilamar, status, catatan, jadwal, hasil_int, tipe_intv, jam, tahapan))
                conn.commit()
            except Exception as e: print(f"❌ Error Kandidat: {e}")
seed_data_from_files()

def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

class PDFSlipGaji(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16); self.cell(0, 10, 'PT UNITED EQUIPMENT INDONESIA', 0, 1, 'C')
        self.set_font('Arial', '', 10); self.cell(0, 5, 'Slip Gaji Karyawan', 0, 1, 'C'); self.ln(10)

def buat_pdf_slip(slip_data):
    pdf = PDFSlipGaji(); pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(40, 8, f"NRP: {slip_data['employee_id']}", border=0); pdf.cell(0, 8, f"Nama: {slip_data['full_name']}", border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(40, 8, f"Periode: {slip_data['periode']}", border=0); pdf.cell(0, 8, f"Jabatan: {slip_data['job_position'] or '-'}", border=0, new_x="LMARGIN", new_y="NEXT"); pdf.ln(5)
    def f_rp(val): return f"Rp {float(val):,.0f}".replace(",", ".")
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, "PENGHASILAN", border=1, new_x="LMARGIN", new_y="NEXT"); pdf.set_font("Arial", size=10)
    for l, v in [("Gaji Pokok", slip_data['gaji_pokok']), ("Tunj. Jabatan", slip_data['tunjangan_jabatan']), ("Tunj. Transport", slip_data['tunjangan_transport']), ("Tunj. Makan", slip_data['tunjangan_makan'])]:
        pdf.cell(100, 7, l, border=1); pdf.cell(0, 7, f_rp(v), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 10); pdf.cell(100, 7, "TOTAL BRUTO", border=1); pdf.cell(0, 7, f_rp(slip_data['total_penghasilan_bruto']), border=1, new_x="LMARGIN", new_y="NEXT"); pdf.ln(5)
    pdf.cell(0, 8, "POTONGAN", border=1, new_x="LMARGIN", new_y="NEXT"); pdf.set_font("Arial", size=10)
    for l, v in [("BPJS Kes (1%)", slip_data['bpjs_kesehatan_karyawan']), ("BPJS JHT (2%)", slip_data['bpjs_jht_karyawan']), ("BPJS JP (1%)", slip_data['bpjs_jp_karyawan']), ("PPh 21", slip_data['pph21'])]:
        pdf.cell(100, 7, l, border=1); pdf.cell(0, 7, f"-{f_rp(v)}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 10); pdf.cell(100, 7, "TOTAL POTONGAN", border=1); pdf.cell(0, 7, f"-{f_rp(slip_data['total_potongan'])}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", 'B', 12); pdf.cell(100, 10, "GAJI BERSIH", border=1); pdf.cell(0, 10, f_rp(slip_data['gaji_bersih']), border=1, new_x="LMARGIN", new_y="NEXT")
    return pdf.output(dest='S').encode('latin-1')

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
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[4] == 1 and bcrypt.checkpw(p.encode('utf-8'), row[1].encode('utf-8')):
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    menu = [
        "🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", 
        "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", 
        "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", 
        "📁 Arsip Dokumen (E-Filing)", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"
    ]
    if st.session_state.role == "admin": menu += ["👤 Manajemen User", "📝 Log Aktivitas"]
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ HRIS, GA & ASET DASHBOARD</h1><p>Selamat datang, <b>{st.session_state.nama}</b></p></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND is_deleted=0").fetchone()[0]
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    lowongan_buka = c.execute("SELECT SUM(jumlah_dibutuhkan) FROM lowongan WHERE status='Buka'").fetchone()[0] or 0
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses' OR status='Wawancara'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"); tgl_skrg = datetime.now().strftime("%Y-%m-%d")
    kontrak_habis = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND is_deleted=0 AND end_date BETWEEN ? AND ?", (tgl_skrg, tgl_30)).fetchone()[0]
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
    
    st.markdown('<div class="section-header"><h3>📢 Detail Kebutuhan (Open Vacant)</h3></div>', unsafe_allow_html=True)
    df_vacant = pd.read_sql_query("SELECT posisi AS 'Posisi / Level', departemen AS 'Departemen', jumlah_dibutuhkan AS 'Jumlah Dibutuhkan', deskripsi AS 'Keterangan' FROM lowongan WHERE status='Buka' ORDER BY id DESC", conn)
    if not df_vacant.empty: st.dataframe(df_vacant, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="section-header"><h3>💡 KPI Utility Melak</h3></div>', unsafe_allow_html=True)
    total_util = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility").fetchone()[0]
    util_belum = c.execute("SELECT COUNT(*) FROM utility WHERE status!='Lunas'").fetchone()[0]
    util_belum_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status!='Lunas'").fetchone()[0]
    pdam_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='PDAM'").fetchone()[0]
    listrik_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='Listrik'").fetchone()[0]
    internet_rp = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE kategori='Internet'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("💰 Total Utility", format_rp(total_util), "semua", "card-blue")
    html += metric_card("💧 PDAM", format_rp(pdam_rp), "", "card-teal")
    html += metric_card("⚡ Listrik", format_rp(listrik_rp), "", "card-gold")
    html += metric_card("🌐 Internet", format_rp(internet_rp), "", "card-purple")
    html += metric_card("❌ Belum Lunas", f"{util_belum}", format_rp(util_belum_rp), "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1></div>', unsafe_allow_html=True)
    search_query = st.text_input("🔍 Masukkan Nama Manpower / Kandidat:")
    if search_query:
        q_karyawan = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, status_employee AS Status, mobile_phone AS HP FROM karyawan WHERE full_name LIKE ? AND is_deleted=0", conn, params=(f'%{search_query}%',))
        q_kandidat = pd.read_sql_query("SELECT nama AS Nama, posisi_dilamar AS Posisi, status AS Status, jadwal_interview AS 'Tgl Interview', jam_interview AS 'Jam', tipe_interview AS 'Tipe', tahapan AS 'Tahapan', catatan AS 'Catatan' FROM kandidat WHERE nama LIKE ?", conn, params=(f'%{search_query}%',))
        q_aset = pd.read_sql_query("SELECT nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi, kondisi AS Kondisi FROM aset WHERE penanggung_jawab LIKE ? AND is_deleted=0", conn, params=(f'%{search_query}%',))
        q_utility = pd.read_sql_query("SELECT kategori AS 'Jenis Utility', label AS Label, periode AS Periode, total_bayar AS Nominal, status AS Status FROM utility WHERE penanggung_jawab LIKE ?", conn, params=(f'%{search_query}%',))
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
        else: st.warning("Data tidak ditemukan.")

elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Kandidat", "📋 Pipeline & Jadwal", "📢 Open Vacant"])
    with tab1:
        with st.form("form_kandidat_baru", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *"); posisi = st.text_input("Posisi Dilamar"); telepon = st.text_input("Telepon/WA"); email = st.text_input("Email"); sumber = st.selectbox("Sumber", ["Job Portal", "Referral", "Walk-in", "LinkedIn", "Job Fair", "Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today()); status = st.selectbox("Status Awal", ["Proses", "Wawancara", "Diterima", "Ditolak"]); tgl_interview = st.date_input("Tanggal Interview"); jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time()); tipe_interview = st.selectbox("Tipe Interview", ["Offline (Kantor)", "Online (Zoom/Meet)"]); tahapan = st.selectbox("Tahapan", ["Screening", "Interview HR", "Interview User", "MCU", "Offering"]); status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
            catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan Kandidat", type="primary"):
                if nama:
                    existing = c.execute("SELECT id FROM kandidat WHERE nama=? AND posisi_dilamar=?", (nama, posisi)).fetchone()
                    if existing: st.error("⚠️ Kandidat sudah ada!")
                    else:
                        c.execute('''INSERT INTO kandidat (nama, posisi_dilamar, telepon, email, sumber, tanggal_lamar, status, catatan, jadwal_interview, jam_interview, tipe_interview, tahapan, status_berkas) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan, str(tgl_interview), jam_interview.strftime('%H:%M'), tipe_interview, tahapan, status_berkas))
                        conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
                else: st.error("⚠️ Nama wajib diisi!")
    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        if not df_k.empty:
            filter_status = st.selectbox("🔍 Filter Status:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]
            st.dataframe(df_filtered[['id','nama','posisi_dilamar','status','jadwal_interview','jam_interview','tahapan','catatan']], use_container_width=True, hide_index=True)
            opsi_kandidat = {f"{row['id']} - {row['nama']}": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]
                    s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(kandidat_id,)).iloc[0]
                    with st.form("form_update_pipeline"):
                        e_status = st.selectbox("Status Akhir", ["Proses", "Wawancara", "Diterima", "Ditolak"], index=["Proses", "Wawancara", "Diterima", "Ditolak"].index(s['status']) if s['status'] in ["Proses", "Wawancara", "Diterima", "Ditolak"] else 0)
                        e_tahapan = st.selectbox("Tahapan", ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"], index=["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"].index(s['tahapan']) if s['tahapan'] in ["Screening", "Interview HR", "Interview User", "MCU", "Offering", "Selesai"] else 0)
                        e_catatan = st.text_area("Catatan", value=s['catatan'] or "")
                        if st.form_submit_button("💾 Simpan", type="primary"):
                            c.execute('''UPDATE kandidat SET status=?, tahapan=?, catatan=? WHERE id=?''', (e_status, e_tahapan, e_catatan, kandidat_id))
                            conn.commit(); st.rerun()
                    if st.button(f"🗑️ Hapus Kandidat", type="primary"): c.execute("DELETE FROM kandidat WHERE id=?", (kandidat_id,)); conn.commit(); st.rerun()
        else: st.info("Belum ada data.")
    with tab3:
        df_vac = pd.read_sql_query("SELECT * FROM lowongan ORDER BY id DESC", conn)
        if not df_vac.empty:
            for _, r in df_vac.iterrows():
                st.markdown(f"**{r['posisi']} ({r['departemen']})** - Butuh: {r['jumlah_dibutuhkan']} | Status: {r['status']}")
                colA, colB = st.columns(2)
                with colA:
                    if st.button(f"Tutup {r['posisi']}", key=f"tutup_{r['id']}"): c.execute("UPDATE lowongan SET status='Tutup' WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                with colB:
                    if st.button(f"Hapus {r['posisi']}", key=f"hapus_{r['id']}"): c.execute("DELETE FROM lowongan WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Daftar Karyawan", "✏️ Tambah / Edit"])
    with tab1:
        q_kar = st.text_input("🔍 Cari Nama / NRP", "")
        q_kar_sql = "SELECT id, employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan, join_date AS 'Tgl Masuk', status_employee AS Status, mobile_phone AS HP FROM karyawan WHERE is_deleted=0"
        p_kar = []
        if q_kar:
            q_kar_sql += " AND (full_name LIKE ? OR employee_id LIKE ?)"
            p_kar.extend([f"%{q_kar}%"] * 2)
        df_kar = pd.read_sql_query(q_kar_sql + " ORDER BY full_name", conn, params=p_kar)
        st.dataframe(df_kar.drop(columns=['id']), use_container_width=True, hide_index=True)
    with tab2:
        list_kar_all = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE is_deleted=0 ORDER BY full_name", conn)
        opt_kar_all = {"-- Karyawan Baru --": 0}
        for _, r in list_kar_all.iterrows(): opt_kar_all[f"{r['employee_id']} - {r['full_name']}"] = r['id']
        pilih_kar_all = st.selectbox("Pilih Karyawan", list(opt_kar_all.keys()))
        edit_kar_id = opt_kar_all[pilih_kar_all]
        s_kar = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(edit_kar_id,)).iloc[0] if edit_kar_id > 0 else {}
        with st.form("form_karyawan"):
            c1, c2 = st.columns(2)
            with c1:
                e_nrp = st.text_input("NRP *", value=str(s_kar.get('employee_id', '')) if edit_kar_id else "")
                e_nama = st.text_input("Nama Lengkap *", value=str(s_kar.get('full_name', '')) if edit_kar_id else "")
                e_org = st.text_input("Organisasi", value=str(s_kar.get('organization', '') or '') if edit_kar_id else "")
            with c2:
                e_tgl_masuk = st.text_input("Tgl Masuk (YYYY-MM-DD)", value=str(s_kar.get('join_date', '') or '') if edit_kar_id else "")
                e_gaji = st.number_input("Gaji Pokok", min_value=0.0, value=float(s_kar.get('gaji', 0) or 0) if edit_kar_id else 0.0, step=100000.0)
            if st.form_submit_button("💾 Simpan", type="primary"):
                if e_nrp and e_nama:
                    if edit_kar_id > 0:
                        c.execute("UPDATE karyawan SET employee_id=?, full_name=?, organization=?, join_date=?, gaji=? WHERE id=?", (e_nrp, e_nama, e_org, e_tgl_masuk, e_gaji, edit_kar_id))
                    else:
                        c.execute("INSERT INTO karyawan (employee_id, full_name, organization, join_date, gaji) VALUES (?,?,?,?,?)", (e_nrp, e_nama, e_org, e_tgl_masuk, e_gaji))
                    conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
                    
elif pilihan == "🚛 Aset & Properti":
    # === FITUR SCRAPING UNIQUIP ===
    with st.expander("🔄 Sinkronisasi Data dari UniQuip (V2)", expanded=False):
        col_u, col_p, col_b = st.columns([2, 2, 1])
        uq_user = col_u.text_input("Username UniQuip", key="uq_user")
        uq_pass = col_p.text_input("Password UniQuip", type="password", key="uq_pass")
        
        if col_b.button("Tarik Data", type="primary", use_container_width=True):
            if uq_user and uq_pass:
                with st.spinner("Menghubungi server UniQuip... Mohon tunggu."):
                    try:
                        df_uniquip = scraper_uniquip.scrape_aset_uniquip(uq_user, uq_pass)
                        if not df_uniquip.empty:
                            st.success(f"Berhasil menarik data aset!")
                            st.dataframe(df_uniquip, use_container_width=True)
                    except Exception as e:
                        st.error(str(e))
            else:
                st.warning("Username dan Password wajib diisi!")
    # === SELESAI FITUR SCRAPING ===

    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1><p>Manajemen Inventaris Perusahaan</p></div>', unsafe_allow_html=True)
    
    total_aset = c.execute("SELECT COUNT(*) FROM aset WHERE is_deleted=0").fetchone()[0]
    total_nilai = c.execute("SELECT COALESCE(SUM(nilai),0) FROM aset WHERE is_deleted=0").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("📦 Total Aset", str(total_aset), "unit", "card-blue")
    html += metric_card("💰 Total Nilai", format_rp(total_nilai), "", "card-green")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Aset", "➕ Tambah Aset", "✏️ Edit / Hapus Aset"])
    with tab1:
        df_aset = pd.read_sql_query("SELECT kode AS Kode, nama AS 'Nama Aset', kategori AS Kategori, lokasi AS Lokasi, kondisi AS Kondisi, penanggung_jawab AS 'Penanggung Jawab', status AS Status, catatan AS Catatan FROM aset WHERE is_deleted=0 ORDER BY id DESC", conn)
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
                        c.execute('''INSERT INTO aset (kode, nama, kategori, lokasi, kondisi, penanggung_jawab, status, catatan) VALUES (?,?,?,?,?,?,?,?)''', (a_kode, a_nama, a_kategori, a_lokasi, a_kondisi, a_pj, "Aktif", a_catatan))
                        conn.commit(); st.success("✅ Aset berhasil ditambahkan!"); st.rerun()
                    except sqlite3.IntegrityError: st.error("❌ Kode Aset sudah digunakan!")
                else: st.error("⚠️ Kode dan Nama Aset wajib diisi!")

    with tab3:
        st.subheader("✏️ Edit / Hapus Data Aset")
        df_aset_all = pd.read_sql_query("SELECT * FROM aset WHERE is_deleted=0 ORDER BY id DESC", conn)
        if not df_aset_all.empty:
            opt_aset = {f"{r['kode']} - {r['nama']}": r['id'] for _, r in df_aset_all.iterrows()}
            pilih_aset = st.selectbox("Pilih Aset:", ["-- Pilih --"] + list(opt_aset.keys()))
            if pilih_aset != "-- Pilih --":
                aid = opt_aset[pilih_aset]
                s_aset = pd.read_sql_query("SELECT * FROM aset WHERE id=?", conn, params=(aid,)).iloc[0]
                with st.form("form_edit_aset"):
                    col1, col2 = st.columns(2)
                    with col1:
                        ea_kode = st.text_input("Kode Aset", value=s_aset['kode'])
                        ea_nama = st.text_input("Nama Aset", value=s_aset['nama'])
                        kat_opts = ["Kendaraan", "Elektronik", "Furniture", "Peralatan Kerja", "Bangunan", "Lainnya"]
                        ea_kategori = st.selectbox("Kategori", kat_opts, index=kat_opts.index(s_aset['kategori']) if s_aset['kategori'] in kat_opts else 5)
                    with col2:
                        ea_lokasi = st.text_input("Lokasi", value=s_aset['lokasi'] or "")
                        ea_pj = st.text_input("Penanggung Jawab", value=s_aset['penanggung_jawab'] or "")
                        kond_opts = ["Baik", "Rusak Ringan", "Rusak Berat"]
                        ea_kondisi = st.selectbox("Kondisi", kond_opts, index=kond_opts.index(s_aset['kondisi']) if s_aset['kondisi'] in kond_opts else 0)
                    ea_catatan = st.text_area("Catatan Tambahan", value=s_aset['catatan'] or "")
                    if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                        c.execute('''UPDATE aset SET kode=?, nama=?, kategori=?, lokasi=?, kondisi=?, penanggung_jawab=?, catatan=? WHERE id=?''', (ea_kode, ea_nama, ea_kategori, ea_lokasi, ea_kondisi, ea_pj, ea_catatan, aid))
                        conn.commit(); st.success("✅ Data Aset diperbarui!"); st.rerun()
                if st.button("🗑️ Hapus Aset Ini (Arsipkan)", type="primary"):
                    c.execute("UPDATE aset SET is_deleted=1 WHERE id=?", (aid,)); conn.commit(); st.success("✅ Aset diarsipkan!"); st.rerun()

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
        df_util = pd.read_sql_query("SELECT kategori AS Kategori, periode AS Periode, id_pelanggan AS 'ID Pelanggan', label AS 'Nama / Lokasi', penanggung_jawab AS 'Penanggung Jawab', total_bayar AS Nominal, status AS Status, tanggal_bayar AS 'Tgl Bayar' FROM utility ORDER BY id DESC", conn)
        if not df_util.empty: st.dataframe(df_util, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data utility.")
        st.markdown("---")
        df_util_all = pd.read_sql_query("SELECT * FROM utility ORDER BY id DESC", conn)
        if not df_util_all.empty:
            opt_util = {f"#{r['id']} - {r['kategori']} ({r['periode']}) - {r['label']}": r['id'] for _, r in df_util_all.iterrows()}
            pilih_util = st.selectbox("Pilih Data Utility:", ["-- Pilih --"] + list(opt_util.keys()))
            if pilih_util != "-- Pilih --":
                uid = opt_util[pilih_util]
                s_util = pd.read_sql_query("SELECT * FROM utility WHERE id=?", conn, params=(uid,)).iloc[0]
                with st.form("form_edit_util"):
                    eu_kat = st.selectbox("Kategori", ["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"], index=["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"].index(s_util['kategori']) if s_util['kategori'] in ["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"] else 0)
                    eu_stat = st.selectbox("Status", ["Lunas", "Belum Lunas"], index=0 if s_util['status']=="Lunas" else 1)
                    if st.form_submit_button("💾 Simpan Perubahan", type="primary"):
                        c.execute('''UPDATE utility SET kategori=?, status=? WHERE id=?''', (eu_kat, eu_stat, uid)); conn.commit(); st.rerun()
                if st.button("🗑️ Hapus Data Utility", type="primary"):
                    c.execute("DELETE FROM utility WHERE id=?", (uid,)); conn.commit(); st.rerun()
    with tab2:
        with st.form("form_tambah_utility"):
            col1, col2 = st.columns(2)
            with col1:
                u_kategori = st.selectbox("Kategori", ["PDAM", "Listrik", "Internet", "Telepon", "Lainnya"])
                u_id_pel = st.text_input("ID Pelanggan / No. Meter")
                u_label = st.text_input("Nama / Lokasi")
                u_pj = st.text_input("Penanggung Jawab")
                u_periode = st.text_input("Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
            with col2:
                u_tgl = st.date_input("Tanggal Bayar", date.today())
                u_nominal = st.number_input("Nominal Tagihan (Rp)", min_value=0.0, step=10000.0)
                u_admin = st.number_input("Biaya Admin (Rp)", min_value=0.0, step=1000.0)
                u_status = st.selectbox("Status", ["Lunas", "Belum Lunas"])
            if st.form_submit_button("💾 Simpan Utility", type="primary"):
                total_bayar = u_nominal + u_admin
                c.execute('''INSERT INTO utility (kategori, id_pelanggan, tanggal_bayar, periode, label, nominal, admin, total_bayar, status, penanggung_jawab, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (u_kategori, u_id_pel, str(u_tgl), u_periode, u_label, u_nominal, u_admin, total_bayar, u_status, u_pj, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit(); st.success("✅ Data Utility disimpan!"); st.rerun()

elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1><p>Manajemen Properti & Penyewa</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🏪 Data Ruko", "🏠 Data Tenant"])
    with tab1:
        df_ruko = pd.read_sql_query("SELECT nama AS 'Nama Ruko', alamat AS Cabang, status AS 'Status Kepemilikan', penyewa AS 'Nama Penyewa', nilai_sewa AS 'Nilai Sewa', mulai_sewa AS 'Mulai', akhir_sewa AS 'Akhir' FROM ruko ORDER BY id DESC", conn)
        if not df_ruko.empty: st.dataframe(df_ruko, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data Ruko.")
    with tab2:
        df_tenant = pd.read_sql_query("SELECT nama AS 'Nama Tenant', lokasi AS Lokasi, penghuni AS Penghuni, status_ci AS 'Status CI', mulai AS Mulai FROM tenant ORDER BY id DESC", conn)
        if not df_tenant.empty: st.dataframe(df_tenant, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data Tenant.")

elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input Harian", "📋 Rekap Harian", "📊 Statistik Bulanan"])
    list_kar_abs = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND is_deleted=0 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
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
                    else: terlambat = 0
                    c.execute('''INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit) VALUES (?,?,?,?,?,?,?)''', (kid, str(tgl_abs), jam_masuk.strftime("%H:%M"), jam_keluar.strftime("%H:%M"), status_abs, ket_abs, terlambat))
                    conn.commit(); st.success("✅ Absensi tersimpan!"); st.rerun()
    with tab2:
        c1, c2 = st.columns(2)
        with c1: filter_tgl_abs = st.date_input("Filter Tanggal", date.today(), key="f_abs_tgl")
        with c2: filter_status_abs = st.selectbox("Filter Status", ["Semua", "Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpha", "Libur"])
        q_abs = """SELECT a.id, a.tanggal, k.employee_id AS NRP, k.full_name AS Nama, a.jam_masuk AS Masuk, a.jam_keluar AS Keluar, a.status AS Status, a.terlambat_menit AS 'Terlambat (menit)', a.keterangan AS Keterangan FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id WHERE a.tanggal = ?"""
        p_abs = [str(filter_tgl_abs)]
        if filter_status_abs != "Semua":
            q_abs += " AND a.status = ?"; p_abs.append(filter_status_abs)
        q_abs += " ORDER BY k.full_name"
        df_abs = pd.read_sql_query(q_abs, conn, params=p_abs)
        if not df_abs.empty: st.dataframe(df_abs.drop(columns=['id']), use_container_width=True, hide_index=True)
        else: st.info("Tidak ada data absensi untuk filter ini")
    with tab3:
        c1, c2 = st.columns(2)
        with c1: stat_bulan = st.selectbox("Pilih Bulan", list(range(1, 13)), index=datetime.now().month - 1, format_func=lambda x: calendar.month_name[x])
        with c2: stat_tahun = st.number_input("Pilih Tahun", 2020, 2100, datetime.now().year)
        df_stat = pd.read_sql_query("""SELECT a.status AS Status, COUNT(*) AS Jumlah FROM absensi a WHERE strftime('%m', a.tanggal) = ? AND strftime('%Y', a.tanggal) = ? GROUP BY a.status""", conn, params=(f"{stat_bulan:02d}", str(stat_tahun)))
        if not df_stat.empty:
            st.altair_chart(alt.Chart(df_stat).mark_bar().encode(x='Status:N', y='Jumlah:Q', color='Status:N', tooltip=['Status','Jumlah']).properties(height=300), use_container_width=True)
            st.dataframe(df_stat, use_container_width=True, hide_index=True)

elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Ajukan Cuti", "📋 Approval & Rekap"])
    list_kar_cuti = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE aktif=1 AND is_deleted=0 AND (resign_date IS NULL OR resign_date='') ORDER BY full_name", conn)
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
                    c.execute('''INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, status) VALUES (?,?,?,?,?,?,?)''', (opt_cuti[pilih_kar_cuti], jenis_cuti, str(tgl_mulai_cuti), str(tgl_selesai_cuti), delta, alasan_cuti, "Menunggu"))
                    conn.commit(); st.success(f"✅ Pengajuan {delta} hari tersimpan!"); st.rerun()
    with tab2:
        filter_status_cuti = st.selectbox("Filter Status", ["Semua", "Menunggu", "Disetujui", "Ditolak"])
        q_cuti = """SELECT c.id, k.employee_id AS NRP, k.full_name AS Nama, c.jenis_cuti AS Jenis, c.tanggal_mulai AS Mulai, c.tanggal_selesai AS Selesai, c.lama_hari AS 'Lama (hari)', c.status AS Status, c.alasan AS Alasan FROM cuti c JOIN karyawan k ON c.karyawan_id = k.id"""
        p_cuti = []
        if filter_status_cuti != "Semua":
            q_cuti += " WHERE c.status = ?"; p_cuti.append(filter_status_cuti)
        q_cuti += " ORDER BY c.id DESC"
        df_cuti = pd.read_sql_query(q_cuti, conn, params=p_cuti)
        if not df_cuti.empty:
            st.dataframe(df_cuti.drop(columns=['id']), use_container_width=True, hide_index=True)
            pending_df = df_cuti[df_cuti['Status'] == 'Menunggu']
            if not pending_df.empty:
                opt_appr = {f"#{r['id']} - {r['Nama']} ({r['Mulai']})": r['id'] for _, r in pending_df.iterrows()}
                pilih_appr = st.selectbox("Pilih Pengajuan", list(opt_appr.keys()))
                cA, cB = st.columns(2)
                with cA:
                    if st.button("✅ Setujui", type="primary", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Disetujui', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr])); conn.commit(); st.rerun()
                with cB:
                    if st.button("❌ Tolak", use_container_width=True):
                        c.execute("UPDATE cuti SET status='Ditolak', approved_by=?, approved_at=? WHERE id=?", (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), opt_appr[pilih_appr])); conn.commit(); st.rerun()

elif pilihan == "💰 Payroll & Slip Gaji":
    def hitung_bpjs(gaji_pokok, tunjangan_tetap):
        upah = gaji_pokok + tunjangan_tetap
        upah_kes = min(upah, 12000000); upah_jp = min(upah, 11086300)
        return {'kes_k': round(upah_kes * 0.01, -2), 'kes_p': round(upah_kes * 0.04, -2), 'jht_k': round(upah * 0.02, -2), 'jht_p': round(upah * 0.037, -2), 'jp_k': round(upah_jp * 0.01, -2), 'jp_p': round(upah_jp * 0.02, -2), 'jkk': round(upah * 0.0024, -2), 'jkm': round(upah * 0.003, -2), 'jkp': round(upah * 0.0005, -2), 'total_k': round(upah_kes*0.01, -2) + round(upah*0.02, -2) + round(upah_jp*0.01, -2), 'total_p': round(upah_kes*0.04, -2) + round(upah*0.037, -2) + round(upah_jp*0.02, -2) + round(upah*0.0024, -2) + round(upah*0.003, -2) + round(upah*0.0005, -2)}
    def hitung_pph21(bruto_bulanan, ptkp_setahun, iuran_pensiun_bulanan):
        biaya_jabatan = min(bruto_bulanan * 0.05, 500000)
        neto_setahun = (bruto_bulanan - biaya_jabatan - iuran_pensiun_bulanan) * 12
        pkp = max(0, round(neto_setahun - ptkp_setahun, -3))
        if pkp <= 60000000: pph = pkp * 0.05
        elif pkp <= 250000000: pph = 60000000*0.05 + (pkp-60000000)*0.15
        elif pkp <= 500000000: pph = 60000000*0.05 + 190000000*0.15 + (pkp-250000000)*0.25
        else: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + (pkp-500000000)*0.30
        return max(0, round(pph / 12, -2))
    PTKP_MAP = {"TK/0": 54000000, "TK/1": 58500000, "TK/2": 63000000, "TK/3": 67500000, "K/0": 58500000, "K/1": 63000000, "K/2": 67500000, "K/3": 72000000}
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["⚙️ Generate Payroll", "📋 Data Payroll", "🧾 Slip Gaji"])
    with tab1:
        with st.form("form_gen_payroll"):
            c1, c2 = st.columns(2)
            with c1: bln_pay = st.selectbox("Bulan", list(range(1, 13)), index=datetime.now().month - 1)
            with c2: thn_pay = st.number_input("Tahun", 2020, 2100, datetime.now().year)
            periode_pay = f"{thn_pay}-{bln_pay:02d}"
            tunj_jab = st.number_input("Tunj. Jabatan", 0.0, step=100000.0); tunj_trans = st.number_input("Tunj. Transport", 0.0, step=50000.0); tunj_makan = st.number_input("Tunj. Makan", 0.0, step=50000.0)
            if st.form_submit_button("🚀 Generate Payroll", type="primary"):
                if c.execute("SELECT COUNT(*) FROM payroll WHERE periode=?", (periode_pay,)).fetchone()[0] > 0: st.warning("Payroll periode ini sudah ada.")
                else:
                    kar_list = pd.read_sql_query("SELECT id, ptkp_status, gaji FROM karyawan WHERE aktif=1 AND is_deleted=0 AND (resign_date IS NULL OR resign_date='')", conn)
                    count = 0
                    for _, kr in kar_list.iterrows():
                        gaji_pokok = float(kr['gaji'] or 0)
                        if gaji_pokok <= 0: continue
                        bpjs = hitung_bpjs(gaji_pokok, tunj_jab); bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                        pph = hitung_pph21(bruto, PTKP_MAP.get(kr['ptkp_status'], 54000000), bpjs['jp_k'])
                        total_pot = bpjs['total_k'] + pph; gaji_bersih = bruto - total_pot
                        c.execute('''INSERT INTO payroll (karyawan_id, periode, gaji_pokok, tunjangan_jabatan, tunjangan_transport, tunjangan_makan, bpjs_kesehatan_karyawan, bpjs_kesehatan_perusahaan, bpjs_jht_karyawan, bpjs_jht_perusahaan, bpjs_jp_karyawan, bpjs_jp_perusahaan, bpjs_jkk, bpjs_jkm, bpjs_jkp, pph21, total_penghasilan_bruto, total_potongan, gaji_bersih, status, tanggal_proses) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (kr['id'], periode_pay, gaji_pokok, tunj_jab, tunj_trans, tunj_makan, bpjs['kes_k'], bpjs['kes_p'], bpjs['jht_k'], bpjs['jht_p'], bpjs['jp_k'], bpjs['jp_p'], bpjs['jkk'], bpjs['jkm'], bpjs['jkp'], pph, bruto, total_pot, gaji_bersih, 'Final', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        count += 1
                    conn.commit(); st.success(f"✅ Generate {count} karyawan berhasil."); st.rerun()
    with tab2:
        periode_filter = st.text_input("Filter Periode", value=datetime.now().strftime("%Y-%m"))
        df_pay = pd.read_sql_query("""SELECT p.id, p.periode, k.employee_id AS NRP, k.full_name AS Nama, p.gaji_pokok AS 'Gaji Pokok', p.total_penghasilan_bruto AS Bruto, p.total_potongan AS Potongan, p.gaji_bersih AS 'Gaji Bersih' FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id WHERE p.periode = ?""", conn, params=(periode_filter,))
        if not df_pay.empty: st.dataframe(df_pay.drop(columns=['id']), use_container_width=True, hide_index=True)
        else: st.info("Belum ada data.")
    with tab3:
        q_slip_opts = pd.read_sql_query("SELECT p.id, p.periode, k.employee_id, k.full_name FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id ORDER BY p.periode DESC", conn)
        if not q_slip_opts.empty:
            opt_slip = {f"{r['periode']} | {r['employee_id']} - {r['full_name']}": r['id'] for _, r in q_slip_opts.iterrows()}
            pilih_slip = st.selectbox("Pilih Slip Gaji", list(opt_slip.keys()))
            slip = pd.read_sql_query("""SELECT p.*, k.employee_id, k.full_name, k.job_position, k.organization FROM payroll p JOIN karyawan k ON p.karyawan_id=k.id WHERE p.id=?""", conn, params=(opt_slip[pilih_slip],)).iloc[0]
            st.markdown(f"""<div class="payroll-slip"><h3>🧾 SLIP GAJI — {slip['periode']}</h3><p><b>NRP:</b> {slip['employee_id']} | <b>Nama:</b> {slip['full_name']}</p><hr><div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(slip['gaji_pokok'])}</span></div><div class="payroll-row payroll-total"><span>GAJI BERSIH</span><span>{format_rp(slip['gaji_bersih'])}</span></div></div>""", unsafe_allow_html=True)
            pdf_bytes = buat_pdf_slip(slip)
            st.download_button("📥 Download Slip Gaji (PDF)", data=pdf_bytes, file_name=f"Slip_Gaji_{slip['employee_id']}_{slip['periode']}.pdf", mime="application/pdf", type="primary")

elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk & KPI</h1></div>', unsafe_allow_html=True)
    df_jd = pd.read_sql_query("SELECT id, posisi, departemen, tugas_utama, kpi FROM jobdesk ORDER BY id", conn)
    edited_df = st.data_editor(df_jd, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
        cur = conn.cursor()
        for _, row in edited_df.iterrows():
            if row['id'] == 0: cur.execute("INSERT INTO jobdesk (posisi, departemen, tugas_utama, kpi) VALUES (?,?,?,?)", (row['posisi'], row['departemen'], row['tugas_utama'], row['kpi']))
            else: cur.execute("UPDATE jobdesk SET posisi=?, departemen=?, tugas_utama=?, kpi=? WHERE id=?", (row['posisi'], row['departemen'], row['tugas_utama'], row['kpi'], row['id']))
        conn.commit(); st.success("✅ Tersimpan!"); st.rerun()

elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 Continuous Improvement Report</h1></div>', unsafe_allow_html=True)
    with st.form("form_ci", clear_on_submit=True):
        ci_tgl = st.date_input("Tanggal", date.today()); ci_judul = st.text_input("Judul *"); ci_dept = st.text_input("Departemen")
        ci_status = st.selectbox("Status", ["Draft", "Proses", "Selesai", "Ditolak"]); ci_desk = st.text_area("Deskripsi")
        if st.form_submit_button("💾 Simpan", type="primary"):
            if ci_judul: c.execute("INSERT INTO ci (tanggal, judul, departemen, deskripsi, status) VALUES (?,?,?,?,?)", (str(ci_tgl), ci_judul, ci_dept, ci_desk, ci_status)); conn.commit(); st.rerun()
    df_ci = pd.read_sql_query("SELECT * FROM ci ORDER BY id DESC", conn)
    if not df_ci.empty:
        for _, r in df_ci.iterrows():
            with st.expander(f"💡 [{r['tanggal']}] {r['judul']} — {r['status']}"):
                st.markdown(f"**Dept:** {r['departemen']}\n\n**Deskripsi:**\n{r['deskripsi']}")

elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 Surat Keterangan Dokter (SKD)</h1></div>', unsafe_allow_html=True)
    with st.form("form_skd", clear_on_submit=True):
        skd_tgl = st.date_input("Tanggal", date.today()); skd_no = st.text_input("No. Surat"); skd_nama = st.text_input("Nama Karyawan *")
        skd_jenis = st.selectbox("Jenis Surat", ["SKD Umum", "SKD Sakit", "SKD Hamil", "SKD Kecelakaan Kerja"]); skd_ket = st.text_area("Keterangan")
        if st.form_submit_button("💾 Simpan", type="primary"):
            if skd_nama: c.execute("INSERT INTO skd (tanggal, no_surat, nama_karyawan, jenis_surat, keterangan) VALUES (?,?,?,?,?)", (str(skd_tgl), skd_no, skd_nama, skd_jenis, skd_ket)); conn.commit(); st.rerun()
    df_skd = pd.read_sql_query("SELECT * FROM skd ORDER BY id DESC", conn)
    if not df_skd.empty: st.dataframe(df_skd, use_container_width=True, hide_index=True)

elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo</h1></div>', unsafe_allow_html=True)
    with st.form("form_im", clear_on_submit=True):
        im_tgl = st.date_input("Tanggal", date.today()); im_no = st.text_input("No. Memo"); im_perihal = st.text_input("Perihal *")
        im_pengirim = st.text_input("Pengirim"); im_penerima = st.text_input("Penerima"); im_isi = st.text_area("Isi Memo")
        if st.form_submit_button("💾 Simpan Memo", type="primary"):
            if im_perihal: c.execute("INSERT INTO im (tanggal, no_memo, perihal, pengirim, penerima, isi) VALUES (?,?,?,?,?,?)", (str(im_tgl), im_no, im_perihal, im_pengirim, im_penerima, im_isi)); conn.commit(); st.rerun()
    df_im = pd.read_sql_query("SELECT * FROM im ORDER BY id DESC", conn)
    if not df_im.empty:
        for _, r in df_im.iterrows():
            with st.expander(f"📝 {r['perihal']} ({r['tanggal']})"): st.text(r['isi'])

elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input Mutasi", "📅 PKWT Habis (30 Hari)"])
    with tab1:
        with st.form("form_mutasi"):
            tgl_mut = st.date_input("Tanggal Mutasi", date.today()); dari_div = st.text_input("Dari Divisi"); ke_div = st.text_input("Ke Divisi"); alasan_mut = st.text_area("Alasan")
            if st.form_submit_button("💾 Simpan"): st.success("Disimpan (Demo)")
    with tab2:
        tgl_30 = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
        df_pkwt = pd.read_sql_query("SELECT employee_id, full_name, end_date FROM karyawan WHERE end_date BETWEEN ? AND ?", conn, params=(date.today().strftime("%Y-%m-%d"), tgl_30))
        st.dataframe(df_pkwt, use_container_width=True)

elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    df_res = pd.read_sql_query("SELECT r.id, k.full_name AS Nama, r.tanggal_resign AS Tanggal, r.alasan AS Alasan FROM resign r JOIN karyawan k ON r.karyawan_id=k.id ORDER BY r.id DESC", conn)
    st.dataframe(df_res, use_container_width=True, hide_index=True)

elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & SP</h1></div>', unsafe_allow_html=True)
    df_sp = pd.read_sql_query("SELECT d.id, k.full_name AS Nama, d.jenis_sanksi AS Sanksi, d.tanggal_mulai AS Mulai, d.status AS Status FROM disiplin d JOIN karyawan k ON d.karyawan_id=k.id", conn)
    st.dataframe(df_sp, use_container_width=True, hide_index=True)

elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1></div>', unsafe_allow_html=True)
    df_exit = pd.read_sql_query("SELECT r.id, k.full_name AS Nama, r.tanggal_resign AS Tanggal, r.clearance_status AS Clearance FROM resign r JOIN karyawan k ON r.karyawan_id=k.id", conn)
    st.dataframe(df_exit, use_container_width=True, hide_index=True)

elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1></div>', unsafe_allow_html=True)
    st.info("Modul ini membutuhkan integrasi dengan WhatsApp API (Fonnte/Wablas) atau Selenium. (UI saja)")

elif pilihan == "📁 Arsip Dokumen (E-Filing)":
    st.markdown('<div class="main-header"><h1>📁 Arsip Dokumen</h1></div>', unsafe_allow_html=True)
    with st.form("form_upload"):
        nama_dok = st.text_input("Nama Dokumen"); file_up = st.file_uploader("Upload File", type=["pdf", "jpg", "png"])
        if st.form_submit_button("💾 Simpan"):
            if nama_dok and file_up: st.success("Dokumen tersimpan (Simulasi).")

elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1></div>', unsafe_allow_html=True)
    st.info("Grafik dan laporan analitik ditampilkan di sini.")

elif pilihan == "📈 Manpower Report":
    st.markdown('<div class="main-header"><h1>📈 Manpower Report</h1></div>', unsafe_allow_html=True)
    df_mp = pd.read_sql_query("SELECT employee_id AS NRP, full_name AS Nama, organization AS Organisasi, job_position AS Jabatan FROM karyawan WHERE is_deleted=0", conn)
    st.dataframe(df_mp, use_container_width=True)
    st.download_button("📥 Export CSV", df_mp.to_csv(index=False).encode('utf-8'), "manpower.csv", "text/csv")

elif pilihan == "💾 Import, Export & Backup":
    st.markdown('<div class="main-header"><h1>💾 Import, Export & Backup</h1></div>', unsafe_allow_html=True)
    st.markdown("### 💾 Backup Database")
    try:
        with open('hris_ga.db', 'rb') as f: db_bytes = f.read()
        st.download_button("📥 Download Backup Database (SQLite)", db_bytes, f"backup_hris_{date.today()}.db", "application/octet-stream", type="primary", use_container_width=True)
    except Exception as e: st.error(f"Gagal membaca database: {e}")

elif pilihan == "👤 Manajemen User":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1></div>', unsafe_allow_html=True)
    if st.session_state.role != "admin": st.error("⛔ Hanya admin")
    else:
        df_users = pd.read_sql_query("SELECT username, nama_lengkap, role, aktif FROM users", conn)
        st.dataframe(df_users, use_container_width=True)

elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
    if st.session_state.role != "admin": st.error("⛔ Hanya admin")
    else:
        df_log = pd.read_sql_query("SELECT username, aksi, waktu FROM log_aktivitas ORDER BY id DESC LIMIT 100", conn)
        st.dataframe(df_log, use_container_width=True)

st.markdown(f"""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © {datetime.now().year} — All Rights Reserved
</div>
""", unsafe_allow_html=True)
