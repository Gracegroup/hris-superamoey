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

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA SUPER v3.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("uploads/foto", exist_ok=True)
os.makedirs("uploads/dokumen", exist_ok=True)

# ==================== FITUR INSTALL APLIKASI (POJOK KANAN) ====================
def create_install_button():
    bat_content = """@echo off\ntitle Aplikasi HRIS & GA\ncolor 0A\necho ========================================================\necho MENGINSTALL APLIKASI HRIS ^& GA\necho ========================================================\necho.\necho [1/2] Menginstall library yang dibutuhkan (Mohon tunggu)...\npip install -r requirements.txt\necho.\necho [2/2] Menjalankan Aplikasi...\nstreamlit run app.py\npause\n"""
    req_content = "streamlit\npandas\naltair\nopenpyxl\n"
    
    app_content = ""
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            app_content = f.read()
    except:
        app_content = "# Silakan copy-paste kode utama Anda di sini\n"

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("app.py", app_content)
        zip_file.writestr("requirements.txt", req_content)
        zip_file.writestr("run.bat", bat_content)
        zip_file.writestr("CARA_INSTALL.txt", "CARA INSTALL:\n1. Ekstrak file ZIP ini.\n2. Klik 2x file 'run.bat'.\n3. Browser akan otomatis terbuka.")
        
    b64 = base64.b64encode(zip_buffer.getvalue()).decode()
    
    html_button = f"""
    <style>
        .install-btn {{
            position: fixed; top: 70px; right: 20px; z-index: 9999;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white !important; padding: 12px 20px; border-radius: 10px;
            text-decoration: none; font-weight: 700; font-family: 'Segoe UI', sans-serif;
            font-size: 14px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
            transition: all 0.3s ease; display: flex; align-items: center; gap: 8px;
        }}
        .install-btn:hover {{ transform: translateY(-3px) scale(1.02); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.6); color: white !important; }}
    </style>
    <a href="data:application/zip;base64,{b64}" download="Aplikasi_HRIS_GA.zip" class="install-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
        Install Aplikasi
    </a>
    """
    st.markdown(html_button, unsafe_allow_html=True)

create_install_button()
# ==============================================================================


# ==================== FITUR FLYER MELAYANG-LAYANG (DIPERBARUI) ====================
def get_image_base64(path_options):
    for path in path_options:
        try:
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            continue
    return ""

def show_floating_flyers():
    # Deteksi fleksibel (handle ekstensi ganda atau typo)
    img_mekanik_b64 = get_image_base64(["flyer_mekanik.png", "flyer_mekanik.png.jpeg", "flyer_mekanik.jpeg", "flyer_mekanik.jpg"])
    img_warehouse_b64 = get_image_base64(["flyer_warehouse.png", "flyer_warehouse.png.jpeg", "flyer_warehouse.jpeg", "flyer_warehouse.jpg"])
    
    # Placeholder jika gambar tidak ada
    src_mekanik = f"data:image/png;base64,{img_mekanik_b64}" if img_mekanik_b64 else "https://placehold.co/400x600/FFD700/000000.png?text=Flyer+Mekanik"
    src_warehouse = f"data:image/png;base64,{img_warehouse_b64}" if img_warehouse_b64 else "https://placehold.co/400x600/1e3a8a/FFFFFF.png?text=Flyer+Warehouse"
    
    html_flyers = """
    <style>
        @keyframes floatBounce {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
        }
        .flyer-container {
            position: fixed;
            top: 130px; /* Dipindah ke atas layar */
            z-index: 999;
            width: 160px; /* Ukuran sedikit lebih kecil agar tidak menutupi layar */
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            animation: floatBounce 4s ease-in-out infinite;
            transition: transform 0.3s;
            background-color: #fff;
            padding: 5px;
        }
        .flyer-container:hover { animation-play-state: paused; transform: scale(1.05); z-index: 1000; }
        /* Posisi Kiri dan Kanan */
        .flyer-left { left: 260px; animation-delay: 0s; } 
        .flyer-right { right: 20px; animation-delay: 2s; }
        
        @media (max-width: 768px) { .flyer-container { display: none; } }
    </style>
    """
    
    html_flyers += f'<div class="flyer-container flyer-left"><img src="{src_mekanik}" style="width:100%; border-radius:8px;"></div>'
    html_flyers += f'<div class="flyer-container flyer-right"><img src="{src_warehouse}" style="width:100%; border-radius:8px;"></div>'
    
    st.markdown(html_flyers, unsafe_allow_html=True)
# =====================================================================

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2f7 0%, #d9e4f5 100%); }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e57c2 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4);
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 2.2em; }
    .main-header p { color: #e0e7ff; margin: 5px 0 0 0; }
    .metric-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px; margin-bottom: 20px;
    }
    .metric-card {
        padding: 18px; border-radius: 15px; color: white;
        box-shadow: 0 6px 15px rgba(0,0,0,0.15); transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-4px); }
    .metric-card .label { font-size: 0.8em; opacity: 0.95; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
    .metric-card .value { font-size: 1.5em; font-weight: bold; }
    .metric-card .sub { font-size: 0.75em; opacity: 0.85; margin-top: 5px; }
    .card-blue   { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .card-pink   { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .card-green  { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-dark   { background: linear-gradient(135deg, #232526 0%, #414345 100%); }
    .card-teal   { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .card-red    { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-gold   { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
    .section-header {
        background: white; padding: 15px 20px; border-radius: 12px;
        border-left: 5px solid #2a5298; margin: 20px 0 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .section-header h3 { margin: 0; color: #1e3c72; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%);
        color: white !important; border: none; border-radius: 10px;
        padding: 10px 20px; font-weight: 600; transition: all 0.3s; width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 15px rgba(42,82,152,0.5);
    }
    .wa-btn {
        background: #25D366; color: white !important; padding: 8px 15px;
        border-radius: 8px; text-decoration: none; font-weight: 600;
        display: inline-block; font-size: 0.9em; border: none;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: white; border-radius: 10px 10px 0 0;
        padding: 10px 20px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%);
        color: white !important;
    }
    .payroll-slip {
        background: white; padding: 25px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .payroll-slip h3 { color: #1e3c72; border-bottom: 2px dashed #2a5298; padding-bottom: 10px; }
    .payroll-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dotted #ddd; }
    .payroll-total { font-weight: bold; font-size: 1.2em; color: #11998e; border-top: 2px solid #2a5298; padding-top: 10px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ====================
@st.cache_resource
def get_conn():
    return sqlite3.connect('hris_ga.db', check_same_thread=False)

conn = get_conn()
c = conn.cursor()

try:
    c.execute("SELECT employee_id FROM karyawan LIMIT 1")
except:
    c.execute("DROP TABLE IF EXISTS karyawan")
    conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT,
    nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')

c.execute('''CREATE TABLE IF NOT EXISTS karyawan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE,
    full_name TEXT,
    barcode TEXT,
    organization TEXT,
    job_position TEXT,
    job_level TEXT,
    join_date TEXT,
    resign_date TEXT,
    status_employee TEXT,
    end_date TEXT,
    sign_date TEXT,
    email TEXT,
    birth_date TEXT,
    age TEXT,
    birth_place TEXT,
    citizen_id_address TEXT,
    residential_address TEXT,
    npwp TEXT,
    ptkp_status TEXT,
    employee_tax_status TEXT,
    tax_config TEXT,
    bank_name TEXT,
    bank_account TEXT,
    bank_account_holder TEXT,
    bpjs_ketenagakerjaan TEXT,
    bpjs_kesehatan TEXT,
    nik_npwp_16 TEXT,
    mobile_phone TEXT,
    phone TEXT,
    branch_name TEXT,
    parent_branch_name TEXT,
    religion TEXT,
    gender TEXT,
    marital_status TEXT,
    blood_type TEXT,
    nationality_code TEXT,
    currency TEXT,
    length_of_service TEXT,
    payment_schedule TEXT,
    approval_line TEXT,
    manager TEXT,
    grade TEXT,
    class TEXT,
    profile_picture TEXT,
    cost_center TEXT,
    cost_center_category TEXT,
    sbu TEXT,
    npwp_16_new TEXT,
    passport TEXT,
    passport_expiration_date TEXT,
    jenis_dok_referensi_bukti_potong TEXT,
    nomor_dok_referensi_bukti_potong TEXT,
    tanggal_dok_referensi_bukti_potong TEXT,
    tin TEXT,
    divisi TEXT,
    keterangan TEXT,
    versatility TEXT,
    pendidikan_terakhir TEXT,
    asal_sekolah TEXT,
    no_ktp TEXT,
    no_kk TEXT,
    poh TEXT,
    status_poh TEXT,
    mine_permit_start TEXT,
    mine_permit_end TEXT,
    status_mine_permit TEXT,
    peringatan_pkwt TEXT,
    gaji REAL DEFAULT 0,
    aktif INTEGER DEFAULT 1)''')

c.execute('''CREATE TABLE IF NOT EXISTS kandidat (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, posisi_dilamar TEXT,
    telepon TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT,
    status TEXT, catatan TEXT, jadwal_interview TEXT, status_berkas TEXT, catatan_berkas TEXT,
    tgl_interview TEXT, hasil_interview TEXT,
    tgl_ground_test TEXT, hasil_ground_test TEXT,
    tgl_induksi TEXT, hasil_induksi TEXT,
    tgl_mcu TEXT, hasil_mcu TEXT,
    tgl_sign_contract TEXT, tmk TEXT,
    lead_time_hari INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS lowongan (
    id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT,
    jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka',
    deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')

# === DATA SEEDING LOWONGAN ===
c.execute("SELECT COUNT(*) FROM lowongan")
if c.fetchone()[0] == 0:
    tgl_buka = date.today().strftime("%Y-%m-%d")
    tgl_tutup = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup)
                 VALUES (?,?,?,?,?,?,?)''',
              ("Mekanik 2 (M2)", "PRODUCT SUPPORT", 5, "Buka",
               "Pengganti: La Hajar, Ronald, Herdinus, Galant, Kurnia Bangun Samudera", tgl_buka, tgl_tutup))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup)
                 VALUES (?,?,?,?,?,?,?)''',
              ("Mekanik 3 (M3)", "PRODUCT SUPPORT", 4, "Buka",
               "Pengganti: Indra S, Mardiansyah, Fahri A, Ikmal", tgl_buka, tgl_tutup))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup)
                 VALUES (?,?,?,?,?,?,?)''',
              ("Warehouseman", "AFTER MARKET & INVENTORY WAREHOUSE", 1, "Buka",
               "Pengganti: PTE_SNB-EBK / Site PT. SNS-BEK", tgl_buka, tgl_tutup))
    conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS resign (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT,
    alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT,
    kategori_penyebab TEXT, tanggal_sign_in TEXT, tanggal_sign_out TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS aset (
    id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT,
    lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT,
    penanggung_jawab TEXT, status TEXT, catatan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS ruko (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT,
    penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT, catatan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS tenant (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT,
    penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT, catatan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS absensi (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT,
    jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT,
    terlambat_menit INTEGER DEFAULT 0)''')

c.execute('''CREATE TABLE IF NOT EXISTS cuti (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT,
    tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER,
    alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT,
    periode_cuti_ke INTEGER, actual_cuti TEXT, status_pengambilan TEXT, saldo_cuti INTEGER)''')

c.execute('''CREATE TABLE IF NOT EXISTS payroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT,
    gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL,
    tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL,
    bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL,
    bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL,
    bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL,
    pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL,
    gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS disiplin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    karyawan_id INTEGER,
    jenis_sanksi TEXT,
    tanggal_mulai TEXT,
    tanggal_akhir TEXT,
    rincian_pelanggaran TEXT,
    status TEXT DEFAULT 'Aktif',
    periode TEXT)''')

# === TABEL UTILITY MELAK ===
c.execute('''CREATE TABLE IF NOT EXISTS utility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kategori TEXT,
    tanggal_bayar TEXT,
    periode TEXT,
    id_pelanggan TEXT,
    label TEXT,
    nominal REAL DEFAULT 0,
    admin REAL DEFAULT 0,
    total_bayar REAL DEFAULT 0,
    metode TEXT,
    status TEXT DEFAULT 'Lunas',
    catatan TEXT,
    created_at TEXT)''')

# === TABEL BARU (Sesuai Request) ===
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT,
    dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (
    id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT,
    tugas_utama TEXT, kpi TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS ci (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT,
    departemen TEXT, deskripsi TEXT, status TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS skd (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT,
    nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS im (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT,
    perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# ==================== AUTO MIGRATION ====================
def _migrate():
    migrations = [
        ("karyawan", "versatility", "TEXT"), ("karyawan", "pendidikan_terakhir", "TEXT"),
        ("karyawan", "asal_sekolah", "TEXT"), ("karyawan", "no_ktp", "TEXT"),
        ("karyawan", "no_kk", "TEXT"), ("karyawan", "poh", "TEXT"),
        ("karyawan", "status_poh", "TEXT"), ("karyawan", "mine_permit_start", "TEXT"),
        ("karyawan", "mine_permit_end", "TEXT"), ("karyawan", "status_mine_permit", "TEXT"),
        ("karyawan", "peringatan_pkwt", "TEXT"),
        ("kandidat", "tgl_interview", "TEXT"), ("kandidat", "hasil_interview", "TEXT"),
        ("kandidat", "tgl_ground_test", "TEXT"), ("kandidat", "hasil_ground_test", "TEXT"),
        ("kandidat", "tgl_induksi", "TEXT"), ("kandidat", "hasil_induksi", "TEXT"),
        ("kandidat", "tgl_mcu", "TEXT"), ("kandidat", "hasil_mcu", "TEXT"),
        ("kandidat", "tgl_sign_contract", "TEXT"), ("kandidat", "tmk", "TEXT"),
        ("kandidat", "lead_time_hari", "INTEGER"),
        ("resign", "kategori_penyebab", "TEXT"), ("resign", "tanggal_sign_in", "TEXT"),
        ("resign", "tanggal_sign_out", "TEXT"),
        ("cuti", "periode_cuti_ke", "INTEGER"), ("cuti", "actual_cuti", "TEXT"),
        ("cuti", "status_pengambilan", "TEXT"), ("cuti", "saldo_cuti", "INTEGER"),
    ]
    for tbl, col, typ in migrations:
        try:
            c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass
    conn.commit()

_migrate()

# ==================== HELPER ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"

def hitung_umur(birth_date_str):
    try:
        bd = datetime.strptime(str(birth_date_str)[:10], "%Y-%m-%d").date()
        today = date.today()
        return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    except: return None

def hitung_masa_kerja(join_date_str):
    try:
        jd = datetime.strptime(str(join_date_str)[:10], "%Y-%m-%d").date()
        today = date.today()
        years = today.year - jd.year - ((today.month, today.day) < (jd.month, jd.day))
        months = (today.month - jd.month) % 12
        return f"{years} tahun {months} bulan"
    except: return "-"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)",
              (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

def normalize_col(col):
    s = str(col).lower().strip()
    for ch in [' ', '.', '-', '/', '\\', ':', ',']: s = s.replace(ch, '_')
    for ch in ['(', ')', '[', ']', '{', '}', '&', "'", '"']: s = s.replace(ch, '')
    while '__' in s: s = s.replace('__', '_')
    return s.strip('_')

def map_columns(df, tabel):
    SPECIAL_MAP = {"nik_npwp_16_digit": "nik_npwp_16", "nik_npwp_16": "nik_npwp_16",
                   "npwp_16_digit_new": "npwp_16_new", "npwp_16_new": "npwp_16_new",
                   "tin_taxpayer_identification_number": "tin"}
    cur = conn.execute(f"PRAGMA table_info({tabel})")
    kolom_db = [r[1] for r in cur.fetchall()]
    mapping = {}
    for col in df.columns:
        norm = normalize_col(col)
        if norm in SPECIAL_MAP: target = SPECIAL_MAP[norm]
        elif norm in kolom_db: target = norm
        else: target = None
        mapping[col] = target
    return mapping, kolom_db

# ==================== PARSER TANGGAL INDONESIA ====================
_BULAN_ID = {'jan':'01','feb':'02','mar':'03','apr':'04','mei':'05','may':'05',
             'jun':'06','jul':'07','agt':'08','aug':'08','agu':'08',
             'sep':'09','okt':'10','oct':'10','nov':'11','des':'12','dec':'12'}

def parse_tanggal_id(s):
    try:
        parts = str(s).strip().split()
        if len(parts) == 3:
            d, m, y = parts
            m_num = _BULAN_ID.get(m.lower()[:3])
            if m_num: return f"{y}-{m_num}-{int(d):02d}"
    except: pass
    return date.today().strftime("%Y-%m-%d")

def to_float_id(v):
    try: return float(str(v).replace('.', '').replace(',', '').strip())
    except: return 0.0

# ==================== MULTI-FORMAT FILE PARSERS ====================
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

def parse_json(file):
    raw = file.read(); file.seek(0)
    try: data = json.loads(raw.decode("utf-8"))
    except: data = json.loads(raw.decode("latin-1"))
    if isinstance(data, list): return pd.DataFrame(data)
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and len(v) > 0: return pd.DataFrame(v)
        return pd.DataFrame([data])
    return pd.DataFrame()

def parse_word(file):
    try: from docx import Document
    except ImportError: raise Exception("pip install python-docx")
    raw = file.read(); file.seek(0)
    doc = Document(io.BytesIO(raw))
    tables_data = []
    for tbl in doc.tables:
        data = [[cell.text.strip() for cell in row.cells] for row in tbl.rows]
        if data:
            tables_data.append(pd.DataFrame(data[1:], columns=data[0]))
    if not tables_data:
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return pd.DataFrame({"text": lines}) if lines else pd.DataFrame()
    return tables_data[0] if len(tables_data) == 1 else pd.concat(tables_data, ignore_index=True)

def parse_pdf(file):
    raw = file.read(); file.seek(0)
    try: import pdfplumber
    except ImportError: raise Exception("pip install pdfplumber")
    tables_data = []; text_lines = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            for tbl in page.extract_tables():
                if tbl and len(tbl) > 1:
                    header = [str(h) if h else f"col_{i}" for i, h in enumerate(tbl[0])]
                    rows = [[str(c) if c else "" for c in row] for row in tbl[1:]]
                    max_len = len(header)
                    rows = [r + [""] * (max_len - len(r)) for r in rows]
                    rows = [r[:max_len] for r in rows]
                    tables_data.append(pd.DataFrame(rows, columns=header))
            txt = page.extract_text()
            if txt: text_lines.extend(txt.split("\n"))
    if tables_data: return tables_data[0] if len(tables_data) == 1 else pd.concat(tables_data, ignore_index=True)
    elif text_lines: return pd.DataFrame({"text": text_lines})
    return pd.DataFrame()

def parse_any_file(file, filename):
    ext = filename.lower().split('.')[-1]
    if ext == 'csv': return parse_csv(file)
    elif ext in ['xlsx', 'xls', 'xlsm']: return parse_excel(file)
    elif ext == 'json': return parse_json(file)
    elif ext == 'docx': return parse_word(file)
    elif ext == 'pdf': return parse_pdf(file)
    elif ext in ['txt', 'tsv']: return parse_csv(file)
    else: raise Exception(f"Format .{ext} tidak didukung")

# ==================== IMPORT KHUSUS: DATA MANPOWER SITE MELAK ====================
def import_data_manpower_melak(file):
    raw = file.read(); file.seek(0)
    xls = pd.ExcelFile(io.BytesIO(raw))
    sheet = 'DATABASE' if 'DATABASE' in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, header=None, skiprows=2)
    df.columns = df.iloc[0].astype(str).str.strip()
    df = df.iloc[1:].reset_index(drop=True)
    mask_skip = df['No'].astype(str).str.contains('DATA KARYAWAN|DEPARTEMENT|DEPARTEMEN|PLANT DEPARTEMENT', na=False, case=False)
    df = df[~mask_skip].copy()
    df = df[df['NRP'].notna()].copy()
    df = df[df['NRP'].astype(str).str.strip() != ''].copy()
    df = df[df['NRP'].astype(str) != 'nan'].copy()
    if df.empty: return 0, 0, ["Tidak ada baris data valid"]

    col_map = {
        'NRP': 'employee_id', 'Nama': 'full_name', 'Jabatan': 'job_position',
        'Departemen': 'organization', 'Golongan': 'grade', 'GOL GJ': 'grade',
        'No . HP': 'mobile_phone', 'No. HP': 'mobile_phone',
        'Tgl_Masuk Kerja (DOH)': 'join_date', 'Tgl. Mulai PKWT': 'sign_date',
        'Tgl. Akhir PKWT': 'end_date', 'Status kontrak': 'status_employee',
        'Pendidikan terakhir': 'pendidikan_terakhir', 'Asal Sekolah': 'asal_sekolah',
        'Jenis Kelamin': 'gender', 'Agama': 'religion', 'Golongan Darah': 'blood_type',
        'Tempat Lahir': 'birth_place', 'Tanggal Lahir': 'birth_date',
        'Status Keluarga': 'marital_status', 'No Rekening': 'bank_account',
        'Nama Rekening': 'bank_account_holder', 'Bank': 'bank_name',
        'Alamat Sesuai KTP': 'citizen_id_address', 'POH': 'poh', 'Status POH': 'status_poh',
        'Tempat Tinggal': 'residential_address', 'Tgl. Keluar': 'resign_date',
        'No KTP': 'no_ktp', 'NO KK': 'no_kk',
        'No_BPJS Kesehatan': 'bpjs_kesehatan', 'No_BPJS ketenaga kerjaan': 'bpjs_ketenagakerjaan',
        'Tgl. Awal Mine permit': 'mine_permit_start', 'Tgl. Akhir Mine Permit': 'mine_permit_end',
        'Status Mine Permit': 'status_mine_permit', 'Versality': 'versatility',
        'Versatility': 'versatility', 'Peringatan jatuh tempo PKWT': 'peringatan_pkwt',
        'Keterangan karyawan': 'keterangan',
    }

    sukses, gagal, errors = 0, 0, []
    for idx, row in df.iterrows():
        try:
            nrp = str(row.get('NRP', '')).strip()
            if nrp.lower() in ['nan', '', 'none']: continue
            data = {'employee_id': nrp}
            for xls_col, db_col in col_map.items():
                if xls_col in df.columns and db_col not in data:
                    val = row.get(xls_col)
                    if pd.notna(val) and str(val).strip().lower() not in ['nan', 'none', '']:
                        if isinstance(val, (datetime, pd.Timestamp)):
                            data[db_col] = val.strftime('%Y-%m-%d')
                        elif db_col in ['join_date','sign_date','end_date','resign_date','mine_permit_start','mine_permit_end']:
                            try: data[db_col] = pd.to_datetime(val).strftime('%Y-%m-%d')
                            except: data[db_col] = str(val).strip()
                        else: data[db_col] = str(val).strip()
            if not data.get('full_name'): continue
            c.execute("SELECT id FROM karyawan WHERE employee_id=?", (nrp,))
            exists = c.fetchone()
            if exists:
                set_clause = ", ".join([f"{k}=?" for k in data.keys() if k != 'employee_id'])
                vals = [v for k, v in data.items() if k != 'employee_id']
                vals.append(exists[0])
                c.execute(f"UPDATE karyawan SET {set_clause} WHERE id=?", vals)
            else:
                cols = ", ".join(data.keys()); phs = ", ".join(["?"] * len(data))
                c.execute(f"INSERT INTO karyawan ({cols}) VALUES ({phs})", list(data.values()))
            sukses += 1
        except Exception as e:
            gagal += 1; errors.append(f"Baris {idx+3}: {str(e)[:100]}")
    conn.commit()
    return sukses, gagal, errors

# ==================== PAYROLL HELPER ====================
def hitung_bpjs(gaji_pokok, tunjangan_tetap):
    upah = gaji_pokok + tunjangan_tetap
    upah_kes = min(upah, 12000000); upah_jp = min(upah, 11086300)
    return {
        'kes_k': round(upah_kes * 0.01, -2), 'kes_p': round(upah_kes * 0.04, -2),
        'jht_k': round(upah * 0.02, -2), 'jht_p': round(upah * 0.037, -2),
        'jp_k': round(upah_jp * 0.01, -2), 'jp_p': round(upah_jp * 0.02, -2),
        'jkk': round(upah * 0.0024, -2), 'jkm': round(upah * 0.003, -2),
        'jkp': round(upah * 0.0005, -2),
        'total_k': round(upah_kes*0.01, -2) + round(upah*0.02, -2) + round(upah_jp*0.01, -2),
        'total_p': round(upah_kes*0.04, -2) + round(upah*0.037, -2) + round(upah_jp*0.02, -2) + round(upah*0.0024, -2) + round(upah*0.003, -2) + round(upah*0.0005, -2)
    }

def hitung_pph21(bruto_bulanan, ptkp_setahun, iuran_pensiun_bulanan):
    biaya_jabatan = min(bruto_bulanan * 0.05, 500000)
    neto_bulanan = bruto_bulanan - biaya_jabatan - iuran_pensiun_bulanan
    neto_setahun = neto_bulanan * 12
    pkp = max(0, round(neto_setahun - ptkp_setahun, -3))
    if pkp <= 60000000: pph = pkp * 0.05
    elif pkp <= 250000000: pph = 60000000*0.05 + (pkp-60000000)*0.15
    elif pkp <= 500000000: pph = 60000000*0.05 + 190000000*0.15 + (pkp-250000000)*0.25
    elif pkp <= 5000000000: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + (pkp-500000000)*0.30
    else: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + 4500000000*0.30 + (pkp-5000000000)*0.35
    return max(0, round(pph / 12, -2))

PTKP_MAP = {"TK/0": 54000000, "TK/1": 58500000, "TK/2": 63000000, "TK/3": 67500000,
            "K/0": 58500000, "K/1": 63000000, "K/2": 67500000, "K/3": 72000000}

def render_crud_table(table_name, title, original_df):
    st.markdown(f"### 📋 Data {title}")
    edited_df = st.data_editor(original_df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button(f"💾 Simpan Perubahan {title}", type="primary", use_container_width=True):
        cur = conn.cursor()
        edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
        old_ids = set(original_df['id'].dropna().astype(int).tolist()) if not original_df.empty else set()
        new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
        for did in (old_ids - new_ids): cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        cols = [col for col in edited_df.columns if col != 'id']
        for _, row in edited_df.iterrows():
            vals = [None if pd.isna(row[col]) else row[col] for col in cols]
            if row['id'] == 0:
                ph = ", ".join(["?"] * len(cols)); cur.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})", tuple(vals))
            else:
                set_c = ", ".join([f"{col}=?" for col in cols]); cur.execute(f"UPDATE {table_name} SET {set_c} WHERE id=?", tuple(vals) + (row['id'],))
        conn.commit(); st.success(f"✅ Perubahan data {title} berhasil disimpan!"); st.rerun()

# ==================== SEED USER ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hash_password("admin123"), "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("hrd", hash_password("hrd123"), "HRD Staff", "hrd"))
    conn.commit()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA & ASET SUPER v3.0</h1><p>Sistem Manajemen SDM, Absensi, Payroll, GA & Utility<br><span style="font-size:0.8em;">Terintegrasi DATA MANPOWER SITE MELAK & Utility Melak</span></p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username"); p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**  •  **hrd** / **hrd123**")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p><p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = ["🏠 Dashboard HRIS", "👥 Data Karyawan", "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"]
    if st.session_state.role == "admin": menu += ["👤 Manajemen User", "📝 Log Aktivitas"]
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    
    st.markdown("---")
    tampilkan_flyer = st.checkbox("📢 Tampilkan Flyer Lowongan", value=True)
    
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================

if pilihan == "🏠 Dashboard HRIS" and tampilkan_flyer:
    show_floating_flyers()

if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f'<div class="main-header"><h1>⚡ HRIS, GA & ASET DASHBOARD</h1><p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime("%d/%m/%Y, %H.%M.%S")}</p></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h3>👥 KPI HRIS & GENERAL AFFAIR</h3></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None'").fetchone()[0]
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    lowongan_buka = c.execute("SELECT SUM(jumlah_dibutuhkan) FROM lowongan WHERE status='Buka'").fetchone()[0] or 0
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    tgl_skrg = datetime.now().strftime("%Y-%m-%d")
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

    st.markdown('<div class="section-header"><h3>📢 Detail Kebutuhan (Open Vacant)</h3></div>', unsafe_allow_html=True)
    df_vacant = pd.read_sql_query("SELECT posisi AS 'Posisi / Level', departemen AS 'Departemen', jumlah_dibutuhkan AS 'Jumlah Dibutuhkan', deskripsi AS 'Keterangan' FROM lowongan WHERE status='Buka' ORDER BY id DESC", conn)
    if not df_vacant.empty: st.dataframe(df_vacant, use_container_width=True, hide_index=True)
    else: st.info("✅ Tidak ada posisi yang sedang open vacant saat ini.")

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

    st.markdown('<div class="section-header"><h3>📅 Absensi Hari Ini</h3></div>', unsafe_allow_html=True)
    hadir = c.execute("SELECT COUNT(*) FROM absensi WHERE tanggal=? AND status='Hadir'", (tgl_skrg,)).fetchone()[0]
    telat = c.execute("SELECT COUNT(*) FROM absensi WHERE tanggal=? AND terlambat_menit > 0", (tgl_skrg,)).fetchone()[0]
    izin = c.execute("SELECT COUNT(*) FROM absensi WHERE tanggal=? AND status='Izin'", (tgl_skrg,)).fetchone()[0]
    sakit = c.execute("SELECT COUNT(*) FROM absensi WHERE tanggal=? AND status='Sakit'", (tgl_skrg,)).fetchone()[0]
    cuti_menunggu = c.execute("SELECT COUNT(*) FROM cuti WHERE status='Menunggu'").fetchone()[0]

    html = '<div class="metric-grid">'
    html += metric_card("✅ Hadir", str(hadir), "hari ini", "card-green")
    html += metric_card("⚠️ Terlambat", str(telat), "hari ini", "card-orange")
    html += metric_card("📝 Izin", str(izin), "hari ini", "card-blue")
    html += metric_card("🤒 Sakit", str(sakit), "hari ini", "card-red")
    html += metric_card("🏖️ Cuti Menunggu", str(cuti_menunggu), "approval", "card-purple")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>📊 Analitik</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👔 Job Position (Aktif)**")
        df_jab = pd.read_sql_query("SELECT job_position as JABATAN, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND job_position IS NOT NULL GROUP BY job_position ORDER BY JML DESC LIMIT 15", conn)
        if not df_jab.empty:
            chart = alt.Chart(df_jab).mark_bar(cornerRadiusTopRight=10).encode(
                x=alt.X('JML:Q', title='Jumlah'),
                y=alt.Y('JABATAN:N', sort='-x', title=''),
                color=alt.Color('JML:Q', scale=alt.Scale(scheme='blues'), legend=None)
            ).properties(height=max(300, len(df_jab)*35))
            st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("**🏢 Organization (Aktif)**")
        df_div = pd.read_sql_query("SELECT organization as DIVISI, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND organization IS NOT NULL GROUP BY organization ORDER BY JML DESC", conn)
        if not df_div.empty:
            chart = alt.Chart(df_div).mark_arc(innerRadius=60).encode(
                theta=alt.Theta('JML:Q'),
                color=alt.Color('DIVISI:N', scale=alt.Scale(scheme='purples')),
                tooltip=['DIVISI', 'JML']
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

# (Menu lainnya sama persis seperti script sebelumnya)
