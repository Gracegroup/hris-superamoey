import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import json
from datetime import datetime, timedelta, date
import calendar
import altair as alt
from urllib.parse import quote

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA SUPER",
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
    gaji REAL DEFAULT 0,
    aktif INTEGER DEFAULT 1)''')

c.execute('''CREATE TABLE IF NOT EXISTS kandidat (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, posisi_dilamar TEXT,
    telepon TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT,
    status TEXT, catatan TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS resign (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT,
    alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT)''')

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
    alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS payroll (
    id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT,
    gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL,
    tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_kesehatan_perusahaan REAL,
    bpjs_jht_karyawan REAL, bpjs_jht_perusahaan REAL,
    bpjs_jp_karyawan REAL, bpjs_jp_perusahaan REAL,
    bpjs_jkk REAL, bpjs_jkm REAL, bpjs_jkp REAL,
    pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL,
    gaji_bersih REAL, status TEXT DEFAULT 'Final', tanggal_proses TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
conn.commit()

# ==================== HELPER ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def format_rp(n):
    try: return f"Rp {float(n):,.0f}".replace(",", ".")
    except: return "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)",
              (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

def normalize_col(col):
    s = str(col).lower().strip()
    for ch in [' ', '.', '-', '/', '\\', ':', ',']:
        s = s.replace(ch, '_')
    for ch in ['(', ')', '[', ']', '{', '}', '&', "'", '"']:
        s = s.replace(ch, '')
    while '__' in s:
        s = s.replace('__', '_')
    return s.strip('_')

def map_columns(df, tabel):
    SPECIAL_MAP = {
        "nik_npwp_16_digit": "nik_npwp_16",
        "nik_npwp_16": "nik_npwp_16",
        "npwp_16_digit_new": "npwp_16_new",
        "npwp_16_new": "npwp_16_new",
        "tin_taxpayer_identification_number": "tin",
    }
    cur = conn.execute(f"PRAGMA table_info({tabel})")
    kolom_db = [r[1] for r in cur.fetchall()]
    mapping = {}
    for col in df.columns:
        norm = normalize_col(col)
        if norm in SPECIAL_MAP:
            target = SPECIAL_MAP[norm]
        elif norm in kolom_db:
            target = norm
        else:
            target = None
        mapping[col] = target
    return mapping, kolom_db

# ==================== MULTI-FORMAT FILE PARSERS ====================
def parse_csv(file, delim=None, encoding=None):
    raw = file.read()
    file.seek(0)
    if encoding is None:
        for enc in ["utf-8-sig", "utf-8", "latin-1", "iso-8859-1"]:
            try:
                raw.decode(enc)
                encoding = enc
                break
            except:
                continue
        encoding = encoding or "utf-8"
    if delim is None:
        try:
            text = raw.decode(encoding)
        except:
            text = raw.decode("latin-1")
        first_lines = "\n".join(text.split("\n")[:5])
        counts = {
            ",": first_lines.count(","),
            ";": first_lines.count(";"),
            "\t": first_lines.count("\t"),
            "|": first_lines.count("|"),
        }
        delim = max(counts, key=counts.get)
        if counts[delim] == 0:
            delim = ","
    return pd.read_csv(io.BytesIO(raw), delimiter=delim, encoding=encoding,
                       on_bad_lines='skip', engine='python')

def parse_excel(file):
    raw = file.read()
    file.seek(0)
    try:
        xls = pd.ExcelFile(io.BytesIO(raw))
        sheet_names = xls.sheet_names
        dfs = []
        for sheet in sheet_names:
            df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
            if not df.empty:
                dfs.append(df)
        if len(dfs) == 1:
            return dfs[0]
        elif len(dfs) > 1:
            return pd.concat(dfs, ignore_index=True)
        else:
            return pd.DataFrame()
    except Exception as e:
        raise Exception(f"Gagal baca Excel: {e}")

def parse_json(file):
    raw = file.read()
    file.seek(0)
    try:
        data = json.loads(raw.decode("utf-8"))
    except:
        data = json.loads(raw.decode("latin-1"))
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0:
                return pd.DataFrame(val)
        return pd.DataFrame([data])
    return pd.DataFrame()

def parse_word(file):
    try:
        from docx import Document
    except ImportError:
        raise Exception("Package python-docx belum diinstall. Jalankan: pip install python-docx")
    raw = file.read()
    file.seek(0)
    doc = Document(io.BytesIO(raw))
    tables_data = []
    for tbl in doc.tables:
        data = []
        for row in tbl.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            data.append(row_data)
        if data:
            header = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=header)
            tables_data.append(df)
    if not tables_data:
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if lines:
            return pd.DataFrame({"text": lines})
        return pd.DataFrame()
    if len(tables_data) == 1:
        return tables_data[0]
    return pd.concat(tables_data, ignore_index=True)

def parse_pdf(file):
    raw = file.read()
    file.seek(0)
    try:
        import pdfplumber
    except ImportError:
        raise Exception("Package pdfplumber belum diinstall. Jalankan: pip install pdfplumber")
    tables_data = []
    text_lines = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tbl in tables:
                if tbl and len(tbl) > 1:
                    header = tbl[0]
                    rows = tbl[1:]
                    header = [str(h) if h else f"col_{i}" for i, h in enumerate(header)]
                    rows_clean = [[str(c) if c else "" for c in row] for row in rows]
                    max_len = len(header)
                    rows_clean = [r + [""] * (max_len - len(r)) for r in rows_clean]
                    rows_clean = [r[:max_len] for r in rows_clean]
                    df = pd.DataFrame(rows_clean, columns=header)
                    tables_data.append(df)
            txt = page.extract_text()
            if txt:
                text_lines.extend(txt.split("\n"))
    if tables_data:
        if len(tables_data) == 1:
            return tables_data[0]
        return pd.concat(tables_data, ignore_index=True)
    elif text_lines:
        return pd.DataFrame({"text": text_lines})
    return pd.DataFrame()

def parse_txt(file, delim=None):
    return parse_csv(file, delim=delim)

def parse_any_file(file, filename):
    ext = filename.lower().split('.')[-1]
    if ext in ['csv']:
        return parse_csv(file)
    elif ext in ['xlsx', 'xls', 'xlsm']:
        return parse_excel(file)
    elif ext in ['json']:
        return parse_json(file)
    elif ext in ['docx']:
        return parse_word(file)
    elif ext in ['pdf']:
        return parse_pdf(file)
    elif ext in ['txt', 'tsv']:
        return parse_txt(file)
    else:
        raise Exception(f"Format .{ext} tidak didukung")

def hitung_bpjs(gaji_pokok, tunjangan_tetap):
    upah = gaji_pokok + tunjangan_tetap
    upah_kes = min(upah, 12000000)
    kes_k = round(upah_kes * 0.01, -2)
    kes_p = round(upah_kes * 0.04, -2)
    jht_k = round(upah * 0.02, -2)
    jht_p = round(upah * 0.037, -2)
    upah_jp = min(upah, 11086300)
    jp_k = round(upah_jp * 0.01, -2)
    jp_p = round(upah_jp * 0.02, -2)
    jkk = round(upah * 0.0024, -2)
    jkm = round(upah * 0.003, -2)
    jkp = round(upah * 0.0005, -2)
    return {
        'kes_k': kes_k, 'kes_p': kes_p, 'jht_k': jht_k, 'jht_p': jht_p,
        'jp_k': jp_k, 'jp_p': jp_p, 'jkk': jkk, 'jkm': jkm, 'jkp': jkp,
        'total_k': kes_k + jht_k + jp_k,
        'total_p': kes_p + jht_p + jp_p + jkk + jkm + jkp
    }

def hitung_pph21(bruto_bulanan, ptkp_setahun, iuran_pensiun_bulanan):
    biaya_jabatan = min(bruto_bulanan * 0.05, 500000)
    neto_bulanan = bruto_bulanan - biaya_jabatan - iuran_pensiun_bulanan
    neto_setahun = neto_bulanan * 12
    pkp = max(0, neto_setahun - ptkp_setahun)
    pkp = round(pkp, -3)
    if pkp <= 60000000: pph = pkp * 0.05
    elif pkp <= 250000000: pph = 60000000*0.05 + (pkp-60000000)*0.15
    elif pkp <= 500000000: pph = 60000000*0.05 + 190000000*0.15 + (pkp-250000000)*0.25
    elif pkp <= 5000000000: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + (pkp-500000000)*0.30
    else: pph = 60000000*0.05 + 190000000*0.15 + 250000000*0.25 + 4500000000*0.30 + (pkp-5000000000)*0.35
    return max(0, round(pph / 12, -2))

PTKP_MAP = {"TK/0": 54000000, "TK/1": 58500000, "TK/2": 63000000, "TK/3": 67500000,
            "K/0": 58500000, "K/1": 63000000, "K/2": 67500000, "K/3": 72000000}

# ==================== SEED USER ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)",
              ("admin", hash_password("admin123"), "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)",
              ("hrd", hash_password("hrd123"), "HRD Staff", "hrd"))
    conn.commit()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.nama = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown("""
    <div class="main-header">
        <h1>⚡ HRIS, GA & ASET SUPER</h1>
        <p>Sistem Manajemen SDM, Absensi, Payroll & General Affair</p>
    </div>
    """, unsafe_allow_html=True)

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
        st.info("🔑 Default: **admin** / **admin123**  •  **hrd** / **hrd123**")
    st.stop()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 15px 0;">
        <div style="font-size:3em;">👤</div>
        <h3 style="margin:5px 0;">{st.session_state.nama}</h3>
        <p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p>
        <p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    menu = [
        "🏠 Dashboard HRIS",
        "👥 Data Karyawan",
        "📅 Absensi & Kehadiran",
        "🏖️ Cuti & Izin",
        "💰 Payroll & Slip Gaji",
        "📋 Rekrutmen & CV",
        "📉 Resign & Turnover",
        "📤 Exit Clearance",
        "📱 WhatsApp Reminder",
        "🚛 Aset & Properti",
        "🏪 Ruko & Tenant",
        "📊 Laporan & Analitik",
        "💾 Import, Export & Backup",
    ]
    if st.session_state.role == "admin":
        menu += ["👤 Manajemen User", "📝 Log Aktivitas"]

    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]:
            st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== 1. DASHBOARD ====================
if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f"""
    <div class="main-header">
        <h1>⚡ HRIS, GA & ASET DASHBOARD</h1>
        <p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime('%d/%m/%Y, %H.%M.%S')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>👥 KPI HRIS & GENERAL AFFAIR</h3></div>', unsafe_allow_html=True)

    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None'").fetchone()[0]
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    tgl_skrg = datetime.now().strftime("%Y-%m-%d")
    kontrak_habis = c.execute("SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date BETWEEN ? AND ?", (tgl_skrg, tgl_30)).fetchone()[0]

    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", f"{aktif}", "belum resign", "card-blue")
    html += metric_card("📋 Kandidat CV", f"{kandidat}", "screening", "card-purple")
    html += metric_card("📝 Kontrak Habis", f"{kontrak_habis}", "30 hari", "card-orange")
    html += metric_card("✅ Diterima", f"{diterima}", "lolos rekrutmen", "card-green")
    html += metric_card("❌ Ditolak", f"{ditolak}", "tidak lolos", "card-red")
    html += metric_card("⏳ Proses", f"{proses}", "on going", "card-gold")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>📉 KPI TURNOVER & RETENTION</h3></div>', unsafe_allow_html=True)
    total_resign = c.execute("SELECT COUNT(*) FROM resign").fetchone()[0]
    total = aktif + total_resign if (aktif + total_resign) > 0 else 1
    turnover = (total_resign / total) * 100
    retention = 100 - turnover
    clearance_ok = c.execute("SELECT COUNT(*) FROM resign WHERE clearance_status='Selesai'").fetchone()[0]
    clearance_proc = c.execute("SELECT COUNT(*) FROM resign WHERE clearance_status='Proses'").fetchone()[0]

    html = '<div class="metric-grid">'
    html += metric_card("📉 Turnover Rate", f"{turnover:.1f}%", "kumulatif", "card-red")
    html += metric_card("📈 Retention Rate", f"{retention:.1f}%", "bertahan", "card-green")
    html += metric_card("📤 Total Resign", f"{total_resign}", "sepanjang waktu", "card-orange")
    html += metric_card("🎯 Bisa Direkrut", f"{diterima}", "rehire OK", "card-blue")
    html += metric_card("📤 Clearance OK", f"{clearance_ok}", "selesai", "card-teal")
    html += metric_card("⏳ Clearance Proc", f"{clearance_proc}", "proses", "card-gold")
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

    st.markdown('<div class="section-header"><h3>📊 Analitik Job Position & Organization</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👔 Job Position (Aktif)**")
        df_jab = pd.read_sql_query("SELECT job_position as JABATAN, COUNT(*) as JML FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND job_position IS NOT NULL GROUP BY job_position ORDER BY JML DESC", conn)
        if not df_jab.empty:
            chart = alt.Chart(df_jab).mark_bar(cornerRadiusTopRight=10, cornerRadiusBottomRight=10).encode(
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
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["➕ Tambah", "📋 Daftar", "🔍 Detail"])

    with tab1:
        with st.form("form_karyawan", clear_on_submit=True):
            st.subheader("📋 Data Karyawan")
            col1, col2, col3 = st.columns(3)
            with col1:
                employee_id = st.text_input("Employee ID *")
                full_name = st.text_input("Full Name *")
                barcode = st.text_input("Barcode")
                organization = st.text_input("Organization")
                job_position = st.text_input("Job Position")
            with col2:
                job_level = st.selectbox("Job Level", ["staff", "Non - Staff", "Supervisor", "Foreman", "Manager"])
                join_date = st.date_input("Join Date", date.today())
                resign_date = st.text_input("Resign Date (YYYY-MM-DD, kosong jika aktif)", value="")
                status_employee = st.selectbox("Status Employee", ["Contract", "Tetap", "Probation", "Magang"])
                end_date = st.date_input("End Date", date.today() + timedelta(days=365))
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
                citizen_id_address = st.text_area("Citizen ID Address")
                residential_address = st.text_area("Residential Address")
                nik_npwp_16 = st.text_input("NIK (NPWP 16 Digit)")
            with col6:
                npwp = st.text_input("NPWP")
                ptkp_status = st.selectbox("PTKP Status", list(PTKP_MAP.keys()))
                employee_tax_status = st.selectbox("Employee Tax Status", ["Pegawai Tetap","Pegawai Tidak Tetap","Bukan Pegawai"])
                tax_config = st.selectbox("Tax Config", ["Gross Up","Gross","Net"])
                tin = st.text_input("TIN (Taxpayer Identification Number)")

            col7, col8, col9 = st.columns(3)
            with col7:
                bank_name = st.selectbox("Bank Name", ["BCA","Mandiri","BNI","BRI","CIMB","Permata"])
                bank_account = st.text_input("Bank Account")
                bank_account_holder = st.text_input("Bank Account Holder")
            with col8:
                bpjs_ketenagakerjaan = st.text_input("BPJS Ketenagakerjaan")
                bpjs_kesehatan = st.text_input("BPJS Kesehatan")
                currency = st.text_input("Currency", value="IDR")
            with col9:
                manager = st.text_input("Manager")
                approval_line = st.text_input("Approval Line")
                payment_schedule = st.text_input("Payment Schedule")

            col10, col11 = st.columns(2)
            with col10:
                divisi = st.selectbox("Divisi", ["PRODUCT SUPPORT","AFTER MARKET & INVENTORY WAREHOUSE","SALES & OPERATION","HRD","FINANCE","GA","PARTS","Adm.PS"])
                gaji = st.number_input("Gaji (Rp)", min_value=0.0, step=100000.0)
            with col11:
                grade = st.text_input("Grade")
                class_ = st.text_input("Class")

            keterangan = st.text_area("Keterangan")

            if st.form_submit_button("💾 Simpan"):
                if employee_id and full_name:
                    try:
                        c.execute('''INSERT INTO karyawan (employee_id, full_name, barcode, organization, job_position,
                                     job_level, join_date, resign_date, status_employee, end_date, email,
                                     birth_date, birth_place, citizen_id_address, residential_address, npwp,
                                     ptkp_status, employee_tax_status, tax_config, bank_name, bank_account,
                                     bank_account_holder, bpjs_ketenagakerjaan, bpjs_kesehatan, nik_npwp_16,
                                     mobile_phone, phone, branch_name, parent_branch_name, religion, gender,
                                     marital_status, blood_type, nationality_code, currency, payment_schedule,
                                     approval_line, manager, grade, class, tin, divisi, keterangan, gaji)
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                  (employee_id, full_name, barcode, organization, job_position,
                                   job_level, str(join_date), resign_date, status_employee, str(end_date), email,
                                   str(birth_date), birth_place, citizen_id_address, residential_address, npwp,
                                   ptkp_status, employee_tax_status, tax_config, bank_name, bank_account,
                                   bank_account_holder, bpjs_ketenagakerjaan, bpjs_kesehatan, nik_npwp_16,
                                   mobile_phone, phone, branch_name, parent_branch_name, religion, gender,
                                   marital_status, blood_type, nationality_code, currency, payment_schedule,
                                   approval_line, manager, grade, class_, tin, divisi, keterangan, gaji))
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
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown(f"""
            **Employee ID**: {d['employee_id']}  |  **Gender**: {d['gender'] or '-'}  |  **Religion**: {d['religion'] or '-'}  
            **Email**: {d['email'] or '-'}  |  **Mobile**: {d['mobile_phone'] or '-'}  
            **Birth**: {d['birth_place'] or '-'}, {d['birth_date'] or '-'}  
            **Alamat KTP**: {d['citizen_id_address'] or '-'}  
            **Alamat Domisili**: {d['residential_address'] or '-'}  
            **Bank**: {d['bank_name'] or '-'} - {d['bank_account'] or '-'}  
            **NPWP**: {d['npwp'] or '-'}  |  **PTKP**: {d['ptkp_status'] or '-'}  
            **Join Date**: {d['join_date']}  |  **End Date**: {d['end_date']}  |  **Resign**: {d['resign_date'] or '-'}  
            **Manager**: {d['manager'] or '-'}
            """)

# ==================== 3. ABSENSI ====================
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["✍️ Input Absensi", "📋 Rekap", "📊 Statistik"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date='' OR resign_date='None' ORDER BY full_name", conn)
        if df_k.empty:
            st.warning("Belum ada karyawan aktif")
        else:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}

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
            if telat > 0:
                st.warning(f"⚠️ Terlambat **{telat} menit**")

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
            csv = df_a.to_csv(index=False).encode()
            st.download_button("📥 Export CSV", csv, "absensi.csv", "text/csv")

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

    tab1, tab2 = st.tabs(["➕ Ajukan", "📋 Daftar & Approval"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_cuti"):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                jenis = st.selectbox("Jenis Cuti", ["Cuti Tahunan","Cuti Sakit","Cuti Melahirkan","Cuti Menikah","Cuti Duka","Izin","Dinas Luar"])
                col1, col2 = st.columns(2)
                with col1: tm = st.date_input("Mulai", date.today())
                with col2: ts = st.date_input("Selesai", date.today())
                alasan = st.text_area("Alasan")
                if st.form_submit_button("📤 Ajukan"):
                    lama = (ts - tm).days + 1
                    c.execute("""INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai,
                                 lama_hari, alasan, status) VALUES (?,?,?,?,?,?,?)""",
                              (opsi[pilih], jenis, str(tm), str(ts), lama, alasan, "Menunggu"))
                    conn.commit()
                    st.success(f"✅ Pengajuan cuti {lama} hari terkirim!")
                    st.rerun()

    with tab2:
        df_cuti = pd.read_sql_query("""
            SELECT c.id, k.employee_id, k.full_name, c.jenis_cuti, c.tanggal_mulai, c.tanggal_selesai,
                   c.lama_hari, c.alasan, c.status
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
                        conn.commit()
                        st.rerun()
                with colB:
                    if st.button("❌ Tolak"):
                        c.execute("UPDATE cuti SET status='Ditolak', approved_by=?, approved_at=? WHERE id=?",
                                  (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M"), cid))
                        conn.commit()
                        st.rerun()
        else:
            st.info("Belum ada pengajuan cuti")

# ==================== 5. PAYROLL ====================
elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🧮 Proses Payroll", "📋 Riwayat", "🖨️ Slip Gaji"])

    with tab1:
        df_k = pd.read_sql_query("""
            SELECT id, employee_id, full_name, gaji, ptkp_status, job_position
            FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND gaji > 0 ORDER BY full_name
        """, conn)

        if df_k.empty:
            st.warning("Belum ada karyawan aktif dengan gaji. Isi gaji di menu Data Karyawan dulu.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                bulan = st.selectbox("Bulan", list(range(1,13)), index=datetime.now().month-1,
                                     format_func=lambda x: calendar.month_name[x])
            with col2:
                tahun = st.number_input("Tahun", 2020, 2030, datetime.now().year)
            periode = f"{tahun}-{bulan:02d}"

            preview = []
            for _, r in df_k.iterrows():
                gaji_pokok = r['gaji']
                tunj_jab = round(gaji_pokok * 0.15, -2)
                tunj_trans = 500000
                tunj_makan = 600000
                bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                pph = hitung_pph21(bruto, PTKP_MAP.get(r['ptkp_status'] or "TK/0", 54000000), bpjs['total_k'])
                bersih = bruto - bpjs['total_k'] - pph
                preview.append({
                    'Nama': r['full_name'], 'Jabatan': r['job_position'],
                    'Gaji Pokok': format_rp(gaji_pokok),
                    'Bruto': format_rp(bruto),
                    'BPJS': format_rp(bpjs['total_k']),
                    'PPh 21': format_rp(pph),
                    'Take Home': format_rp(bersih)
                })
            st.dataframe(pd.DataFrame(preview), use_container_width=True, hide_index=True)

            if st.button("🚀 Proses Payroll"):
                for _, r in df_k.iterrows():
                    gaji_pokok = r['gaji']
                    tunj_jab = round(gaji_pokok * 0.15, -2)
                    tunj_trans = 500000
                    tunj_makan = 600000
                    bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                    bpjs = hitung_bpjs(gaji_pokok, tunj_jab)
                    pph = hitung_pph21(bruto, PTKP_MAP.get(r['ptkp_status'] or "TK/0", 54000000), bpjs['total_k'])
                    bersih = bruto - bpjs['total_k'] - pph

                    c.execute("DELETE FROM payroll WHERE karyawan_id=? AND periode=?", (r['id'], periode))
                    c.execute('''INSERT INTO payroll (karyawan_id, periode, gaji_pokok, tunjangan_jabatan,
                                 tunjangan_transport, tunjangan_makan, bpjs_kesehatan_karyawan, bpjs_kesehatan_perusahaan,
                                 bpjs_jht_karyawan, bpjs_jht_perusahaan, bpjs_jp_karyawan, bpjs_jp_perusahaan,
                                 bpjs_jkk, bpjs_jkm, bpjs_jkp, pph21, total_penghasilan_bruto, total_potongan,
                                 gaji_bersih, status, tanggal_proses)
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                              (r['id'], periode, gaji_pokok, tunj_jab, tunj_trans, tunj_makan,
                               bpjs['kes_k'], bpjs['kes_p'], bpjs['jht_k'], bpjs['jht_p'],
                               bpjs['jp_k'], bpjs['jp_p'], bpjs['jkk'], bpjs['jkm'], bpjs['jkp'],
                               pph, bruto, bpjs['total_k'] + pph, bersih, "Final",
                               datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success(f"🎉 Payroll {periode} berhasil!")
                st.balloons()
                st.rerun()

    with tab2:
        df_p = pd.read_sql_query("""
            SELECT p.periode, k.employee_id, k.full_name, p.gaji_pokok, p.total_penghasilan_bruto as bruto,
                   p.bpjs_kesehatan_karyawan + p.bpjs_jht_karyawan + p.bpjs_jp_karyawan as bpjs,
                   p.pph21, p.gaji_bersih as take_home
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
                FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id
                WHERE p.periode=? ORDER BY k.full_name
            """, conn, params=(pilih_p,))

            if not df_slip.empty:
                opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_slip.iterrows()}
                pilih_k = st.selectbox("Pilih Karyawan", list(opsi.keys()))
                row = df_slip[df_slip['id'] == opsi[pilih_k]].iloc[0]

                html = f"""
                <div class="payroll-slip">
                    <h3>🏢 SLIP GAJI — {pilih_p}</h3>
                    <p><b>Employee ID:</b> {row['employee_id']} | <b>Nama:</b> {row['full_name']}</p>
                    <p><b>Jabatan:</b> {row['job_position']} | <b>Organization:</b> {row['organization']}</p>
                    <p><b>Bank:</b> {row['bank_name']} - {row['bank_account']}</p>
                    <h4>💰 Penghasilan</h4>
                    <div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(row['gaji_pokok'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Jabatan</span><span>{format_rp(row['tunjangan_jabatan'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Transport</span><span>{format_rp(row['tunjangan_transport'])}</span></div>
                    <div class="payroll-row"><span>Tunjangan Makan</span><span>{format_rp(row['tunjangan_makan'])}</span></div>
                    <div class="payroll-row"><b>Total Bruto</b><b>{format_rp(row['total_penghasilan_bruto'])}</b></div>
                    <h4>📉 Potongan</h4>
                    <div class="payroll-row"><span>BPJS Kesehatan (1%)</span><span>-{format_rp(row['bpjs_kesehatan_karyawan'])}</span></div>
                    <div class="payroll-row"><span>BPJS JHT (2%)</span><span>-{format_rp(row['bpjs_jht_karyawan'])}</span></div>
                    <div class="payroll-row"><span>BPJS JP (1%)</span><span>-{format_rp(row['bpjs_jp_karyawan'])}</span></div>
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
# ==================== 6. REKRUTMEN ====================
# ==================== 6. REKRUTMEN ====================
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Input Kandidat", "📋 Pipeline & Aksi"])

    with tab1:
        with st.form("form_kandidat", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat *")
                posisi = st.text_input("Posisi Dilamar")
                telepon = st.text_input("Telepon/WA")
                email = st.text_input("Email")
            with col2:
                sumber = st.selectbox("Sumber", ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair"])
                tgl_lamar = st.date_input("Tanggal Lamar", date.today())
                status = st.selectbox("Status", ["Proses","Wawancara","Diterima","Ditolak"])
                catatan = st.text_area("Catatan")
            if st.form_submit_button("💾 Simpan Kandidat Baru"):
                if nama:
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,catatan)
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan))
                    conn.commit()
                    log_aksi(st.session_state.username, "TAMBAH_KANDIDAT", nama)
                    st.success(f"✅ Kandidat {nama} berhasil disimpan!")
                    st.rerun()

    with tab2:
        # Inisialisasi session state untuk menyimpan notifikasi dan ID yang dipilih
        if "notif_kandidat" not in st.session_state:
            st.session_state.notif_kandidat = ""
        if "edit_kandidat_id" not in st.session_state:
            st.session_state.edit_kandidat_id = None

        # Tampilkan notifikasi sukses (jika ada)
        if st.session_state.notif_kandidat:
            st.success(st.session_state.notif_kandidat)
            st.session_state.notif_kandidat = "" # Reset setelah ditampilkan

        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        
        if not df_k.empty:
            # Metrik Atas
            html = '<div class="metric-grid">'
            html += metric_card("Total", str(len(df_k)), "", "card-blue")
            html += metric_card("Diterima", str(len(df_k[df_k['status']=='Diterima'])), "", "card-green")
            html += metric_card("Ditolak", str(len(df_k[df_k['status']=='Ditolak'])), "", "card-red")
            html += metric_card("Proses", str(len(df_k[df_k['status']=='Proses'])), "", "card-gold")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("---")
            st.info("👇 **Klik salah satu baris pada tabel di bawah untuk memunculkan menu Edit & Hapus.**")

            # Tabel Interaktif
            event = st.dataframe(
                df_k, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Menyimpan ID yang diklik ke dalam session state
            if len(event.selection.rows) > 0:
                selected_index = event.selection.rows[0]
                st.session_state.edit_kandidat_id = df_k.iloc[selected_index]['id']

            # Jika ada ID yang tersimpan di session state, tampilkan form edit
            if st.session_state.edit_kandidat_id is not None:
                # Ambil data terbaru dari database berdasarkan ID
                df_selected = pd.read_sql_query("SELECT * FROM kandidat WHERE id=?", conn, params=(st.session_state.edit_kandidat_id,))
                
                if not df_selected.empty:
                    selected_data = df_selected.iloc[0]
                    st.markdown(f"### ⚙️ Kelola Data: **{selected_data['nama']}**")
                    
                    col_edit, col_delete = st.columns([3, 1])

                    # === FITUR EDIT & SAVE ===
                    with col_edit:
                        with st.form("form_edit_kandidat"):
                            st.markdown("**✏️ Form Edit Kandidat**")
                            
                            try:
                                db_tgl = datetime.strptime(selected_data['tanggal_lamar'], "%Y-%m-%d").date()
                            except:
                                db_tgl = date.today()

                            col1, col2 = st.columns(2)
                            with col1:
                                edit_nama = st.text_input("Nama Kandidat", value=selected_data['nama'])
                            with col2:
                                edit_posisi = st.text_input("Posisi Dilamar", value=selected_data['posisi_dilamar'])
                            
                            col3, col4 = st.columns(2)
                            with col3:
                                edit_telepon = st.text_input("Telepon/WA", value=selected_data['telepon'])
                            with col4:
                                edit_email = st.text_input("Email", value=selected_data['email'])
                            
                            colA, colB, colC = st.columns(3)
                            with colA:
                                list_sumber = ["Job Portal","Referral","Walk-in","LinkedIn","Job Fair"]
                                idx_sumber = list_sumber.index(selected_data['sumber']) if selected_data['sumber'] in list_sumber else 0
                                edit_sumber = st.selectbox("Sumber", list_sumber, index=idx_sumber)
                            with colB:
                                edit_tgl = st.date_input("Tanggal Lamar", value=db_tgl)
                            with colC:
                                list_status = ["Proses","Wawancara","Diterima","Ditolak"]
                                idx_status = list_status.index(selected_data['status']) if selected_data['status'] in list_status else 0
                                edit_status = st.selectbox("Status", list_status, index=idx_status)
                            
                            edit_catatan = st.text_area("Catatan", value=selected_data['catatan'], height=100)

                            # TOMBOL SAVE / SIMPAN
                            if st.form_submit_button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                                c.execute('''UPDATE kandidat 
                                             SET nama=?, posisi_dilamar=?, telepon=?, email=?, sumber=?, tanggal_lamar=?, status=?, catatan=?
                                             WHERE id=?''',
                                          (edit_nama, edit_posisi, edit_telepon, edit_email, edit_sumber, str(edit_tgl), edit_status, edit_catatan, selected_data['id']))
                                conn.commit()
                                log_aksi(st.session_state.username, "EDIT_KANDIDAT", f"ID: {selected_data['id']}")
                                
                                # Simpan pesan sukses ke session state agar tidak hilang saat rerun
                                st.session_state.notif_kandidat = f"✅ Data kandidat {edit_nama} berhasil diupdate dan tersimpan di database!"
                                st.rerun()

                    # === FITUR DELETE ===
                    with col_delete:
                        st.markdown("**🗑️ Hapus Data**")
                        st.write("Klik tombol di bawah untuk menghapus kandidat ini secara permanen.")
                        if st.button("🗑️ Hapus Kandidat", type="primary", use_container_width=True):
                            c.execute("DELETE FROM kandidat WHERE id=?", (selected_data['id'],))
                            conn.commit()
                            log_aksi(st.session_state.username, "HAPUS_KANDIDAT", f"ID: {selected_data['id']}")
                            
                            st.session_state.notif_kandidat = f"✅ Kandidat {selected_data['nama']} berhasil dihapus!"
                            st.session_state.edit_kandidat_id = None # Reset form setelah dihapus
                            st.rerun()
        else:
            st.info("Belum ada kandidat")
# ==================== 8. EXIT CLEARANCE ====================
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
            conn.commit()
            st.rerun()

# ==================== 9. WHATSAPP REMINDER ====================
elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1></div>', unsafe_allow_html=True)

    tgl_skrg = datetime.now().date()

    st.markdown('<div class="section-header"><h3>📝 Kontrak Akan Habis (30 Hari)</h3></div>', unsafe_allow_html=True)
    tgl_30 = (tgl_skrg + timedelta(days=30)).strftime("%Y-%m-%d")
    df_k = pd.read_sql_query("""
        SELECT id, employee_id, full_name, job_position, mobile_phone, end_date
        FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date BETWEEN ? AND ?
        ORDER BY end_date
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"), tgl_30))

    if df_k.empty:
        st.success("✅ Tidak ada kontrak habis dalam 30 hari")
    else:
        for _, r in df_k.iterrows():
            try:
                hari = (datetime.strptime(r['end_date'], "%Y-%m-%d").date() - tgl_skrg).days
            except:
                hari = 0
            col1, col2 = st.columns([4, 1])
            with col1:
                st.warning(f"📝 **{r['full_name']}** ({r['job_position']}) - Habis {r['end_date']} ({hari} hari lagi)")
            with col2:
                if r['mobile_phone']:
                    nomor = str(r['mobile_phone']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['full_name']}, kontrak kerja Anda akan berakhir pada {r['end_date']} ({hari} hari lagi). Mohon konfirmasi ke HRD untuk perpanjangan. Terima kasih 🙏"
                    link = f"https://wa.me/{nomor}?text={quote(pesan)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="wa-btn">📱 WA</a>', unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>❌ Belum Absen Hari Ini</h3></div>', unsafe_allow_html=True)
    df_alpha = pd.read_sql_query("""
        SELECT full_name, mobile_phone, job_position FROM karyawan
        WHERE (resign_date IS NULL OR resign_date='') 
        AND id NOT IN (SELECT karyawan_id FROM absensi WHERE tanggal=?)
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"),))
    if df_alpha.empty:
        st.success("✅ Semua karyawan sudah absen hari ini")
    else:
        for _, r in df_alpha.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.error(f"❌ **{r['full_name']}** ({r['job_position']}) - Belum absen")
            with col2:
                if r['mobile_phone']:
                    nomor = str(r['mobile_phone']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['full_name']}, kami belum menerima absensi Anda hari ini ({tgl_skrg.strftime('%d-%m-%Y')}). Mohon konfirmasi. Terima kasih 🙏"
                    link = f"https://wa.me/{nomor}?text={quote(pesan)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="wa-btn">📱 WA</a>', unsafe_allow_html=True)

# ==================== 10. ASET ====================
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Input Aset", "📋 Daftar"])

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
                        c.execute('''INSERT INTO aset (kode,nama,kategori,lokasi,kondisi,nilai,tanggal_perolehan,
                                     penanggung_jawab,status,catatan) VALUES (?,?,?,?,?,?,?,?,?,?)''',
                                  (kode, nama, kategori, lokasi, kondisi, nilai, str(tgl), pj, status, ""))
                        conn.commit()
                        st.success("✅ Aset disimpan!")
                        st.rerun()
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

# ==================== 11. RUKO & TENANT ====================
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
                    c.execute('''INSERT INTO ruko (nama,alamat,status,penyewa,nilai_sewa,mulai_sewa,akhir_sewa,catatan)
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, alamat, status_r, penyewa, nilai, str(mulai), str(akhir), ""))
                    conn.commit()
                    st.rerun()

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
                    c.execute('''INSERT INTO tenant (nama,lokasi,kamar,penghuni,biaya_bulanan,status_ci,mulai,catatan)
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, lokasi, kamar, penghuni, biaya, ci, str(mulai), ""))
                    conn.commit()
                    st.rerun()

        df_t = pd.read_sql_query("SELECT * FROM tenant ORDER BY id DESC", conn)
        st.dataframe(df_t, use_container_width=True, hide_index=True)

# ==================== 12. LAPORAN ====================
elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["👥 HR", "💰 Payroll"])

    with tab1:
        df_k = pd.read_sql_query("SELECT * FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total Karyawan", str(len(df_k)), "", "card-blue")
            html += metric_card("Total Gaji Pokok", format_rp(df_k['gaji'].sum()), "", "card-gold")
            html += metric_card("Rata-rata Gaji", format_rp(df_k['gaji'].mean()), "", "card-purple")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("### 💰 Gaji per Organization")
            df_g = pd.read_sql_query("""
                SELECT organization, SUM(gaji) as total_gaji, COUNT(*) as jumlah
                FROM karyawan WHERE (resign_date IS NULL OR resign_date='') 
                GROUP BY organization ORDER BY total_gaji DESC
            """, conn)
            if not df_g.empty:
                chart = alt.Chart(df_g).mark_bar(cornerRadiusTopRight=8).encode(
                    x=alt.X('total_gaji:Q', title='Total Gaji'),
                    y=alt.Y('organization:N', sort='-x', title=''),
                    color=alt.Color('total_gaji:Q', scale=alt.Scale(scheme='goldgreen'), legend=None)
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

    with tab2:
        periode_ini = datetime.now().strftime("%Y-%m")
        df_p = pd.read_sql_query("SELECT * FROM payroll WHERE periode=?", conn, params=(periode_ini,))
        if not df_p.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total Payroll", format_rp(df_p['gaji_bersih'].sum()), f"{len(df_p)} karyawan", "card-gold")
            html += metric_card("Total Bruto", format_rp(df_p['total_penghasilan_bruto'].sum()), "", "card-blue")
            html += metric_card("Total BPJS", format_rp(df_p['total_potongan'].sum()), "", "card-orange")
            html += metric_card("Total PPh 21", format_rp(df_p['pph21'].sum()), "", "card-red")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Belum ada payroll bulan ini")

# ==================== 13. IMPORT/EXPORT ====================
elif pilihan == "💾 Import, Export & Backup":
    st.markdown('<div class="main-header"><h1>💾 Import, Export & Backup</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📤 Export", "📥 Import (Multi-Format)", "🗄️ Backup"])

    with tab1:
        tabel = st.selectbox("Tabel", ["karyawan","absensi","cuti","payroll","kandidat","resign","aset","ruko","tenant","log_aktivitas"])
        df = pd.read_sql_query(f"SELECT * FROM {tabel}", conn)
        if not df.empty:
            st.dataframe(df.head(100), use_container_width=True, hide_index=True)

            # Export ke Excel, CSV, JSON
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(f"📥 Download CSV", df.to_csv(index=False).encode(),
                                  f"{tabel}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            with col2:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df.to_excel(w, index=False)
                st.download_button(f"📥 Download Excel", buf.getvalue(),
                                  f"{tabel}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            with col3:
                st.download_button(f"📥 Download JSON", df.to_json(orient="records", indent=2).encode(),
                                  f"{tabel}_{datetime.now().strftime('%Y%m%d')}.json", "application/json")
        else:
            st.info("Kosong")

    with tab2:
        st.subheader("📥 Import File (Multi-Format)")
        st.markdown("""
        **Format yang didukung:**
        | Format | Ekstensi | Keterangan |
        |--------|----------|------------|
        | 📊 Excel | `.xlsx`, `.xls`, `.xlsm` | Semua sheet otomatis dibaca |
        | 📄 CSV | `.csv` | Auto-detect delimiter |
        | 📝 JSON | `.json` | Array of objects |
        | 📃 Word | `.docx` | Extract tabel dari dokumen |
        | 📕 PDF | `.pdf` | Extract tabel dari halaman |
        | 📄 Text | `.txt`, `.tsv` | Delimiter otomatis |
        """)

        tabel = st.selectbox("Tabel Target", ["karyawan", "kandidat", "aset", "absensi", "cuti"])

        with st.expander("📖 Panduan Kolom"):
            st.markdown("""
            **✅ Auto-Konversi Header** — `Employee ID` → `employee_id`, dst.

            **🔥 Kolom WAJIB:**
            - `karyawan`: **Employee ID** & **Full Name**
            - `kandidat`: **nama**
            - `aset`: **kode** & **nama**
            - `absensi`: **karyawan_id** & **tanggal**
            - `cuti`: **karyawan_id** & **jenis_cuti**
            """)

        f = st.file_uploader(
            f"📂 Upload file untuk {tabel}",
            type=["csv", "xlsx", "xls", "xlsm", "json", "docx", "pdf", "txt", "tsv"]
        )

        if f is not None:
            filename = f.name
            ext = filename.lower().split('.')[-1]

            with st.spinner(f"⏳ Membaca file .{ext}..."):
                try:
                    df_imp = parse_any_file(f, filename)

                    if df_imp.empty:
                        st.warning("⚠️ File terbaca tapi tidak ada data. Cek apakah file berisi tabel/data.")
                    else:
                        st.success(f"✅ File **{filename}** berhasil dibaca: **{len(df_imp)} baris, {len(df_imp.columns)} kolom**")

                        mapping, kolom_db = map_columns(df_imp, tabel)

                        st.markdown("### 🔄 Konversi Header")
                        map_data = []
                        tidak_match = []
                        for csv_col, db_col in mapping.items():
                            if db_col:
                                map_data.append({"Header File": csv_col, "→ Database": db_col, "Status": "✅ Cocok"})
                            else:
                                tidak_match.append(csv_col)
                                map_data.append({"Header File": csv_col, "→ Database": "-", "Status": "⚠️ Diabaikan"})
                        st.dataframe(pd.DataFrame(map_data), use_container_width=True, hide_index=True)

                        if tidak_match:
                            with st.expander(f"⚠️ {len(tidak_match)} kolom tidak cocok"):
                                st.write(tidak_match)

                        wajib_map = {
                            "karyawan": ["employee_id", "full_name"],
                            "kandidat": ["nama"],
                            "aset": ["kode", "nama"],
                            "absensi": ["karyawan_id", "tanggal"],
                            "cuti": ["karyawan_id", "jenis_cuti"],
                        }
                        wajib = wajib_map.get(tabel, [])
                        mapped_targets = [v for v in mapping.values() if v]
                        missing = [k for k in wajib if k not in mapped_targets]

                        if missing:
                            st.error(f"❌ **Kolom wajib tidak ditemukan**: `{'`, `'.join(missing)}`")
                        else:
                            st.success(f"✅ Semua kolom wajib ada: {', '.join(wajib)}")

                        st.markdown("### 📋 Preview Data")
                        df_preview = df_imp.copy()
                        rename_map = {k: v for k, v in mapping.items() if v}
                        df_preview = df_preview.rename(columns=rename_map)
                        st.dataframe(df_preview.head(10), use_container_width=True, hide_index=True)

                        if st.button("✅ PROSES IMPORT", type="primary"):
                            if missing:
                                st.error(f"❌ Kolom wajib hilang: {', '.join(missing)}")
                            else:
                                try:
                                    df_filtered = df_imp.rename(columns=rename_map)
                                    df_filtered = df_filtered[[cc for cc in df_filtered.columns if cc in kolom_db]]

                                    for k in kolom_db:
                                        if k == "id": continue
                                        if k not in df_filtered.columns:
                                            df_filtered[k] = None

                                    sukses = 0
                                    gagal = 0
                                    errors = []

                                    for idx, row in df_filtered.iterrows():
                                        try:
                                            cols = ", ".join(df_filtered.columns)
                                            placeholders = ", ".join(["?"] * len(df_filtered.columns))
                                            sql = f"INSERT INTO {tabel} ({cols}) VALUES ({placeholders})"
                                            c.execute(sql, tuple(row.values))
                                            sukses += 1
                                        except Exception as e:
                                            gagal += 1
                                            errors.append(f"Baris {idx+2}: {str(e)[:80]}")

                                    conn.commit()

                                    if sukses > 0:
                                        st.success(f"🎉 **{sukses} data berhasil diimport!**")
                                        st.balloons()
                                    if gagal > 0:
                                        st.warning(f"⚠️ **{gagal} baris gagal**")
                                        with st.expander(f"Lihat {len(errors)} error"):
                                            for e in errors[:20]:
                                                st.caption(f"• {e}")
                                    if sukses > 0:
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error database: {e}")

                except ImportError as e:
                    st.error(f"❌ **Package belum terinstall**: {e}")
                    st.info("💡 Tambahkan package di `requirements.txt` lalu push ulang ke GitHub.")

                except Exception as e:
                    st.error(f"❌ **Error**: {str(e)[:500]}")

    with tab3:
        st.markdown("### 🗄️ Backup Database")
        conn.commit()
        try:
            with open('hris_ga.db', 'rb') as f:
                st.download_button("💾 Download Backup DB", f.read(),
                                  f"backup_hris_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                                  "application/octet-stream")
        except Exception as e:
            st.warning(f"Backup tidak tersedia: {e}")

# ==================== 14. USER MANAGEMENT ====================
elif pilihan == "👤 Manajemen User" and st.session_state.role == "admin":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1></div>', unsafe_allow_html=True)

    with st.form("form_user", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
        with col2:
            n = st.text_input("Nama Lengkap")
            r = st.selectbox("Role", ["hrd","admin","viewer"])
        if st.form_submit_button("💾 Simpan"):
            if u and p and n:
                try:
                    c.execute("INSERT INTO users (username,password,nama_lengkap,role) VALUES (?,?,?,?)",
                              (u, hash_password(p), n, r))
                    conn.commit()
                    st.success(f"✅ User {u} ditambahkan!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("❌ Username sudah ada")

    df_u = pd.read_sql_query("SELECT id, username, nama_lengkap, role, aktif FROM users", conn)
    st.dataframe(df_u, use_container_width=True, hide_index=True)

# ==================== 15. LOG ====================
elif pilihan == "📝 Log Aktivitas" and st.session_state.role == "admin":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)

    df_log = pd.read_sql_query("SELECT * FROM log_aktivitas ORDER BY id DESC LIMIT 200", conn)
    if not df_log.empty:
        st.dataframe(df_log, use_container_width=True, hide_index=True)
        st.download_button("📥 Export", df_log.to_csv(index=False).encode(), "log.csv", "text/csv")
    else:
        st.info("Belum ada log")
