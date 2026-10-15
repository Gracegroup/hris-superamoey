import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
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

# ==================== RESET & CREATE TABLES ====================
# Hapus tabel lama jika struktur berbeda (sekali saja saat deploy baru)
try:
    c.execute("SELECT tanggal_resign FROM karyawan LIMIT 1")
except:
    c.execute("DROP TABLE IF EXISTS karyawan")
    conn.commit()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT,
    nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')

c.execute('''CREATE TABLE IF NOT EXISTS karyawan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE, nama TEXT, barcode TEXT, organization TEXT,
    jabatan TEXT, job_level TEXT, tanggal_masuk TEXT, tanggal_resign TEXT,
    status_karyawan TEXT, tanggal_berakhir TEXT, sign_date TEXT, email TEXT,
    tanggal_lahir TEXT, umur TEXT, tempat_lahir TEXT, alamat_ktp TEXT,
    alamat_domisili TEXT, npwp TEXT, status_ptkp TEXT, status_pajak TEXT,
    tax_config TEXT, bank TEXT, rekening TEXT, nama_rekening TEXT,
    bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_16 TEXT,
    telepon TEXT, telepon2 TEXT, cabang TEXT, cabang_pusat TEXT,
    agama TEXT, jenis_kelamin TEXT, status_pernikahan TEXT, golongan_darah TEXT,
    kewarganegaraan TEXT, currency TEXT, masa_kerja TEXT, payment_schedule TEXT,
    approval_line TEXT, manager TEXT, grade TEXT, class TEXT,
    cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT,
    passport TEXT, passport_exp TEXT, jenis_dok_potong TEXT,
    nomor_dok_potong TEXT, tanggal_dok_potong TEXT, tin TEXT,
    divisi TEXT, keterangan TEXT, gaji REAL DEFAULT 0, aktif INTEGER DEFAULT 1)''')

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
    
    try:
        aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE tanggal_resign IS NULL OR tanggal_resign='' OR tanggal_resign='None'").fetchone()[0]
        resign_cnt = c.execute("SELECT COUNT(*) FROM karyawan WHERE tanggal_resign IS NOT NULL AND tanggal_resign!='' AND tanggal_resign!='None'").fetchone()[0]
    except:
        aktif = 0
        resign_cnt = 0
    
    total = aktif + resign_cnt
    kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    diterima = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Diterima'").fetchone()[0]
    ditolak = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Ditolak'").fetchone()[0]
    proses = c.execute("SELECT COUNT(*) FROM kandidat WHERE status='Proses'").fetchone()[0]
    tgl_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    tgl_skrg = datetime.now().strftime("%Y-%m-%d")
    
    try:
        kontrak_habis = c.execute("SELECT COUNT(*) FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') AND tanggal_berakhir BETWEEN ? AND ?", (tgl_skrg, tgl_30)).fetchone()[0]
    except:
        kontrak_habis = 0

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
    if total == 0: total = 1
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

    st.markdown('<div class="section-header"><h3>📊 Analitik Jabatan & Divisi</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👔 Jabatan (Aktif)**")
        df_jab = pd.read_sql_query("SELECT jabatan as JABATAN, COUNT(*) as JML FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') AND jabatan IS NOT NULL GROUP BY jabatan ORDER BY JML DESC", conn)
        if not df_jab.empty:
            chart = alt.Chart(df_jab).mark_bar(cornerRadiusTopRight=10, cornerRadiusBottomRight=10).encode(
                x=alt.X('JML:Q', title='Jumlah'),
                y=alt.Y('JABATAN:N', sort='-x', title=''),
                color=alt.Color('JML:Q', scale=alt.Scale(scheme='blues'), legend=None)
            ).properties(height=max(300, len(df_jab)*35))
            st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("**🏢 Divisi (Aktif)**")
        df_div = pd.read_sql_query("SELECT divisi as DIVISI, COUNT(*) as JML FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') AND divisi IS NOT NULL GROUP BY divisi ORDER BY JML DESC", conn)
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
                nama = st.text_input("Nama Lengkap *")
                barcode = st.text_input("Barcode")
                organization = st.text_input("Organization")
            with col2:
                jabatan = st.text_input("Job Position")
                job_level = st.selectbox("Job Level", ["staff", "Non - Staff", "Supervisor", "Foreman", "Manager"])
                tanggal_masuk = st.date_input("Join Date", date.today())
                status_karyawan = st.selectbox("Status Karyawan", ["Contract", "Tetap", "Probation", "Magang"])
            with col3:
                tanggal_berakhir = st.date_input("End Date", date.today() + timedelta(days=365))
                email = st.text_input("Email")
                telepon = st.text_input("Mobile Phone")
                gaji = st.number_input("Gaji (Rp)", min_value=0.0, step=100000.0)

            col4, col5, col6 = st.columns(3)
            with col4:
                jenis_kelamin = st.selectbox("Gender", ["L", "P"])
                agama = st.selectbox("Religion", ["Islam", "Christian", "Catholic", "Hindu", "Buddha", "Konghucu"])
                status_pernikahan = st.selectbox("Marital Status", ["Single", "Married", "Widower", "Widow"])
                golongan_darah = st.selectbox("Blood Type", ["", "A", "B", "AB", "O"])
            with col5:
                tempat_lahir = st.text_input("Birth Place")
                tanggal_lahir = st.date_input("Birth Date", date(1995, 1, 1))
                status_ptkp = st.selectbox("PTKP Status", list(PTKP_MAP.keys()))
                npwp = st.text_input("NPWP")
            with col6:
                alamat_ktp = st.text_area("Alamat KTP")
                alamat_domisili = st.text_area("Alamat Domisili")
                nik_16 = st.text_input("NIK (NPWP 16 Digit)")
                kewarganegaraan = st.text_input("Nationality", value="IDN")

            col7, col8 = st.columns(2)
            with col7:
                bank = st.selectbox("Bank Name", ["BCA","Mandiri","BNI","BRI","CIMB","Permata"])
                rekening = st.text_input("Bank Account")
                nama_rekening = st.text_input("Bank Account Holder")
                bpjs_ketenagakerjaan = st.text_input("BPJS Ketenagakerjaan")
            with col8:
                bpjs_kesehatan = st.text_input("BPJS Kesehatan")
                divisi = st.selectbox("Divisi", ["PRODUCT SUPPORT","AFTER MARKET & INVENTORY WAREHOUSE","SALES & OPERATION","HRD","FINANCE","GA","PARTS","Adm.PS"])
                manager = st.text_input("Manager")
                tanggal_resign = st.text_input("Resign Date (kosongkan jika aktif)", value="")

            keterangan = st.text_area("Keterangan")

            if st.form_submit_button("💾 Simpan"):
                if employee_id and nama:
                    try:
                        c.execute('''INSERT INTO karyawan (employee_id, nama, barcode, organization, jabatan, job_level,
                                     tanggal_masuk, tanggal_resign, status_karyawan, tanggal_berakhir, email, tanggal_lahir,
                                     tempat_lahir, alamat_ktp, alamat_domisili, npwp, status_ptkp, bank, rekening, nama_rekening,
                                     bpjs_ketenagakerjaan, bpjs_kesehatan, nik_16, telepon, agama, jenis_kelamin, status_pernikahan,
                                     golongan_darah, kewarganegaraan, divisi, manager, gaji, keterangan)
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                  (employee_id, nama, barcode, organization, jabatan, job_level,
                                   str(tanggal_masuk), tanggal_resign, status_karyawan, str(tanggal_berakhir),
                                   email, str(tanggal_lahir), tempat_lahir, alamat_ktp, alamat_domisili, npwp,
                                   status_ptkp, bank, rekening, nama_rekening, bpjs_ketenagakerjaan, bpjs_kesehatan,
                                   nik_16, telepon, agama, jenis_kelamin, status_pernikahan, golongan_darah,
                                   kewarganegaraan, divisi, manager, gaji, keterangan))
                        conn.commit()
                        st.success(f"✅ Karyawan {nama} disimpan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Employee ID sudah ada")
                else:
                    st.warning("Employee ID & Nama wajib diisi")

    with tab2:
        df_k = pd.read_sql_query("SELECT * FROM karyawan ORDER BY id DESC", conn)
        st.dataframe(df_k, use_container_width=True, hide_index=True)

    with tab3:
        df_k = pd.read_sql_query("SELECT id, employee_id, nama FROM karyawan ORDER BY nama", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['nama']}": r['id'] for _, r in df_k.iterrows()}
            pilih = st.selectbox("🔍 Pilih Karyawan", list(opsi.keys()))
            kid = opsi[pilih]
            d = pd.read_sql_query("SELECT * FROM karyawan WHERE id=?", conn, params=(kid,)).iloc[0]

            html = '<div class="metric-grid">'
            html += metric_card("Jabatan", d['jabatan'] or "-", "", "card-blue")
            html += metric_card("Divisi", d['divisi'] or "-", "", "card-purple")
            html += metric_card("Status", d['status_karyawan'] or "-", "", "card-green" if not d['tanggal_resign'] else "card-red")
            html += metric_card("Gaji", format_rp(d['gaji']), "", "card-gold")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown(f"""
            **Employee ID**: {d['employee_id']}  |  **Gender**: {d['jenis_kelamin'] or '-'}  |  **Agama**: {d['agama'] or '-'}  
            **Telepon**: {d['telepon'] or '-'}  |  **Email**: {d['email'] or '-'}  
            **Alamat KTP**: {d['alamat_ktp'] or '-'}  
            **Alamat Domisili**: {d['alamat_domisili'] or '-'}  
            **Bank**: {d['bank'] or '-'} - {d['rekening'] or '-'}  
            **NPWP**: {d['npwp'] or '-'}  |  **PTKP**: {d['status_ptkp'] or '-'}  
            **Masuk**: {d['tanggal_masuk']}  |  **End Date**: {d['tanggal_berakhir']}  
            **Manager**: {d['manager'] or '-'}
            """)

# ==================== 3. ABSENSI ====================
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["✍️ Input Absensi", "📋 Rekap", "📊 Statistik"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, nama FROM karyawan WHERE tanggal_resign IS NULL OR tanggal_resign='' OR tanggal_resign='None' ORDER BY nama", conn)
        if df_k.empty:
            st.warning("Belum ada karyawan aktif")
        else:
            opsi = {f"{r['employee_id']} - {r['nama']}": r['id'] for _, r in df_k.iterrows()}

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
            SELECT a.tanggal, k.employee_id, k.nama, k.jabatan, a.jam_masuk, a.jam_keluar,
                   a.status, a.terlambat_menit, a.keterangan
            FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id
            WHERE a.tanggal BETWEEN ? AND ?
            ORDER BY a.tanggal DESC, k.nama
        """, conn, params=(str(tgl_dari), str(tgl_sampai)))
        st.dataframe(df_a, use_container_width=True, hide_index=True)
        if not df_a.empty:
            csv = df_a.to_csv(index=False).encode()
            st.download_button("📥 Export CSV", csv, "absensi.csv", "text/csv")

    with tab3:
        periode = datetime.now().strftime("%Y-%m")
        df_stat = pd.read_sql_query("""
            SELECT k.nama, k.jabatan,
                   SUM(CASE WHEN a.status='Hadir' THEN 1 ELSE 0 END) as hadir,
                   SUM(CASE WHEN a.status='Izin' THEN 1 ELSE 0 END) as izin,
                   SUM(CASE WHEN a.status='Sakit' THEN 1 ELSE 0 END) as sakit,
                   SUM(CASE WHEN a.status='Alpha' THEN 1 ELSE 0 END) as alpha,
                   SUM(a.terlambat_menit) as total_telat
            FROM karyawan k LEFT JOIN absensi a ON k.id = a.karyawan_id AND substr(a.tanggal,1,7) = ?
            WHERE (k.tanggal_resign IS NULL OR k.tanggal_resign='')
            GROUP BY k.nama ORDER BY hadir DESC
        """, conn, params=(periode,))
        st.dataframe(df_stat, use_container_width=True, hide_index=True)

# ==================== 4. CUTI ====================
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Ajukan", "📋 Daftar & Approval"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, nama FROM karyawan WHERE tanggal_resign IS NULL OR tanggal_resign=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['nama']}": r['id'] for _, r in df_k.iterrows()}
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
            SELECT c.id, k.employee_id, k.nama, c.jenis_cuti, c.tanggal_mulai, c.tanggal_selesai,
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
                opsi = {f"#{r['id']} - {r['nama']} ({r['lama_hari']}h)": r['id'] for _, r in menunggu.iterrows()}
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
            SELECT id, employee_id, nama, gaji, status_ptkp, jabatan
            FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') AND gaji > 0 ORDER BY nama
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
                pph = hitung_pph21(bruto, PTKP_MAP.get(r['status_ptkp'] or "TK/0", 54000000), bpjs['total_k'])
                bersih = bruto - bpjs['total_k'] - pph
                preview.append({
                    'Nama': r['nama'], 'Jabatan': r['jabatan'],
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
                    pph = hitung_pph21(bruto, PTKP_MAP.get(r['status_ptkp'] or "TK/0", 54000000), bpjs['total_k'])
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
            SELECT p.periode, k.employee_id, k.nama, p.gaji_pokok, p.total_penghasilan_bruto as bruto,
                   p.bpjs_kesehatan_karyawan + p.bpjs_jht_karyawan + p.bpjs_jp_karyawan as bpjs,
                   p.pph21, p.gaji_bersih as take_home
            FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id
            ORDER BY p.periode DESC, k.nama
        """, conn)
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    with tab3:
        periode_list = pd.read_sql_query("SELECT DISTINCT periode FROM payroll ORDER BY periode DESC", conn)
        if not periode_list.empty:
            pilih_p = st.selectbox("Periode", periode_list['periode'].tolist())
            df_slip = pd.read_sql_query("""
                SELECT p.*, k.employee_id, k.nama, k.jabatan, k.divisi, k.bank, k.rekening
                FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id
                WHERE p.periode=? ORDER BY k.nama
            """, conn, params=(pilih_p,))

            if not df_slip.empty:
                opsi = {f"{r['employee_id']} - {r['nama']}": r['id'] for _, r in df_slip.iterrows()}
                pilih_k = st.selectbox("Pilih Karyawan", list(opsi.keys()))
                row = df_slip[df_slip['id'] == opsi[pilih_k]].iloc[0]

                html = f"""
                <div class="payroll-slip">
                    <h3>🏢 SLIP GAJI — {pilih_p}</h3>
                    <p><b>Employee ID:</b> {row['employee_id']} | <b>Nama:</b> {row['nama']}</p>
                    <p><b>Jabatan:</b> {row['jabatan']} | <b>Divisi:</b> {row['divisi']}</p>
                    <p><b>Bank:</b> {row['bank']} - {row['rekening']}</p>
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
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Input Kandidat", "📋 Pipeline"])

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
            if st.form_submit_button("💾 Simpan"):
                if nama:
                    c.execute('''INSERT INTO kandidat (nama,posisi_dilamar,telepon,email,sumber,tanggal_lamar,status,catatan)
                                 VALUES (?,?,?,?,?,?,?,?)''',
                              (nama, posisi, telepon, email, sumber, str(tgl_lamar), status, catatan))
                    conn.commit()
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
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            st.dataframe(df_k, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada kandidat")

# ==================== 7. RESIGN ====================
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Input Resign", "📋 Daftar"])

    with tab1:
        df_k = pd.read_sql_query("SELECT id, employee_id, nama FROM karyawan WHERE tanggal_resign IS NULL OR tanggal_resign=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['nama']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_resign"):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                tgl = st.date_input("Tanggal Resign", date.today())
                jenis = st.selectbox("Jenis", ["Resign Sendiri","PHK","Pensiun","Kontrak Habis"])
                alasan = st.text_area("Alasan")
                interview = st.text_area("Hasil Exit Interview")
                if st.form_submit_button("💾 Simpan"):
                    kid = opsi[pilih]
                    c.execute('''INSERT INTO resign (karyawan_id,tanggal_resign,alasan,jenis,exit_interview,clearance_status)
                                 VALUES (?,?,?,?,?,?)''', (kid, str(tgl), alasan, jenis, interview, "Proses"))
                    c.execute("UPDATE karyawan SET tanggal_resign=? WHERE id=?", (str(tgl), kid))
                    conn.commit()
                    st.success("✅ Data resign disimpan!")
                    st.rerun()

    with tab2:
        df_r = pd.read_sql_query("""
            SELECT r.id, k.employee_id, k.nama, r.tanggal_resign, r.jenis, r.alasan, r.clearance_status
            FROM resign r JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC
        """, conn)
        st.dataframe(df_r, use_container_width=True, hide_index=True)

# ==================== 8. EXIT CLEARANCE ====================
elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1></div>', unsafe_allow_html=True)

    df_r = pd.read_sql_query("""
        SELECT r.id, k.nama, k.jabatan, r.tanggal_resign, r.clearance_status
        FROM resign r JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC
    """, conn)
    if df_r.empty:
        st.info("Belum ada data")
    else:
        st.dataframe(df_r, use_container_width=True, hide_index=True)
        opsi = {f"{r['nama']} ({r['tanggal_resign']})": r['id'] for _, r in df_r.iterrows()}
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
        SELECT id, employee_id, nama, jabatan, telepon, tanggal_berakhir
        FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') AND tanggal_berakhir BETWEEN ? AND ?
        ORDER BY tanggal_berakhir
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"), tgl_30))

    if df_k.empty:
        st.success("✅ Tidak ada kontrak habis dalam 30 hari")
    else:
        for _, r in df_k.iterrows():
            try:
                hari = (datetime.strptime(r['tanggal_berakhir'], "%Y-%m-%d").date() - tgl_skrg).days
            except:
                hari = 0
            col1, col2 = st.columns([4, 1])
            with col1:
                st.warning(f"📝 **{r['nama']}** ({r['jabatan']}) - Habis {r['tanggal_berakhir']} ({hari} hari lagi)")
            with col2:
                if r['telepon']:
                    nomor = str(r['telepon']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['nama']}, kontrak kerja Anda akan berakhir pada {r['tanggal_berakhir']} ({hari} hari lagi). Mohon konfirmasi ke HRD untuk perpanjangan. Terima kasih 🙏"
                    link = f"https://wa.me/{nomor}?text={quote(pesan)}"
                    st.markdown(f'<a href="{link}" target="_blank" class="wa-btn">📱 WA</a>', unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h3>❌ Belum Absen Hari Ini</h3></div>', unsafe_allow_html=True)
    df_alpha = pd.read_sql_query("""
        SELECT nama, telepon, jabatan FROM karyawan
        WHERE (tanggal_resign IS NULL OR tanggal_resign='') 
        AND id NOT IN (SELECT karyawan_id FROM absensi WHERE tanggal=?)
    """, conn, params=(tgl_skrg.strftime("%Y-%m-%d"),))
    if df_alpha.empty:
        st.success("✅ Semua karyawan sudah absen hari ini")
    else:
        for _, r in df_alpha.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.error(f"❌ **{r['nama']}** ({r['jabatan']}) - Belum absen")
            with col2:
                if r['telepon']:
                    nomor = str(r['telepon']).replace('-','').replace(' ','').replace('+','')
                    if nomor.startswith('0'): nomor = '62' + nomor[1:]
                    pesan = f"Halo {r['nama']}, kami belum menerima absensi Anda hari ini ({tgl_skrg.strftime('%d-%m-%Y')}). Mohon konfirmasi. Terima kasih 🙏"
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
        df_k = pd.read_sql_query("SELECT * FROM karyawan WHERE tanggal_resign IS NULL OR tanggal_resign=''", conn)
        if not df_k.empty:
            html = '<div class="metric-grid">'
            html += metric_card("Total Karyawan", str(len(df_k)), "", "card-blue")
            html += metric_card("Total Gaji Pokok", format_rp(df_k['gaji'].sum()), "", "card-gold")
            html += metric_card("Rata-rata Gaji", format_rp(df_k['gaji'].mean()), "", "card-purple")
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

            st.markdown("### 💰 Gaji per Departemen")
            df_g = pd.read_sql_query("""
                SELECT divisi, SUM(gaji) as total_gaji, COUNT(*) as jumlah
                FROM karyawan WHERE (tanggal_resign IS NULL OR tanggal_resign='') 
                GROUP BY divisi ORDER BY total_gaji DESC
            """, conn)
            if not df_g.empty:
                chart = alt.Chart(df_g).mark_bar(cornerRadiusTopRight=8).encode(
                    x=alt.X('total_gaji:Q', title='Total Gaji'),
                    y=alt.Y('divisi:N', sort='-x', title=''),
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

    tab1, tab2, tab3 = st.tabs(["📤 Export", "📥 Import", "🗄️ Backup"])

    with tab1:
        tabel = st.selectbox("Tabel", ["karyawan","absensi","cuti","payroll","kandidat","resign","aset","ruko","tenant","log_aktivitas"])
        df = pd.read_sql_query(f"SELECT * FROM {tabel}", conn)
        if not df.empty:
            st.dataframe(df.head(100), use_container_width=True, hide_index=True)
            st.download_button(f"📥 Download {tabel}.csv", df.to_csv(index=False).encode(),
                              f"{tabel}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("Kosong")

    with tab2:
        st.subheader("📥 Import CSV")
        tabel = st.selectbox("Tabel Target", ["karyawan", "kandidat", "aset", "absensi", "cuti"])

        with st.expander("📖 Format CSV"):
            st.markdown("""
            **Tips:**
            1. Delimiter koma (`,`) atau pilih dropdown
            2. Kalau ada koma dalam data, apit dengan `"..."`  
            3. Header CSV harus sesuai kolom database
            """)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            delimiter = st.selectbox("Delimiter CSV", [",", ";", "Tab (\\t)", "|"])
            delim_actual = "\t" if "Tab" in delimiter else delimiter
        with col_d2:
            encoding = st.selectbox("Encoding", ["utf-8", "latin-1", "iso-8859-1", "utf-8-sig"])

        f = st.file_uploader(f"📂 Upload file CSV untuk {tabel}", type=["csv", "txt"])

        if f is not None:
            try:
                df_imp = pd.read_csv(
                    f, delimiter=delim_actual, encoding=encoding,
                    on_bad_lines='skip', engine='python'
                )

                st.success(f"✅ File berhasil dibaca: **{len(df_imp)} baris, {len(df_imp.columns)} kolom**")
                st.markdown("### 📋 Preview Data")
                st.dataframe(df_imp.head(20), use_container_width=True, hide_index=True)

                with st.expander(f"📊 Info Kolom"):
                    st.code(", ".join(df_imp.columns.tolist()))
                    kolom_wajib = {
                        "karyawan": ["employee_id", "nama"],
                        "kandidat": ["nama"],
                        "aset": ["kode", "nama"],
                        "absensi": ["karyawan_id", "tanggal"],
                        "cuti": ["karyawan_id", "jenis_cuti"],
                    }
                    wajib = kolom_wajib.get(tabel, [])
                    missing = [k for k in wajib if k not in df_imp.columns]
                    if missing:
                        st.error(f"❌ Kolom wajib hilang: **{', '.join(missing)}**")
                    else:
                        st.success("✅ Semua kolom wajib ada!")

                if st.button("✅ PROSES IMPORT", type="primary"):
                    if missing:
                        st.error(f"❌ Kolom wajib hilang: {', '.join(missing)}")
                    else:
                        try:
                            cur = conn.execute(f"PRAGMA table_info({tabel})")
                            kolom_db = [r[1] for r in cur.fetchall()]
                            df_filtered = df_imp[[cc for cc in df_imp.columns if cc in kolom_db]]

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

            except pd.errors.ParserError as e:
                st.error(f"❌ **Error parsing CSV**: {str(e)[:200]}")
                st.info("💡 Coba ganti Delimiter atau Encoding di atas")

            except UnicodeDecodeError as e:
                st.error(f"❌ **Error encoding**: {str(e)[:200]}")
                st.info("💡 Coba ganti Encoding ke **latin-1** atau **utf-8-sig**")

            except Exception as e:
                st.error(f"❌ **Error**: {str(e)[:300]}")

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
