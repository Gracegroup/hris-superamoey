import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import json
import calendar
import altair as alt
import urllib.parse
from datetime import datetime, timedelta, date
from io import StringIO

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA SUPER v4.0",
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
    .card-red    { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-gold   { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
    .section-header {
        background: white; padding: 15px 20px; border-radius: 12px;
        border-left: 5px solid #2a5298; margin: 20px 0 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .section-header h3 { margin: 0; color: #1e3c72; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%);
        color: white !important; border: none; border-radius: 10px;
        padding: 10px 20px; font-weight: 600; transition: all 0.3s; width: 100%;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(42,82,152,0.5); }
    .wa-btn { background: #25D366; color: white !important; padding: 8px 15px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE SETUP ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)

conn = get_conn()
c = conn.cursor()

def init_db():
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
    # Karyawan
    c.execute('''CREATE TABLE IF NOT EXISTS karyawan (
        id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, job_level TEXT,
        join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, email TEXT, birth_date TEXT, birth_place TEXT,
        citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT,
        bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, mobile_phone TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT,
        pendidikan_terakhir TEXT, asal_sekolah TEXT, no_ktp TEXT, no_kk TEXT, divisi TEXT, keterangan TEXT, versatility TEXT, gaji REAL DEFAULT 0)''')
    # Kandidat
    c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, posisi_dilamar TEXT, telepon TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, jadwal_interview TEXT, status_berkas TEXT)''')
    # Lowongan
    c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT, deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
    # Resign
    c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, exit_interview TEXT, clearance_status TEXT, kategori_penyebab TEXT)''')
    # Aset
    c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT)''')
    # Ruko & Tenant
    c.execute('''CREATE TABLE IF NOT EXISTS ruko (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tenant (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT)''')
    # Absensi
    c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT, terlambat_menit INTEGER DEFAULT 0)''')
    # Cuti
    c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT, approved_by TEXT, approved_at TEXT)''')
    # Payroll
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_jht_karyawan REAL, bpjs_jp_karyawan REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, status TEXT, tanggal_proses TEXT)''')
    # Disiplin
    c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT, periode TEXT)''')
    # Mutasi
    c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, dari_jabatan TEXT, ke_jabatan TEXT, alasan TEXT, created_at TEXT)''')
    # Utility
    c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL, admin REAL, total_bayar REAL, metode TEXT, status TEXT, catatan TEXT, created_at TEXT)''')
    # Log
    c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
    conn.commit()

init_db()

# ==================== HELPERS (Universal Functions) ====================
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

# UNIVERSAL: Export & Print
def render_export_print(df, filename):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode(), f"{filename}.csv", "text/csv", use_container_width=True)
    with col2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with col3:
        # HTML Print
        html_table = df.to_html(classes='table table-striped', index=False)
        html_full = f"<html><head><title>Print {filename}</title><style>table{{border-collapse: collapse; width:100%;}} th,td{{border:1px solid #ddd; padding:8px; text-align:left;}} th{{background-color:#f2f2f2;}}</style></head><body><h2>Data {filename.capitalize()}</h2>{html_table}</body></html>"
        st.download_button("🖨️ Cetak (HTML)", html_full, f"{filename}_print.html", "text/html", use_container_width=True)

# UNIVERSAL: Data Editor (CRUD) sync to SQLite
def sync_dataframe_to_db(table_name, df_new, conn):
    cur = conn.cursor()
    old_df = pd.read_sql_query(f"SELECT id FROM {table_name}", conn)
    old_ids = set(old_df['id'].tolist()) if not old_df.empty else set()
    
    # Handle new IDs (None or NaN)
    df_new['id'] = df_new['id'].fillna(0).astype(int)
    new_ids = set(df_new[df_new['id'] > 0]['id'].tolist())
    
    # Deletes
    deleted_ids = old_ids - new_ids
    for did in deleted_ids:
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        
    # Inserts & Updates
    cols = [col for col in df_new.columns if col != 'id']
    for _, row in df_new.iterrows():
        if row['id'] == 0: # Insert
            ph = ", ".join(["?"] * len(cols))
            cur.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})", tuple(row[cols]))
        else: # Update
            set_c = ", ".join([f"{col}=?" for col in cols])
            cur.execute(f"UPDATE {table_name} SET {set_c} WHERE id=?", tuple(row[cols]) + (row['id'],))
    conn.commit()

# UNIVERSAL: Import Data
def render_import_ui(table_name, required_cols):
    st.markdown("#### 📥 Import Data")
    f = st.file_uploader(f"Upload CSV/Excel untuk {table_name}", type=["csv", "xlsx", "xls"], key=f"up_{table_name}")
    if f:
        try:
            if f.name.endswith('csv'): df_imp = pd.read_csv(f)
            else: df_imp = pd.read_excel(f)
            
            df_imp.columns = [str(col).lower().replace(' ', '_') for col in df_imp.columns]
            missing = [c for c in required_cols if c not in df_imp.columns]
            
            if missing:
                st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
            else:
                st.dataframe(df_imp.head(3), use_container_width=True)
                if st.button("🚀 Proses Import", key=f"btn_imp_{table_name}"):
                    if table_name == "utility":
                        df_imp['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    df_imp.to_sql(table_name, conn, if_exists='append', index=False)
                    st.success(f"Berhasil import {len(df_imp)} baris!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==================== UI COMPONENTS ====================
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": "", "nama": "", "role": ""})

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS & GA SUPER v4.0</h1></div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            row = c.execute("SELECT username, password, nama_lengkap, role FROM users WHERE username=?", (u,)).fetchone()
            if row and row[1] == hash_password(p):
                st.session_state.update({"logged_in": True, "username": row[0], "nama": row[2], "role": row[3]})
                log_aksi(u, "LOGIN")
                st.rerun()
            else: st.error("Salah!")
    st.stop()

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.nama}")
    menu = [
        "🏠 Dashboard", "👥 Karyawan", "📅 Absensi", "🏖️ Cuti", "💰 Payroll",
        "📋 Rekrutmen", "🔄 Mutasi & PKWT", "⚠️ Disiplin & SP", "📉 Resign",
        "💡 Utility Melak", "🚛 Aset", "🏪 Ruko & Tenant", "⚙️ Pengaturan"
    ]
    pilihan = st.radio("Navigasi", menu)
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ==================== 1. DASHBOARD ====================
if pilihan == "🏠 Dashboard":
    st.markdown('<div class="main-header"><h1>🏠 Dashboard</h1></div>', unsafe_allow_html=True)
    
    # KPI
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date=''").fetchone()[0]
    sp = c.execute("SELECT COUNT(*) FROM disiplin WHERE status='Aktif'").fetchone()[0]
    util_belum = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status!='Lunas'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("Karyawan Aktif", str(aktif), "", "card-blue")
    html += metric_card("SP Aktif", str(sp), "", "card-red")
    html += metric_card("Tagihan Utility", format_rp(util_belum), "Belum Lunas", "card-orange")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ==================== 2. KARYAWAN ====================
elif pilihan == "👥 Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📋 Tabel & CRUD", "➕ Tambah Manual", "📥 Import"])
    
    with t1:
        df_k = pd.read_sql_query("SELECT * FROM karyawan ORDER BY id DESC", conn)
        render_export_print(df_k, "karyawan")
        st.markdown("💡 **Tips:** Klik sel untuk edit. Centang baris lalu tekan `Delete` di keyboard untuk hapus. Klik `+` di bawah untuk tambah baris.")
        edited = st.data_editor(df_k, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Simpan Perubahan Tabel"):
            sync_dataframe_to_db("karyawan", edited, conn)
            st.success("Tersimpan!"); st.rerun()
            
    with t2:
        with st.form("form_kar"):
            col1, col2 = st.columns(2)
            eid = col1.text_input("NRP *")
            name = col2.text_input("Nama *")
            div = col1.text_input("Divisi")
            job = col2.text_input("Jabatan")
            gaji = col1.number_input("Gaji", min_value=0)
            if st.form_submit_button("Simpan"):
                c.execute("INSERT INTO karyawan (employee_id, full_name, organization, job_position, gaji) VALUES (?,?,?,?,?)", (eid, name, div, job, gaji))
                conn.commit(); st.rerun()

    with t3:
        render_import_ui("karyawan", ["employee_id", "full_name"])

# ==================== 3. ABSENSI ====================
elif pilihan == "📅 Absensi":
    st.markdown('<div class="main-header"><h1>📅 Absensi</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📋 Tabel & CRUD", "➕ Input"])
    with t1:
        df_a = pd.read_sql_query("SELECT a.*, k.full_name FROM absensi a JOIN karyawan k ON a.karyawan_id = k.id ORDER BY a.tanggal DESC LIMIT 100", conn)
        render_export_print(df_a, "absensi")
        st.data_editor(df_a, num_rows="dynamic", use_container_width=True, disabled=["full_name"])
    with t2:
        st.info("Gunakan form di bawah untuk input cepat")
        with st.form("f_abs"):
            tgl = st.date_input("Tanggal")
            if st.form_submit_button("Hadir Semua"):
                kars = pd.read_sql_query("SELECT id FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
                for _, r in kars.iterrows():
                    c.execute("INSERT INTO absensi (karyawan_id, tanggal, status) VALUES (?,?,?)", (r['id'], str(tgl), "Hadir"))
                conn.commit(); st.success("Berhasil!"); st.rerun()

# ==================== 4. CUTI ====================
elif pilihan == "🏖️ Cuti":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    df_c = pd.read_sql_query("SELECT c.*, k.full_name FROM cuti c JOIN karyawan k ON c.karyawan_id = k.id ORDER BY c.id DESC", conn)
    render_export_print(df_c, "cuti")
    st.data_editor(df_c, num_rows="dynamic", use_container_width=True, disabled=["full_name"])

# ==================== 5. PAYROLL ====================
elif pilihan == "💰 Payroll":
    st.markdown('<div class="main-header"><h1>💰 Payroll</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📋 Riwayat Gaji", "⚙️ Proses Gaji"])
    with t1:
        df_p = pd.read_sql_query("SELECT p.*, k.full_name FROM payroll p JOIN karyawan k ON p.karyawan_id = k.id ORDER BY p.periode DESC", conn)
        render_export_print(df_p, "payroll")
        st.data_editor(df_p, use_container_width=True, disabled=["full_name"])
    with t2:
        st.info("Form kalkulasi payroll otomatis bisa ditambahkan di sini.")

# ==================== 6. REKRUTMEN ====================
elif pilihan == "📋 Rekrutmen":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Kandidat", "Lowongan"])
    with tab1:
        df_k = pd.read_sql_query("SELECT * FROM kandidat ORDER BY id DESC", conn)
        render_export_print(df_k, "kandidat")
        st.data_editor(df_k, num_rows="dynamic", use_container_width=True)
    with tab2:
        df_l = pd.read_sql_query("SELECT * FROM lowongan ORDER BY id DESC", conn)
        render_export_print(df_l, "lowongan")
        st.data_editor(df_l, num_rows="dynamic", use_container_width=True)

# ==================== 7. MUTASI & PKWT ====================
elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📋 Riwayat Mutasi", "⏳ PKWT Habis"])
    with t1:
        df_m = pd.read_sql_query("SELECT m.*, k.full_name FROM mutasi m JOIN karyawan k ON m.karyawan_id = k.id ORDER BY m.id DESC", conn)
        render_export_print(df_m, "mutasi")
        st.data_editor(df_m, num_rows="dynamic", use_container_width=True, disabled=["full_name"])
    with t2:
        tgl_60 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        df_pkwt = pd.read_sql_query(f"SELECT id, employee_id, full_name, end_date FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date <= '{tgl_60}'", conn)
        st.dataframe(df_pkwt, use_container_width=True)

# ==================== 8. DISIPLIN & SP ====================
elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & SP</h1></div>', unsafe_allow_html=True)
    df_d = pd.read_sql_query("SELECT d.*, k.full_name FROM disiplin d JOIN karyawan k ON d.karyawan_id = k.id ORDER BY d.id DESC", conn)
    render_export_print(df_d, "disiplin")
    st.data_editor(df_d, num_rows="dynamic", use_container_width=True, disabled=["full_name"])

# ==================== 9. RESIGN ====================
elif pilihan == "📉 Resign":
    st.markdown('<div class="main-header"><h1>📉 Resign</h1></div>', unsafe_allow_html=True)
    df_r = pd.read_sql_query("SELECT r.*, k.full_name FROM resign r JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC", conn)
    render_export_print(df_r, "resign")
    st.data_editor(df_r, num_rows="dynamic", use_container_width=True, disabled=["full_name"])

# ==================== 10. UTILITY MELAK ====================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📋 Data & CRUD", "📥 Import Data"])
    with t1:
        df_u = pd.read_sql_query("SELECT * FROM utility ORDER BY tanggal_bayar DESC", conn)
        render_export_print(df_u, "utility")
        st.data_editor(df_u, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Simpan Perubahan Utility"):
            sync_dataframe_to_db("utility", df_u, conn) # Simplified, see note below
            st.success("Tersimpan"); st.rerun()
    with t2:
        render_import_ui("utility", ["kategori", "nominal"])

# ==================== 11. ASET ====================
elif pilihan == "🚛 Aset":
    st.markdown('<div class="main-header"><h1>🚛 Aset</h1></div>', unsafe_allow_html=True)
    df_as = pd.read_sql_query("SELECT * FROM aset ORDER BY id DESC", conn)
    render_export_print(df_as, "aset")
    st.data_editor(df_as, num_rows="dynamic", use_container_width=True)

# ==================== 12. RUKO & TENANT ====================
elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Ruko", "Tenant"])
    with tab1:
        df_rk = pd.read_sql_query("SELECT * FROM ruko", conn)
        render_export_print(df_rk, "ruko")
        st.data_editor(df_rk, num_rows="dynamic", use_container_width=True)
    with tab2:
        df_tn = pd.read_sql_query("SELECT * FROM tenant", conn)
        render_export_print(df_tn, "tenant")
        st.data_editor(df_tn, num_rows="dynamic", use_container_width=True)

# ==================== 13. PENGATURAN ====================
elif pilihan == "⚙️ Pengaturan":
    st.markdown('<div class="main-header"><h1>⚙️ Pengaturan</h1></div>', unsafe_allow_html=True)
    st.subheader("👤 Manajemen User")
    df_usr = pd.read_sql_query("SELECT id, username, nama_lengkap, role FROM users", conn)
    st.data_editor(df_usr, num_rows="dynamic", use_container_width=True)
    
    st.subheader("📝 Log Aktivitas")
    df_log = pd.read_sql_query("SELECT * FROM log_aktivitas ORDER BY id DESC LIMIT 50", conn)
    st.dataframe(df_log, use_container_width=True)
