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


# ==================== FITUR FLYER MELAYANG-LAYANG ====================
def get_image_base64(path_options):
    for path in path_options:
        try:
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            continue
    return ""

def show_floating_flyers():
    img_mekanik_b64 = get_image_base64(["flyer_mekanik.png", "flyer_mekanik.png.jpeg", "flyer_mekanik.jpeg", "flyer_mekanik.jpg"])
    img_warehouse_b64 = get_image_base64(["flyer_warehouse.png", "flyer_warehouse.png.jpeg", "flyer_warehouse.jpeg", "flyer_warehouse.jpg"])
    
    src_mekanik = f"data:image/png;base64,{img_mekanik_b64}" if img_mekanik_b64 else "https://placehold.co/400x600/FFD700/000000.png?text=Flyer+Mekanik"
    src_warehouse = f"data:image/png;base64,{img_warehouse_b64}" if img_warehouse_b64 else "https://placehold.co/400x600/1e3a8a/FFFFFF.png?text=Flyer+Warehouse"
    
    html_flyers = """
    <style>
        @keyframes floatBounce {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        .flyer-container {
            position: fixed;
            right: 20px;
            z-index: 999;
            width: 260px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
            animation: floatBounce 4s ease-in-out infinite;
            transition: transform 0.3s;
            background-color: #fff;
            padding: 6px;
            border: 2px solid #f59e0b;
        }
        .flyer-container:hover { animation-play-state: paused; transform: scale(1.05); z-index: 1000; }
        .flyer-top { top: 150px; animation-delay: 0s; }
        .flyer-bottom { top: 550px; animation-delay: 2s; }
        @media (max-width: 1024px) { .flyer-container { display: none; } }
    </style>
    """
    
    html_flyers += f'<div class="flyer-container flyer-top"><img src="{src_mekanik}" style="width:100%; border-radius:8px;"></div>'
    html_flyers += f'<div class="flyer-container flyer-bottom"><img src="{src_warehouse}" style="width:100%; border-radius:8px;"></div>'
    
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

# ==================== 2. DATA KARYAWAN ====================
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1><p>Terintegrasi Template DATA MANPOWER SITE MELAK</p></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Tambah", "📋 Daftar", "🔍 Detail"])

    with tab1:
        with st.form("form_karyawan", clear_on_submit=True):
            st.subheader("📋 Data Karyawan")
            col1, col2, col3 = st.columns(3)
            with col1:
                employee_id = st.text_input("Employee ID / NRP *")
                full_name = st.text_input("Full Name *")
                barcode = st.text_input("Barcode")
                organization = st.text_input("Organization")
                job_position = st.text_input("Job Position")
            with col2:
                job_level = st.selectbox("Job Level", ["staff", "Non - Staff", "Supervisor", "Foreman", "Manager"])
                join_date = st.date_input("Join Date", date.today())
                resign_date = st.text_input("Resign Date (kosong jika aktif)", value="")
                status_employee = st.selectbox("Status Employee", ["Contract", "Tetap", "Probation", "Magang"])
                end_date = st.date_input("End Date PKWT", date.today() + timedelta(days=365))
            with col3:
                email = st.text_input("Email")
                mobile_phone = st.text_input("Mobile Phone")
                phone = st.text_input("Phone")
                branch_name = st.text_input("Branch Name", value="PT. United Equipment Indonesia Cab Melak")
                parent_branch_name = st.text_input("Parent Branch Name", value="PT. United Equipment Indonesia")

            col4, col5, col6 = st.columns(3)
            with col4:
                birth_place = st.text_input("Birth Place")
                birth_date = st.date_input("Birth Date", date(1995, 1, 1))
                gender = st.selectbox("Gender", ["Male", "Female"])
                religion = st.selectbox("Religion", ["Islam","Christian","Catholic","Hindu","Buddha","Konghucu"])
                marital_status = st.selectbox("Marital Status", ["Single","Married","Widower","Widow"])
            with col5:
                blood_type = st.selectbox("Blood Type", ["","A","B","AB","O"])
                nationality_code = st.text_input("Nationality Code", value="IDN")
                citizen_id_address = st.text_area("Alamat Sesuai KTP")
                residential_address = st.text_area("Tempat Tinggal")
                no_ktp = st.text_input("No KTP")
            with col6:
                npwp = st.text_input("NPWP")
                no_kk = st.text_input("No KK")
                nik_npwp_16 = st.text_input("NIK (NPWP 16 Digit)")
                ptkp_status = st.selectbox("PTKP Status", list(PTKP_MAP.keys()))
                employee_tax_status = st.selectbox("Employee Tax Status", ["Pegawai Tetap","Pegawai Tidak Tetap","Bukan Pegawai"])

            st.markdown("**🎓 Pendidikan & Versatility**")
            col7, col8, col9 = st.columns(3)
            with col7:
                pendidikan_terakhir = st.selectbox("Pendidikan Terakhir", ["","SD","SMP","SMA/SMU","SMK","D3","D4","S1","S2","S3"])
                asal_sekolah = st.text_input("Asal Sekolah")
            with col8:
                versatility = st.text_input("Versatility (DT, DZR, EX, MG, dll)")
                grade = st.selectbox("Golongan (GOL GJ)", ["","I","II","III","IV","V","Staff"])
            with col9:
                divisi = st.selectbox("Divisi", ["PRODUKSI","PLANT","ENGINEERING","LOGISTIC","HRGA","PRODUCT SUPPORT","AFTER MARKET & INVENTORY WAREHOUSE","SALES & OPERATION","FINANCE","GA","PARTS","Adm.PS"])

            st.markdown("**🏦 Bank & BPJS**")
            col10, col11, col12 = st.columns(3)
            with col10:
                bank_name = st.selectbox("Bank Name", ["BCA","Mandiri","BNI","BRI","CIMB","Permata"])
                bank_account = st.text_input("No Rekening")
                bank_account_holder = st.text_input("Nama Rekening")
            with col11:
                bpjs_ketenagakerjaan = st.text_input("BPJS Ketenagakerjaan")
                bpjs_kesehatan = st.text_input("BPJS Kesehatan")
                currency = st.text_input("Currency", value="IDR")
            with col12:
                manager = st.text_input("Manager")
                approval_line = st.text_input("Approval Line")
                payment_schedule = st.text_input("Payment Schedule")

            st.markdown("**⛏️ Mine Permit & POH**")
            col13, col14, col15 = st.columns(3)
            with col13:
                poh = st.text_input("POH")
                status_poh = st.text_input("Status POH")
            with col14:
                mine_permit_start = st.date_input("Tgl Awal Mine Permit", date.today())
                mine_permit_end = st.date_input("Tgl Akhir Mine Permit", date.today() + timedelta(days=365))
            with col15:
                status_mine_permit = st.selectbox("Status Mine Permit", ["","Aktif","Akan Habis","Habis"])
                peringatan_pkwt = st.text_input("Peringatan Jatuh Tempo PKWT")

            col16, col17 = st.columns(2)
            with col16: gaji = st.number_input("Gaji Pokok (Rp)", min_value=0.0, step=100000.0)
            with col17: keterangan = st.text_input("Keterangan Karyawan")

            if st.form_submit_button("💾 Simpan"):
                if employee_id and full_name:
                    try:
                        c.execute('''INSERT INTO karyawan (
                            employee_id, full_name, barcode, organization, job_position, job_level,
                            join_date, resign_date, status_employee, end_date, email, birth_date, birth_place,
                            citizen_id_address, residential_address, npwp, ptkp_status, employee_tax_status,
                            bank_name, bank_account, bank_account_holder, bpjs_ketenagakerjaan, bpjs_kesehatan,
                            nik_npwp_16, mobile_phone, phone, branch_name, parent_branch_name, religion, gender,
                            marital_status, blood_type, nationality_code, currency, payment_schedule, approval_line,
                            manager, grade, tin, divisi, keterangan, versatility, pendidikan_terakhir, asal_sekolah,
                            no_ktp, no_kk, poh, status_poh, mine_permit_start, mine_permit_end, status_mine_permit,
                            peringatan_pkwt, gaji)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                            (employee_id, full_name, barcode, organization, job_position, job_level,
                             str(join_date), resign_date, status_employee, str(end_date), email,
                             str(birth_date), birth_place, citizen_id_address, residential_address, npwp,
                             ptkp_status, employee_tax_status, bank_name, bank_account, bank_account_holder,
                             bpjs_ketenagakerjaan, bpjs_kesehatan, nik_npwp_16, mobile_phone, phone,
                             branch_name, parent_branch_name, religion, gender, marital_status, blood_type,
                             nationality_code, currency, payment_schedule, approval_line, manager, grade, "",
                             divisi, keterangan, versatility, pendidikan_terakhir, asal_sekolah, no_ktp, no_kk,
                             poh, status_poh, str(mine_permit_start), str(mine_permit_end), status_mine_permit,
                             peringatan_pkwt, gaji))
                        conn.commit()
                        st.success(f"✅ Karyawan {full_name} disimpan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Employee ID sudah ada")
                else:
                    st.warning("Employee ID & Full Name wajib diisi")

    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM karyawan ORDER BY id DESC", conn)
        st.dataframe(df_k, use_container_width=True, hide_index=True)
        if not df_k.empty:
            st.download_button("📥 Export CSV", df_k.to_csv(index=False).encode(), "karyawan.csv", "text/csv")

    with tab3:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan ORDER BY full_name", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            pilih = st.selectbox("🔍 Pilih Karyawan", list(opsi.keys()))
            kid = opsi[pilih]
            d = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(kid,)).iloc[0]

            html = '<div class="metric-grid">'
            html += metric_card("Job Position", d['job_position'] or "-", "", "card-blue")
            html += metric_card("Organization", d['organization'] or "-", "", "card-purple")
            html += metric_card("Status", d['status_employee'] or "-", "", "card-green" if not d['resign_date'] else "card-red")
            html += metric_card("Gaji", format_rp(d['gaji']), "", "card-gold")
            html += metric_card("Umur", f"{hitung_umur(d['birth_date']) or '-'} thn", d['birth_date'] or "-", "card-teal")
            html += metric_card("Masa Kerja", hitung_masa_kerja(d['join_date']), d['join_date'] or "-", "card-orange")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown(f"""
            **NRP**: {d['employee_id']} | **Gender**: {d['gender'] or '-'} | **Agama**: {d['religion'] or '-'}  
            **Email**: {d['email'] or '-'} | **HP**: {d['mobile_phone'] or '-'}  
            **Lahir**: {d['birth_place'] or '-'}, {d['birth_date'] or '-'}  
            **Alamat KTP**: {d['citizen_id_address'] or '-'}  
            **Tempat Tinggal**: {d['residential_address'] or '-'}  
            **Bank**: {d['bank_name'] or '-'} - {d['bank_account'] or '-'}  
            **NPWP**: {d['npwp'] or '-'} | **PTKP**: {d['ptkp_status'] or '-'}  
            **No KTP**: {d['no_ktp'] or '-'} | **No KK**: {d['no_kk'] or '-'}  
            **Pendidikan**: {d['pendidikan_terakhir'] or '-'} — {d['asal_sekolah'] or '-'}  
            **Versatility**: {d['versatility'] or '-'}  
            **BPJS Kes**: {d['bpjs_kesehatan'] or '-'} | **BPJS TK**: {d['bpjs_ketenagakerjaan'] or '-'}  
            **Mine Permit**: {d['mine_permit_start'] or '-'} s/d {d['mine_permit_end'] or '-'} ({d['status_mine_permit'] or '-'})  
            **POH**: {d['poh'] or '-'} ({d['status_poh'] or '-'})  
            **Join**: {d['join_date']} | **End PKWT**: {d['end_date']} | **Resign**: {d['resign_date'] or '-'}
            """)

# ==================== 3. ABSENSI ====================
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["✍️ Input", "📋 Rekap", "📊 Statistik"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None' ORDER BY full_name", conn)
        if df_k.empty:
            st.warning("Belum ada karyawan aktif")
        else:
            st.markdown("**⚡ Input Cepat (Bulk)**")
            col1, col2 = st.columns(2)
            with col1:
                tgl_bulk = st.date_input("Tanggal Bulk", date.today(), key="tgl_bulk")
                status_bulk = st.selectbox("Status Default", ["Hadir","Izin","Sakit","Cuti","Dinas Luar"], key="st_bulk")
            with col2:
                jam_m = st.time_input("Jam Masuk", datetime.strptime("08:00","%H:%M").time(), key="jm_bulk")
                jam_k = st.time_input("Jam Keluar", datetime.strptime("17:00","%H:%M").time(), key="jk_bulk")

            if st.button("📥 Input Massal Semua Karyawan Aktif"):
                for _, r in df_k.iterrows():
                    exist = c.execute("SELECT id FROM absensi WHERE karyawan_id=? AND tanggal=?", (r['id'], str(tgl_bulk))).fetchone()
                    if not exist:
                        c.execute("""INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit)
                                     VALUES (?,?,?,?,?,?,?)""",
                                  (r['id'], str(tgl_bulk), str(jam_m), str(jam_k), status_bulk, "Bulk input", 0))
                conn.commit()
                st.success(f"✅ Absensi massal {len(df_k)} karyawan disimpan!")
                st.rerun()

            st.markdown("---")
            st.markdown("**✍️ Input Individual**")
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            col3, col4 = st.columns(2)
            with col3:
                pilih = st.selectbox("Karyawan", list(opsi.keys()), key="ind_kar")
                tgl = st.date_input("Tanggal", date.today(), key="ind_tgl")
            with col4:
                jm = st.time_input("Jam Masuk", datetime.strptime("08:00","%H:%M").time(), key="ind_jm")
                jk = st.time_input("Jam Keluar", datetime.strptime("17:00","%H:%M").time(), key="ind_jk")

            status = st.selectbox("Status", ["Hadir","Izin","Sakit","Cuti","Alpha","Dinas Luar"])
            ket = st.text_input("Keterangan")

            jm_dt = datetime.combine(tgl, jm)
            batas = datetime.combine(tgl, datetime.strptime("08:15","%H:%M").time())
            telat = max(0, int((jm_dt - batas).total_seconds()/60)) if jm_dt > batas else 0
            if telat > 0: st.warning(f"⚠️ Terlambat **{telat} menit**")

            if st.button("💾 Simpan Absensi"):
                c.execute("""INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit)
                             VALUES (?,?,?,?,?,?,?)""",
                          (opsi[pilih], str(tgl), str(jm), str(jk), status, ket, telat))
                conn.commit()
                st.success("✅ Absensi disimpan!")
                st.rerun()

    with tab2:
        col1, col2 = st.columns(2)
        with col1: tgl_dari = st.date_input("Dari", date.today()-timedelta(days=30))
        with col2: tgl_sampai = st.date_input("Sampai", date.today())
        df_a = pd.read_sql_query("""
            SELECT a.tanggal, k.employee_id, k.full_name, k.job_position, a.jam_masuk, a.jam_keluar,
                   a.status, a.terlambat_menit, a.keterangan
            FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id
            WHERE a.tanggal BETWEEN ? AND ?
            ORDER BY a.tanggal DESC, k.full_name
        """, conn, params=(str(tgl_dari), str(tgl_sampai)))
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        if not df_a.empty:
            st.download_button("📥 Export CSV", df_a.to_csv(index=False).encode(), "absensi.csv", "text/csv")

    with tab3:
        periode = datetime.now().strftime("%Y-%m")
        df_stat = pd.read_sql_query("""
            SELECT k.full_name, k.job_position,
                   SUM(CASE WHEN a.status='Hadir' THEN 1 ELSE 0 END) as hadir,
                   SUM(CASE WHEN a.status='Izin' THEN 1 ELSE 0 END) as izin,
                   SUM(CASE WHEN a.status='Sakit' THEN 1 ELSE 0 END) as sakit,
                   SUM(CASE WHEN a.status='Alpha' THEN 1 ELSE 0 END) as alpha,
                   SUM(a.terlambat_menit) as total_telat
            FROM karyawan k LEFT JOIN absensi a ON k.id = a.karyawan_id AND substr(a.tanggal,1,7) = ?
            WHERE (k.resign_date IS NULL OR k.resign_date='')
            GROUP BY k.full_name ORDER BY hadir DESC
        """, conn, params=(periode,))
        st.dataframe(df_stat, use_container_width=True, hide_index=True)

# ==================== 4. CUTI ====================
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Ajukan", "📋 Approval"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_cuti"):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                jenis = st.selectbox("Jenis Cuti", ["Cuti Tahunan","Cuti Sakit","Cuti Melahirkan","Cuti Menikah","Cuti Duka","Izin","Dinas Luar"])
                col1, col2 = st.columns(2)
                with col1:
                    tm = st.date_input("Mulai", date.today())
                    periode_ke = st.number_input("Periode Cuti ke-", 1, 5, 1)
                with col2:
                    ts = st.date_input("Selesai", date.today())
                    status_pengambilan = st.selectbox("Status", ["Diambil", "Diuangkan"])
                alasan = st.text_area("Alasan")
                if st.form_submit_button("📤 Ajukan"):
                    lama = (ts - tm).days + 1
                    c.execute("""INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai,
                                 lama_hari, alasan, status, periode_cuti_ke, status_pengambilan, actual_cuti, saldo_cuti)
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                              (opsi[pilih], jenis, str(tm), str(ts), lama, alasan, "Menunggu",
                               periode_ke, status_pengambilan, str(tm), 12))
                    conn.commit()
                    st.success(f"✅ Pengajuan cuti {lama} hari terkirim!")
                    st.rerun()

    with tab2:
        df_cuti = pd.read_sql_query("""
            SELECT c.id, k.employee_id, k.full_name, c.jenis_cuti, c.tanggal_mulai, c.tanggal_selesai,
                   c.lama_hari, c.periode_cuti_ke, c.status_pengambilan, c.status, c.alasan
            FROM cuti c JOIN karyawan k ON c.karyawan_id = k.id ORDER BY c.id DESC
        """, conn)
        if not df_cuti.empty:
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("⏳ Menunggu", len(df_cuti[df_cuti['status']=="Menunggu"]))
            with col2: st.metric("✅ Disetujui", len(df_cuti[df_cuti['status']=="Disetujui"]))
            with col3: st.metric("❌ Ditolak", len(df_cuti[df_cuti['status']=="Ditolak"]))
            st.dataframe(df_cuti, use_container_width=True, hide_index=True)

            menunggu = df_cuti[df_cuti['status']=="Menunggu"]
            if not menunggu.empty:
                opsi = {f"#{r['id']} - {r['full_name']} ({r['lama_hari']}h)": r['id'] for _, r in menunggu.iterrows()}
                pilih = st.selectbox("Approval", list(opsi.keys()))
                cid = opsi[pilih]
                colA, colB = st.columns(2)
                with colA:
                    if st.button("✅ Setujui"):
                        c.execute("UPDATE cuti SET status='Disetujui', approved_by=?, approved_at=? WHERE id=?",
                                  (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M"), cid))
                        conn.commit(); st.rerun()
                with colB:
                    if st.button("❌ Tolak"):
                        c.execute("UPDATE cuti SET status='Ditolak', approved_by=?, approved_at=? WHERE id=?",
                                  (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M"), cid))
                        conn.commit(); st.rerun()
        else:
            st.info("Belum ada pengajuan cuti")

# ==================== 5. PAYROLL ====================
elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🧮 Proses", "📋 Riwayat", "🖨️ Slip"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name, gaji, ptkp_status, job_position FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND gaji > 0 ORDER BY full_name", conn)
        if df_k.empty:
            st.warning("Belum ada karyawan aktif dengan gaji.")
        else:
            col1, col2 = st.columns(2)
            with col1: bulan = st.selectbox("Bulan", list(range(1,13)), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
            with col2: tahun = st.number_input("Tahun", 2020, 2030, datetime.now().year)
            periode = f"{tahun}-{bulan:02d}"

            preview = []
            for _, r in df_k.iterrows():
                gaji_pokok = r['gaji']; tunj_jab = round(gaji_pokok * 0.15, -2)
                bruto = gaji_pokok + tunj_jab + 500000 + 600000
                bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                pph = hitung_pph21(bruto, PTKP_MAP.get(r['ptkp_status'] or "TK/0", 54000000), bpjs['total_k'])
                bersih = bruto - bpjs['total_k'] - pph
                preview.append({'Nama': r['full_name'], 'Jabatan': r['job_position'],
                                'Gaji Pokok': format_rp(gaji_pokok), 'Bruto': format_rp(bruto),
                                'BPJS': format_rp(bpjs['total_k']), 'PPh 21': format_rp(pph),
                                'Take Home': format_rp(bersih)})
            st.dataframe(pd.DataFrame(preview), use_container_width=True, hide_index=True)

            if st.button("🚀 Proses Payroll"):
                for _, r in df_k.iterrows():
                    gaji_pokok = r['gaji']; tunj_jab = round(gaji_pokok * 0.15, -2)
                    bruto = gaji_pokok + tunj_jab + 500000 + 600000
                    bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                    pph = hitung_pph21(bruto, PTKP_MAP.get(r['ptkp_status'] or "TK/0", 54000000), bpjs['total_k'])
                    bersih = bruto - bpjs['total_k'] - pph
                    c.execute("DELETE FROM payroll WHERE karyawan_id=? AND periode=?", (r['id'], periode))
                    c.execute('''INSERT INTO payroll (karyawan_id, periode, gaji_pokok, tunjangan_jabatan,
                                 tunjangan_transport, tunjangan_makan, bpjs_kesehatan_karyawan, bpjs_kesehatan_perusahaan,
                                 bpjs_jht_karyawan, bpjs_jht_perusahaan, bpjs_jp_karyawan, bpjs_jp_perusahaan,
                                 bpjs_jkk, bpjs_jkm, bpjs_jkp, pph21, total_penghasilan_bruto, total_potongan,
                                 gaji_bersih, status, tanggal_proses) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (r['id'], periode, gaji_pokok, tunj_jab, 500000, 600000,
                               bpjs['kes_k'], bpjs['kes_p'], bpjs['jht_k'], bpjs['jht_p'],
                               bpjs['jp_k'], bpjs['jp_p'], bpjs['jkk'], bpjs['jkm'], bpjs['jkp'],
                               pph, bruto, bpjs['total_k'] + pph, bersih, "Final",
                               datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success(f"🎉 Payroll {periode} berhasil!"); st.balloons(); st.rerun()

    with tab2:
        df_p = pd.read_sql_query("""
            SELECT p.periode, k.employee_id, k.full_name, p.gaji_pokok,
                   p.total_penghasilan_bruto as bruto, p.pph21, p.gaji_bersih as take_home
            FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id
            ORDER BY p.periode DESC, k.full_name
        """, conn)
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    with tab3:
        periode_list = pd.read_sql_query("SELECT DISTINCT periode FROM payroll ORDER BY periode DESC", conn)
        if not periode_list.empty:
            pilih_p = st.selectbox("Periode", periode_list['periode'].tolist())
            df_slip = pd.read_sql_query("""
                SELECT p.*, k.employee_id, k.full_name, k.job_position, k.organization, k.bank_name, k.bank_account
                FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id WHERE p.periode=? ORDER BY k.full_name
            """, conn, params=(pilih_p,))
            if not df_slip.empty:
                opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_slip.iterrows()}
                pilih_k = st.selectbox("Karyawan", list(opsi.keys()))
                row = df_slip[df_slip['id'] == opsi[pilih_k]].iloc[0]
                html = f"""
                <div class="payroll-slip">
                    <h3>🏢 SLIP GAJI — {pilih_p}</h3>
                    <p><b>NRP:</b> {row['employee_id']} | <b>Nama:</b> {row['full_name']}</p>
                    <p><b>Jabatan:</b> {row['job_position']} | <b>Organization:</b> {row['organization']}</p>
                    <p><b>Bank:</b> {row['bank_name']} - {row['bank_account']}</p>
                    <h4>💰 Penghasilan</h4>
                    <div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(row['gaji_pokok'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Jabatan</span><span>{format_rp(row['tunjangan_jabatan'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Transport</span><span>{format_rp(row['tunjangan_transport'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Makan</span><span>{format_rp(row['tunjangan_makan'])}</span></div>
                    <div class="payroll-row"><b>Total Bruto</b><b>{format_rp(row['total_penghasilan_bruto'])}</b></div>
                    <h4>📉 Potongan</h4>
                    <div class="payroll-row"><span>BPJS Kesehatan</span><span>-{format_rp(row['bpjs_kesehatan_karyawan'])}</span></div>
                    <div class="payroll-row"><span>BPJS JHT</span><span>-{format_rp(row['bpjs_jht_karyawan'])}</span></div>
                    <div class="payroll-row"><span>BPJS JP</span><span>-{format_rp(row['bpjs_jp_karyawan'])}</span></div>
                    <div class="payroll-row"><span>PPh 21</span><span>-{format_rp(row['pph21'])}</span></div>
                    <div class="payroll-row"><b>Total Potongan</b><b>-{format_rp(row['total_potongan'])}</b></div>
                    <div class="payroll-total"><span>GAJI BERSIH</span><span>{format_rp(row['gaji_bersih'])}</span></div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
                st.download_button("📥 Download Slip (HTML)", html, f"slip_{row['employee_id']}_{pilih_p}.html", "text/html")
        else:
            st.info("Belum ada payroll")

# ==================== 6. REKRUTMEN ====================
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input", "📋 Pipeline", "📢 Open Vacant"])

    with tab1:
        with st.form("form_kandidat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *")
                posisi = st.text_input("Posisi Dilamar")
                telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email")
                sumber = st.selectbox("Sumber", ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair","Import Open Interview"])
            with col2:
                tgl_lamar = st.date_input("Tanggal Lamar", date.today())
                status = st.selectbox("Status", ["Proses","Wawancara","Diterima","Ditolak"])
                tgl_interview = st.date_input("Tanggal Interview")
                jam_interview = st.time_input("Jam Interview", datetime.strptime("09:00", "%H:%M").time())
                status_berkas = st.selectbox("Kelengkapan Berkas", ["Lengkap", "Kurang", "Belum Ada"])
            catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    jadwal_str = f"{tgl_interview} {jam_interview.strftime('%H:%M')}"
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,
                                 catatan,jadwal_interview,status_berkas,tgl_interview) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                              (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan,
                               jadwal_str, status_berkas, str(tgl_interview)))
                    conn.commit()
                    log_aksi(st.session_state.username, "TAMBAH_KANDIDAT", nama)
                    st.success(f"✅ Kandidat {nama} disimpan!")
                    st.rerun()

    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        if not df_k.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total", str(len(df_k)), "", "card-blue")
            html += metric_card("Diterima", str(len(df_k[df_k['status']=='Diterima'])), "", "card-green")
            html += metric_card("Ditolak", str(len(df_k[df_k['status']=='Ditolak'])), "", "card-red")
            html += metric_card("Proses", str(len(df_k[df_k['status']=='Proses'])), "", "card-gold")
            html += metric_card("Interview", str(len(df_k[df_k['status']=='Wawancara'])), "", "card-purple")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            filter_status = st.selectbox("🔍 Filter:", ["Semua", "Proses", "Wawancara", "Diterima", "Ditolak"])
            df_filtered = df_k if filter_status == "Semua" else df_k[df_k['status'] == filter_status]

            def highlight_diterima(row):
                return ['background-color: #d4edda'] * len(row) if row['status'] == 'Diterima' else [''] * len(row)

            st.dataframe(df_filtered[['id','nama','posisi_dilamar','status','jadwal_interview','hasil_interview','hasil_mcu','status_berkas']].style.apply(highlight_diterima, axis=1), use_container_width=True, hide_index=True)

            opsi_kandidat = {f"{row['id']} - {row['nama']} ({row['posisi_dilamar']})": row['id'] for _, row in df_filtered.iterrows()}
            if opsi_kandidat:
                pilihan_edit = st.selectbox("Pilih Kandidat:", ["-- Pilih --"] + list(opsi_kandidat.keys()))
                if pilihan_edit != "-- Pilih --":
                    kandidat_id = opsi_kandidat[pilihan_edit]
                    s = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(kandidat_id,)).iloc[0]
                    with st.form("form_pipeline"):
                        st.markdown(f"**✏️ Pipeline: {s['nama']}**")
                        colA, colB = st.columns(2)
                        with colA:
                            e_nama = st.text_input("Nama", value=s['nama'])
                            e_posisi = st.text_input("Posisi", value=s['posisi_dilamar'])
                        with colB:
                            list_status = ["Proses","Wawancara","Diterima","Ditolak"]
                            e_status = st.selectbox("Status", list_status, index=list_status.index(s['status']) if s['status'] in list_status else 0)
                        st.markdown("**Tahapan Seleksi**")
                        cA, cB = st.columns(2)
                        with cA:
                            e_tgl_int = st.text_input("Tgl Interview", value=s['tgl_interview'] or "")
                            e_hasil_int = st.selectbox("Hasil Interview", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_interview']) if s['hasil_interview'] in ["", "OK", "FAIL", "N/A"] else 0)
                            e_tgl_gt = st.text_input("Tgl Ground Test", value=s['tgl_ground_test'] or "")
                            e_hasil_gt = st.selectbox("Hasil GT", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_ground_test']) if s['hasil_ground_test'] in ["", "OK", "FAIL", "N/A"] else 0)
                        with cB:
                            e_tgl_ind = st.text_input("Tgl Induksi", value=s['tgl_induksi'] or "")
                            e_tgl_mcu = st.text_input("Tgl MCU", value=s['tgl_mcu'] or "")
                            e_hasil_mcu = st.selectbox("Hasil MCU", ["", "OK", "FAIL", "N/A"], index=["", "OK", "FAIL", "N/A"].index(s['hasil_mcu']) if s['hasil_mcu'] in ["", "OK", "FAIL", "N/A"] else 0)
                            e_tmk = st.text_input("TMK", value=s['tmk'] or "")
                        if st.form_submit_button("💾 Simpan", type="primary"):
                            c.execute('''UPDATE kandidat SET nama=?, posisi_dilamar=?, status=?, tgl_interview=?, hasil_interview=?,
                                         tgl_ground_test=?, hasil_ground_test=?, tgl_induksi=?, tgl_mcu=?, hasil_mcu=?, tmk=? WHERE id=?''',
                                      (e_nama, e_posisi, e_status, e_tgl_int, e_hasil_int, e_tgl_gt, e_hasil_gt, e_tgl_ind, e_tgl_mcu, e_hasil_mcu, e_tmk, kandidat_id))
                            conn.commit(); st.success("✅ Diperbarui!"); st.rerun()
                    if st.button(f"🗑️ Hapus {s['nama']}", type="primary"):
                        c.execute("DELETE FROM kandidat WHERE id=?", (kandidat_id,))
                        conn.commit(); st.rerun()
        else:
            st.info("Belum ada kandidat")

    with tab3:
        st.markdown("### 📢 Open Vacant")
        with st.form("form_lowongan", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                vac_posisi = st.text_input("Posisi *")
                vac_dept = st.selectbox("Departemen", ["PRODUCT SUPPORT","AFTER MARKET & INVENTORY WAREHOUSE","PRODUKSI","PLANT","ENGINEERING","LOGISTIC","HRGA","FINANCE","GA","PARTS","Adm.PS","Lainnya"])
            with col2:
                vac_jumlah = st.number_input("Jumlah *", min_value=1, step=1, value=1)
                vac_status = st.selectbox("Status", ["Buka", "Tutup"])
            with col3:
                vac_tgl_buka = st.date_input("Tgl Dibuka", date.today())
                vac_tgl_tutup = st.date_input("Batas", date.today() + timedelta(days=30))
            vac_deskripsi = st.text_area("Kualifikasi")
            if st.form_submit_button("💾 Tambah", type="primary"):
                if vac_posisi:
                    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup) VALUES (?,?,?,?,?,?,?)''',
                              (vac_posisi, vac_dept, vac_jumlah, vac_status, vac_deskripsi, str(vac_tgl_buka), str(vac_tgl_tutup)))
                    conn.commit(); st.rerun()

        st.markdown("---")
        df_vac = pd.read_sql_query("SELECT * FROM lowongan ORDER BY id DESC", conn)
        if not df_vac.empty:
            for _, r in df_vac.iterrows():
                pelamar = c.execute("SELECT COUNT(*) FROM kandidat WHERE posisi_dilamar=?", (r['posisi'],)).fetchone()[0]
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
                colA, colB, _ = st.columns([1, 1, 4])
                with colA:
                    if r['status'] == 'Buka':
                        if st.button(f"🔒 Tutup (ID:{r['id']})", key=f"t_{r['id']}"):
                            c.execute("UPDATE lowongan SET status='Tutup' WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                    else:
                        if st.button(f"🔓 Buka (ID:{r['id']})", key=f"b_{r['id']}"):
                            c.execute("UPDATE lowongan SET status='Buka' WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                with colB:
                    if st.button(f"🗑️ Hapus (ID:{r['id']})", key=f"h_{r['id']}"):
                        c.execute("DELETE FROM lowongan WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

# ==================== MENU BARU: JOBDESK ====================
elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk Karyawan</h1></div>', unsafe_allow_html=True)
    df_job = pd.read_sql_query("SELECT * FROM jobdesk ORDER BY id DESC", conn)
    render_crud_table("jobdesk", "Jobdesk", df_job)

# ==================== MENU BARU: CI REPORT ====================
elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 Continuous Improvement (CI)</h1></div>', unsafe_allow_html=True)
    df_ci = pd.read_sql_query("SELECT * FROM ci ORDER BY id DESC", conn)
    render_crud_table("ci", "CI Report", df_ci)

# ==================== MENU BARU: SKD ====================
elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 Surat Keterangan (SKD)</h1></div>', unsafe_allow_html=True)
    df_skd = pd.read_sql_query("SELECT * FROM skd ORDER BY id DESC", conn)
    render_crud_table("skd", "SKD", df_skd)

# ==================== MENU BARU: INTERNAL MEMO ====================
elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo (IM)</h1></div>', unsafe_allow_html=True)
    df_im = pd.read_sql_query("SELECT * FROM im ORDER BY id DESC", conn)
    render_crud_table("im", "Internal Memo", df_im)

# ==================== MENU BARU: MUTASI & PKWT ====================
elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT Habis</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Mutasi Karyawan", "PKWT Akan Habis"])
    
    with tab1:
        df_mut = pd.read_sql_query("SELECT * FROM mutasi ORDER BY id DESC", conn)
        render_crud_table("mutasi", "Mutasi", df_mut)
        
    with tab2:
        st.markdown("### ⏳ Kontrak Berakhir dalam 60 Hari")
        tgl_skrg = datetime.now().strftime("%Y-%m-%d")
        tgl_60 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        
        df_pkwt = pd.read_sql_query("""
            SELECT id, employee_id as NRP, full_name as Nama, organization as Divisi, job_position as Jabatan, end_date as 'Tgl Habis PKWT'
            FROM karyawan 
            WHERE (resign_date IS NULL OR resign_date='') 
            AND end_date BETWEEN ? AND ?
            ORDER BY end_date ASC
        """, conn, params=(tgl_skrg, tgl_60))
        
        if df_pkwt.empty:
            st.success("✅ Tidak ada kontrak PKWT yang akan habis dalam 60 hari ke depan.")
        else:
            st.dataframe(df_pkwt, use_container_width=True, hide_index=True)

# ==================== 7. RESIGN ====================
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input", "📋 Daftar", "📊 Turnover"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_resign"):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                tgl = st.date_input("Tgl Resign", date.today())
                jenis = st.selectbox("Jenis", ["Resign Sendiri","PHK","Pensiun","Kontrak Habis"])
                kategori = st.selectbox("Kategori Penyebab", ["Mengundurkan Diri","Gagal Induksi","Medical Unfit","Contract Complete","Pelanggaran Indisipliner PP","Pelanggaran Indisipliner Pidana","Mutasi Job Site","Meninggal Dunia"])
                alasan = st.text_area("Alasan")
                interview = st.text_area("Exit Interview")
                if st.form_submit_button("💾 Simpan"):
                    kid = opsi[pilih]
                    c.execute('''INSERT INTO resign (karyawan_id,tanggal_resign,alasan,jenis,exit_interview,clearance_status,kategori_penyebab,tanggal_sign_out) VALUES (?,?,?,?,?,?,?,?)''',
                              (kid, str(tgl), alasan, jenis, interview, "Proses", kategori, str(tgl)))
                    c.execute("UPDATE karyawan SET resign_date=? WHERE id=?", (str(tgl), kid))
                    conn.commit(); st.success("✅ Tersimpan!"); st.rerun()

    with tab2:
        df_r = pd.read_sql_query("""
            SELECT r.id, k.employee_id, k.full_name, r.tanggal_resign, r.jenis, r.kategori_penyebab, r.clearance_status
            FROM resign r JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC
        """, conn)
        st.dataframe(df_r, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 📊 Causes of Turnover")
        df_cause = pd.read_sql_query("SELECT COALESCE(kategori_penyebab,'Tidak Diketahui') as KATEGORI, COUNT(*) as JML FROM resign GROUP BY kategori_penyebab ORDER BY JML DESC", conn)
        if not df_cause.empty:
            total = df_cause['JML'].sum()
            df_cause['%'] = (df_cause['JML'] / total * 100).round(1)
            st.dataframe(df_cause, use_container_width=True, hide_index=True)
            chart = alt.Chart(df_cause).mark_bar(cornerRadiusTopRight=8).encode(
                x=alt.X('JML:Q'), y=alt.Y('KATEGORI:N', sort='-x', title=''),
                color=alt.Color('JML:Q', scale=alt.Scale(scheme='reds'), legend=None)
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

# ==================== 8. DISIPLIN & SP ====================
elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & Surat Peringatan</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Tabel Data & CRUD", "➕ Input Baru"])

    with tab1:
        st.markdown("💡 **Tips:** Klik sel untuk edit, centang kiri + `Delete` untuk hapus, klik `+` di bawah untuk tambah.")
        df_d = pd.read_sql_query("SELECT * FROM disiplin ORDER BY id DESC", conn)
        render_crud_table("disiplin", "Disiplin & SP", df_d)

    with tab2:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_disiplin", clear_on_submit=True):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                col1, col2, col3 = st.columns(3)
                with col1:
                    jenis = st.selectbox("Jenis", ["SP1", "SP2", "SP3", "PHK"])
                    tgl_mulai = st.date_input("Tgl Mulai", date.today())
                with col2:
                    tgl_akhir = st.date_input("Tgl Akhir", date.today() + timedelta(days=180))
                    status = st.selectbox("Status", ["Aktif", "Selesai"])
                with col3:
                    periode = st.text_input("Periode (YYYY-MM)", value=date.today().strftime("%Y-%m"))
                rincian = st.text_area("Rincian Pelanggaran")
                if st.form_submit_button("💾 Simpan"):
                    c.execute('''INSERT INTO disiplin (karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status, periode) VALUES (?,?,?,?,?,?,?)''',
                              (opsi[pilih], jenis, str(tgl_mulai), str(tgl_akhir), rincian, status, periode))
                    conn.commit(); st.success(f"✅ {jenis} disimpan!"); st.rerun()

# ==================== 9. EXIT CLEARANCE ====================
elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1></div>', unsafe_allow_html=True)
    df_r = pd.read_sql_query("""
        SELECT r.id, k.full_name, k.job_position, r.tanggal_resign, r.clearance_status
        FROM resign r JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC
    """, conn)
    if df_r.empty:
        st.info("Belum ada data")
    else:
        st.dataframe(df_r, use_container_width=True, hide_index=True)
        opsi = {f"{r['full_name']} ({r['tanggal_resign']})": r['id'] for _, r in df_r.iterrows()}
        pilih = st.selectbox("Pilih", list(opsi.keys()))
        ns = st.selectbox("Status", ["Proses", "Selesai"])
        if st.button("💾 Update"):
            c.execute("UPDATE resign SET clearance_status=? WHERE id=?", (ns, opsi[pilih]))
            conn.commit(); st.rerun()

# ==================== 10. WHATSAPP REMINDER ====================
elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1></div>', unsafe_allow_html=True)
    tgl_skrg = datetime.now().date()

    st.markdown('<div class="section-header"><h3>📝 Kontrak Habis (30 Hari)</h3></div>', unsafe_allow_html=True)
    tgl_30 = (tgl_skrg + timedelta(days=30)).strftime("%Y-%m-%d")
    df_k = pd.read_sql_query("""
        SELECT id, employee_id, full_name, job_position, mobile_phone, end_date
        FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date BETWEEN ? AND ? ORDER BY end_date
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"), tgl_30))
    if df_k.empty:
        st.success("✅ Tidak ada kontrak habis dalam 30 hari")
    else:
        for _, r in df_k.iterrows():
            try: hari = (datetime.strptime(r['end_date'], "%Y-%m-%d").date() - tgl_skrg).days
            except: hari = 0
            col1, col2 = st.columns([4, 1])
            with col1:
                st.warning(f"📝 **{r['full_name']}** ({r['job_position']}) - Habis {r['end_date']} ({hari} hari lagi)")
            with col2:
                if r['mobile_phone']:
                    nomor = str(r['mobile_phone']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['full_name']}, kontrak kerja Anda berakhir {r['end_date']} ({hari} hari lagi). Mohon konfirmasi ke HRD. Terima kasih 🙏"
                    link = f"https://wa.me/{nomor}?text={quote(pesan)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="wa-btn">📱 WA</a>', unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>❌ Belum Absen Hari Ini</h3></div>', unsafe_allow_html=True)
    df_alpha = pd.read_sql_query("""
        SELECT full_name, mobile_phone, job_position FROM karyawan
        WHERE (resign_date IS NULL OR resign_date='') AND id NOT IN (SELECT karyawan_id FROM absensi WHERE tanggal=?)
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"),))
    if df_alpha.empty:
        st.success("✅ Semua sudah absen")
    else:
        for _, r in df_alpha.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.error(f"❌ **{r['full_name']}** ({r['job_position']}) - Belum absen")
            with col2:
                if r['mobile_phone']:
                    nomor = str(r['mobile_phone']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['full_name']}, kami belum menerima absensi Anda hari ini. Mohon konfirmasi. Terima kasih 🙏"
                    link = f"https://wa.me/{nomor}?text={quote(pesan)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="wa-btn">📱 WA</a>', unsafe_allow_html=True)

# ==================== 11. ASET ====================
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Input", "📋 Daftar"])
    with tab1:
        with st.form("form_aset", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                kode = st.text_input("Kode Aset *")
                nama = st.text_input("Nama Aset *")
                kategori = st.selectbox("Kategori", ["Kendaraan","Mobil","AC","CCTV","Kursi","Meja","Lemari","APAR","Komputer","Lainnya"])
                lokasi = st.text_input("Lokasi")
            with col2:
                kondisi = st.selectbox("Kondisi", ["Baik","Rusak Ringan","Rusak Berat"])
                nilai = st.number_input("Nilai (Rp)", min_value=0.0, step=100000.0)
                tgl = st.date_input("Tanggal Perolehan", date.today())
                pj = st.text_input("Penanggung Jawab")
                status = st.selectbox("Status", ["Aktif","Maintenance","Disposal"])
            if st.form_submit_button("💾 Simpan"):
                if kode and nama:
                    try:
                        c.execute('''INSERT INTO aset (kode,nama,kategori,lokasi,kondisi,nilai,tanggal_perolehan,penanggung_jawab,status,catatan) VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                  (kode, nama, kategori, lokasi, kondisi, nilai, str(tgl), pj, status, ""))
                        conn.commit(); st.success("✅ Tersimpan!"); st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Kode sudah ada")
    with tab2:
        df_a = pd.read_sql_query("SELECT * FROM aset ORDER BY id DESC", conn)
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        if not df_a.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total Aset", str(len(df_a)), "item", "card-blue")
            html += metric_card("Total Nilai", format_rp(df_a['nilai'].sum()), "", "card-green")
            html += metric_card("Aktif", str(len(df_a[df_a['status']=='Aktif'])), "", "card-teal")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

# ==================== 12. RUKO & TENANT ====================
elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🏪 Ruko", "🏠 Tenant"])
    with tab1:
        with st.form("form_ruko", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Ruko *")
                alamat = st.text_input("Alamat")
                status_r = st.selectbox("Status", ["Milik Sendiri","Sewa Aktif","Sewa Akan Habis","Sewa Habis"])
            with col2:
                penyewa = st.text_input("Penyewa")
                nilai = st.number_input("Nilai Sewa", min_value=0.0, step=100000.0)
                mulai = st.date_input("Mulai", date.today())
                akhir = st.date_input("Akhir", date.today()+timedelta(days=365))
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    c.execute('''INSERT INTO ruko (nama,alamat,status,penyewa,nilai_sewa,mulai_sewa,akhir_sewa,catatan) VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, alamat, status_r, penyewa, nilai, str(mulai), str(akhir), ""))
                    conn.commit(); st.rerun()
        df_r = pd.read_sql_query("SELECT * FROM ruko ORDER BY id DESC", conn)
        st.dataframe(df_r, use_container_width=True, hide_index=True)
    with tab2:
        with st.form("form_tenant", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Tenant *")
                lokasi = st.text_input("Lokasi")
                kamar = st.text_input("Kamar")
                penghuni = st.text_input("Penghuni")
            with col2:
                biaya = st.number_input("Biaya Bulanan", min_value=0.0, step=100000.0)
                ci = st.selectbox("Status CI", ["Sesuai CI","Belum Sesuai CI"])
                mulai = st.date_input("Mulai", date.today())
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    c.execute('''INSERT INTO tenant (nama,lokasi,kamar,penghuni,biaya_bulanan,status_ci,mulai,catatan) VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, lokasi, kamar, penghuni, biaya, ci, str(mulai), ""))
                    conn.commit(); st.rerun()
        df_t = pd.read_sql_query("SELECT * FROM tenant ORDER BY id DESC", conn)
        st.dataframe(df_t, use_container_width=True, hide_index=True)

# ==================== 13. UTILITY MELAK ====================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>PDAM • Listrik • Internet — Site Melak</p></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", "➕ Input Manual", "📋 Daftar & Filter", "📥 Import File", "🔔 Reminder"
    ])

    with tab1:
        df_u = pd.read_sql_query("SELECT * FROM utility ORDER BY tanggal_bayar DESC", conn)
        if df_u.empty:
            st.info("📭 Belum ada data utility. Buka tab **📥 Import File** untuk upload data tagihan.")
        else:
            total_all = df_u['total_bayar'].sum()
            pdam_total = df_u[df_u['kategori']=='PDAM']['total_bayar'].sum()
            listrik_total = df_u[df_u['kategori']=='Listrik']['total_bayar'].sum()
            internet_total = df_u[df_u['kategori']=='Internet']['total_bayar'].sum()
            belum_bayar = len(df_u[df_u['status']!='Lunas'])
            total_belum = df_u[df_u['status']!='Lunas']['total_bayar'].sum()

            html = '<div class="metric-grid">'
            html += metric_card("💰 Total Pengeluaran", format_rp(total_all), f"{len(df_u)} transaksi", "card-blue")
            html += metric_card("💧 PDAM", format_rp(pdam_total), "", "card-teal")
            html += metric_card("⚡ Listrik", format_rp(listrik_total), "", "card-gold")
            html += metric_card("🌐 Internet", format_rp(internet_total), "", "card-purple")
            html += metric_card("❌ Belum Lunas", str(belum_bayar), format_rp(total_belum), "card-red")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown('<div class="section-header"><h3>📊 Pengeluaran per Bulan</h3></div>', unsafe_allow_html=True)
            df_u['bulan'] = pd.to_datetime(df_u['tanggal_bayar'], errors='coerce').dt.strftime('%Y-%m')
            df_bulan = df_u.groupby(['bulan','kategori'])['total_bayar'].sum().reset_index()
            if not df_bulan.empty:
                chart = alt.Chart(df_bulan).mark_bar(cornerRadiusTopRight=4).encode(
                    x=alt.X('bulan:N', title='Bulan'),
                    y=alt.Y('total_bayar:Q', title='Total Bayar (Rp)'),
                    color=alt.Color('kategori:N', scale=alt.Scale(scheme='tableau10')),
                    xOffset='kategori:N', tooltip=['bulan','kategori','total_bayar']
                ).properties(height=380)
                st.altair_chart(chart, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**🥧 Proporsi per Kategori**")
                df_kat = df_u.groupby('kategori')['total_bayar'].sum().reset_index()
                chart2 = alt.Chart(df_kat).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta('total_bayar:Q'),
                    color=alt.Color('kategori:N', scale=alt.Scale(scheme='tableau10')),
                    tooltip=['kategori','total_bayar']
                ).properties(height=320)
                st.altair_chart(chart2, use_container_width=True)
            with col2:
                st.markdown("**🏷️ Top 10 Label / Lokasi**")
                df_lbl = df_u.groupby('label')['total_bayar'].sum().reset_index().sort_values('total_bayar', ascending=False).head(10)
                chart3 = alt.Chart(df_lbl).mark_bar(cornerRadiusTopRight=8).encode(
                    x=alt.X('total_bayar:Q', title='Total'),
                    y=alt.Y('label:N', sort='-x', title=''),
                    color=alt.Color('total_bayar:Q', scale=alt.Scale(scheme='blues'), legend=None)
                ).properties(height=320)
                st.altair_chart(chart3, use_container_width=True)

            st.markdown("**💳 Distribusi Metode Pembayaran**")
            df_met = df_u.groupby('metode')['total_bayar'].agg(['sum','count']).reset_index().sort_values('sum', ascending=False)
            df_met.columns = ['Metode','Total','Transaksi']
            st.dataframe(df_met, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("➕ Input Transaksi Utility Baru")
        with st.form("form_utility", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                kat = st.selectbox("Kategori *", ["PDAM", "Listrik", "Internet", "Air", "Gas", "Lainnya"])
                tgl = st.date_input("Tanggal Bayar", date.today())
                periode = st.text_input("Periode / Jenis", placeholder="Mei 2025 / Token Prabayar / Tagihan Internet")
            with col2:
                idp = st.text_input("ID Pelanggan", placeholder="216010004 / 231411239835 / 161307012250")
                label = st.text_input("Label / Lokasi", placeholder="KANTOR / MESS OFFICE LAMA / BUSINESS CENTER A.4")
                metode = st.selectbox("Metode Bayar", ["BCA m-Payment","BCA","BCA / Bankaltim","Bankaltimtara","Cash","Transfer","-"])
            with col3:
                nominal = st.number_input("Nominal (Rp)", min_value=0.0, step=1000.0)
                admin = st.number_input("Admin (Rp)", min_value=0.0, step=1000.0, value=3000.0)
                status = st.selectbox("Status", ["Lunas", "Belum", "Pending"])
            total_prev = nominal + admin
            st.info(f"💰 **Total Bayar otomatis: {format_rp(total_prev)}**")
            catatan = st.text_area("Catatan (opsional)")

            if st.form_submit_button("💾 Simpan Transaksi"):
                if kat and nominal > 0:
                    c.execute('''INSERT INTO utility (kategori, tanggal_bayar, periode, id_pelanggan, label,
                                 nominal, admin, total_bayar, metode, status, catatan, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (kat, str(tgl), periode, idp, label, nominal, admin, total_prev, metode, status, catatan,
                               datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    log_aksi(st.session_state.username, "TAMBAH_UTILITY", f"{kat} {label} {format_rp(total_prev)}")
                    st.success(f"✅ Transaksi {kat} — {label} tersimpan!")
                    st.rerun()
                else:
                    st.warning("⚠️ Kategori & Nominal wajib diisi")

    with tab3:
        st.subheader("📋 Daftar Transaksi Utility")
        col1, col2, col3, col4 = st.columns([1,1,1,2])
        with col1: f_kat = st.selectbox("Kategori", ["Semua","PDAM","Listrik","Internet","Air","Gas","Lainnya"], key="u_kat")
        with col2: f_status = st.selectbox("Status", ["Semua","Lunas","Belum","Pending"], key="u_st")
        with col3: f_tahun = st.selectbox("Tahun", ["Semua"] + [str(y) for y in range(2025, datetime.now().year+2)], key="u_th")
        with col4: f_label = st.text_input("🔍 Cari Label / ID Pelanggan", key="u_lbl")

        query = "SELECT * FROM utility WHERE 1=1"; params = []
        if f_kat != "Semua": query += " AND kategori=?"; params.append(f_kat)
        if f_status != "Semua": query += " AND status=?"; params.append(f_status)
        if f_tahun != "Semua": query += " AND substr(tanggal_bayar,1,4)=?"; params.append(f_tahun)
        if f_label:
            query += " AND (label LIKE ? OR id_pelanggan LIKE ?)"
            params.extend([f"%{f_label}%", f"%{f_label}%"])
        query += " ORDER BY tanggal_bayar DESC"

        df_filter = pd.read_sql_query(query, conn, params=params)
        total_filter = df_filter['total_bayar'].sum() if not df_filter.empty else 0
        colA, colB, colC = st.columns(3)
        with colA: st.metric("📊 Jumlah", len(df_filter))
        with colB: st.metric("💰 Total", format_rp(total_filter))
        with colC: st.metric("❌ Belum Lunas", len(df_filter[df_filter['status']!='Lunas']) if not df_filter.empty else 0)

        if df_filter.empty:
            st.info("Tidak ada data sesuai filter.")
        else:
            def color_status(row):
                if row['status'] == 'Lunas': return ['background-color: #d4edda'] * len(row)
                if row['status'] == 'Belum': return ['background-color: #f8d7da'] * len(row)
                if row['status'] == 'Pending': return ['background-color: #fff3cd'] * len(row)
                return [''] * len(row)

            show_cols = ['id','kategori','tanggal_bayar','periode','id_pelanggan','label','nominal','admin','total_bayar','metode','status']
            st.dataframe(df_filter[show_cols].style.apply(color_status, axis=1), use_container_width=True, hide_index=True)

            colD, colE = st.columns(2)
            with colD:
                st.download_button("📥 Export CSV", df_filter.to_csv(index=False).encode(),
                                   f"utility_filter_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            with colE:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df_filter.to_excel(w, index=False)
                st.download_button("📥 Export Excel", buf.getvalue(),
                                   f"utility_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            st.markdown("---")
            st.markdown("### ⚙️ Kelola Transaksi")
            opsi_del = {f"#{r['id']} | {r['kategori']} - {r['label']} | {r['periode']} | {format_rp(r['total_bayar'])}": r['id'] for _, r in df_filter.iterrows()}
            pilih_del = st.selectbox("Pilih transaksi:", ["-- Pilih --"] + list(opsi_del.keys()))
            if pilih_del != "-- Pilih --":
                tid = opsi_del[pilih_del]
                row_sel = df_filter[df_filter['id'] == tid].iloc[0]

                with st.form("form_edit_utility"):
                    st.markdown(f"**✏️ Edit Transaksi #{tid}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        e_kat = st.selectbox("Kategori", ["PDAM","Listrik","Internet","Air","Gas","Lainnya"],
                                             index=["PDAM","Listrik","Internet","Air","Gas","Lainnya"].index(row_sel['kategori']) if row_sel['kategori'] in ["PDAM","Listrik","Internet","Air","Gas","Lainnya"] else 0)
                        try: e_tgl = st.date_input("Tanggal Bayar", datetime.strptime(row_sel['tanggal_bayar'], "%Y-%m-%d").date())
                        except: e_tgl = st.date_input("Tanggal Bayar", date.today())
                        e_periode = st.text_input("Periode", value=row_sel['periode'] or "")
                    with col2:
                        e_status = st.selectbox("Status", ["Lunas","Belum","Pending"],
                                                index=["Lunas","Belum","Pending"].index(row_sel['status']) if row_sel['status'] in ["Lunas","Belum","Pending"] else 0)
                        e_nominal = st.number_input("Nominal", min_value=0.0, value=float(row_sel['nominal'] or 0), step=1000.0)
                        e_admin = st.number_input("Admin", min_value=0.0, value=float(row_sel['admin'] or 0), step=1000.0)
                    if st.form_submit_button("💾 Update", type="primary"):
                        new_total = e_nominal + e_admin
                        c.execute('''UPDATE utility SET kategori=?, tanggal_bayar=?, periode=?, nominal=?, admin=?, total_bayar=?, status=? WHERE id=?''',
                                  (e_kat, str(e_tgl), e_periode, e_nominal, e_admin, new_total, e_status, tid))
                        conn.commit(); st.success("✅ Diperbarui!"); st.rerun()

                if st.button("🗑️ Hapus Permanen", type="primary", key="del_util"):
                    c.execute("DELETE FROM utility WHERE id=?", (tid,))
                    conn.commit(); st.success("✅ Dihapus"); st.rerun()

    with tab4:
        st.subheader("📥 Import Data Utility dari File")
        st.info("""
        **Format:** `.txt` (tab-separated) • `.csv` • `.xlsx` • `.xls`

        **Kolom Wajib:** `Kategori`, `Nominal (Rp)`  
        **Kolom Opsional:** Tanggal Bayar, Periode / Jenis, ID Pelanggan, Label, Admin (Rp), Total Bayar (Rp), Metode, Status

        💡 Tanggal Indonesia (`03 Jun 2025`) otomatis dikonversi. Angka `1.234.567` otomatis dibaca ribuan.
        """)

        with st.expander("📄 Contoh Format File TXT"):
            st.code("""Kategori\tTanggal Bayar\tPeriode / Jenis\tID Pelanggan\tLabel\tNominal (Rp)\tAdmin (Rp)\tTotal Bayar (Rp)\tMetode\tStatus
PDAM\t03 Jun 2025\tMei 2025\t216010004\tBISNIS CENTER A.4\t17500\t3000\t20500\tBankaltimtara\tLunas
Listrik\t06 Mei 2025\tTagihan Pascabayar\t231411239835\tBUSINESS CENTRE A.4/OFFICE\t266200\t3000\t269200\tBCA\tLunas
Internet\t06 Jan
