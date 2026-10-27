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

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA Amoey",
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
    
    /* CSS Khusus Form Official */
    .form-box { background: white; padding: 25px; border-radius: 10px; border: 2px solid #555; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); color: black;}
    .form-title { text-align: center; font-weight: bold; font-size: 1.4em; margin-bottom: 20px; text-transform: uppercase; border-bottom: 2px solid black; padding-bottom: 10px; }
    .form-table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
    .form-table th, .form-table td { border: 1px solid black; padding: 8px; text-align: left; vertical-align: top; }
    .form-table th { background: #f0f0f0; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE ====================
@st.cache_resource
def get_conn(): 
    return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

# ==================== HELPER ANTI-NAN ====================
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

# ==================== PEMBUATAN TABEL ====================
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
c.execute('''CREATE TABLE IF NOT EXISTS lampiran (id INTEGER PRIMARY KEY AUTOINCREMENT, ref_modul TEXT, ref_id TEXT, file_name TEXT, file_type TEXT, file_data BLOB, tanggal_upload TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')

# ==================== TABEL TAMBAHAN FORMULIR HRD ====================
c.execute('''CREATE TABLE IF NOT EXISTS formulir_wawancara (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, jabatan TEXT, usia TEXT, tanggal_wawancara TEXT, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, f5 TEXT, kelebihan TEXT, kekurangan TEXT, keputusan TEXT, pewawancara TEXT, nama_pewawancara TEXT, jabatan_pewawancara TEXT, data_fisik TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_coaching (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_karyawan TEXT, nik TEXT, tanggal_masuk TEXT, jabatan TEXT, status_karyawan TEXT, isu TEXT, observasi TEXT, langkah_perbaikan TEXT, komitmen TEXT, rekomendasi TEXT, hal_dilakukan TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_fpk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, divisi TEXT, jumlah INTEGER, penempatan TEXT, lokasi TEXT, tanggal_pengajuan TEXT, tujuan TEXT, alasan TEXT, magang TEXT, jangka_waktu TEXT, pendidikan TEXT, rentang_usia TEXT, jenis_kelamin TEXT, pengalaman TEXT, keahlian TEXT, bahasa TEXT, sertifikasi TEXT, persyaratan_tambahan TEXT, sumber_kandidat TEXT, proses_rekrutmen TEXT, technical_tes TEXT, deskripsi_pekerjaan TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_exit (id INTEGER PRIMARY KEY AUTOINCREMENT, jenis_form TEXT, nama TEXT, nik TEXT, posisi TEXT, departemen TEXT, data_json TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_izin (id INTEGER PRIMARY KEY AUTOINCREMENT, jenis_form TEXT, nama TEXT, jabatan TEXT, tanggal TEXT, alasan TEXT, pukul TEXT, keterangan TEXT, data_json TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_perubahan (id INTEGER PRIMARY KEY AUTOINCREMENT, no_urut TEXT, tanggal TEXT, data_json TEXT, pengaju TEXT, created_by TEXT, created_at TEXT)''')
conn.commit()

# ==================== MIGRASI KOLOM EXCEL KE DATABASE ====================
kolom_tambahan = [
    "npwp TEXT", "ptkp_status TEXT", "bank_name TEXT", "bank_account TEXT", 
    "bank_account_holder TEXT", "bpjs_ketenagakerjaan TEXT", "bpjs_kesehatan TEXT",
    "citizen_id_address TEXT", "residential_address TEXT", "nik_npwp_16 TEXT", 
    "phone TEXT", "branch_name TEXT", "religion TEXT", "marital_status TEXT", 
    "blood_type TEXT", "length_of_service TEXT", "manager TEXT", "grade TEXT"
]
for kol in kolom_tambahan:
    try:
        c.execute(f"ALTER TABLE karyawan ADD COLUMN {kol}")
    except sqlite3.OperationalError:
        pass
conn.commit()

# ==================== SEEDING DEFAULT ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "OKANAHARIANTO", "admin"))
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("hrd", hashlib.sha256("hrd123".encode()).hexdigest(), "HRD Staff", "hrd"))
    conn.commit()

# ==================== FUNGSI GLOBAL & DROPDOWN ====================
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

def safe_get_session(key, default=""):
    return st.session_state.get(key, default)

# -- FUNGSI DROPDOWN KARYAWAN (DIPERBAIKI DARI FILE ANDA) --
def get_karyawan_dropdown(only_active=True):
    """Mengambil daftar karyawan untuk dropdown: {'ID - Nama': ID}"""
    q = "SELECT employee_id, full_name FROM karyawan"
    if only_active:
        q += " WHERE aktif=1"
    q += " ORDER BY full_name"
    df = pd.read_sql_query(q, conn)
    return {f"{r['employee_id']} - {r['full_name']}": r['employee_id'] for _, r in df.iterrows()}

def get_karyawan_data(emp_id):
    """Mengambil 1 baris data karyawan lengkap berdasarkan Employee ID"""
    df = pd.read_sql_query("SELECT * FROM karyawan WHERE employee_id=?", conn, params=(emp_id,))
    return df.iloc[0] if not df.empty else None

# ==================== FUNGSI HELPER CRUD TABEL ====================
def render_edit_delete_table(table_name, query, editable_cols, display_cols, key_prefix, col_config=None, calc_func=None):
    df = pd.read_sql_query(query, conn)
    if df.empty:
        st.info(f"Belum ada data {table_name}. Silakan tambah melalui form di atas.")
        return
    df['Hapus?'] = False
    config = {"id": st.column_config.NumberColumn("ID", disabled=True, width="small"), "Hapus?": st.column_config.CheckboxColumn("Hapus?", default=False, width="small")}
    if col_config: config.update(col_config)
    edited_df = st.data_editor(df[display_cols + ['Hapus?']], column_config=config, num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_{table_name}_{key_prefix}")
    if st.button("💾 Simpan Perubahan / Hapus Data Terpilih", key=f"sv_{table_name}_{key_prefix}", type="primary", use_container_width=True):
        success_count = 0; delete_count = 0
        to_delete = edited_df[edited_df['Hapus?'] == True]['id'].dropna().tolist()
        for did in to_delete:
            try: c.execute(f"DELETE FROM {table_name} WHERE id=?", (did,)); delete_count += 1
            except Exception as e: st.error(f"Gagal menghapus ID {did}: {e}")
        for _, row in edited_df.iterrows():
            if row['Hapus?']: continue
            row_id = row.get('id')
            vals = []
            for col in editable_cols:
                val = row.get(col)
                if pd.isna(val): val = None
                vals.append(val)
            if calc_func: vals = calc_func(row, editable_cols, vals)
            try:
                if pd.isna(row_id) or row_id == 0 or row_id == "":
                    c.execute(f"INSERT INTO {table_name} ({', '.join(editable_cols)}) VALUES ({', '.join(['?'] * len(editable_cols))})", tuple(vals))
                else:
                    c.execute(f"UPDATE {table_name} SET {', '.join([f'{col}=?' for col in editable_cols])} WHERE id=?", tuple(vals) + (int(row_id),))
                success_count += 1
            except Exception as e: st.error(f"Error pada baris ID {row_id}: {e}")
        conn.commit()
        st.success(f"✅ Berhasil menyimpan {success_count} data dan menghapus {delete_count} data.")
        time.sleep(1); st.rerun()# ==================== LOGIN SYSTEM ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.nama = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1><p>Sistem Manajemen SDM, Absensi, Payroll, GA & Utility</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            st.subheader("🔐 Login Sistem")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk", use_container_width=True):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.logged_in = True
                    st.session_state.username = row[0]
                    st.session_state.nama = row[2]
                    st.session_state.role = row[3]
                    log_aksi(u, "LOGIN")
                    st.rerun()
                else: 
                    st.error("❌ Username / password salah atau akun tidak aktif.")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR MENU ====================
# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3 style="margin:5px 0;">{st.session_state.nama}</h3><p style="opacity:0.8; margin:0; font-size:0.9em;">Role: {st.session_state.role.upper()}</p><p style="opacity:0.6; margin:5px 0 0 0; font-size:0.75em;">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = [
        "🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", 
        "📅 Absensi & Kehadiran", "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", 
        "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", "🏥 SKD", 
        "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", 
        "⚠️ Disiplin & SP", "📤 Exit Clearance", "📱 WhatsApp Reminder", 
        "🚛 Aset & Properti", "🏪 Ruko & Tenant", "💡 Utility Melak", 
        "📁 Arsip Dokumen (E-Filing)", "📎 Lampiran / Attachment", "📋 Formulir HRD (Official)",
        "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"
    ]
    
    if st.session_state.role == "admin": 
        menu += ["👤 Manajemen User", "🔄 Sinkronisasi Uniquip", "📝 Log Aktivitas"]
        
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    tampilkan_flyer = st.checkbox("📢 Tampilkan Flyer Lowongan", value=True)
    st.markdown("---")
    
    # TOMBOL DARURAT UNTUK MENGHAPUS DATABASE LAMA (SPASI SUDAH DIPERBAIKI)
    if st.button("🛠️ Reset Database (Perbaikan Error)", key="btn_reset_db"):
        if os.path.exists("hris_ga.db"):
            os.remove("hris_ga.db")
        st.success("✅ Database lama dihapus. Silakan refresh halaman (F5).")
        time.sleep(2)
        st.rerun()
        
    st.markdown("---")
    
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: 
            st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU ====================

# ==================== KONTEN MENU ====================

# --- 1. DASHBOARD HRIS ---
if pilihan == "🏠 Dashboard HRIS":
    st.markdown('<div class="main-header"><h1>🏠 Dashboard HRIS</h1><p>Ringkasan Data SDM & GA</p></div>', unsafe_allow_html=True)
    
    total_karyawan = c.execute("SELECT COUNT(*) FROM karyawan WHERE aktif=1").fetchone()[0]
    total_kandidat = c.execute("SELECT COUNT(*) FROM kandidat").fetchone()[0]
    total_lowongan = c.execute("SELECT COUNT(*) FROM lowongan WHERE status='Buka'").fetchone()[0]
    total_cuti_menunggu = c.execute("SELECT COUNT(*) FROM cuti WHERE status='Menunggu'").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", str(total_karyawan), "Karyawan", "card-blue")
    html += metric_card("🎯 Kandidat", str(total_kandidat), "Total pelamar", "card-purple")
    html += metric_card("📋 Lowongan Buka", str(total_lowongan), "Posisi", "card-green")
    html += metric_card("🏖️ Cuti Menunggu", str(total_cuti_menunggu), "Perlu approval", "card-orange")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h3>📊 Statistik Karyawan per Divisi</h3></div>', unsafe_allow_html=True)
    df_div = pd.read_sql_query("SELECT COALESCE(NULLIF(divisi,''),'(Belum diisi)') as divisi, COUNT(*) as jumlah FROM karyawan WHERE aktif=1 GROUP BY divisi ORDER BY jumlah DESC", conn)
    if not df_div.empty:
        chart_div = alt.Chart(df_div).mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
            x=alt.X('jumlah:Q', title='Jumlah Karyawan'),
            y=alt.Y('divisi:N', sort='-x', title='Divisi'),
            color=alt.Color('jumlah:Q', scale=alt.Scale(scheme='purples'), legend=None)
        ).properties(height=250)
        st.altair_chart(chart_div, use_container_width=True)
    else:
        st.info("Belum ada data karyawan aktif.")

# --- 2. FILING DATA MANPOWER ---
elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1><p>Pencarian & Filter Data Karyawan</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 Cari (nama / employee ID / email)", key="filing_search")
    with col2:
        filter_status = st.selectbox("Filter Status", ["(Semua)", "Contract", "Permanent", "Resign"], key="filing_status")
    
    q = "SELECT employee_id, full_name, divisi, job_position, status_employee, join_date, mobile_phone, email FROM karyawan WHERE 1=1"
    params = []
    if search:
        q += " AND (full_name LIKE ? OR employee_id LIKE ? OR email LIKE ?)"
        params += [f"%{search}%"] * 3
    if filter_status != "(Semua)":
        if filter_status == "Resign":
            q += " AND aktif=0"
        else:
            q += " AND status_employee=?"; params.append(filter_status)
    q += " ORDER BY full_name"
    
    df = pd.read_sql_query(q, conn, params=tuple(params))
    st.caption(f"Menampilkan **{len(df)}** karyawan")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 3. DATA KARYAWAN ---
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1><p>CRUD Lengkap Data Karyawan</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Karyawan Baru", expanded=False):
        with st.form("add_karyawan_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                emp_id = st.text_input("Employee ID *", key="add_emp_id")
                full_name = st.text_input("Nama Lengkap *", key="add_full_name")
                join_date = st.date_input("Join Date", key="add_join_date")
            with col2:
                divisi = st.text_input("Divisi", key="add_divisi")
                posisi = st.text_input("Job Position", key="add_posisi")
                status_emp = st.selectbox("Status Karyawan", ["Contract", "Permanent", "Percobaan"], key="add_status_emp")
            with col3:
                email = st.text_input("Email", key="add_email")
                mobile_phone = st.text_input("Mobile Phone", key="add_mobile")
                gaji = st.number_input("Gaji Pokok", min_value=0.0, step=100000.0, key="add_gaji")
            
            if st.form_submit_button("💾 Simpan Karyawan", type="primary", use_container_width=True):
                if not emp_id or not full_name:
                    st.error("❌ Employee ID dan Nama wajib diisi.")
                else:
                    try:
                        c.execute("""INSERT INTO karyawan (employee_id, full_name, divisi, job_position, join_date, email, mobile_phone, status_employee, gaji, aktif) VALUES (?,?,?,?,?,?,?,?,?,1)""",
                                  (emp_id, full_name, divisi, posisi, str(join_date), email, mobile_phone, status_emp, gaji))
                        conn.commit()
                        st.success(f"✅ Karyawan **{full_name}** berhasil ditambahkan.")
                        time.sleep(1); st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Employee ID **{emp_id}** sudah ada.")
    
    render_edit_delete_table("karyawan",
        "SELECT id, employee_id, full_name, divisi, job_position, status_employee, join_date, email, gaji, aktif FROM karyawan ORDER BY id DESC",
        ["employee_id", "full_name", "divisi", "job_position", "status_employee", "join_date", "email", "gaji", "aktif"],
        ["id", "employee_id", "full_name", "divisi", "job_position", "status_employee", "join_date", "email", "gaji", "aktif"],
        "main_karyawan"
    )

# --- 4. MANPOWER REPORT (UPGRADE + IMPORT EXCEL) ---
elif pilihan == "📈 Manpower Report":
    st.markdown('<div class="main-header"><h1>📈 Manpower Report</h1><p>Analitik Data Karyawan Terintegrasi</p></div>', unsafe_allow_html=True)
    
    tab_mp1, tab_mp2 = st.tabs(["📊 Dashboard Manpower", "📥 Import Excel Manpower"])
    
    with tab_mp1:
        # Filter
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_org = st.selectbox("Filter Divisi/Organization", ["(Semua)"] + [r[0] for r in c.execute("SELECT DISTINCT divisi FROM karyawan WHERE divisi IS NOT NULL AND divisi != ''").fetchall()])
        with col2:
            filter_status = st.selectbox("Filter Status", ["(Semua)", "Contract", "Permanent", "Resign"])
        with col3:
            search_mp = st.text_input("Cari Nama / ID")
            
        q_mp = "SELECT employee_id, full_name, divisi as organization, job_position, job_level, join_date, resign_date, status_employee, end_date, gender, age, pendidikan_terakhir FROM karyawan WHERE 1=1"
        params_mp = []
        if filter_org != "(Semua)":
            q_mp += " AND divisi=?"; params_mp.append(filter_org)
        if filter_status != "(Semua)":
            if filter_status == "Resign":
                q_mp += " AND aktif=0"
            else:
                q_mp += " AND status_employee=?"; params_mp.append(filter_status)
        if search_mp:
            q_mp += " AND (full_name LIKE ? OR employee_id LIKE ?)"; params_mp.extend([f"%{search_mp}%", f"%{search_mp}%"])
        
        df_mp = pd.read_sql_query(q_mp, conn, params=tuple(params_mp))
        
        # Metrik
        total_mp = len(df_mp)
        aktif_mp = len(df_mp[df_mp['resign_date'].isna() | (df_mp['resign_date'] == '')])
        st.markdown(f"**Total Karyawan (Terfilter): {total_mp} | Aktif: {aktif_mp}**")
        
        st.dataframe(df_mp, use_container_width=True, hide_index=True)
        
        # Chart Distribusi
        if not df_mp.empty:
            st.markdown('<div class="section-header"><h3>📊 Distribusi Karyawan</h3></div>', unsafe_allow_html=True)
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                df_org = df_mp['organization'].value_counts().reset_index()
                df_org.columns = ['Organization', 'Jumlah']
                chart_org = alt.Chart(df_org).mark_bar().encode(
                    x='Jumlah:Q', y=alt.Y('Organization:N', sort='-x'), color=alt.value('#4facfe')
                ).properties(title="Berdasarkan Divisi", height=300)
                st.altair_chart(chart_org, use_container_width=True)
            with c_chart2:
                df_gender = df_mp['gender'].value_counts().reset_index()
                df_gender.columns = ['Gender', 'Jumlah']
                chart_gender = alt.Chart(df_gender).mark_arc(innerRadius=50).encode(
                    theta='Jumlah:Q', color='Gender:N'
                ).properties(title="Berdasarkan Gender", height=300)
                st.altair_chart(chart_gender, use_container_width=True)

    with tab_mp2:
        st.subheader("Upload Data Excel Karyawan")
        st.info("Gunakan file Excel dengan format standar HRIS (seperti Employee_10670_20260827142808.xlsx).")
        uploaded_excel = st.file_uploader("Pilih File Excel (.xlsx)", type=["xlsx"], key="up_excel")
        
        if uploaded_excel is not None:
            try:
                df_ex = pd.read_excel(uploaded_excel)
                st.write(f"✅ File terbaca: **{len(df_ex)} baris data**.")
                st.dataframe(df_ex.head(3), use_container_width=True)
                
                if st.button("💾 Import ke Database", type="primary"):
                    berhasil = 0
                    gagal = 0
                    for _, row in df_ex.iterrows():
                        try:
                            # Mapping kolom Excel ke kolom SQLite (Sesuaikan dengan header Excel Anda)
                            c.execute("""INSERT OR REPLACE INTO karyawan 
                                (employee_id, full_name, organization, job_position, job_level, join_date, resign_date, status_employee, end_date, email, birth_date, age, birth_place, citizen_id_address, residential_address, npwp, ptkp_status, bank_name, bank_account, mobile_phone, phone, branch_name, religion, gender, marital_status, divisi, aktif)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                (str(row.get('Employee ID', '')), str(row.get('Full Name', '')), str(row.get('Organization', '')), str(row.get('Job Position', '')), str(row.get('Job Level', '')), 
                                 str(row.get('Join Date', '')), str(row.get('Resign Date', '')), str(row.get('Status Employee', '')), str(row.get('End Date', '')), str(row.get('Email', '')), 
                                 str(row.get('Birth Date', '')), str(row.get('Age', '')), str(row.get('Birth Place', '')), str(row.get('Citizen ID Address', '')), str(row.get('Residential Address', '')), 
                                 str(row.get('NPWP', '')), str(row.get('PTKP Status', '')), str(row.get('Bank Name', '')), str(row.get('Bank Account', '')), str(row.get('Mobile Phone', '')), 
                                 str(row.get('Phone', '')), str(row.get('Branch Name', '')), str(row.get('Religion', '')), str(row.get('Gender', '')), str(row.get('Marital Status', '')),
                                 str(row.get('Organization', '')), # Divisi menggunakan Organization
                                 1 if pd.isna(row.get('Resign Date')) or str(row.get('Resign Date')).strip() == '' else 0))
                            berhasil += 1
                        except Exception as e:
                            gagal += 1
                    conn.commit()
                    st.success(f"✅ Import selesai: {berhasil} berhasil, {gagal} gagal.")
                    log_aksi(st.session_state.username, "IMPORT_EXCEL_MANPOWER", f"{berhasil} data")
                    time.sleep(2); st.rerun()
            except Exception as e:
                st.error(f"Gagal membaca file: {e}")# --- 4. ABSENSI & KEHADIRAN (TERINTEGRASI DROPDOWN) ---
elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi & Kehadiran</h1><p>Pencatatan Kehadiran Harian</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Input Absensi", expanded=False):
        karyawan_options = get_karyawan_dropdown()
        
        if not karyawan_options:
            st.warning("⚠️ Belum ada data karyawan. Silakan ke menu 'Manpower Report' dan Import Excel terlebih dahulu.")
        else:
            with st.form("absensi_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    # DROPDOWN KARYAWAN
                    pilih_kar = st.selectbox("Pilih Karyawan *", list(karyawan_options.keys()), key="abs_kar")
                    emp_id_abs = karyawan_options[pilih_kar]
                    data_kar = get_karyawan_data(emp_id_abs)
                    
                    # Otomatis tampil divisi & jabatan
                    st.info(f"Divisi: {data_kar.get('divisi', '-')} | Jabatan: {data_kar.get('job_position', '-')}")
                    
                    tgl_abs = st.date_input("Tanggal *", key="abs_tgl")
                with col2:
                    jam_masuk = st.text_input("Jam Masuk (HH:MM)", key="abs_jam_in", placeholder="08:00")
                    jam_keluar = st.text_input("Jam Keluar (HH:MM)", key="abs_jam_out", placeholder="17:00")
                    status_abs = st.selectbox("Status *", ["Hadir", "Terlambat", "Izin", "Sakit", "Alpha", "Cuti"], key="abs_status")
                with col3:
                    terlambat_menit = st.number_input("Terlambat (menit)", min_value=0, step=1, value=0, key="abs_terlambat")
                    ket_abs = st.text_area("Keterangan", key="abs_ket")
                
                if st.form_submit_button("💾 Simpan Absensi", type="primary", use_container_width=True):
                    try:
                        c.execute("""INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, keterangan, terlambat_menit)
                                     VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?,?,?)""",
                                  (emp_id_abs, str(tgl_abs), jam_masuk, jam_keluar, status_abs, ket_abs, int(terlambat_menit)))
                        conn.commit()
                        st.success(f"✅ Absensi untuk **{data_kar['full_name']}** tersimpan.")
                        log_aksi(st.session_state.username, "INPUT_ABSENSI", pilih_kar)
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Riwayat Absensi (100 Terakhir)</h3></div>', unsafe_allow_html=True)
    df_abs = pd.read_sql_query(
        """SELECT a.id, COALESCE(k.full_name,'(N/A)') as karyawan, a.tanggal, a.jam_masuk, a.jam_keluar, 
                  a.status, a.terlambat_menit, a.keterangan
           FROM absensi a LEFT JOIN karyawan k ON a.karyawan_id=k.id
           ORDER BY a.tanggal DESC, a.id DESC LIMIT 100""",
        conn
    )
    if not df_abs.empty:
        st.dataframe(df_abs, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data absensi.")

# --- 5. CUTI & IZIN ---
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1><p>Pengajuan & Approval Cuti Karyawan</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Ajukan Cuti", expanded=False):
        karyawan_options = get_karyawan_dropdown()
        
        if not karyawan_options:
            st.warning("Belum ada karyawan aktif.")
        else:
            with st.form("cuti_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    pilih_kar = st.selectbox("Karyawan *", list(karyawan_options.keys()), key="cuti_kar")
                    emp_id_cuti = karyawan_options[pilih_kar]
                    
                    jenis = st.selectbox("Jenis Cuti *", ["Tahunan", "Sakit", "Izin", "Melahirkan", "Cuti Khusus (Menikah)", "Cuti Khusus (Keluarga Meninggal)", "Lainnya"], key="cuti_jenis")
                with col2:
                    tgl_mulai = st.date_input("Tanggal Mulai *", key="cuti_mulai")
                    tgl_selesai = st.date_input("Tanggal Selesai *", key="cuti_selesai")
                    lama = st.number_input("Lama (hari) *", min_value=1, value=1, key="cuti_lama")
                with col3:
                    alasan = st.text_area("Alasan *", key="cuti_alasan")
                
                if st.form_submit_button("💾 Ajukan Cuti", type="primary", use_container_width=True):
                    if not alasan:
                        st.error("❌ Alasan wajib diisi.")
                    else:
                        try:
                            # Ambil ID asli karyawan dari Employee ID
                            c.execute("""INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, status)
                                         VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?,?,?)""",
                                      (emp_id_cuti, jenis, str(tgl_mulai), str(tgl_selesai), int(lama), alasan, "Menunggu"))
                            conn.commit()
                            st.success(f"✅ Cuti diajukan, menunggu approval.")
                            log_aksi(st.session_state.username, "AJUKAN_CUTI", f"{pilih_kar} - {jenis}")
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Pengajuan Cuti</h3></div>', unsafe_allow_html=True)
    df_cuti = pd.read_sql_query(
        """SELECT c.id, COALESCE(k.full_name,'(N/A)') as karyawan, c.jenis_cuti, c.tanggal_mulai, c.tanggal_selesai, 
                  c.lama_hari, c.status, c.alasan, c.approved_by, c.approved_at
           FROM cuti c LEFT JOIN karyawan k ON c.karyawan_id=k.id
           ORDER BY c.id DESC LIMIT 100""",
        conn
    )
    if not df_cuti.empty:
        st.dataframe(df_cuti, use_container_width=True, hide_index=True)
        
        # Approve / Reject
        st.markdown("**Approve / Reject Cuti:**")
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            cuti_id = st.number_input("ID Cuti", min_value=0, step=1, key="cuti_approve_id")
        with col_b:
            if st.button("✅ Approve", key="btn_approve_cuti", use_container_width=True):
                if cuti_id > 0:
                    c.execute("UPDATE cuti SET status='Approved', approved_by=?, approved_at=? WHERE id=? AND status='Menunggu'",
                              (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(cuti_id)))
                    conn.commit()
                    st.success(f"✅ Cuti ID {cuti_id} di-approve.")
                    log_aksi(st.session_state.username, "APPROVE_CUTI", f"ID {cuti_id}")
                    time.sleep(1); st.rerun()
        with col_c:
            if st.button("❌ Reject", key="btn_reject_cuti", use_container_width=True):
                if cuti_id > 0:
                    c.execute("UPDATE cuti SET status='Rejected', approved_by=?, approved_at=? WHERE id=? AND status='Menunggu'",
                              (st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(cuti_id)))
                    conn.commit()
                    st.success(f"✅ Cuti ID {cuti_id} di-reject.")
                    log_aksi(st.session_state.username, "REJECT_CUTI", f"ID {cuti_id}")
                    time.sleep(1); st.rerun()
    else:
        st.info("Belum ada pengajuan cuti.")

# --- 6. PAYROLL & SLIP GAJI ---
elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll & Slip Gaji</h1><p>Generate & Riwayat Payroll</p></div>', unsafe_allow_html=True)
    
    karyawan_options = get_karyawan_dropdown()
    if not karyawan_options:
        st.info("Belum ada karyawan aktif.")
    else:
        tab_pay1, tab_pay2 = st.tabs(["📝 Generate Payroll", "📋 Riwayat Payroll"])
        
        with tab_pay1:
            # Taruh dropdown di LUAR form agar gaji pokok bisa reaktif berubah saat nama diganti
            periode = st.text_input("Periode (YYYY-MM) *", value=datetime.now().strftime("%Y-%m"), key="pay_periode")
            pilih_kar = st.selectbox("Karyawan *", list(karyawan_options.keys()), key="pay_kar")
            emp_id_pay = karyawan_options[pilih_kar]
            data_kar_pay = get_karyawan_data(emp_id_pay)
            
            gaji_pokok = float(data_kar_pay.get('gaji', 0) or 0)
            st.info(f"Gaji Pokok (dari database): **{format_rp(gaji_pokok)}**")
            
            with st.form("payroll_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tunj_jab = st.number_input("Tunjangan Jabatan", min_value=0.0, value=0.0, step=100000.0, key="pay_tj")
                    tunj_trans = st.number_input("Tunjangan Transport", min_value=0.0, value=0.0, step=50000.0, key="pay_tt")
                    tunj_makan = st.number_input("Tunjangan Makan", min_value=0.0, value=0.0, step=50000.0, key="pay_tm")
                with col2:
                    bpjs_kes_kar = st.number_input("BPJS Kesehatan (Karyawan)", min_value=0.0, value=0.0, step=10000.0, key="pay_bpjs_kes")
                    bpjs_jht_kar = st.number_input("BPJS JHT (Karyawan)", min_value=0.0, value=0.0, step=10000.0, key="pay_bpjs_jht")
                    pph21 = st.number_input("PPh21", min_value=0.0, value=0.0, step=50000.0, key="pay_pph21")
                
                bruto = gaji_pokok + tunj_jab + tunj_trans + tunj_makan
                total_pot = bpjs_kes_kar + bpjs_jht_kar + pph21
                bersih = bruto - total_pot
                
                st.markdown(f"""
                **Rincian Perhitungan:**
                - Total Penghasilan Bruto: **{format_rp(bruto)}**
                - Total Potongan: **{format_rp(total_pot)}**
                - **Gaji Bersih: {format_rp(bersih)}**
                """)
                
                if st.form_submit_button("💾 Simpan Payroll", type="primary", use_container_width=True):
                    try:
                        c.execute("""INSERT INTO payroll 
                            (karyawan_id, periode, gaji_pokok, tunjangan_jabatan, tunjangan_transport, tunjangan_makan,
                             bpjs_kesehatan_karyawan, bpjs_jht_karyawan, pph21,
                             total_penghasilan_bruto, total_potongan, gaji_bersih, tanggal_proses)
                            VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (emp_id_pay, periode, gaji_pokok, tunj_jab, tunj_trans, tunj_makan,
                             bpjs_kes_kar, bpjs_jht_kar, pph21,
                             bruto, total_pot, bersih, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success(f"✅ Payroll {pilih_kar} periode {periode} tersimpan.")
                        log_aksi(st.session_state.username, "SIMPAN_PAYROLL", f"{pilih_kar} - {periode}")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
        
        with tab_pay2:
            df_pr = pd.read_sql_query(
                """SELECT p.id, COALESCE(k.full_name,'(N/A)') as karyawan, p.periode,
                          p.gaji_pokok, p.total_penghasilan_bruto as bruto, p.total_potongan, 
                          p.gaji_bersih, p.tanggal_proses
                   FROM payroll p LEFT JOIN karyawan k ON p.karyawan_id=k.id
                   ORDER BY p.id DESC LIMIT 100""",
                conn
            )
            if not df_pr.empty:
                st.dataframe(df_pr, use_container_width=True, hide_index=True)
                
                # Slip gaji viewer
                st.markdown("---")
                st.subheader("🖨️ Lihat Slip Gaji")
                slip_id = st.number_input("ID Payroll", min_value=0, step=1, key="slip_id")
                if st.button("📄 Tampilkan Slip", key="btn_show_slip"):
                    if slip_id > 0:
                        row = c.execute("""SELECT p.*, k.full_name, k.employee_id, k.divisi, k.job_position
                                           FROM payroll p LEFT JOIN karyawan k ON p.karyawan_id=k.id
                                           WHERE p.id=?""", (int(slip_id),)).fetchone()
                        if row:
                            kolom = [desc[0] for desc in c.description]
                            data = dict(zip(kolom, row))
                            st.markdown(f"""
                            <div class="payroll-slip">
                                <h3 style="text-align:center;color:#1e3c72;">SLIP GAJI</h3>
                                <p style="text-align:center;">Periode: <b>{data.get('periode','')}</b></p>
                                <hr>
                                <div class="payroll-row"><span>Nama</span><span><b>{data.get('full_name','')}</b></span></div>
                                <div class="payroll-row"><span>Employee ID</span><span>{data.get('employee_id','')}</span></div>
                                <div class="payroll-row"><span>Divisi</span><span>{data.get('divisi','') or '-'}</span></div>
                                <div class="payroll-row"><span>Jabatan</span><span>{data.get('job_position','') or '-'}</span></div>
                                <hr>
                                <div class="payroll-row"><span>Gaji Pokok</span><span>{format_rp(data.get('gaji_pokok',0))}</span></div>
                                <div class="payroll-row"><span>Tunjangan Jabatan</span><span>{format_rp(data.get('tunjangan_jabatan',0))}</span></div>
                                <div class="payroll-row"><span>Tunjangan Transport</span><span>{format_rp(data.get('tunjangan_transport',0))}</span></div>
                                <div class="payroll-row"><span>Tunjangan Makan</span><span>{format_rp(data.get('tunjangan_makan',0))}</span></div>
                                <div class="payroll-row payroll-total"><span>Total Bruto</span><span>{format_rp(data.get('total_penghasilan_bruto',0))}</span></div>
                                <div class="payroll-row"><span>BPJS Kesehatan</span><span>- {format_rp(data.get('bpjs_kesehatan_karyawan',0))}</span></div>
                                <div class="payroll-row"><span>BPJS JHT</span><span>- {format_rp(data.get('bpjs_jht_karyawan',0))}</span></div>
                                <div class="payroll-row"><span>PPh21</span><span>- {format_rp(data.get('pph21',0))}</span></div>
                                <div class="payroll-row payroll-total"><span>Total Potongan</span><span>- {format_rp(data.get('total_potongan',0))}</span></div>
                                <div class="payroll-row payroll-total"><span>GAJI BERSIH</span><span>{format_rp(data.get('gaji_bersih',0))}</span></div>
                                <hr>
                                <p style="text-align:center;font-size:0.8em;">Diproses: {data.get('tanggal_proses','')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"❌ Payroll ID {slip_id} tidak ditemukan.")
            else:
                st.info("Belum ada riwayat payroll.")# --- 7. REKRUTMEN & CV ---
elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen & CV</h1><p>Manajemen Kandidat & Lowongan</p></div>', unsafe_allow_html=True)
    
    tab_rek1, tab_rek2 = st.tabs(["🎯 Kandidat", "📢 Lowongan"])
    
    with tab_rek1:
        with st.expander("➕ Tambah Kandidat Baru", expanded=False):
            with st.form("kandidat_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    k_nama = st.text_input("Nama Lengkap *", key="k_nama")
                    k_telp = st.text_input("Telepon", key="k_telp")
                    k_posisi = st.text_input("Posisi Dilamar *", key="k_posisi")
                with col2:
                    k_email = st.text_input("Email", key="k_email")
                    k_sumber = st.selectbox("Sumber", ["Jobstreet", "Referral", "Walk-in", "LinkedIn", "Glints", "Lainnya"], key="k_sumber")
                    k_tgl_lamar = st.date_input("Tanggal Lamaran", key="k_tgl_lamar")
                with col3:
                    k_status = st.selectbox("Status", ["Baru", "Screening", "Interview", "MCU", "Diterima", "Ditolak"], key="k_status")
                    k_tahapan = st.selectbox("Tahapan", ["-", "Berkas", "Interview HR", "Interview User", "Ground Test", "Induksi", "MCU", "Sign Contract"], key="k_tahapan")
                k_catatan = st.text_area("Catatan", key="k_catatan")
                
                if st.form_submit_button("💾 Simpan Kandidat", type="primary", use_container_width=True):
                    if not k_nama or not k_posisi:
                        st.error("❌ Nama dan Posisi wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO kandidat 
                                (nama, telepon, posisi_dilamar, email, sumber, tanggal_lamar, status, catatan, tahapan)
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                                (k_nama, k_telp, k_posisi, k_email, k_sumber, str(k_tgl_lamar), k_status, k_catatan, k_tahapan))
                            conn.commit()
                            st.success(f"✅ Kandidat **{k_nama}** tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_KANDIDAT", k_nama)
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
        
        st.markdown('<div class="section-header"><h3>📋 Daftar Kandidat</h3></div>', unsafe_allow_html=True)
        df_k = pd.read_sql_query(
            """SELECT id, nama, telepon, posisi_dilamar, email, sumber, tanggal_lamar, 
                      status, tahapan, catatan 
               FROM kandidat ORDER BY id DESC""",
            conn
        )
        if not df_k.empty:
            st.dataframe(df_k, use_container_width=True, hide_index=True)
            
            st.markdown("**Update Status Kandidat:**")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                kid_update = st.number_input("ID Kandidat", min_value=0, step=1, key="kid_update")
            with col2:
                status_baru = st.selectbox("Status Baru", ["Baru", "Screening", "Interview", "MCU", "Diterima", "Ditolak"], key="status_baru")
            with col3:
                if st.button("💾 Update", key="btn_update_status", use_container_width=True):
                    if kid_update > 0:
                        c.execute("UPDATE kandidat SET status=? WHERE id=?", (status_baru, int(kid_update)))
                        conn.commit()
                        st.success(f"✅ Status kandidat ID {kid_update} diubah ke {status_baru}.")
                        log_aksi(st.session_state.username, "UPDATE_KANDIDAT", f"ID {kid_update} → {status_baru}")
                        time.sleep(1); st.rerun()
        else:
            st.info("Belum ada data kandidat.")
    
    with tab_rek2:
        with st.expander("➕ Tambah Lowongan Baru", expanded=False):
            with st.form("lowongan_form"):
                col1, col2 = st.columns(2)
                with col1:
                    l_posisi = st.text_input("Posisi *", key="l_posisi")
                    l_dept = st.text_input("Departemen", key="l_dept")
                    l_jumlah = st.number_input("Jumlah Dibutuhkan", min_value=1, step=1, key="l_jumlah")
                with col2:
                    l_tgl_buka = st.date_input("Tanggal Dibuka", key="l_tgl_buka")
                    l_tgl_tutup = st.date_input("Tanggal Ditutup", key="l_tgl_tutup")
                    l_status = st.selectbox("Status", ["Buka", "Tutup"], key="l_status")
                l_deskripsi = st.text_area("Deskripsi", key="l_deskripsi")
                
                if st.form_submit_button("💾 Simpan Lowongan", type="primary", use_container_width=True):
                    if not l_posisi:
                        st.error("❌ Posisi wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO lowongan 
                                (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka, tanggal_ditutup)
                                VALUES (?,?,?,?,?,?,?)""",
                                (l_posisi, l_dept, int(l_jumlah), l_status, l_deskripsi, str(l_tgl_buka), str(l_tgl_tutup)))
                            conn.commit()
                            st.success(f"✅ Lowongan **{l_posisi}** tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_LOWONGAN", l_posisi)
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
        
        st.markdown('<div class="section-header"><h3>📋 Daftar Lowongan</h3></div>', unsafe_allow_html=True)
        df_l = pd.read_sql_query(
            """SELECT id, posisi, departemen, jumlah_dibutuhkan, status, 
                      tanggal_dibuka, tanggal_ditutup, deskripsi 
               FROM lowongan ORDER BY id DESC""",
            conn
        )
        if not df_l.empty:
            st.dataframe(df_l, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data lowongan.")

# --- 8. JOBDESK ---
elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk</h1><p>Deskripsi Pekerjaan & KPI per Posisi</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Jobdesk", expanded=False):
        with st.form("jobdesk_form"):
            col1, col2 = st.columns(2)
            with col1:
                jd_posisi = st.text_input("Posisi *", key="jd_posisi")
                jd_dept = st.text_input("Departemen", key="jd_dept")
            with col2:
                jd_tugas = st.text_area("Tugas Utama", key="jd_tugas")
            jd_kpi = st.text_area("KPI", key="jd_kpi")
            
            if st.form_submit_button("💾 Simpan Jobdesk", type="primary", use_container_width=True):
                if not jd_posisi:
                    st.error("❌ Posisi wajib diisi.")
                else:
                    try:
                        c.execute("INSERT INTO jobdesk (posisi, departemen, tugas_utama, kpi) VALUES (?,?,?,?)",
                                  (jd_posisi, jd_dept, jd_tugas, jd_kpi))
                        conn.commit()
                        st.success(f"✅ Jobdesk **{jd_posisi}** tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_JOBDESK", jd_posisi)
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Jobdesk</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "jobdesk",
        "SELECT id, posisi, departemen, tugas_utama, kpi FROM jobdesk ORDER BY id DESC",
        ["posisi", "departemen", "tugas_utama", "kpi"],
        ["id", "posisi", "departemen", "tugas_utama", "kpi"],
        "main_jobdesk"
    )

# --- 9. CI REPORT ---
elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 CI Report</h1><p>Continuous Improvement Report</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah CI Report", expanded=False):
        with st.form("ci_form"):
            col1, col2 = st.columns(2)
            with col1:
                ci_tgl = st.date_input("Tanggal", key="ci_tgl")
                ci_judul = st.text_input("Judul *", key="ci_judul")
                ci_dept = st.text_input("Departemen", key="ci_dept")
            with col2:
                ci_status = st.selectbox("Status", ["Draft", "Submitted", "Approved", "Rejected", "Implemented"], key="ci_status")
            ci_deskripsi = st.text_area("Deskripsi Perbaikan", key="ci_deskripsi")
            
            if st.form_submit_button("💾 Simpan CI Report", type="primary", use_container_width=True):
                if not ci_judul:
                    st.error("❌ Judul wajib diisi.")
                else:
                    try:
                        c.execute("INSERT INTO ci (tanggal, judul, departemen, deskripsi, status) VALUES (?,?,?,?,?)",
                                  (str(ci_tgl), ci_judul, ci_dept, ci_deskripsi, ci_status))
                        conn.commit()
                        st.success(f"✅ CI Report **{ci_judul}** tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_CI", ci_judul)
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar CI Report</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "ci",
        "SELECT id, tanggal, judul, departemen, deskripsi, status FROM ci ORDER BY id DESC",
        ["tanggal", "judul", "departemen", "deskripsi", "status"],
        ["id", "tanggal", "judul", "departemen", "status"],
        "main_ci"
    )

# --- 10. SKD ---
elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 SKD</h1><p>Surat Keterangan Dokter</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah SKD", expanded=False):
        with st.form("skd_form"):
            col1, col2 = st.columns(2)
            with col1:
                skd_tgl = st.date_input("Tanggal", key="skd_tgl")
                skd_no = st.text_input("No. Surat", key="skd_no")
                skd_nama = st.text_input("Nama Karyawan *", key="skd_nama")
            with col2:
                skd_jenis = st.selectbox("Jenis Surat", ["SKD Sakit", "SKD Hamil", "SKD Sehat", "SKD Lainnya"], key="skd_jenis")
            skd_ket = st.text_area("Keterangan", key="skd_ket")
            
            if st.form_submit_button("💾 Simpan SKD", type="primary", use_container_width=True):
                if not skd_nama:
                    st.error("❌ Nama karyawan wajib diisi.")
                else:
                    try:
                        c.execute("INSERT INTO skd (tanggal, no_surat, nama_karyawan, jenis_surat, keterangan) VALUES (?,?,?,?,?)",
                                  (str(skd_tgl), skd_no, skd_nama, skd_jenis, skd_ket))
                        conn.commit()
                        st.success(f"✅ SKD untuk **{skd_nama}** tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_SKD", skd_nama)
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar SKD</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "skd",
        "SELECT id, tanggal, no_surat, nama_karyawan, jenis_surat, keterangan FROM skd ORDER BY id DESC",
        ["tanggal", "no_surat", "nama_karyawan", "jenis_surat", "keterangan"],
        ["id", "tanggal", "no_surat", "nama_karyawan", "jenis_surat", "keterangan"],
        "main_skd"
    )

# --- 11. INTERNAL MEMO ---
elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo</h1><p>Memo Internal Perusahaan</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Internal Memo", expanded=False):
        with st.form("im_form"):
            col1, col2 = st.columns(2)
            with col1:
                im_tgl = st.date_input("Tanggal", key="im_tgl")
                im_no = st.text_input("No. Memo", key="im_no")
                im_perihal = st.text_input("Perihal *", key="im_perihal")
            with col2:
                im_pengirim = st.text_input("Pengirim", key="im_pengirim")
                im_penerima = st.text_input("Penerima", key="im_penerima")
            im_isi = st.text_area("Isi Memo", height=150, key="im_isi")
            
            if st.form_submit_button("💾 Simpan Memo", type="primary", use_container_width=True):
                if not im_perihal:
                    st.error("❌ Perihal wajib diisi.")
                else:
                    try:
                        c.execute("""INSERT INTO im (tanggal, no_memo, perihal, pengirim, penerima, isi)
                                     VALUES (?,?,?,?,?,?)""",
                                  (str(im_tgl), im_no, im_perihal, im_pengirim, im_penerima, im_isi))
                        conn.commit()
                        st.success(f"✅ Memo **{im_perihal}** tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_IM", im_perihal)
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Internal Memo</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "im",
        "SELECT id, tanggal, no_memo, perihal, pengirim, penerima, isi FROM im ORDER BY id DESC",
        ["tanggal", "no_memo", "perihal", "pengirim", "penerima", "isi"],
        ["id", "tanggal", "no_memo", "perihal", "pengirim", "penerima"],
        "main_im"
    )

# --- 12. MUTASI & PKWT (TERINTEGRASI DROPDOWN) ---
elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi & PKWT</h1><p>Mutasi Karyawan Antar Divisi/Departemen</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Mutasi", expanded=False):
        karyawan_options = get_karyawan_dropdown()
        if not karyawan_options:
            st.warning("Belum ada karyawan aktif.")
        else:
            with st.form("mutasi_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pilih_kar = st.selectbox("Karyawan *", list(karyawan_options.keys()), key="mut_kar")
                    emp_id_mut = karyawan_options[pilih_kar]
                    data_kar_mut = get_karyawan_data(emp_id_mut)
                    
                    mut_tgl = st.date_input("Tanggal Mutasi", key="mut_tgl")
                    mut_dari = st.text_input("Dari Divisi", value=str(data_kar_mut.get('divisi', '') or ""), key="mut_dari")
                with col2:
                    mut_ke = st.text_input("Ke Divisi *", key="mut_ke")
                    mut_alasan = st.text_area("Alasan", key="mut_alasan")
                
                if st.form_submit_button("💾 Simpan Mutasi", type="primary", use_container_width=True):
                    if not mut_ke:
                        st.error("❌ Divisi tujuan wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO mutasi (karyawan_id, tanggal_mutasi, dari_divisi, ke_divisi, alasan)
                                         VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?)""",
                                      (emp_id_mut, str(mut_tgl), mut_dari, mut_ke, mut_alasan))
                            # Update divisi karyawan
                            c.execute("UPDATE karyawan SET divisi=? WHERE employee_id=?", (mut_ke, emp_id_mut))
                            conn.commit()
                            st.success(f"✅ Mutasi **{pilih_kar}** → **{mut_ke}** tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_MUTASI", f"{pilih_kar} → {mut_ke}")
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Mutasi</h3></div>', unsafe_allow_html=True)
    df_mut = pd.read_sql_query(
        """SELECT m.id, COALESCE(k.full_name,'(N/A)') as karyawan, 
                  m.tanggal_mutasi, m.dari_divisi, m.ke_divisi, m.alasan
           FROM mutasi m LEFT JOIN karyawan k ON m.karyawan_id=k.id
           ORDER BY m.id DESC""",
        conn
    )
    if not df_mut.empty:
        st.dataframe(df_mut, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data mutasi.")

# --- 13. RESIGN & TURNOVER (TERINTEGRASI DROPDOWN) ---
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1><p>Data Karyawan Keluar</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Input Resign", expanded=False):
        karyawan_options = get_karyawan_dropdown()
        if not karyawan_options:
            st.warning("Belum ada karyawan aktif.")
        else:
            with st.form("resign_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pilih_kar = st.selectbox("Karyawan *", list(karyawan_options.keys()), key="r_kar")
                    emp_id_res = karyawan_options[pilih_kar]
                    
                    r_tgl = st.date_input("Tanggal Resign", key="r_tgl")
                    r_jenis = st.selectbox("Jenis", ["Atas Kemauan Sendiri", "PHK", "Pensiun", "Kontrak Habis", "Meninggal"], key="r_jenis")
                with col2:
                    r_kategori = st.selectbox("Kategori Penyebab", ["-", "Karier", "Gaji", "Lingkungan", "Keluarga", "Kesehatan", "Lainnya"], key="r_kategori")
                    r_alasan = st.text_area("Alasan *", key="r_alasan")
                
                if st.form_submit_button("💾 Simpan Resign", type="primary", use_container_width=True):
                    if not r_alasan:
                        st.error("❌ Alasan wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO resign (karyawan_id, tanggal_resign, alasan, jenis, kategori_penyebab)
                                         VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?)""",
                                      (emp_id_res, str(r_tgl), r_alasan, r_jenis, r_kategori))
                            # Nonaktifkan karyawan
                            c.execute("UPDATE karyawan SET aktif=0, resign_date=? WHERE employee_id=?", (str(r_tgl), emp_id_res))
                            conn.commit()
                            st.success(f"✅ Resign **{pilih_kar}** tersimpan, karyawan dinonaktifkan.")
                            log_aksi(st.session_state.username, "SIMPAN_RESIGN", pilih_kar)
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Resign</h3></div>', unsafe_allow_html=True)
    df_r = pd.read_sql_query(
        """SELECT r.id, COALESCE(k.full_name,'(N/A)') as karyawan, r.tanggal_resign, 
                  r.alasan, r.jenis, r.kategori_penyebab, r.clearance_status
           FROM resign r LEFT JOIN karyawan k ON r.karyawan_id=k.id
           ORDER BY r.id DESC""",
        conn
    )
    if not df_r.empty:
        st.dataframe(df_r, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data resign.")
    
    st.markdown('<div class="section-header"><h3>📊 Turnover per Jenis</h3></div>', unsafe_allow_html=True)
    df_turn = pd.read_sql_query("SELECT jenis, COUNT(*) as jumlah FROM resign GROUP BY jenis ORDER BY jumlah DESC", conn)
    if not df_turn.empty:
        st.dataframe(df_turn, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data turnover.")

# --- 14. DISIPLIN & SP (TERINTEGRASI DROPDOWN) ---
elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ Disiplin & SP</h1><p>Surat Peringatan & Sanksi Karyawan</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Disiplin/SP", expanded=False):
        karyawan_options = get_karyawan_dropdown()
        if not karyawan_options:
            st.warning("Belum ada karyawan aktif.")
        else:
            with st.form("disiplin_form"):
                col1, col2 = st.columns(2)
                with col1:
                    pilih_kar = st.selectbox("Karyawan *", list(karyawan_options.keys()), key="d_kar")
                    emp_id_disp = karyawan_options[pilih_kar]
                    
                    d_jenis = st.selectbox("Jenis Sanksi", ["SP1", "SP2", "SP3", "Teguran Lisan", "Teguran Tertulis", "Skorsing"], key="d_jenis")
                with col2:
                    d_mulai = st.date_input("Tanggal Mulai", key="d_mulai")
                    d_akhir = st.date_input("Tanggal Akhir", key="d_akhir")
                    d_periode = st.text_input("Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"), key="d_periode")
                d_rincian = st.text_area("Rincian Pelanggaran *", key="d_rincian")
                
                if st.form_submit_button("💾 Simpan Sanksi", type="primary", use_container_width=True):
                    if not d_rincian:
                        st.error("❌ Rincian pelanggaran wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO disiplin 
                                (karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status, periode)
                                VALUES ((SELECT id FROM karyawan WHERE employee_id=?),?,?,?,?,?,?)""",
                                (emp_id_disp, d_jenis, str(d_mulai), str(d_akhir), d_rincian, "Aktif", d_periode))
                            conn.commit()
                            st.success(f"✅ Sanksi **{d_jenis}** untuk {pilih_kar} tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_SP", f"{pilih_kar} - {d_jenis}")
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Disiplin/SP</h3></div>', unsafe_allow_html=True)
    df_d = pd.read_sql_query(
        """SELECT d.id, COALESCE(k.full_name,'(N/A)') as karyawan, d.jenis_sanksi, 
                  d.tanggal_mulai, d.tanggal_akhir, d.rincian_pelanggaran, d.status, d.periode
           FROM disiplin d LEFT JOIN karyawan k ON d.karyawan_id=k.id
           ORDER BY d.id DESC""",
        conn
    )
    if not df_d.empty:
        st.dataframe(df_d, use_container_width=True, hide_index=True)
        
        st.markdown("**Update Status SP:**")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            sp_id = st.number_input("ID SP", min_value=0, step=1, key="sp_id")
        with col2:
            sp_status = st.selectbox("Status Baru", ["Aktif", "Selesai", "Dibatalkan"], key="sp_status")
        with col3:
            if st.button("💾 Update", key="btn_update_sp", use_container_width=True):
                if sp_id > 0:
                    c.execute("UPDATE disiplin SET status=? WHERE id=?", (sp_status, int(sp_id)))
                    conn.commit()
                    st.success(f"✅ SP ID {sp_id} diubah ke {sp_status}.")
                    log_aksi(st.session_state.username, "UPDATE_SP", f"ID {sp_id} → {sp_status}")
                    time.sleep(1); st.rerun()
    else:
        st.info("Belum ada data disiplin/SP.")

# --- 15. EXIT CLEARANCE ---
elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1><p>Clearance Karyawan Keluar</p></div>', unsafe_allow_html=True)
    
    st.info("💡 Untuk cetak & isi form Exit Clearance lengkap, silakan buka menu **📋 Formulir HRD (Official) → Tab Exit & Clearance**.")
    
    st.markdown('<div class="section-header"><h3>📋 Status Clearance Karyawan Resign</h3></div>', unsafe_allow_html=True)
    df_ec = pd.read_sql_query(
        """SELECT r.id, COALESCE(k.full_name,'(N/A)') as karyawan, r.tanggal_resign, 
                  r.clearance_status, r.exit_interview, r.jenis
           FROM resign r LEFT JOIN karyawan k ON r.karyawan_id=k.id
           ORDER BY r.id DESC""",
        conn
    )
    if not df_ec.empty:
        st.dataframe(df_ec, use_container_width=True, hide_index=True)
        
        st.markdown("**Update Clearance Status:**")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            ec_id = st.number_input("ID Resign", min_value=0, step=1, key="ec_id")
        with col2:
            ec_status = st.selectbox("Status Clearance", ["-", "In Progress", "Selesai", "Bermasalah"], key="ec_status")
        with col3:
            if st.button("💾 Update", key="btn_update_ec", use_container_width=True):
                if ec_id > 0:
                    c.execute("UPDATE resign SET clearance_status=? WHERE id=?", (ec_status, int(ec_id)))
                    conn.commit()
                    st.success(f"✅ Clearance ID {ec_id} diubah ke {ec_status}.")
                    log_aksi(st.session_state.username, "UPDATE_CLEARANCE", f"ID {ec_id} → {ec_status}")
                    time.sleep(1); st.rerun()
    else:
        st.info("Belum ada data resign.")

# --- 16. WHATSAPP REMINDER ---
elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WhatsApp Reminder</h1><p>Generate Link WA untuk Reminder</p></div>', unsafe_allow_html=True)
    
    st.info("💡 Fitur ini membuat link WhatsApp otomatis. Anda tinggal klik link untuk membuka WA (Web/Desktop/Mobile).")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("📝 Format Pesan")
        wa_phone = st.text_input("No. WhatsApp (format: 628xxx tanpa spasi/+/)", placeholder="6281234567890", key="wa_phone")
        wa_jenis = st.selectbox("Jenis Reminder", [
            "Reminder Payroll", "Reminder Cuti", "Reminder Kontrak Habis",
            "Reminder Interview", "Reminder MCU", "Reminder Absensi", "Custom"
        ], key="wa_jenis")
        
        templates = {
            "Reminder Payroll": "Halo, ini reminder dari HRD. Slip gaji Anda periode ini sudah tersedia. Silakan hubungi HRD untuk informasi lebih lanjut. Terima kasih.",
            "Reminder Cuti": "Halo, ini reminder dari HRD. Anda memiliki pengajuan cuti yang menunggu approval. Mohon hubungi atasan Anda. Terima kasih.",
            "Reminder Kontrak Habis": "Halo, ini reminder dari HRD. Kontrak kerja Anda akan segera berakhir. Mohon hubungi HRD untuk proses perpanjangan. Terima kasih.",
            "Reminder Interview": "Halo, ini reminder dari HRD. Anda memiliki jadwal interview. Mohon hadir tepat waktu. Terima kasih.",
            "Reminder MCU": "Halo, ini reminder dari HRD. Anda memiliki jadwal Medical Check-Up. Mohon hadir tepat waktu. Terima kasih.",
            "Reminder Absensi": "Halo, ini reminder dari HRD. Kami mendeteksi ketidakhadiran Anda. Mohon konfirmasi ke HRD. Terima kasih.",
            "Custom": ""
        }
        wa_msg = st.text_area("Pesan", value=templates.get(wa_jenis, ""), height=200, key="wa_msg")
    
    with col2:
        st.subheader("🔗 Preview & Link")
        if wa_phone and wa_msg:
            clean_phone = re.sub(r"[^\d]", "", wa_phone)
            if clean_phone.startswith("0"):
                clean_phone = "62" + clean_phone[1:]
            elif not clean_phone.startswith("62"):
                clean_phone = "62" + clean_phone
            
            wa_url = f"https://wa.me/{clean_phone}?text={quote(wa_msg)}"
            
            st.markdown(f"""
            **Nomor tersanitasi:** `{clean_phone}`  
            **Jenis Reminder:** {wa_jenis}
            """)
            st.markdown(f"[📱 Buka WhatsApp (Klik di sini)]({wa_url})", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("**Preview Pesan:**")
            st.info(wa_msg)
            
            if st.button("📋 Copy Link ke Clipboard (via text area)", use_container_width=True, key="btn_copy_wa"):
                st.code(wa_url, language="text")
                st.success("✅ Copy URL di atas dengan Ctrl+C / Cmd+C")
        else:
            st.warning("⚠️ Isi nomor WA dan pesan dulu.")# --- 17. ASET & PROPERTI ---
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1><p>Manajemen Aset Perusahaan</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Aset Baru", expanded=False):
        with st.form("aset_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                as_kode = st.text_input("Kode Aset *", key="as_kode")
                as_nama = st.text_input("Nama Aset *", key="as_nama")
                as_kategori = st.selectbox("Kategori", [
                    "Kendaraan", "Elektronik", "Furnitur", "Gedung", "Tanah",
                    "Peralatan Kantor", "Mesin", "Lainnya"
                ], key="as_kategori")
            with col2:
                as_lokasi = st.text_input("Lokasi", key="as_lokasi")
                as_kondisi = st.selectbox("Kondisi", ["Baik", "Rusak Ringan", "Rusak Berat", "Hilang"], key="as_kondisi")
                as_nilai = st.number_input("Nilai (Rp)", min_value=0.0, step=1000000.0, key="as_nilai")
            with col3:
                as_tgl = st.date_input("Tanggal Perolehan", key="as_tgl")
                as_pj = st.text_input("Penanggung Jawab", key="as_pj")
                as_status = st.selectbox("Status", ["Aktif", "Dijual", "Disposed", "Rusak"], key="as_status")
            as_catatan = st.text_area("Catatan", key="as_catatan")
            
            if st.form_submit_button("💾 Simpan Aset", type="primary", use_container_width=True):
                if not as_kode or not as_nama:
                    st.error("❌ Kode dan Nama Aset wajib diisi.")
                else:
                    try:
                        c.execute("""INSERT INTO aset 
                            (kode, nama, kategori, lokasi, kondisi, nilai, tanggal_perolehan, penanggung_jawab, status, catatan)
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (as_kode, as_nama, as_kategori, as_lokasi, as_kondisi, as_nilai,
                             str(as_tgl), as_pj, as_status, as_catatan))
                        conn.commit()
                        st.success(f"✅ Aset **{as_nama}** tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_ASET", as_nama)
                        time.sleep(1); st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Kode aset **{as_kode}** sudah ada.")
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📊 Ringkasan Aset</h3></div>', unsafe_allow_html=True)
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    total_aset = c.execute("SELECT COUNT(*) FROM aset").fetchone()[0]
    total_nilai = c.execute("SELECT COALESCE(SUM(nilai),0) FROM aset").fetchone()[0]
    total_aktif = c.execute("SELECT COUNT(*) FROM aset WHERE status='Aktif'").fetchone()[0]
    total_rusak = c.execute("SELECT COUNT(*) FROM aset WHERE kondisi IN ('Rusak Ringan','Rusak Berat','Hilang')").fetchone()[0]
    with col_sum1: st.metric("Total Aset", total_aset)
    with col_sum2: st.metric("Total Nilai", format_rp(total_nilai))
    with col_sum3: st.metric("Aset Aktif", total_aktif)
    with col_sum4: st.metric("Aset Bermasalah", total_rusak)
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Aset (Edit / Hapus)</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "aset",
        """SELECT id, kode, nama, kategori, lokasi, kondisi, nilai, 
                  tanggal_perolehan, penanggung_jawab, status 
           FROM aset ORDER BY id DESC""",
        ["kode", "nama", "kategori", "lokasi", "kondisi", "nilai",
         "tanggal_perolehan", "penanggung_jawab", "status"],
        ["id", "kode", "nama", "kategori", "lokasi", "kondisi", "nilai", "status"],
        "main_aset"
    )

# --- 18. RUKO & TENANT ---
elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1><p>Manajemen Properti Ruko & Tenant</p></div>', unsafe_allow_html=True)
    
    tab_rt1, tab_rt2 = st.tabs(["🏪 Ruko", "🏠 Tenant"])
    
    # --- TAB RUKO ---
    with tab_rt1:
        with st.expander("➕ Tambah Ruko Baru", expanded=False):
            with st.form("ruko_form"):
                col1, col2 = st.columns(2)
                with col1:
                    rk_nama = st.text_input("Nama Ruko *", key="rk_nama")
                    rk_alamat = st.text_area("Alamat", key="rk_alamat")
                    rk_status = st.selectbox("Status", ["Kosong", "Disewa", "Dijual", "Maintenance"], key="rk_status")
                with col2:
                    rk_penyewa = st.text_input("Penyewa", key="rk_penyewa")
                    rk_nilai = st.number_input("Nilai Sewa / Bulan (Rp)", min_value=0.0, step=500000.0, key="rk_nilai")
                    rk_mulai = st.date_input("Mulai Sewa", key="rk_mulai")
                    rk_akhir = st.date_input("Akhir Sewa", key="rk_akhir")
                rk_catatan = st.text_area("Catatan", key="rk_catatan")
                
                if st.form_submit_button("💾 Simpan Ruko", type="primary", use_container_width=True):
                    if not rk_nama:
                        st.error("❌ Nama Ruko wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO ruko 
                                (nama, alamat, status, penyewa, nilai_sewa, mulai_sewa, akhir_sewa, catatan)
                                VALUES (?,?,?,?,?,?,?,?)""",
                                (rk_nama, rk_alamat, rk_status, rk_penyewa, rk_nilai,
                                 str(rk_mulai), str(rk_akhir), rk_catatan))
                            conn.commit()
                            st.success(f"✅ Ruko **{rk_nama}** tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_RUKO", rk_nama)
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
        
        st.markdown('<div class="section-header"><h3>📊 Ringkasan Ruko</h3></div>', unsafe_allow_html=True)
        col_rk1, col_rk2, col_rk3 = st.columns(3)
        rk_total = c.execute("SELECT COUNT(*) FROM ruko").fetchone()[0]
        rk_disewa = c.execute("SELECT COUNT(*) FROM ruko WHERE status='Disewa'").fetchone()[0]
        rk_income = c.execute("SELECT COALESCE(SUM(nilai_sewa),0) FROM ruko WHERE status='Disewa'").fetchone()[0]
        with col_rk1: st.metric("Total Ruko", rk_total)
        with col_rk2: st.metric("Disewa", rk_disewa)
        with col_rk3: st.metric("Pendapatan / Bulan", format_rp(rk_income))
        
        st.markdown('<div class="section-header"><h3>📋 Daftar Ruko</h3></div>', unsafe_allow_html=True)
        render_edit_delete_table(
            "ruko",
            """SELECT id, nama, alamat, status, penyewa, nilai_sewa, 
                      mulai_sewa, akhir_sewa FROM ruko ORDER BY id DESC""",
            ["nama", "alamat", "status", "penyewa", "nilai_sewa", "mulai_sewa", "akhir_sewa"],
            ["id", "nama", "alamat", "status", "penyewa", "nilai_sewa", "mulai_sewa", "akhir_sewa"],
            "main_ruko"
        )
    
    # --- TAB TENANT ---
    with tab_rt2:
        with st.expander("➕ Tambah Tenant Baru", expanded=False):
            with st.form("tenant_form"):
                col1, col2 = st.columns(2)
                with col1:
                    tn_nama = st.text_input("Nama Tenant *", key="tn_nama")
                    tn_lokasi = st.text_input("Lokasi", key="tn_lokasi")
                    tn_kamar = st.text_input("Kamar / Unit", key="tn_kamar")
                with col2:
                    tn_penghuni = st.text_input("Penghuni", key="tn_penghuni")
                    tn_biaya = st.number_input("Biaya / Bulan (Rp)", min_value=0.0, step=500000.0, key="tn_biaya")
                    tn_status_ci = st.selectbox("Status CI (Check In)", ["-", "Sudah CI", "Belum CI"], key="tn_status_ci")
                tn_mulai = st.date_input("Mulai Sewa", key="tn_mulai")
                tn_catatan = st.text_area("Catatan", key="tn_catatan")
                
                if st.form_submit_button("💾 Simpan Tenant", type="primary", use_container_width=True):
                    if not tn_nama:
                        st.error("❌ Nama Tenant wajib diisi.")
                    else:
                        try:
                            c.execute("""INSERT INTO tenant 
                                (nama, lokasi, kamar, penghuni, biaya_bulanan, status_ci, mulai, catatan)
                                VALUES (?,?,?,?,?,?,?,?)""",
                                (tn_nama, tn_lokasi, tn_kamar, tn_penghuni, tn_biaya,
                                 tn_status_ci, str(tn_mulai), tn_catatan))
                            conn.commit()
                            st.success(f"✅ Tenant **{tn_nama}** tersimpan.")
                            log_aksi(st.session_state.username, "TAMBAH_TENANT", tn_nama)
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Gagal: {e}")
        
        st.markdown('<div class="section-header"><h3>📊 Ringkasan Tenant</h3></div>', unsafe_allow_html=True)
        col_tn1, col_tn2, col_tn3 = st.columns(3)
        tn_total = c.execute("SELECT COUNT(*) FROM tenant").fetchone()[0]
        tn_occupied = c.execute("SELECT COUNT(*) FROM tenant WHERE penghuni IS NOT NULL AND penghuni != ''").fetchone()[0]
        tn_income = c.execute("SELECT COALESCE(SUM(biaya_bulanan),0) FROM tenant WHERE penghuni IS NOT NULL AND penghuni != ''").fetchone()[0]
        with col_tn1: st.metric("Total Unit", tn_total)
        with col_tn2: st.metric("Terisi", tn_occupied)
        with col_tn3: st.metric("Pendapatan / Bulan", format_rp(tn_income))
        
        st.markdown('<div class="section-header"><h3>📋 Daftar Tenant</h3></div>', unsafe_allow_html=True)
        render_edit_delete_table(
            "tenant",
            """SELECT id, nama, lokasi, kamar, penghuni, biaya_bulanan, 
                      status_ci, mulai FROM tenant ORDER BY id DESC""",
            ["nama", "lokasi", "kamar", "penghuni", "biaya_bulanan", "status_ci", "mulai"],
            ["id", "nama", "lokasi", "kamar", "penghuni", "biaya_bulanan", "status_ci", "mulai"],
            "main_tenant"
        )

# --- 19. UTILITY MELAK ---
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1><p>Pembayaran Listrik, Air, Internet, Telepon</p></div>', unsafe_allow_html=True)
    
    with st.expander("➕ Tambah Pembayaran Utility", expanded=False):
        with st.form("utility_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                ut_kategori = st.selectbox("Kategori *", [
                    "Listrik", "Air (PDAM)", "Internet", "Telepon", 
                    "Gas", "BPJS", "Kebersihan", "Lainnya"
                ], key="ut_kategori")
                ut_tgl = st.date_input("Tanggal Bayar", key="ut_tgl")
                ut_periode = st.text_input("Periode (YYYY-MM)", value=datetime.now().strftime("%Y-%m"), key="ut_periode")
            with col2:
                ut_id_pelanggan = st.text_input("ID Pelanggan / No Meter", key="ut_id_pelanggan")
                ut_label = st.text_input("Label / Lokasi", key="ut_label", placeholder="Contoh: Gedung A / Ruko 1")
                ut_nominal = st.number_input("Nominal (Rp) *", min_value=0.0, step=50000.0, key="ut_nominal")
            with col3:
                ut_admin = st.number_input("Biaya Admin (Rp)", min_value=0.0, step=5000.0, value=0.0, key="ut_admin")
                ut_metode = st.selectbox("Metode Bayar", ["Cash", "Transfer", "Auto-Debit", "QRIS", "Lainnya"], key="ut_metode")
                ut_status = st.selectbox("Status", ["Lunas", "Pending", "Belum Bayar"], key="ut_status")
            ut_pj = st.text_input("Penanggung Jawab", key="ut_pj")
            ut_catatan = st.text_area("Catatan", key="ut_catatan")
            
            if st.form_submit_button("💾 Simpan Utility", type="primary", use_container_width=True):
                if ut_nominal <= 0:
                    st.error("❌ Nominal wajib > 0.")
                else:
                    try:
                        total_bayar = float(ut_nominal) + float(ut_admin)
                        c.execute("""INSERT INTO utility 
                            (kategori, tanggal_bayar, periode, id_pelanggan, label, 
                             nominal, admin, total_bayar, metode, status, penanggung_jawab, catatan, created_at)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (ut_kategori, str(ut_tgl), ut_periode, ut_id_pelanggan, ut_label,
                             ut_nominal, ut_admin, total_bayar, ut_metode, ut_status, ut_pj, ut_catatan,
                             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success(f"✅ Utility **{ut_kategori}** ({format_rp(total_bayar)}) tersimpan.")
                        log_aksi(st.session_state.username, "TAMBAH_UTILITY", f"{ut_kategori} - {format_rp(total_bayar)}")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📊 Ringkasan Utility</h3></div>', unsafe_allow_html=True)
    col_ut1, col_ut2 = st.columns(2)
    with col_ut1:
        periode_filter = st.text_input("Filter Periode (YYYY-MM, kosongkan untuk semua)", key="ut_filter_periode")
    with col_ut2:
        kategori_filter = st.selectbox("Filter Kategori", ["(Semua)", "Listrik", "Air (PDAM)", "Internet", "Telepon", "Gas", "BPJS", "Kebersihan", "Lainnya"], key="ut_filter_kategori")
    
    q_ut = "SELECT COALESCE(SUM(total_bayar),0) as total, COUNT(*) as jumlah FROM utility WHERE 1=1"
    params_ut = []
    if periode_filter:
        q_ut += " AND periode=?"
        params_ut.append(periode_filter)
    if kategori_filter != "(Semua)":
        q_ut += " AND kategori=?"
        params_ut.append(kategori_filter)
    
    res_ut = c.execute(q_ut, tuple(params_ut)).fetchone()
    col_ut_a, col_ut_b = st.columns(2)
    with col_ut_a: st.metric("Total Pengeluaran", format_rp(res_ut[0]))
    with col_ut_b: st.metric("Jumlah Transaksi", res_ut[1])
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Utility (Edit / Hapus)</h3></div>', unsafe_allow_html=True)
    render_edit_delete_table(
        "utility",
        """SELECT id, kategori, tanggal_bayar, periode, id_pelanggan, label, 
                  nominal, admin, total_bayar, metode, status, penanggung_jawab 
           FROM utility ORDER BY id DESC""",
        ["kategori", "tanggal_bayar", "periode", "id_pelanggan", "label",
         "nominal", "admin", "total_bayar", "metode", "status", "penanggung_jawab"],
        ["id", "kategori", "tanggal_bayar", "periode", "label", "total_bayar", "metode", "status"],
        "main_utility"
    )

# --- 20. ARSIP DOKUMEN (E-FILING) ---
elif pilihan == "📁 Arsip Dokumen (E-Filing)":
    st.markdown('<div class="main-header"><h1>📁 Arsip Dokumen (E-Filing)</h1><p>Upload & Simpan Dokumen Digital</p></div>', unsafe_allow_html=True)
    
    with st.form("arsip_form", clear_on_submit=True):
        st.subheader("📤 Upload Dokumen Baru")
        col1, col2 = st.columns(2)
        with col1:
            ar_nama = st.text_input("Nama Dokumen *", key="ar_nama")
            ar_kategori = st.selectbox("Kategori", [
                "Kontrak Kerja", "KTP", "NPWP", "Ijazah", "Sertifikat",
                "SK (Surat Keputusan)", "Slip Gaji", "Surat Peringatan",
                "Surat Lamaran", "CV", "Lainnya"
            ], key="ar_kategori")
        with col2:
            ar_ket = st.text_area("Keterangan", key="ar_ket")
        ar_file = st.file_uploader("Upload File (max 200MB)", key="ar_file")
        
        if st.form_submit_button("💾 Upload Dokumen", type="primary", use_container_width=True):
            if not ar_nama:
                st.error("❌ Nama dokumen wajib diisi.")
            elif ar_file is None:
                st.error("❌ File wajib di-upload.")
            else:
                try:
                    file_data = ar_file.read()
                    c.execute("""INSERT INTO arsip_dokumen 
                        (tanggal_upload, nama_dokumen, kategori, keterangan, file_data, file_name, file_type)
                        VALUES (?,?,?,?,?,?,?)""",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ar_nama, ar_kategori, ar_ket,
                         file_data, ar_file.name, ar_file.type))
                    conn.commit()
                    st.success(f"✅ File **{ar_file.name}** tersimpan ke arsip.")
                    log_aksi(st.session_state.username, "UPLOAD_ARSIP", ar_file.name)
                    time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Arsip Dokumen</h3></div>', unsafe_allow_html=True)
    df_arsip = pd.read_sql_query(
        """SELECT id, tanggal_upload, nama_dokumen, kategori, keterangan, 
                  file_name, file_type 
           FROM arsip_dokumen ORDER BY id DESC""",
        conn
    )
    if not df_arsip.empty:
        st.dataframe(df_arsip, use_container_width=True, hide_index=True)
        
        st.markdown("**⬇️ Download / 🗑️ Hapus Dokumen:**")
        col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
        with col_dl1:
            ar_dl_id = st.number_input("ID Dokumen", min_value=0, step=1, key="ar_dl_id")
        with col_dl2:
            if st.button("⬇️ Siapkan Download", key="btn_dl_arsip", use_container_width=True):
                if ar_dl_id > 0:
                    row = c.execute("SELECT file_name, file_type, file_data FROM arsip_dokumen WHERE id=?", (int(ar_dl_id),)).fetchone()
                    if row:
                        st.session_state["ar_download"] = {"filename": row[0], "mime": row[1] or "application/octet-stream", "data": row[2]}
                        st.success(f"✅ File **{row[0]}** siap diunduh.")
                    else:
                        st.warning(f"❌ Dokumen ID {ar_dl_id} tidak ditemukan.")
        with col_dl3:
            if st.button("🗑️ Hapus Dokumen", key="btn_del_arsip", use_container_width=True):
                if ar_dl_id > 0:
                    c.execute("DELETE FROM arsip_dokumen WHERE id=?", (int(ar_dl_id),))
                    conn.commit()
                    st.success(f"✅ Dokumen ID {ar_dl_id} dihapus.")
                    log_aksi(st.session_state.username, "HAPUS_ARSIP", f"ID {ar_dl_id}")
                    time.sleep(1); st.rerun()
        
        if "ar_download" in st.session_state and st.session_state["ar_download"]:
            d = st.session_state["ar_download"]
            st.download_button(
                f"💾 Klik untuk Download: {d['filename']}",
                data=d["data"],
                file_name=d["filename"],
                mime=d["mime"],
                key="dl_arsip_btn"
            )
    else:
        st.info("Belum ada dokumen yang di-upload.")

# --- 21. LAMPIRAN / ATTACHMENT ---
elif pilihan == "📎 Lampiran / Attachment":
    st.markdown('<div class="main-header"><h1>📎 Lampiran / Attachment</h1><p>Lampiran File Terkait Modul Lain</p></div>', unsafe_allow_html=True)
    
    st.info("💡 Modul ini digunakan untuk melampirkan file ke modul lain (misal: cuti butuh lampiran surat dokter, kandidat butuh lampiran CV, dll).")
    
    with st.form("lampiran_form", clear_on_submit=True):
        st.subheader("📤 Upload Lampiran Baru")
        col1, col2 = st.columns(2)
        with col1:
            lm_modul = st.selectbox("Referensi Modul *", [
                "cuti", "kandidat", "karyawan", "resign", "disiplin",
                "payroll", "arsip_dokumen", "lainnya"
            ], key="lm_modul")
            lm_id = st.text_input("Referensi ID (misal: 15) *", key="lm_id")
        with col2:
            lm_ket = st.text_area("Keterangan", key="lm_ket")
        lm_file = st.file_uploader("Upload File", key="lm_file")
        
        if st.form_submit_button("💾 Upload Lampiran", type="primary", use_container_width=True):
            if not lm_id:
                st.error("❌ Referensi ID wajib diisi.")
            elif lm_file is None:
                st.error("❌ File wajib di-upload.")
            else:
                try:
                    file_data = lm_file.read()
                    c.execute("""INSERT INTO lampiran 
                        (ref_modul, ref_id, file_name, file_type, file_data, tanggal_upload, keterangan)
                        VALUES (?,?,?,?,?,?,?)""",
                        (lm_modul, lm_id, lm_file.name, lm_file.type, file_data,
                         datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lm_ket))
                    conn.commit()
                    st.success(f"✅ Lampiran **{lm_file.name}** → {lm_modul}#{lm_id} tersimpan.")
                    log_aksi(st.session_state.username, "UPLOAD_LAMPIRAN", f"{lm_modul}#{lm_id} - {lm_file.name}")
                    time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"Gagal: {e}")
    
    st.markdown('<div class="section-header"><h3>📋 Daftar Lampiran</h3></div>', unsafe_allow_html=True)
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        lm_filter_modul = st.selectbox("Filter Modul", ["(Semua)", "cuti", "kandidat", "karyawan", "resign", "disiplin", "payroll", "arsip_dokumen", "lainnya"], key="lm_filter_modul")
    with col_f2:
        lm_filter_id = st.text_input("Filter ID (opsional)", key="lm_filter_id")
    
    q_lm = "SELECT id, ref_modul, ref_id, file_name, file_type, tanggal_upload, keterangan FROM lampiran WHERE 1=1"
    params_lm = []
    if lm_filter_modul != "(Semua)":
        q_lm += " AND ref_modul=?"
        params_lm.append(lm_filter_modul)
    if lm_filter_id:
        q_lm += " AND ref_id=?"
        params_lm.append(lm_filter_id)
    q_lm += " ORDER BY id DESC"
    
    df_lm = pd.read_sql_query(q_lm, conn, params=tuple(params_lm))
    if not df_lm.empty:
        st.dataframe(df_lm, use_container_width=True, hide_index=True)
        st.caption(f"Menampilkan **{len(df_lm)}** lampiran")
        
        st.markdown("**⬇️ Download / 🗑️ Hapus Lampiran:**")
        col_lm1, col_lm2, col_lm3 = st.columns([1, 1, 1])
        with col_lm1:
            lm_dl_id = st.number_input("ID Lampiran", min_value=0, step=1, key="lm_dl_id")
        with col_lm2:
            if st.button("⬇️ Siapkan Download", key="btn_dl_lm", use_container_width=True):
                if lm_dl_id > 0:
                    row = c.execute("SELECT file_name, file_type, file_data FROM lampiran WHERE id=?", (int(lm_dl_id),)).fetchone()
                    if row:
                        st.session_state["lm_download"] = {"filename": row[0], "mime": row[1] or "application/octet-stream", "data": row[2]}
                        st.success(f"✅ File **{row[0]}** siap diunduh.")
                    else:
                        st.warning(f"❌ Lampiran ID {lm_dl_id} tidak ditemukan.")
        with col_lm3:
            if st.button("🗑️ Hapus Lampiran", key="btn_del_lm", use_container_width=True):
                if lm_dl_id > 0:
                    c.execute("DELETE FROM lampiran WHERE id=?", (int(lm_dl_id),))
                    conn.commit()
                    st.success(f"✅ Lampiran ID {lm_dl_id} dihapus.")
                    log_aksi(st.session_state.username, "HAPUS_LAMPIRAN", f"ID {lm_dl_id}")
                    time.sleep(1); st.rerun()
        
        if "lm_download" in st.session_state and st.session_state["lm_download"]:
            d = st.session_state["lm_download"]
            st.download_button(
                f"💾 Klik untuk Download: {d['filename']}",
                data=d["data"],
                file_name=d["filename"],
                mime=d["mime"],
                key="dl_lm_btn"
            )
    else:
        st.info("Belum ada lampiran.")# --- 22. FORMULIR HRD (OFFICIAL) ---
elif pilihan == "📋 Formulir HRD (Official)":
    st.markdown('<div class="main-header"><h1>📋 Formulir HRD (Official)</h1><p>Cetak & Input Data Formulir Standar Perusahaan</p></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Wawancara & Coaching", "🌴 Permohonan Cuti", "🧑‍💼 Data Pelamar", 
        "📋 Permintaan Karyawan (FPK)", "🚪 Exit & Clearance", "⏱️ Izin & Kehadiran"
    ])
    
    # ================= TAB 1: WAWANCARA & COACHING =================
    with tab1:
        st.subheader("Formulir Laporan Wawancara & Data Fisik Pelamar")
        
        # --- FORM 1: LAPORAN WAWANCARA ---
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR LAPORAN WAWANCARA</div>', unsafe_allow_html=True)
            
            # Data Diri
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.text_input("Nama", key="w_nama")
            with c2: st.text_input("Jabatan yang dilamar", key="w_jabatan")
            with c3: st.text_input("Usia", key="w_usia")
            with c4: st.date_input("Tanggal Wawancara", key="w_tgl")
            
            st.info("Isilah kolom dengan checklist (v) pada kolom 1,2,3,4,5 sesuai dengan kelompok nilai yang tertera di bawah ini. **5 = Baik Sekali, 4 = Baik, 3 = Cukup, 2 = Kurang, 1 = Kurang Sekali**")
            
            # Penilaian Faktor (1-5)
            st.markdown("**Penilaian Faktor:**")
            st.radio("1. KUALIFIKASI (Pendidikan, Training, Organisasi, Jenis Kelamin, Usia, dsb.)", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f1")
            st.radio("2. PENGALAMAN (Pengalaman bekerja yang dimiliki berhubungan dengan jabatan yang dilamar.)", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f2")
            st.radio("3. PENGETAHUAN DAN KETERAMPILAN (Pengetahuan/ketrampilan yang digunakan dalam jabatan yang dilamar.)", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f3")
            st.radio("4. KARAKTERISTIK KEPRIBADIAN (Unity, Responsibility, & Enthusiasm)", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f4")
            st.radio("5. KOMUNIKASI (Lancar > Tidak lancar/berbelit-belit)", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f5")
            
            st.markdown("---")
            
            # Kelebihan, Kekurangan, Keputusan
            c_kiri, c_kanan = st.columns(2)
            with c_kiri:
                st.text_area("Kelebihan", height=100, key="w_kelebihan")
                st.text_area("Kekurangan", height=100, key="w_kekurangan")
            with c_kanan:
                st.markdown("**KEPUTUSAN**")
                st.checkbox("DITOLAK", key="w_dec_tolak")
                st.checkbox("DIPERTIMBANGKAN", key="w_dec_pertimbangkan")
                st.checkbox("DITERIMA", key="w_dec_terima")
                st.text_input("Pewawancara* (I / II / III / IV)", key="w_pewawancara")
                st.text_input("Nama Pewawancara", key="w_nama_pewawancara")
                st.text_input("Jabatan Pewawancara", key="w_jabatan_pewawancara")

        # --- FORM 2: DATA FISIK & CHECKLIST PELAMAR ---
        st.markdown("---")
        with st.container(border=True):
            st.markdown('<div class="form-title">DATA PELAMAR & CHECKLIST FISIK</div>', unsafe_allow_html=True)
            
            # Data Diri Tambahan
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Posisi", key="p_posisi")
                st.text_input("Nama Lengkap", key="p_nama")
                st.text_input("Suku", key="p_suku")
            with c2:
                st.text_input("Pendidikan", key="p_pendidikan")
                st.radio("Jenis Kelamin", ["Pria", "Wanita"], horizontal=True, key="p_gender")
                st.text_input("Penempatan", key="p_penempatan")
            
            st.info("Isilah kolom dengan checklist (v) sesuai dengan keterangan yang ada.")
            
            # Tabel Checklist Fisik
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.number_input("1. Usia (Minimal 21 Tahun)", min_value=0, step=1, key="p_usia", help="Tahun")
                st.number_input("2. Tinggi Badan (Pria min 165 cm / Wanita min 155 cm)", min_value=0, step=1, key="p_tinggi", help="cm")
                st.number_input("3. Berat Badan", min_value=0, step=1, key="p_berat", help="kg")
                st.text_input("4. Pendidikan (Detail)", key="p_pendidikan_detail")
                st.number_input("5. Jarak Dari Tempat Tinggal ke Kantor UEI", min_value=0, step=1, key="p_jarak", help="km")
                st.text_input("6. Riwayat Penyakit", key="p_riwayat_penyakit")
                
                st.radio("7. Tidak Buta Warna", ["YA", "TIDAK"], horizontal=True, key="p_buta_warna")
                st.radio("8. Tidak Bertato", ["YA", "TIDAK"], horizontal=True, key="p_tato")
                st.radio("9. Tidak Mengkonsumsi NAPZA", ["YA", "TIDAK"], horizontal=True, key="p_napza")
                st.radio("10. Tidak Memiliki Catatan Kriminal (SKCK)", ["YA", "TIDAK"], horizontal=True, key="p_skck")
                st.radio("11. Bersedia Ditempatkan di Seluruh Cabang Perusahaan", ["YA", "TIDAK"], horizontal=True, key="p_penempatan_cabang")

            with col_b:
                st.selectbox("12. Cara Berkomunikasi", ["Sopan - Tertata", "Sopan - Tidak Tertata", "Tidak Sopan"], key="p_komunikasi")
                st.selectbox("13. Cara Berjalan", ["Normal", "Cepat", "Lambat"], key="p_jalan")
                st.radio("14. Digital Savvy (Menguasai Teknologi Digital)", ["BISA", "TIDAK BISA"], horizontal=True, key="p_digital")
                st.selectbox("15. Penampilan", ["Normal / Rapi / Berdandanan", "Menor / Berlebihan", "Tidak berdandan"], key="p_penampilan")
                st.selectbox("16. Postur Tubuh", ["Tegak - Normal", "Bungkuk"], key="p_postur")
                st.selectbox("17. Proporsional Badan", ["Normal", "Underweight (Kurus)", "Overweight (Gemuk)"], key="p_proporsional")
                st.selectbox("18. Tekanan Darah", ["Normal", "Rendah", "Tinggi"], key="p_darah")
                st.selectbox("19. Pengelihatan", ["Normal", "Rabun Jauh", "Rabun Dekat"], key="p_mata")
                
            st.markdown("---")
            st.markdown("**KEPUTUSAN & TANDA TANGAN**")
            c_dec1, c_dec2 = st.columns(2)
            with c_dec1:
                st.checkbox("DITOLAK", key="p_dec_tolak")
                st.checkbox("DIPERTIMBANGKAN", key="p_dec_pertimbangkan")
                st.checkbox("DITERIMA", key="p_dec_terima")
            with c_dec2:
                st.text_input("Pewawancara* (I / II / III / IV)", key="p_pewawancara")
                st.text_input("Nama Pewawancara", key="p_nama_pewawancara")
                st.text_input("Jabatan Pewawancara", key="p_jabatan_pewawancara")

        # Tombol Simpan Wawancara & Fisik (SEKARANG BENAR-BENAR SIMPAN KE DATABASE)
        if st.button("💾 Simpan Formulir Wawancara & Fisik", type="primary", use_container_width=True, key="btn_save_wawancara_full"):
            try:
                w_nama_val = st.session_state.get("w_nama", "")
                w_jabatan_val = st.session_state.get("w_jabatan", "")
                w_usia_val = st.session_state.get("w_usia", "")
                w_tgl_val = str(st.session_state.get("w_tgl", ""))
                w_kelebihan_val = st.session_state.get("w_kelebihan", "")
                w_kekurangan_val = st.session_state.get("w_kekurangan", "")
                w_pewawancara_val = st.session_state.get("w_pewawancara", "")
                w_nama_p_val = st.session_state.get("w_nama_pewawancara", "")
                w_jabatan_p_val = st.session_state.get("w_jabatan_pewawancara", "")
                
                keputusan_list = []
                if st.session_state.get("w_dec_tolak"): keputusan_list.append("DITOLAK")
                if st.session_state.get("w_dec_pertimbangkan"): keputusan_list.append("DIPERTIMBANGKAN")
                if st.session_state.get("w_dec_terima"): keputusan_list.append("DITERIMA")
                
                data_fisik = {
                    "posisi": st.session_state.get("p_posisi", ""),
                    "nama": st.session_state.get("p_nama", ""),
                    "suku": st.session_state.get("p_suku", ""),
                    "pendidikan": st.session_state.get("p_pendidikan", ""),
                    "gender": st.session_state.get("p_gender", ""),
                    "penempatan": st.session_state.get("p_penempatan", ""),
                    "usia": st.session_state.get("p_usia", 0),
                    "tinggi": st.session_state.get("p_tinggi", 0),
                    "berat": st.session_state.get("p_berat", 0),
                    "pendidikan_detail": st.session_state.get("p_pendidikan_detail", ""),
                    "jarak_km": st.session_state.get("p_jarak", 0),
                    "riwayat_penyakit": st.session_state.get("p_riwayat_penyakit", ""),
                    "buta_warna": st.session_state.get("p_buta_warna", ""),
                    "tato": st.session_state.get("p_tato", ""),
                    "napza": st.session_state.get("p_napza", ""),
                    "skck": st.session_state.get("p_skck", ""),
                    "penempatan_cabang": st.session_state.get("p_penempatan_cabang", ""),
                    "komunikasi": st.session_state.get("p_komunikasi", ""),
                    "jalan": st.session_state.get("p_jalan", ""),
                    "digital": st.session_state.get("p_digital", ""),
                    "penampilan": st.session_state.get("p_penampilan", ""),
                    "postur": st.session_state.get("p_postur", ""),
                    "proporsional": st.session_state.get("p_proporsional", ""),
                    "darah": st.session_state.get("p_darah", ""),
                    "mata": st.session_state.get("p_mata", ""),
                    "keputusan": [x for x, v in [
                        ("DITOLAK", st.session_state.get("p_dec_tolak")),
                        ("DIPERTIMBANGKAN", st.session_state.get("p_dec_pertimbangkan")),
                        ("DITERIMA", st.session_state.get("p_dec_terima"))
                    ] if v],
                    "pewawancara": st.session_state.get("p_pewawancara", ""),
                    "nama_pewawancara": st.session_state.get("p_nama_pewawancara", ""),
                    "jabatan_pewawancara": st.session_state.get("p_jabatan_pewawancara", "")
                }
                
                c.execute("""INSERT INTO formulir_wawancara 
                    (nama, jabatan, usia, tanggal_wawancara, f1, f2, f3, f4, f5, 
                     kelebihan, kekurangan, keputusan, pewawancara, nama_pewawancara, jabatan_pewawancara, 
                     data_fisik, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (w_nama_val, w_jabatan_val, w_usia_val, w_tgl_val,
                     st.session_state.get("w_f1", "5"), st.session_state.get("w_f2", "5"),
                     st.session_state.get("w_f3", "5"), st.session_state.get("w_f4", "5"),
                     st.session_state.get("w_f5", "5"),
                     w_kelebihan_val, w_kekurangan_val, ",".join(keputusan_list),
                     w_pewawancara_val, w_nama_p_val, w_jabatan_p_val,
                     json.dumps(data_fisik, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Formulir Wawancara untuk **{w_nama_val or st.session_state.get('p_nama','(tanpa nama)')}** berhasil disimpan ke database.")
                log_aksi(st.session_state.username, "SIMPAN_WAWANCARA", w_nama_val or "tanpa nama")
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal menyimpan: {e}")

        # Riwayat Wawancara
        st.markdown("---")
        st.markdown("**📋 Riwayat Formulir Wawancara:**")
        df_waw = pd.read_sql_query(
            """SELECT id, nama, jabatan, usia, tanggal_wawancara, keputusan, pewawancara, created_by, created_at 
               FROM formulir_wawancara ORDER BY id DESC LIMIT 20""",
            conn
        )
        if not df_waw.empty:
            st.dataframe(df_waw, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada formulir wawancara yang tersimpan.")

        st.divider()
        st.subheader("2. Form Coaching & Counselling")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORM COACHING & COUNSELLING</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                co_nama = st.text_input("Nama Karyawan", key="co_nama")
                co_nik = st.text_input("NIK", key="co_nik")
            with c2:
                co_tgl_masuk = st.text_input("Tanggal Masuk", key="co_tgl_masuk")
                co_jabatan = st.text_input("Jabatan / Departemen", key="co_jabatan")
            co_status = st.radio("Status Karyawan", ["Tetap", "Kontrak (PKWT)", "Percobaan"], horizontal=True, key="co_status")
            co_isu = st.text_area("Isu/Permasalahan & Penyebabnya", height=80, key="co_isu")
            co_obs = st.text_area("Observasi/Kesaksian (Kolom saksi jika ada saksinya)", height=80, key="co_obs")
            co_langkah = st.text_area("Langkah perbaikan yang akan dilakukan", height=80, key="co_langkah")
            co_komit = st.text_area("Komitmen Karyawan akan sanksi yang diberikan apabila tidak melakukan perbaikan", height=80, key="co_komit")
            
            st.markdown("**Rekomendasi (Atasan/HRD):**")
            co_rek1 = st.checkbox("Diberi kesempatan melakukan perubahan selama ... setelah coaching & counselling", key="co_rek1")
            co_rek2 = st.checkbox("Direlokasi ke posisi lain", key="co_rek2")
            co_rek3 = st.checkbox("Mendapat sanksi sesuai peraturan perusahaan", key="co_rek3")
            co_rek4 = st.checkbox("Masa kerja tidak dapat dilanjutkan (termination)", key="co_rek4")
            co_hal = st.text_area("Hal yang akan dilakukan (Atasan/HRD)", height=80, key="co_hal")
            
            if st.button("💾 Simpan Form Coaching", type="primary", use_container_width=True, key="btn_save_coaching_full"):
                try:
                    rekomendasi_list = []
                    if co_rek1: rekomendasi_list.append("Diberi kesempatan")
                    if co_rek2: rekomendasi_list.append("Direlokasi")
                    if co_rek3: rekomendasi_list.append("Sanksi")
                    if co_rek4: rekomendasi_list.append("Termination")
                    
                    c.execute("""INSERT INTO formulir_coaching 
                        (nama_karyawan, nik, tanggal_masuk, jabatan, status_karyawan, isu, observasi, 
                         langkah_perbaikan, komitmen, rekomendasi, hal_dilakukan, created_by, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (co_nama, co_nik, co_tgl_masuk, co_jabatan, co_status, co_isu, co_obs,
                         co_langkah, co_komit, ", ".join(rekomendasi_list), co_hal,
                         st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"✅ Form Coaching untuk **{co_nama or '(tanpa nama)'}** tersimpan.")
                    log_aksi(st.session_state.username, "SIMPAN_COACHING", co_nama or "tanpa nama")
                    time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan: {e}")

        # Riwayat Coaching
        st.markdown("---")
        st.markdown("**📋 Riwayat Form Coaching:**")
        df_co = pd.read_sql_query(
            """SELECT id, nama_karyawan, nik, jabatan, status_karyawan, rekomendasi, created_by, created_at 
               FROM formulir_coaching ORDER BY id DESC LIMIT 20""",
            conn
        )
        if not df_co.empty:
            st.dataframe(df_co, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada form coaching yang tersimpan.")    # ================= TAB 2: PERMOHONAN CUTI (FULL ORIGINAL) =================
    with tab2:
        st.subheader("1. Surat Permohonan Cuti (Standard)")
        with st.container(border=True):
            st.markdown('<div class="form-title">SURAT PERMOHONAN CUTI</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: st.text_input("Nama", key="c_nama")
            with c2: st.text_input("NIK / Divisi", key="c_nik")
            st.markdown("**Jenis Cuti:**")
            st.checkbox("Tahunan", key="c_tahunan"); st.checkbox("Melahirkan", key="c_melahirkan"); st.checkbox("Jobsite", key="c_jobsite"); st.checkbox("Mangkir", key="c_mangkir")
            c3, c4 = st.columns(2)
            with c3: st.number_input("Lama Cuti (Hari)", min_value=1, step=1, key="c_lama")
            with c4: st.text_input("Mulai s/d", key="c_tgl")
            st.text_area("Keterangan", key="c_ket")
            
            st.markdown("---")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Pemohon<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Mengetahui<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Menyetujui (HRD)<br><br><br>(............................)</center>", unsafe_allow_html=True)

        # Tombol simpan
        if st.button("💾 Simpan Surat Permohonan Cuti (Standard)", type="primary", use_container_width=True, key="btn_save_cuti_std_full"):
            try:
                jenis_list = []
                if st.session_state.get("c_tahunan"): jenis_list.append("Tahunan")
                if st.session_state.get("c_melahirkan"): jenis_list.append("Melahirkan")
                if st.session_state.get("c_jobsite"): jenis_list.append("Jobsite")
                if st.session_state.get("c_mangkir"): jenis_list.append("Mangkir")
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, nama, jabatan, tanggal, alasan, keterangan, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    ("CUTI_STANDARD", st.session_state.get("c_nama",""), st.session_state.get("c_nik",""),
                     st.session_state.get("c_tgl",""), ", ".join(jenis_list), st.session_state.get("c_ket",""),
                     json.dumps({"lama_hari": st.session_state.get("c_lama", 1)}),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Surat permohonan cuti **{st.session_state.get('c_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_CUTI_STD", st.session_state.get("c_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        st.subheader("2. Permohonan Cuti Khusus")
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN CUTI KHUSUS</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: st.date_input("Tgl. Permohonan", key="ck_tgl"); st.text_input("Nama", key="ck_nama")
            with c2: st.text_input("Dept.", key="ck_dept"); st.text_input("NIK", key="ck_nik")
            with c3: st.text_input("Bagian", key="ck_bagian"); st.text_input("Tanggal (s/d)", key="ck_tgl_akhir")
            
            st.markdown("Dengan ini saya mengajukan cuti untuk:")
            st.radio("Alasan Cuti Khusus", [
                "Menikah (3 Hari Kerja)",
                "Pernikahan anak (2 Hari Kerja)",
                "Mengkhitankan / membaptiskan anak (2 Hari Kerja)",
                "Istri Melahirkan / Gugur kandungan (2 Hari Kerja)",
                "Istri/ Suami/ Anak meninggal (2 Hari Kerja)",
                "Orang tua/ Mertua / Menantu meninggal (2 Hari Kerja)",
                "Anggota keluarga Karyawan yang serumah meninggal dunia (1 Hari Kerja)",
                "Melahirkan / Keguguran (45 hari sblm dan ssdh melahirkan)",
                "Ibadah Haji (40 hari, hanya 1 kali pengajuan)",
                "Bencana alam (Max. 2 Hari Kerja)"
            ], key="ck_alasan")
            st.warning("Catatan: Setiap pengajuan cuti khusus ini harus melampirkan dokumen resmi sebagai pendukungnya.")
            st.markdown("---")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Pemohon<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>KA Dept.<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Disetujui Oleh<br>HR Manager / Direktur<br><br>(............................)</center>", unsafe_allow_html=True)

        # Tombol simpan
        if st.button("💾 Simpan Permohonan Cuti Khusus", type="primary", use_container_width=True, key="btn_save_cuti_khusus_full"):
            try:
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, nama, jabatan, tanggal, alasan, keterangan, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    ("CUTI_KHUSUS", st.session_state.get("ck_nama",""), st.session_state.get("ck_dept",""),
                     str(st.session_state.get("ck_tgl","")), st.session_state.get("ck_alasan",""), 
                     st.session_state.get("ck_bagian",""),
                     json.dumps({"nik": st.session_state.get("ck_nik",""), "sampai": st.session_state.get("ck_tgl_akhir","")}),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Cuti khusus **{st.session_state.get('ck_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_CUTI_KHUSUS", st.session_state.get("ck_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        # Riwayat
        st.markdown("---")
        st.markdown("**📋 Riwayat Permohonan Cuti (Formulir HRD):**")
        df_cuti_hr = pd.read_sql_query(
            "SELECT id, jenis_form, nama, jabatan, tanggal, alasan, created_by, created_at FROM formulir_izin WHERE jenis_form IN ('CUTI_STANDARD', 'CUTI_KHUSUS') ORDER BY id DESC LIMIT 20",
            conn
        )
        if not df_cuti_hr.empty:
            st.dataframe(df_cuti_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat permohonan cuti.")

    # ================= TAB 3: DATA PELAMAR (FULL ORIGINAL) =================
    with tab3:
        st.subheader("Formulir Data Pelamar")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR DATA PELAMAR</div>', unsafe_allow_html=True)
            with st.expander("A. DATA PRIBADI", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Pekerjaan yang Dilamar", key="dp_pekerjaan")
                    st.text_input("Nama Lengkap", key="dp_nama")
                    st.text_input("Nama Panggilan", key="dp_panggilan")
                    st.radio("Jenis Kelamin", ["Laki-Laki", "Perempuan"], horizontal=True, key="dp_jk")
                    st.text_area("Alamat Tempat Tinggal", key="dp_alamat_tinggal")
                    st.text_area("Alamat Sesuai KTP", key="dp_alamat_ktp")
                with c2:
                    st.text_input("Email", key="dp_email")
                    st.text_input("Tempat & Tanggal Lahir", key="dp_ttl")
                    st.selectbox("Agama", ["Islam", "Kristen", "Katholik", "Hindu", "Budha"], key="dp_agama")
                    st.selectbox("Status Perkawinan", ["Menikah", "Tidak Menikah", "Janda/Duda"], key="dp_status_perkawinan")
                    st.selectbox("Tempat Tinggal", ["Sendiri", "Ikut Orang Tua", "Kost/Kontrak"], key="dp_tempat_tinggal")
                    st.text_input("Nomor KTP", key="dp_no_ktp")
                    st.text_input("Nomor SIM", key="dp_no_sim")
            
            with st.expander("B. SUSUNAN KELUARGA"):
                st.info("Tabel susunan keluarga (Ayah, Ibu, Saudara 1-5, Isteri/Suami, Anak 1-5) dapat diinput menggunakan tabel dinamis di bawah ini.")
                df_keluarga = st.data_editor(pd.DataFrame(columns=["Hubungan", "Nama", "Pendidikan", "Pekerjaan", "Jabatan", "Perusahaan", "Telepon", "Keterangan"]), num_rows="dynamic", use_container_width=True, key="dp_de_keluarga")
                
            with st.expander("C. LATAR BELAKANG PENDIDIKAN FORMAL / INFORMAL"):
                df_pendidikan = st.data_editor(pd.DataFrame(columns=["Tingkat", "Nama Sekolah", "Tempat/Kota", "Jurusan", "Tahun Masuk", "Tahun Keluar", "Lulus/Tidak"]), num_rows="dynamic", use_container_width=True, key="dp_de_pendidikan")
            
            with st.expander("D. KURSUS / PELATIHAN YANG PERNAH DIKUTI"):
                df_kursus = st.data_editor(pd.DataFrame(columns=["Bidang/Jenis", "Lembaga", "Tempat/Kota", "Lama Kursus", "Tahun", "Dibiayai Oleh"]), num_rows="dynamic", use_container_width=True, key="dp_de_kursus")

            with st.expander("E. PENGETAHUAN BAHASA ASING"):
                df_bahasa = st.data_editor(pd.DataFrame(columns=["Bahasa", "Bicara", "Mendengar", "Membaca", "Menulis", "Pemakaian"]), num_rows="dynamic", use_container_width=True, key="dp_de_bahasa")

            with st.expander("F. KEGIATAN SOSIAL"):
                df_sosial = st.data_editor(pd.DataFrame(columns=["Tahun", "Nama Organisasi", "Jenis Kegiatan", "Jabatan"]), num_rows="dynamic", use_container_width=True, key="dp_de_sosial")

            with st.expander("G. HOBBY DAN KEGIATAN WAKTU LUANG"):
                st.text_area("Hobby", key="dp_hobby")

            with st.expander("H. RIWAYAT PEKERJAAN"):
                df_pekerjaan = st.data_editor(pd.DataFrame(columns=["Nama/Perusahaan", "Jabatan", "Awal", "Akhir", "Lama Kerja", "Jenis Usaha", "Alasan Berhenti", "Atasan Langsung", "Direktur", "Gaji Terakhir"]), num_rows="dynamic", use_container_width=True, key="dp_de_pekerjaan")

            with st.expander("I. REFERENSI"):
                df_referensi = st.data_editor(pd.DataFrame(columns=["Nama", "Alamat", "Telepon", "Pekerjaan", "Hubungan"]), num_rows="dynamic", use_container_width=True, key="dp_de_referensi")

            with st.expander("J. URAIAN TUGAS DAN TANGGUNG JAWAB"):
                st.text_area("Uraikan tugas dan tanggung jawab Anda pada jabatan terakhir Anda:", height=100, key="dp_uraian_tugas")

            with st.expander("K. HAL-HAL POSITIF & NEGATIF"):
                st.text_area("Hal-Hal Yang Positif", height=100, key="dp_positif")
                st.text_area("Hal-Hal Yang Negatif", height=100, key="dp_negatif")

            with st.expander("PERTANYAAN 1 (Aset Pribadi)"):
                df_pertanyaan1 = st.data_editor(pd.DataFrame(columns=["Pertanyaan", "Ya", "Tidak", "Penjelasan"]), num_rows="dynamic", use_container_width=True, key="dp_de_pertanyaan1")

            with st.expander("PERTANYAAN 2"):
                df_pertanyaan2 = st.data_editor(pd.DataFrame(columns=["Pertanyaan", "Ya", "Tidak", "Penjelasan"]), num_rows="dynamic", use_container_width=True, key="dp_de_pertanyaan2")
                
            st.markdown("**Pernyataan:** DENGAN INI SAYA MENYATAKAN BAHWA KETERANGAN YANG SAYA BERIKAN DIATAS ADALAH BENAR. APABILA DIKEMUDIAN HARI DITEMUKAN KETIDAKSESUAIAN, SAYA BERTANGGUNG JAWAB PENUH ATAS AKIBATNYA.")
            st.text_input("JAKARTA, (Tanggal)", key="dp_tgl_pernyataan")
            st.text_input("PELAMAR (Nama Terang)", key="dp_nama_terang")

        # Tombol simpan
        if st.button("💾 Simpan Formulir Data Pelamar", type="primary", use_container_width=True, key="btn_save_data_pelamar"):
            try:
                data_json = json.dumps({
                    "pekerjaan_dilamar": st.session_state.get("dp_pekerjaan", ""),
                    "nama_panggilan": st.session_state.get("dp_panggilan", ""),
                    "jenis_kelamin": st.session_state.get("dp_jk", ""),
                    "alamat_tinggal": st.session_state.get("dp_alamat_tinggal", ""),
                    "alamat_ktp": st.session_state.get("dp_alamat_ktp", ""),
                    "email": st.session_state.get("dp_email", ""),
                    "ttl": st.session_state.get("dp_ttl", ""),
                    "agama": st.session_state.get("dp_agama", ""),
                    "status_perkawinan": st.session_state.get("dp_status_perkawinan", ""),
                    "tempat_tinggal": st.session_state.get("dp_tempat_tinggal", ""),
                    "no_ktp": st.session_state.get("dp_no_ktp", ""),
                    "no_sim": st.session_state.get("dp_no_sim", ""),
                    "keluarga": df_keluarga.to_dict("records") if not df_keluarga.empty else [],
                    "pendidikan": df_pendidikan.to_dict("records") if not df_pendidikan.empty else [],
                    "kursus": df_kursus.to_dict("records") if not df_kursus.empty else [],
                    "bahasa": df_bahasa.to_dict("records") if not df_bahasa.empty else [],
                    "sosial": df_sosial.to_dict("records") if not df_sosial.empty else [],
                    "hobby": st.session_state.get("dp_hobby", ""),
                    "riwayat_pekerjaan": df_pekerjaan.to_dict("records") if not df_pekerjaan.empty else [],
                    "referensi": df_referensi.to_dict("records") if not df_referensi.empty else [],
                    "uraian_tugas": st.session_state.get("dp_uraian_tugas", ""),
                    "hal_positif": st.session_state.get("dp_positif", ""),
                    "hal_negatif": st.session_state.get("dp_negatif", ""),
                    "pertanyaan_1": df_pertanyaan1.to_dict("records") if not df_pertanyaan1.empty else [],
                    "pertanyaan_2": df_pertanyaan2.to_dict("records") if not df_pertanyaan2.empty else [],
                    "tanggal_pernyataan": st.session_state.get("dp_tgl_pernyataan", ""),
                    "nama_terang": st.session_state.get("dp_nama_terang", "")
                }, ensure_ascii=False, default=str)
                
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, posisi, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    ("DATA_PELAMAR", st.session_state.get("dp_nama", ""), st.session_state.get("dp_pekerjaan", ""),
                     data_json, st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Formulir Data Pelamar untuk **{st.session_state.get('dp_nama','(tanpa nama)')}** tersimpan lengkap.")
                log_aksi(st.session_state.username, "SIMPAN_DATA_PELAMAR", st.session_state.get("dp_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        # Riwayat
        st.markdown("---")
        st.markdown("**📋 Riwayat Formulir Data Pelamar:**")
        df_dp_hr = pd.read_sql_query(
            "SELECT id, nama, posisi, created_by, created_at FROM formulir_exit WHERE jenis_form='DATA_PELAMAR' ORDER BY id DESC LIMIT 20",
            conn
        )
        if not df_dp_hr.empty:
            st.dataframe(df_dp_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada formulir data pelamar yang tersimpan.")    # ================= TAB 4: PERMINTAAN KARYAWAN (FPK) — FULL =================
    with tab4:
        st.subheader("Formulir Permintaan Karyawan (FPK)")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR PERMINTAAN KARYAWAN<br>UNTUK PEMENUHAN INTERNAL</div>', unsafe_allow_html=True)
            
            st.markdown("**I. POSISI KARYAWAN YANG DIAJUKAN**")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Posisi", key="fpk_posisi"); st.text_input("Divisi/Departemen", key="fpk_divisi"); st.number_input("Jumlah", min_value=1, key="fpk_jumlah")
            with c2:
                st.radio("Penempatan", ["Head Office", "Cabang", "Site"], horizontal=True, key="fpk_penempatan")
                st.text_input("Lokasi", key="fpk_lokasi"); st.date_input("Tanggal Pengajuan", key="fpk_tgl")
            
            st.markdown("**II. TUJUAN PERMINTAAN**")
            st.checkbox("Penambahan", key="fpk_penambahan")
            st.text_input("Alasan", key="fpk_alasan")
            st.checkbox("Magang", key="fpk_magang")
            st.text_input("Jangka Waktu (Bulan)", key="fpk_jangka_waktu")
            
            st.markdown("**III. PERSYARATAN JABATAN**")
            st.text_input("1. Pendidikan", key="fpk_pendidikan")
            st.text_input("2. Rentang Usia", key="fpk_rentang_usia")
            st.radio("3. Jenis Kelamin", ["Laki-Laki", "Perempuan", "Tidak Spesifik"], horizontal=True, key="fpk_jk")
            st.text_input("4. Pengalaman", key="fpk_pengalaman")
            st.text_input("5. Keahlian Umum", key="fpk_keahlian")
            st.text_input("6. Kemampuan Bahasa", key="fpk_bahasa")
            st.text_input("7. Sertifikasi yang diperlukan", key="fpk_sertifikasi")
            st.text_input("8. Persyaratan Tambahan", key="fpk_persyaratan_tambahan")
            
            st.markdown("**IV. PROSES PENCARIAN KARYAWAN**")
            st.radio("Sumber Kandidat", ["Internal Hiring", "External Hiring", "Labor Supply"], horizontal=True, key="fpk_sumber")
            st.radio("Proses Rekrutmen", ["Publish", "Hide"], horizontal=True, key="fpk_proses")
            st.radio("Technical Tes", ["Ya", "Tidak"], horizontal=True, key="fpk_tes")
            
            st.markdown("**V. URAIAN JABATAN**")
            st.text_area("Deskripsi Pekerjaan & Tanggung Jawab", height=150, key="fpk_deskripsi")
            
            st.markdown("---")
            c_ttd1, c_ttd2, c_ttd3, c_ttd4 = st.columns(4)
            with c_ttd1: st.markdown("<center>Diajukan Oleh<br>(Setingkat Supervisor)<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Ditinjau Oleh<br>(Setingkat Manager)<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Disetujui Oleh<br>(Direksi)<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd4: st.markdown("<center>Diketahui Oleh<br>(HR Manager)<br><br><br>(............................)</center>", unsafe_allow_html=True)

        # Tombol Simpan FPK
        if st.button("💾 Simpan Formulir FPK", type="primary", use_container_width=True, key="btn_save_fpk_full"):
            try:
                tujuan_list = []
                if st.session_state.get("fpk_penambahan"): tujuan_list.append("Penambahan")
                if st.session_state.get("fpk_magang"): tujuan_list.append("Magang")
                c.execute("""INSERT INTO formulir_fpk 
                    (posisi, divisi, jumlah, penempatan, lokasi, tanggal_pengajuan, 
                     tujuan, alasan, magang, jangka_waktu, 
                     pendidikan, rentang_usia, jenis_kelamin, pengalaman, 
                     keahlian, bahasa, sertifikasi, persyaratan_tambahan,
                     sumber_kandidat, proses_rekrutmen, technical_tes, 
                     deskripsi_pekerjaan, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (st.session_state.get("fpk_posisi",""), st.session_state.get("fpk_divisi",""), 
                     st.session_state.get("fpk_jumlah", 1), st.session_state.get("fpk_penempatan",""),
                     st.session_state.get("fpk_lokasi",""), str(st.session_state.get("fpk_tgl","")),
                     ", ".join(tujuan_list), st.session_state.get("fpk_alasan",""),
                     "Magang" if st.session_state.get("fpk_magang") else "",
                     st.session_state.get("fpk_jangka_waktu",""),
                     st.session_state.get("fpk_pendidikan",""), st.session_state.get("fpk_rentang_usia",""),
                     st.session_state.get("fpk_jk",""), st.session_state.get("fpk_pengalaman",""),
                     st.session_state.get("fpk_keahlian",""), st.session_state.get("fpk_bahasa",""),
                     st.session_state.get("fpk_sertifikasi",""), st.session_state.get("fpk_persyaratan_tambahan",""),
                     st.session_state.get("fpk_sumber",""), st.session_state.get("fpk_proses",""),
                     st.session_state.get("fpk_tes",""), st.session_state.get("fpk_deskripsi",""),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Formulir FPK untuk posisi **{st.session_state.get('fpk_posisi','(tanpa posisi)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_FPK", st.session_state.get("fpk_posisi",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        # Riwayat FPK
        st.markdown("---")
        st.markdown("**📋 Riwayat Formulir FPK:**")
        df_fpk_hr = pd.read_sql_query(
            """SELECT id, posisi, divisi, jumlah, penempatan, lokasi, tanggal_pengajuan, 
                      sumber_kandidat, created_by, created_at 
               FROM formulir_fpk ORDER BY id DESC LIMIT 20""",
            conn
        )
        if not df_fpk_hr.empty:
            st.dataframe(df_fpk_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada formulir FPK yang tersimpan.")

    # ================= TAB 5: EXIT & CLEARANCE (5 CONTAINER TERPISAH) =================
    with tab5:
        st.subheader("Formulir Karyawan Keluar dari Perusahaan")
        
        # Form 1: Serah Terima Inventaris
        with st.container(border=True):
            st.markdown('<div class="form-title">SERAH TERIMA INVENTARIS PERUSAHAAN</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: st.text_input("NAMA", key="e_nama"); st.text_input("POSISI/JABATAN", key="e_pos")
            with c2: st.text_input("NIK", key="e_nik"); st.text_input("DEPARTEMEN", key="e_dept")
            st.write("Dengan ini menyerahkan inventaris kantor yang telah saya terima selama saya bekerja di PT.UNITED EQUIPMENT INDONESIA, berupa:")
            df_inventaris = st.data_editor(pd.DataFrame(columns=["No", "Nama Barang", "Jumlah", "Keterangan"]), num_rows="dynamic", use_container_width=True, key="e_de_inventaris")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Yang Menyerahkan<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Yang Menerima<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Saksi<br><br><br>(............................)</center>", unsafe_allow_html=True)
        
        if st.button("💾 Simpan Serah Terima Inventaris", type="primary", use_container_width=True, key="btn_save_inventaris"):
            try:
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, nik, posisi, departemen, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    ("SERAH_TERIMA_INVENTARIS", st.session_state.get("e_nama",""), st.session_state.get("e_nik",""),
                     st.session_state.get("e_pos",""), st.session_state.get("e_dept",""),
                     json.dumps({"items": df_inventaris.to_dict("records")}, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Serah Terima Inventaris **{st.session_state.get('e_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_INVENTARIS", st.session_state.get("e_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        
        # Form 2: Serah Terima Pekerjaan
        with st.container(border=True):
            st.markdown('<div class="form-title">SERAH TERIMA PEKERJAAN</div>', unsafe_allow_html=True)
            st.text_input("NAMA (Yang Menyerahkan)", key="ep_nama1"); st.text_input("JABATAN (Yang Menyerahkan)", key="ep_jab1")
            st.text_input("NAMA (Yang Menerima)", key="ep_nama2"); st.text_input("JABATAN (Yang Menerima)", key="ep_jab2")
            st.write("Yang diserahkan:")
            df_pekerjaan_exit = st.data_editor(pd.DataFrame(columns=["No", "Tugas & Tanggung Jawab", "Keterangan"]), num_rows="dynamic", use_container_width=True, key="ep_de_pekerjaan")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Yang Menyerahkan<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Yang Menerima<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Saksi<br><br><br>(............................)</center>", unsafe_allow_html=True)
        
        if st.button("💾 Simpan Serah Terima Pekerjaan", type="primary", use_container_width=True, key="btn_save_pekerjaan_exit"):
            try:
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, posisi, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    ("SERAH_TERIMA_PEKERJAAN", st.session_state.get("ep_nama1",""), st.session_state.get("ep_jab1",""),
                     json.dumps({
                         "penerima_nama": st.session_state.get("ep_nama2",""),
                         "penerima_jabatan": st.session_state.get("ep_jab2",""),
                         "items": df_pekerjaan_exit.to_dict("records")
                     }, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Serah Terima Pekerjaan **{st.session_state.get('ep_nama1','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_PEKERJAAN_EXIT", st.session_state.get("ep_nama1",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        
        # Form 3: Kerahasiaan
        with st.container(border=True):
            st.markdown('<div class="form-title">KERAHASIAAN</div>', unsafe_allow_html=True)
            st.text_input("NAMA", key="k_nama"); st.text_input("NO. KTP", key="k_ktp"); st.text_area("ALAMAT", key="k_alamat")
            st.write("Dengan ini menyatakan bahwa selama saya bekerja dan setelah mengundurkan diri dan tidak bekerja kembali di PT. UNITED EQUIPMENT INDONESIA pertanggal ... maka dengan ini saya menyatakan secara sadar dan mengerti sepenuhnya bahwa:")
            st.write("1. Saya akan menjaga semua kerahasiaan data perusahaan dari kebocoran terhadap pihak luar...")
            st.write("2. Saya tidak akan membawa/ meng-copy/ memperbanyak data perusahaan...")
            st.write("3. Saya tidak akan memanfaatkan data-data perusahaan...")
            st.write("4. Saya bersedia memberikan informasi yang dibutuhkan perusahaan...")
            st.write("5. Saya akan menjaga hubungan profesional...")
            st.text_input("Jakarta, (Tanggal)", key="k_tgl")
            st.text_input("Yang Menyatakan (Nama)", key="k_ttd")
        
        if st.button("💾 Simpan Pernyataan Kerahasiaan", type="primary", use_container_width=True, key="btn_save_kerahasiaan"):
            try:
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?)""",
                    ("KERAHASIAAN", st.session_state.get("k_nama",""),
                     json.dumps({
                         "no_ktp": st.session_state.get("k_ktp",""),
                         "alamat": st.session_state.get("k_alamat",""),
                         "tanggal": st.session_state.get("k_tgl",""),
                         "ttd_nama": st.session_state.get("k_ttd","")
                     }, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Pernyataan Kerahasiaan **{st.session_state.get('k_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_KERAHASIAAN", st.session_state.get("k_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        
        # Form 4: Surat Referensi Kerja
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN SURAT REFERENSI KERJA</div>', unsafe_allow_html=True)
            st.write("Kepada HRD PT. UNITED EQUIPMENT INDONESIA")
            st.text_input("NAMA (Sesuai KTP)", key="r_nama"); st.text_input("NIK", key="r_nik"); st.text_input("PERUSAHAAN", key="r_perusahaan")
            st.text_input("JABATAN", key="r_jabatan"); st.text_input("MULAI BEKERJA (Tgl/Bln/Thn)", key="r_mulai"); st.text_input("HARI TERAKHIR BEKERJA (Tgl/Bln/Thn)", key="r_akhir")
            st.write("Ingin mengajukan permohonan untuk Surat Referensi Kerja. Terlampir surat pengunduran diri saya sebagai syarat permohonan diatas.")
            st.text_input("Tanggal Permohonan", key="r_tgl_permohonan")
        
        if st.button("💾 Simpan Permohonan Referensi", type="primary", use_container_width=True, key="btn_save_referensi"):
            try:
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, nik, posisi, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    ("REFERENSI_KERJA", st.session_state.get("r_nama",""), st.session_state.get("r_nik",""),
                     st.session_state.get("r_jabatan",""),
                     json.dumps({
                         "perusahaan": st.session_state.get("r_perusahaan",""),
                         "mulai_kerja": st.session_state.get("r_mulai",""),
                         "akhir_kerja": st.session_state.get("r_akhir",""),
                         "tgl_permohonan": st.session_state.get("r_tgl_permohonan","")
                     }, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Permohonan Referensi **{st.session_state.get('r_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_REFERENSI", st.session_state.get("r_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        
        # Form 5: Exit Interview
        with st.container(border=True):
            st.markdown('<div class="form-title">EXIT INTERVIEW FORM</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: st.text_input("Nama", key="ei_nama"); st.text_input("Jabatan", key="ei_jabatan"); st.text_input("Tanggal Masuk", key="ei_tgl_masuk")
            with c2: st.text_input("Nik", key="ei_nik"); st.text_input("Dept/ Divisi", key="ei_dept"); st.text_input("Tanggal Keluar", key="ei_tgl_keluar")
            st.text_area("Apa alasan utama anda keluar dari perusahaan?", key="ei_q1")
            st.text_area("Apa yang paling menyenangkan dari pekerjaan anda?", key="ei_q2")
            st.text_area("Apa yang paling tidak menyenangkan dari pekerjaan anda?", key="ei_q3")
            st.text_area("Apakah ada kebijakan atau prosedur perusahaan yang mempersulit pekerjaan anda? (Sebutkan)", key="ei_q4")
            st.text_area("Fasilitas apa yang diberikan oleh perusahaan selama ini?", key="ei_q5")
            st.text_area("Apakah anda bersedia kembali ke perusahaan ini di masa depan?", key="ei_q6")
            st.text_area("Apakah Anda mau merekomendasikan perusahaan ini ke teman/ orang lain sebagai tempat yang baik untuk bekerja?", key="ei_q7")
            st.text_area("Apakah ada tindakan yang telah dilakukan perusahaan untuk mencegah anda keluar? (Jelaskan)", key="ei_q8")
            st.text_area("Masukan bagi Perusahaan: (atasan, bawahan, rekan kerja, peraturan / kebijakan perusahaan, dll.)", key="ei_q9")
            st.text_input("Mengetahui (HRD)", key="ei_hrd")
        
        if st.button("💾 Simpan Exit Interview", type="primary", use_container_width=True, key="btn_save_exit_interview"):
            try:
                c.execute("""INSERT INTO formulir_exit 
                    (jenis_form, nama, nik, posisi, departemen, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    ("EXIT_INTERVIEW", st.session_state.get("ei_nama",""), st.session_state.get("ei_nik",""),
                     st.session_state.get("ei_jabatan",""), st.session_state.get("ei_dept",""),
                     json.dumps({
                         "tanggal_masuk": st.session_state.get("ei_tgl_masuk",""),
                         "tanggal_keluar": st.session_state.get("ei_tgl_keluar",""),
                         "q1_alasan_utama": st.session_state.get("ei_q1",""),
                         "q2_menyenangkan": st.session_state.get("ei_q2",""),
                         "q3_tidak_menyenangkan": st.session_state.get("ei_q3",""),
                         "q4_kebijakan_mempersulit": st.session_state.get("ei_q4",""),
                         "q5_fasilitas": st.session_state.get("ei_q5",""),
                         "q6_bersedia_kembali": st.session_state.get("ei_q6",""),
                         "q7_rekomendasi": st.session_state.get("ei_q7",""),
                         "q8_tindakan_pencegahan": st.session_state.get("ei_q8",""),
                         "q9_masukan": st.session_state.get("ei_q9",""),
                         "mengetahui_hrd": st.session_state.get("ei_hrd","")
                     }, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Exit Interview **{st.session_state.get('ei_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_EXIT_INTERVIEW", st.session_state.get("ei_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        # Riwayat Exit & Clearance
        st.markdown("---")
        st.markdown("**📋 Riwayat Form Exit & Clearance:**")
        df_exit_hr = pd.read_sql_query(
            """SELECT id, jenis_form, nama, nik, posisi, departemen, created_by, created_at 
               FROM formulir_exit 
               WHERE jenis_form != 'DATA_PELAMAR' 
               ORDER BY id DESC LIMIT 30""",
            conn
        )
        if not df_exit_hr.empty:
            st.dataframe(df_exit_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada form Exit & Clearance yang tersimpan.")    # ================= TAB 6: IZIN & KEHADIRAN — FULL ORIGINAL =================
    with tab6:
        st.subheader("1. Permohonan Izin Pulang Cepat")
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN IZIN PULANG CEPAT</div>', unsafe_allow_html=True)
            st.text_input("HRD No: /RCP-HR/ /20", key="pc_hrd")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Nama Karyawan", key="pc_nama"); st.text_input("Hari/Tanggal", key="pc_tgl"); st.text_area("Alasan", key="pc_alasan")
            with c2:
                st.text_input("Jabatan/Divisi", key="pc_jabatan"); st.text_input("Pukul (s/d)", key="pc_pukul")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Pemohon<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Penanggung Jawab/KA Divisi<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Disetujui<br><br><br>(............................)</center>", unsafe_allow_html=True)

        # Tombol simpan Izin Pulang Cepat
        if st.button("💾 Simpan Izin Pulang Cepat", type="primary", use_container_width=True, key="btn_save_pulang_cepat"):
            try:
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, nama, jabatan, tanggal, alasan, pukul, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    ("IZIN_PULANG_CEPAT", st.session_state.get("pc_nama",""), st.session_state.get("pc_jabatan",""),
                     st.session_state.get("pc_tgl",""), st.session_state.get("pc_alasan",""), st.session_state.get("pc_pukul",""),
                     json.dumps({"hrd_no": st.session_state.get("pc_hrd","")}, ensure_ascii=False),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Izin Pulang Cepat **{st.session_state.get('pc_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_PULANG_CEPAT", st.session_state.get("pc_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        st.subheader("2. Permohonan Izin Keluar Kantor")
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN IZIN KELUAR KANTOR</div>', unsafe_allow_html=True)
            st.text_input("HRD NO: /RCP-HR/ /20", key="ik_hrd")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Nama Karyawan", key="ik_nama"); st.text_area("Alasan", key="ik_alasan")
            with c2:
                st.text_input("Jabatan/Divisi", key="ik_jabatan"); st.text_input("Pukul (s/d)", key="ik_pukul")
            c_ttd1, c_ttd2, c_ttd3 = st.columns(3)
            with c_ttd1: st.markdown("<center>Pemohon<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd2: st.markdown("<center>Disetujui<br><br><br>(............................)</center>", unsafe_allow_html=True)
            with c_ttd3: st.markdown("<center>Satpam<br><br><br>(............................)</center>", unsafe_allow_html=True)

        # Tombol simpan Izin Keluar Kantor
        if st.button("💾 Simpan Izin Keluar Kantor", type="primary", use_container_width=True, key="btn_save_keluar_kantor"):
            try:
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, nama, jabatan, alasan, pukul, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    ("IZIN_KELUAR_KANTOR", st.session_state.get("ik_nama",""), st.session_state.get("ik_jabatan",""),
                     st.session_state.get("ik_alasan",""), st.session_state.get("ik_pukul",""),
                     json.dumps({"hrd_no": st.session_state.get("ik_hrd","")}, ensure_ascii=False),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Izin Keluar Kantor **{st.session_state.get('ik_nama','(tanpa nama)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_KELUAR_KANTOR", st.session_state.get("ik_nama",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        st.subheader("3. Formulir Daftar Hadir")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR DAFTAR HADIR</div>', unsafe_allow_html=True)
            st.text_input("AGENDA", key="dh_agenda"); st.text_input("HARI / TANGGAL", key="dh_tgl"); st.text_input("PUKUL", key="dh_pukul")
            df_daftar_hadir = st.data_editor(pd.DataFrame(columns=["NO", "NAMA", "JABATAN", "BAGIAN", "PARAF"]), num_rows="dynamic", use_container_width=True, key="dh_de_daftar_hadir")

        # Tombol simpan Daftar Hadir
        if st.button("💾 Simpan Formulir Daftar Hadir", type="primary", use_container_width=True, key="btn_save_daftar_hadir"):
            try:
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, tanggal, keterangan, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    ("DAFTAR_HADIR", st.session_state.get("dh_tgl",""), st.session_state.get("dh_agenda",""),
                     json.dumps({"pukul": st.session_state.get("dh_pukul",""), "peserta": df_daftar_hadir.to_dict("records")}, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Formulir Daftar Hadir **{st.session_state.get('dh_agenda','(tanpa agenda)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_DAFTAR_HADIR", st.session_state.get("dh_agenda",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        st.divider()
        st.subheader("4. Notulen Meeting")
        with st.container(border=True):
            st.markdown('<div class="form-title">NOTULEN MEETING</div>', unsafe_allow_html=True)
            st.text_input("Hal: .../.../...", key="nm_hal")
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("Hari / Tanggal", key="nm_tgl"); st.text_input("Jam", key="nm_jam"); st.text_input("Tempat", key="nm_tempat"); st.text_input("Topik", key="nm_topik")
            with c2:
                st.text_input("Nama Bagian Pembuat Notulen Rapat", key="nm_pembuat")
                st.text_input("Tanda Tangan", key="nm_ttd")
                st.text_input("Nama", key="nm_nama")
            
            st.markdown("**Peserta:**")
            df_peserta_rapat = st.data_editor(pd.DataFrame(columns=["No.", "Nama Peserta", "Company"]), num_rows="dynamic", use_container_width=True, key="nm_de_peserta")
            st.markdown("**Hasil Rapat:**")
            df_hasil_rapat = st.data_editor(pd.DataFrame(columns=["No.", "ISSUE", "Activity", "Due Date", "PIC", "Status"]), num_rows="dynamic", use_container_width=True, key="nm_de_hasil")
            
            c_pihak1, c_pihak2 = st.columns(2)
            with c_pihak1: st.text_area("Pihak 1", height=100, key="nm_pihak1")
            with c_pihak2: st.text_area("Pihak 2", height=100, key="nm_pihak2")

        # Tombol simpan Notulen
        if st.button("💾 Simpan Notulen Meeting", type="primary", use_container_width=True, key="btn_save_notulen"):
            try:
                c.execute("""INSERT INTO formulir_izin 
                    (jenis_form, tanggal, keterangan, data_json, created_by, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    ("NOTULEN_MEETING", st.session_state.get("nm_tgl",""), st.session_state.get("nm_topik",""),
                     json.dumps({
                         "hal": st.session_state.get("nm_hal",""),
                         "jam": st.session_state.get("nm_jam",""),
                         "tempat": st.session_state.get("nm_tempat",""),
                         "pembuat_notulen": st.session_state.get("nm_pembuat",""),
                         "ttd": st.session_state.get("nm_ttd",""),
                         "nama": st.session_state.get("nm_nama",""),
                         "peserta": df_peserta_rapat.to_dict("records"),
                         "hasil_rapat": df_hasil_rapat.to_dict("records"),
                         "pihak_1": st.session_state.get("nm_pihak1",""),
                         "pihak_2": st.session_state.get("nm_pihak2","")
                     }, ensure_ascii=False, default=str),
                     st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success(f"✅ Notulen Meeting **{st.session_state.get('nm_topik','(tanpa topik)')}** tersimpan.")
                log_aksi(st.session_state.username, "SIMPAN_NOTULEN", st.session_state.get("nm_topik",""))
                time.sleep(1); st.rerun()
            except Exception as e:
                st.error(f"❌ Gagal: {e}")

        # Riwayat Izin & Kehadiran
        st.markdown("---")
        st.markdown("**📋 Riwayat Form Izin & Kehadiran (dari Tab 6):**")
        df_izin_hr = pd.read_sql_query(
            """SELECT id, jenis_form, nama, jabatan, tanggal, alasan, created_by, created_at 
               FROM formulir_izin 
               WHERE jenis_form IN ('IZIN_PULANG_CEPAT', 'IZIN_KELUAR_KANTOR', 'DAFTAR_HADIR', 'NOTULEN_MEETING')
               ORDER BY id DESC LIMIT 20""",
            conn
        )
        if not df_izin_hr.empty:
            st.dataframe(df_izin_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat form izin & kehadiran.")

    # ================= FORM PERUBAHAN DATA (DI LUAR TABS, SESUAI ASLINYA) =================
    with st.expander("Form Perubahan Data Karyawan"):
        with st.container(border=True):
            st.markdown('<div class="form-title">FORM PERUBAHAN DATA KARYAWAN</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: st.text_input("No. Urut", key="pd_no")
            with c2: st.date_input("Tanggal Pengisian", key="pd_tgl")
            
            df_perubahan = st.data_editor(
                pd.DataFrame({
                    "Keterangan": ["No. ID", "Nama", "No. REK BCA", "Alamat Tinggal Sebenarnya", "Kota", "Kode POS", "Alamat di KTP", "No Telp", "Pendidikan Terakhir", "Agama", "Jabatan", "Status Menikah", "Tanggungan"],
                    "Data Sebelumnya": [""] * 13,
                    "Data Sekarang": [""] * 13
                }),
                hide_index=True, use_container_width=True, disabled=["Keterangan"],
                key="pd_de_perubahan"
            )
            st.text_input("Yang mengajukan (Nama Terang)", key="pd_pengaju")
            
            # Tombol simpan Perubahan Data
            if st.button("💾 Simpan / Cetak Formulir Ini", type="primary", key="pd_simpan"):
                try:
                    c.execute("""INSERT INTO formulir_perubahan 
                        (no_urut, tanggal, data_json, pengaju, created_by, created_at)
                        VALUES (?,?,?,?,?,?)""",
                        (st.session_state.get("pd_no",""), str(st.session_state.get("pd_tgl","")),
                         json.dumps(df_perubahan.to_dict("records"), ensure_ascii=False, default=str),
                         st.session_state.get("pd_pengaju",""),
                         st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"✅ Formulir Perubahan Data (No. Urut **{st.session_state.get('pd_no','-')}**) berhasil disimpan ke database.")
                    log_aksi(st.session_state.username, "SIMPAN_PERUBAHAN_DATA", st.session_state.get("pd_no",""))
                    time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"❌ Gagal: {e}")

        # Riwayat Perubahan Data
        st.markdown("---")
        st.markdown("**📋 Riwayat Perubahan Data:**")
        df_per_hr = pd.read_sql_query(
            """SELECT id, no_urut, tanggal, pengaju, created_by, created_at 
               FROM formulir_perubahan ORDER BY id DESC LIMIT 20""",
            conn
        )
        if not df_per_hr.empty:
            st.dataframe(df_per_hr, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada formulir perubahan data yang tersimpan.")# --- 23. LAPORAN & ANALITIK ---
elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1><p>Rekapitulasi Data HRIS</p></div>', unsafe_allow_html=True)
    
    tab_lap1, tab_lap2, tab_lap3 = st.tabs(["👥 Karyawan", "💰 Payroll", "🏖️ Cuti"])
    
    with tab_lap1:
        df_k = pd.read_sql_query("SELECT divisi, status_employee, COUNT(*) as jumlah FROM karyawan WHERE aktif=1 GROUP BY divisi, status_employee", conn)
        if not df_k.empty:
            chart = alt.Chart(df_k).mark_bar().encode(
                x=alt.X("divisi:N", title="Divisi"),
                y=alt.Y("jumlah:Q", title="Jumlah"),
                color=alt.Color("status_employee:N", title="Status")
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(df_k, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data.")
        
    with tab_lap2:
        df_p = pd.read_sql_query("SELECT periode, SUM(gaji_bersih) as total_bersih, COUNT(*) as jumlah FROM payroll GROUP BY periode ORDER BY periode DESC", conn)
        if not df_p.empty:
            st.dataframe(df_p, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data payroll.")
        
    with tab_lap3:
        df_c = pd.read_sql_query("SELECT jenis_cuti, status, COUNT(*) as jumlah FROM cuti GROUP BY jenis_cuti, status", conn)
        if not df_c.empty:
            st.dataframe(df_c, use_container_width=True, hide_index=True)
        else: st.info("Belum ada data cuti.")

# --- 24. IMPORT, EXPORT & BACKUP ---
elif pilihan == "💾 Import, Export & Backup":
    st.markdown('<div class="main-header"><h1>💾 Import, Export & Backup</h1><p>Ekspor Laporan & Cadangkan Database</p></div>', unsafe_allow_html=True)
    
    tab_e1, tab_e2 = st.tabs(["📤 Export CSV", "📦 Backup ZIP"])
    
    with tab_e1:
        tables = ["karyawan", "kandidat", "lowongan", "absensi", "cuti", "payroll", "resign", "aset", "utility", "ruko", "tenant", "disiplin", "mutasi", "jobdesk", "ci", "skd", "im", "log_aktivitas"]
        pilih_tabel = st.selectbox("Pilih Tabel", tables, key="exp_tabel")
        if st.button("📥 Download CSV", key="btn_exp_csv"):
            try:
                df = pd.read_sql_query(f"SELECT * FROM {pilih_tabel}", conn)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(f"💾 {pilih_tabel}.csv", data=csv, file_name=f"{pilih_tabel}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", key="dl_csv")
            except Exception as e: st.error(f"Gagal: {e}")
            
    with tab_e2:
        if st.button("📦 Buat Backup ZIP (Database + Uploads)", key="btn_backup"):
            try:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    if os.path.exists("hris_ga.db"): zf.write("hris_ga.db")
                    for root, _, files in os.walk("uploads"):
                        for f in files:
                            fp = os.path.join(root, f)
                            zf.write(fp, fp)
                buf.seek(0)
                st.download_button("💾 Download Backup", data=buf, file_name=f"backup_hris_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip", mime="application/zip", key="dl_backup")
            except Exception as e: st.error(f"Gagal: {e}")

# --- 25. MANAJEMEN USER (ADMIN) ---
elif pilihan == "👤 Manajemen User":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1><p>Kelola Akses Aplikasi</p></div>', unsafe_allow_html=True)
    
    with st.form("user_form"):
        st.subheader("Tambah User Baru")
        c1, c2, c3 = st.columns(3)
        with c1: new_u = st.text_input("Username", key="nu_u")
        with c2: new_p = st.text_input("Password", type="password", key="nu_p")
        with c3:
            new_nama = st.text_input("Nama Lengkap", key="nu_nama")
            new_role = st.selectbox("Role", ["admin", "hrd", "staff"], key="nu_role")
        if st.form_submit_button("💾 Tambah User", type="primary"):
            if new_u and new_p:
                try:
                    c.execute("INSERT INTO users (username, password, nama_lengkap, role, aktif) VALUES (?,?,?,?,1)",
                              (new_u, hash_password(new_p), new_nama, new_role))
                    conn.commit(); st.success(f"✅ User {new_u} ditambahkan."); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Gagal: {e}")
    
    df_u = pd.read_sql_query("SELECT id, username, nama_lengkap, role, aktif FROM users ORDER BY id", conn)
    df_u['Hapus?'] = False
    edited = st.data_editor(df_u, column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "username": st.column_config.TextColumn("Username", disabled=True),
        "Hapus?": st.column_config.CheckboxColumn("Hapus?", default=False)
    }, use_container_width=True, hide_index=True, key="user_editor")
    
    if st.button("💾 Update / Hapus User", type="primary", key="btn_save_user"):
        for _, row in edited.iterrows():
            if row['Hapus?'] and row['username'] != 'admin':
                c.execute("DELETE FROM users WHERE id=?", (int(row['id']),))
            else:
                c.execute("UPDATE users SET nama_lengkap=?, role=?, aktif=? WHERE id=?",
                          (row['nama_lengkap'], row['role'], int(row['aktif']), int(row['id'])))
        conn.commit(); st.success("✅ Perubahan tersimpan."); time.sleep(1); st.rerun()

# --- 26. SINKRONISASI UNIQUIP (ADMIN) ---
elif pilihan == "🔄 Sinkronisasi Uniquip":
    st.markdown('<div class="main-header"><h1>🔄 Sinkronisasi Uniquip</h1><p>Sinkronisasi Data dengan Sistem Eksternal</p></div>', unsafe_allow_html=True)
    st.info("Fitur sinkronisasi data karyawan dari sistem Uniquip ke HRIS.")
    st.warning("⚠️ Fitur ini memerlukan kredensial Uniquip. Simpan kredensial di environment variable `UNIQUIP_USER` dan `UNIQUIP_PASS`.")
    if st.button("🔄 Mulai Sinkronisasi", type="primary"):
        st.info("Sinkronisasi belum diimplementasikan. Tambahkan logika scraping/API Uniquip di sini.")

# --- 27. LOG AKTIVITAS (ADMIN) ---
elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1><p>Riwayat Penggunaan Sistem</p></div>', unsafe_allow_html=True)
    df_log = pd.read_sql_query("SELECT id, username, aksi, detail, waktu FROM log_aktivitas ORDER BY id DESC LIMIT 200", conn)
    st.dataframe(df_log, use_container_width=True, hide_index=True)
    if st.button("🗑️ Hapus Log > 30 Hari", key="btn_clear_log"):
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("DELETE FROM log_aktivitas WHERE waktu < ?", (cutoff,))
        conn.commit(); st.success("✅ Log lama dihapus."); time.sleep(1); st.rerun()

# --- FALLBACK ---
else:
    st.warning("⚠️ Menu tidak dikenali.")

# ==================== FOOTER ====================
st.markdown(f"""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>
    © {datetime.now().year} — All Rights Reserved
</div>
""", unsafe_allow_html=True)
