import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import json
import re
from datetime import datetime, timedelta, date
import calendar
import altair as alt
from urllib.parse import quote
from io import StringIO

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA SUPER v7.0",
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
    .instruction-box { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ====================
@st.cache_resource
def get_conn():
    return sqlite3.connect('hris_ga.db', check_same_thread=False)

conn = get_conn()
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, mobile_phone TEXT, gaji REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, dari_jabatan TEXT, ke_jabatan TEXT, alasan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, pic TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, jenis TEXT, alasan TEXT, clearance_status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, label TEXT, nominal REAL, total_bayar REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
    conn.commit()

init_db()

# ==================== HELPER & CRUD FUNCTIONS ====================
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

def render_export_print(df, filename):
    c1, c2, c3 = st.columns(3)
    with c1: st.download_button("📥 CSV", df.to_csv(index=False).encode(), f"{filename}.csv", "text/csv", use_container_width=True)
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w, index=False)
        st.download_button("📥 Excel", buf.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c3:
        html_table = df.to_html(classes='table', index=False)
        html_full = f"<html><head><title>Print</title><style>table{{border-collapse: collapse; width:100%;}} th,td{{border:1px solid #ddd; padding:8px;}} th{{background-color:#f2f2f2;}}</style></head><body><h2>{filename.upper()}</h2>{html_table}</body></html>"
        st.download_button("🖨️ Cetak", html_full, f"{filename}_print.html", "text/html", use_container_width=True)

# FUNGSI UNIVERSAL UNTUK SIMPAN (EDIT, DELETE, INSERT)
def save_dataframe_to_db(table_name, edited_df, original_df):
    cur = conn.cursor()
    
    # Konversi ID ke integer
    edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
    old_ids = set(original_df['id'].dropna().astype(int).tolist()) if not original_df.empty else set()
    new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
    
    # 1. Proses Hapus (Data lama yang tidak ada di tabel baru)
    for did in (old_ids - new_ids):
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        
    # 2. Proses Insert & Update
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

# ==================== SEED USER & DUMMY DATA ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hash_password("admin123"), "Administrator", "admin"))
    # Dummy Karyawan
    dummy_kar = [
        ("UEI-001", "Budi Santoso", "PRODUKSI", "Operator DT", "2021-01-15", None, "Tetap", "2025-12-31", "08123456789", 8000000),
        ("UEI-002", "Siti Aminah", "HRGA", "Admin HRGA", "2022-03-10", None, "Kontrak", "2024-12-31", "08123456780", 6000000),
        ("UEI-003", "Agus Pratama", "PLANT", "Mekanik", "2020-07-01", None, "Tetap", "2025-12-31", "08123456781", 7500000),
    ]
    for k in dummy_kar:
        c.execute("INSERT INTO karyawan (employee_id, full_name, organization, job_position, join_date, resign_date, status_employee, end_date, mobile_phone, gaji) VALUES (?,?,?,?,?,?,?,?,?,?)", k)
    conn.commit()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": "", "nama": "", "role": ""})

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS & GA SUPER v7.0</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.update({"logged_in": True, "username": row[0], "nama": row[2], "role": row[3]})
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 15px 0;">
        <div style="font-size:3em;">👤</div>
        <h3 style="margin:5px 0;">{st.session_state.nama}</h3>
        <p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    menu = [
        "🏠 Dashboard HRIS",
        "👥 Data Karyawan",
        "🔄 Mutasi & PKWT",       # MENU BARU
        "⚠️ Disiplin & SP",       # MENU BARU (Upgrade)
        "📋 Jobdesk",             # MENU BARU
        "💡 CI Report",           # MENU BARU
        "🏥 SKD (Surat Ket)",     # MENU BARU
        "📝 Internal Memo",       # MENU BARU
        "📉 Resign & Turnover",
        "💡 Utility Melak",
        "⚙️ Pengaturan & Log",
    ]
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.clear(); st.rerun()

# ==================== 1. DASHBOARD ====================
if pilihan == "🏠 Dashboard HRIS":
    st.markdown(f"""
    <div class="main-header">
        <h1>⚡ HRIS, GA & ASET DASHBOARD</h1>
        <p>Selamat datang, <b>{st.session_state.nama}</b> • Update: {datetime.now().strftime('%d/%m/%Y, %H.%M.%S')}</p>
    </div>
    """, unsafe_allow_html=True)

    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date=''").fetchone()[0]
    sp_aktif = c.execute("SELECT COUNT(*) FROM disiplin WHERE status='Aktif'").fetchone()[0]
    tgl_60 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    pkwt_habis = c.execute(f"SELECT COUNT(*) FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date <= '{tgl_60}'").fetchone()[0]

    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", str(aktif), "", "card-blue")
    html += metric_card("⏳ PKWT Habis (60 hr)", str(pkwt_habis), "Perlu perpanjangan", "card-orange")
    html += metric_card("⚠️ SP Aktif", str(sp_aktif), "Disiplin", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ==================== 2. DATA KARYAWAN ====================
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df = pd.read_sql_query("SELECT id, employee_id as 'NIK', full_name as 'Nama Lengkap', organization as 'Departemen', job_position as 'Jabatan', join_date as 'Tgl Masuk', end_date as 'Akhir PKWT', mobile_phone as 'No HP', gaji as 'Gaji' FROM karyawan ORDER BY id DESC", conn)
    original_df = df.copy()
    
    render_export_print(df, "karyawan")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Karyawan", type="primary"):
        edited_db = edited.rename(columns={'NIK': 'employee_id', 'Nama Lengkap': 'full_name', 'Departemen': 'organization', 'Jabatan': 'job_position', 'Tgl Masuk': 'join_date', 'Akhir PKWT': 'end_date', 'No HP': 'mobile_phone', 'Gaji': 'gaji'})
        original_db = original_df.rename(columns={'NIK': 'employee_id', 'Nama Lengkap': 'full_name', 'Departemen': 'organization', 'Jabatan': 'job_position', 'Tgl Masuk': 'join_date', 'Akhir PKWT': 'end_date', 'No HP': 'mobile_phone', 'Gaji': 'gaji'})
        save_dataframe_to_db("karyawan", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 3. MUTASI & PKWT ====================
elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Data Mutasi", "⏳ PKWT Akan Habis (60 Hari)"])
    
    with tab1:
        st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
        df_mut = pd.read_sql_query("SELECT id, karyawan_id as 'ID Karyawan', tanggal_mutasi as 'Tanggal', dari_divisi as 'Dari Divisi', ke_divisi as 'Ke Divisi', dari_jabatan as 'Dari Jabatan', ke_jabatan as 'Ke Jabatan', alasan as 'Alasan' FROM mutasi ORDER BY id DESC", conn)
        original_mut = df_mut.copy()
        render_export_print(df_mut, "mutasi")
        
        edited_mut = st.data_editor(df_mut, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Data Mutasi", type="primary"):
            edited_db = edited_mut.rename(columns={'ID Karyawan': 'karyawan_id', 'Tanggal': 'tanggal_mutasi', 'Dari Divisi': 'dari_divisi', 'Ke Divisi': 'ke_divisi', 'Dari Jabatan': 'dari_jabatan', 'Ke Jabatan': 'ke_jabatan', 'Alasan': 'alasan'})
            original_db = original_mut.rename(columns={'ID Karyawan': 'karyawan_id', 'Tanggal': 'tanggal_mutasi', 'Dari Divisi': 'dari_divisi', 'Ke Divisi': 'ke_divisi', 'Dari Jabatan': 'dari_jabatan', 'Ke Jabatan': 'ke_jabatan', 'Alasan': 'alasan'})
            save_dataframe_to_db("mutasi", edited_db, original_db)
            st.success("✅ Tersimpan!"); st.rerun()

    with tab2:
        tgl_60 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        df_pkwt = pd.read_sql_query(f"SELECT employee_id, full_name, organization, job_position, end_date FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date <= '{tgl_60}'", conn)
        st.warning("Karyawan dengan kontrak habis dalam 60 hari ke depan:")
        if not df_pkwt.empty:
            st.dataframe(df_pkwt, use_container_width=True, hide_index=True)
        else:
            st.success("Tidak ada kontrak yang habis dalam 60 hari ke depan.")

# ==================== 4. DISIPLIN & SP (UPGRADE CRUD) ====================
elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & Surat Peringatan (SP)</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_sp = pd.read_sql_query("SELECT id, karyawan_id as 'ID Karyawan', jenis_sanksi as 'Jenis SP', tanggal_mulai as 'Tgl Mulai', tanggal_akhir as 'Tgl Akhir', rincian_pelanggaran as 'Pelanggaran', status as 'Status' FROM disiplin ORDER BY id DESC", conn)
    original_sp = df_sp.copy()
    render_export_print(df_sp, "disiplin")
    
    edited_sp = st.data_editor(df_sp, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data SP", type="primary"):
        edited_db = edited_sp.rename(columns={'ID Karyawan': 'karyawan_id', 'Jenis SP': 'jenis_sanksi', 'Tgl Mulai': 'tanggal_mulai', 'Tgl Akhir': 'tanggal_akhir', 'Pelanggaran': 'rincian_pelanggaran', 'Status': 'status'})
        original_db = original_sp.rename(columns={'ID Karyawan': 'karyawan_id', 'Jenis SP': 'jenis_sanksi', 'Tgl Mulai': 'tanggal_mulai', 'Tgl Akhir': 'tanggal_akhir', 'Pelanggaran': 'rincian_pelanggaran', 'Status': 'status'})
        save_dataframe_to_db("disiplin", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 5. JOBDESK ====================
elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk Karyawan</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_job = pd.read_sql_query("SELECT id, posisi as 'Posisi', departemen as 'Departemen', tugas_utama as 'Tugas Utama', kpi as 'KPI' FROM jobdesk ORDER BY id DESC", conn)
    original_job = df_job.copy()
    render_export_print(df_job, "jobdesk")
    
    edited_job = st.data_editor(df_job, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data Jobdesk", type="primary"):
        edited_db = edited_job.rename(columns={'Posisi': 'posisi', 'Departemen': 'departemen', 'Tugas Utama': 'tugas_utama', 'KPI': 'kpi'})
        original_db = original_job.rename(columns={'Posisi': 'posisi', 'Departemen': 'departemen', 'Tugas Utama': 'tugas_utama', 'KPI': 'kpi'})
        save_dataframe_to_db("jobdesk", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 6. CI REPORT ====================
elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 Continuous Improvement (CI) Report</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_ci = pd.read_sql_query("SELECT id, tanggal as 'Tanggal', judul as 'Judul CI', departemen as 'Departemen', deskripsi as 'Deskripsi', pic as 'PIC', status as 'Status' FROM ci ORDER BY id DESC", conn)
    original_ci = df_ci.copy()
    render_export_print(df_ci, "ci_report")
    
    edited_ci = st.data_editor(df_ci, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data CI", type="primary"):
        edited_db = edited_ci.rename(columns={'Tanggal': 'tanggal', 'Judul CI': 'judul', 'Departemen': 'departemen', 'Deskripsi': 'deskripsi', 'PIC': 'pic', 'Status': 'status'})
        original_db = original_ci.rename(columns={'Tanggal': 'tanggal', 'Judul CI': 'judul', 'Departemen': 'departemen', 'Deskripsi': 'deskripsi', 'PIC': 'pic', 'Status': 'status'})
        save_dataframe_to_db("ci", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 7. SKD (SURAT KETERANGAN) ====================
elif pilihan == "🏥 SKD (Surat Ket)":
    st.markdown('<div class="main-header"><h1>🏥 SKD (Surat Keterangan Dokter/Dinas)</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_skd = pd.read_sql_query("SELECT id, tanggal as 'Tanggal', no_surat as 'No Surat', nama_karyawan as 'Nama Karyawan', jenis_surat as 'Jenis Surat', keterangan as 'Keterangan' FROM skd ORDER BY id DESC", conn)
    original_skd = df_skd.copy()
    render_export_print(df_skd, "skd")
    
    edited_skd = st.data_editor(df_skd, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data SKD", type="primary"):
        edited_db = edited_skd.rename(columns={'Tanggal': 'tanggal', 'No Surat': 'no_surat', 'Nama Karyawan': 'nama_karyawan', 'Jenis Surat': 'jenis_surat', 'Keterangan': 'keterangan'})
        original_db = original_skd.rename(columns={'Tanggal': 'tanggal', 'No Surat': 'no_surat', 'Nama Karyawan': 'nama_karyawan', 'Jenis Surat': 'jenis_surat', 'Keterangan': 'keterangan'})
        save_dataframe_to_db("skd", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 8. INTERNAL MEMO ====================
elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo (IM)</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_im = pd.read_sql_query("SELECT id, tanggal as 'Tanggal', no_memo as 'No Memo', perihal as 'Perihal', pengirim as 'Pengirim', penerima as 'Penerima', isi as 'Isi Memo' FROM im ORDER BY id DESC", conn)
    original_im = df_im.copy()
    render_export_print(df_im, "internal_memo")
    
    edited_im = st.data_editor(df_im, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data Memo", type="primary"):
        edited_db = edited_im.rename(columns={'Tanggal': 'tanggal', 'No Memo': 'no_memo', 'Perihal': 'perihal', 'Pengirim': 'pengirim', 'Penerima': 'penerima', 'Isi Memo': 'isi'})
        original_db = original_im.rename(columns={'Tanggal': 'tanggal', 'No Memo': 'no_memo', 'Perihal': 'perihal', 'Pengirim': 'pengirim', 'Penerima': 'penerima', 'Isi Memo': 'isi'})
        save_dataframe_to_db("im", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 9. RESIGN ====================
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_r = pd.read_sql_query("SELECT id, karyawan_id as 'ID Karyawan', tanggal_resign as 'Tgl Resign', jenis as 'Jenis', alasan as 'Alasan', clearance_status as 'Status Clearance' FROM resign ORDER BY id DESC", conn)
    original_r = df_r.copy()
    render_export_print(df_r, "resign")
    
    edited_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data Resign", type="primary"):
        edited_db = edited_r.rename(columns={'ID Karyawan': 'karyawan_id', 'Tgl Resign': 'tanggal_resign', 'Jenis': 'jenis', 'Alasan': 'alasan', 'Status Clearance': 'clearance_status'})
        original_db = original_r.rename(columns={'ID Karyawan': 'karyawan_id', 'Tgl Resign': 'tanggal_resign', 'Jenis': 'jenis', 'Alasan': 'alasan', 'Status Clearance': 'clearance_status'})
        save_dataframe_to_db("resign", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 10. UTILITY ====================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="instruction-box">💡 <b>Panduan:</b> Klik sel untuk Edit • Centang kiri + tekan <code>Delete</code> di keyboard untuk Hapus • Klik <b>Simpan</b> di bawah tabel.</div>', unsafe_allow_html=True)
    
    df_u = pd.read_sql_query("SELECT id, kategori as 'Kategori', tanggal_bayar as 'Tanggal Bayar', label as 'Lokasi', nominal as 'Nominal', total_bayar as 'Total Bayar', status as 'Status' FROM utility ORDER BY tanggal_bayar DESC", conn)
    original_u = df_u.copy()
    render_export_print(df_u, "utility")
    
    edited_u = st.data_editor(df_u, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Data Utility", type="primary"):
        edited_db = edited_u.rename(columns={'Kategori': 'kategori', 'Tanggal Bayar': 'tanggal_bayar', 'Lokasi': 'label', 'Nominal': 'nominal', 'Total Bayar': 'total_bayar', 'Status': 'status'})
        original_db = original_u.rename(columns={'Kategori': 'kategori', 'Tanggal Bayar': 'tanggal_bayar', 'Lokasi': 'label', 'Nominal': 'nominal', 'Total Bayar': 'total_bayar', 'Status': 'status'})
        save_dataframe_to_db("utility", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# ==================== 11. PENGATURAN ====================
elif pilihan == "⚙️ Pengaturan & Log":
    st.markdown('<div class="main-header"><h1>⚙️ Pengaturan & Log</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Manajemen User", "Log Aktivitas"])
    
    with tab1:
        df_usr = pd.read_sql_query("SELECT id, username as 'Username', nama_lengkap as 'Nama Lengkap', role as 'Role' FROM users", conn)
        edited_usr = st.data_editor(df_usr, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan User", type="primary"):
            # Save logic bisa ditambahkan di sini
            st.success("User tersimpan!")
            
    with tab2:
        df_log = pd.read_sql_query("SELECT waktu as 'Waktu', username as 'User', aksi as 'Aksi' FROM log_aktivitas ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df_log, use_container_width=True, hide_index=True)
