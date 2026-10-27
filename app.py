import time
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import json
import zipfile
from datetime import datetime, date
from urllib.parse import quote
from fpdf import FPDF

# ==================== KONFIGURASI & CSS ====================
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
    .card-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-red { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-teal { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button { background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%); color: white !important; border: none; border-radius: 10px; padding: 10px 20px; font-weight: 600; width: 100%; }
    .form-title { text-align: center; font-weight: bold; font-size: 1.4em; margin-bottom: 20px; text-transform: uppercase; border-bottom: 2px solid black; padding-bottom: 10px; }
    .flyer-card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #2a5298; color: #333; }
    .flyer-title { font-size: 1.1em; font-weight: bold; color: #1e3c72; margin-bottom: 5px; }
    .flyer-sub { font-size: 0.85em; color: #666; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE & HELPER ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

def clean(val, default=""):
    if val is None: return default
    try:
        if pd.isna(val): return default
    except: pass
    s = str(val).strip()
    return default if s.lower() in ("nan", "none", "null", "nat", "") else s

def clean_date(val):
    if val is None: return None
    try:
        if pd.isna(val): return None
    except: pass
    try: return pd.to_datetime(val, errors="coerce").strftime("%Y-%m-%d")
    except: return None

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

def generate_pdf(title, data_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt=title.upper(), ln=True, align='C')
    pdf.line(10, 20, 200, 20)
    pdf.ln(10)
    for key, val in data_dict.items():
        pdf.set_font("Arial", size=11, style='B')
        pdf.cell(50, 8, txt=f"{key}: ", ln=False)
        pdf.set_font("Arial", size=11)
        if isinstance(val, str) and len(val) > 50:
            pdf.multi_cell(0, 8, txt=str(val))
        else:
            pdf.cell(0, 8, txt=str(val), ln=True)
        pdf.ln(2)
    return bytes(pdf.output())

def get_karyawan_dropdown(key, label="Pilih Karyawan", allow_none=False):
    df_kar = pd.read_sql_query("SELECT id, employee_id, full_name, job_position, divisi FROM karyawan WHERE aktif=1 ORDER BY full_name", conn)
    if df_kar.empty:
        st.warning("⚠️ Belum ada data karyawan. Silakan Import Excel.")
        return None, None, None, None, None
    options = [f"{row['employee_id']} | {row['full_name']}" for _, row in df_kar.iterrows()]
    if allow_none: options = ["-"] + options
    selected = st.selectbox(label, options, key=key)
    if selected == "-": return None, None, None, None, None
    idx = options.index(selected) - (1 if allow_none else 0)
    row = df_kar.iloc[idx]
    return row['id'], row['employee_id'], row['full_name'], row['job_position'], row['divisi']

def render_edit_delete_table(table_name, query, editable_cols, display_cols, key_prefix):
    df = pd.read_sql_query(query, conn)
    if df.empty:
        st.info(f"Belum ada data {table_name}.")
        return
    df['Hapus?'] = False
    edited_df = st.data_editor(df[display_cols + ['Hapus?']], num_rows="dynamic", use_container_width=True, hide_index=True, key=f"ed_{table_name}_{key_prefix}")
    if st.button("💾 Simpan / Hapus", key=f"sv_{table_name}_{key_prefix}", type="primary"):
        to_delete = edited_df[edited_df['Hapus?'] == True]['id'].dropna().tolist()
        for did in to_delete: c.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        for _, row in edited_df.iterrows():
            if row['Hapus?']: continue
            row_id = row.get('id')
            vals = [None if pd.isna(row.get(col)) else row.get(col) for col in editable_cols]
            if pd.isna(row_id):
                c.execute(f"INSERT INTO {table_name} ({', '.join(editable_cols)}) VALUES ({', '.join(['?'] * len(editable_cols))})", tuple(vals))
            else:
                c.execute(f"UPDATE {table_name} SET {', '.join([f'{col}=?' for col in editable_cols])} WHERE id=?", tuple(vals) + (int(row_id),))
        conn.commit(); st.success("✅ Tersimpan."); time.sleep(1); st.rerun()

# ==================== INISIALISASI TABEL DATABASE ====================
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, barcode TEXT, organization TEXT, job_position TEXT, job_level TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, sign_date TEXT, email TEXT, birth_date TEXT, age TEXT, birth_place TEXT, citizen_id_address TEXT, residential_address TEXT, npwp TEXT, ptkp_status TEXT, employee_tax_status TEXT, tax_config TEXT, bank_name TEXT, bank_account TEXT, bank_account_holder TEXT, bpjs_ketenagakerjaan TEXT, bpjs_kesehatan TEXT, nik_npwp_16 TEXT, mobile_phone TEXT, phone TEXT, branch_name TEXT, parent_branch_name TEXT, religion TEXT, gender TEXT, marital_status TEXT, blood_type TEXT, nationality_code TEXT, currency TEXT, length_of_service TEXT, payment_schedule TEXT, approval_line TEXT, manager TEXT, grade TEXT, class TEXT, profile_picture TEXT, cost_center TEXT, cost_center_category TEXT, sbu TEXT, npwp_16_new TEXT, passport TEXT, passport_expiration_date TEXT, jenis_dok_referensi_bukti_potong TEXT, nomor_dok_referensi_bukti_potong TEXT, tanggal_dok_referensi_bukti_potong TEXT, tin TEXT, divisi TEXT, keterangan TEXT, aktif INTEGER DEFAULT 1)''')
c.execute('''CREATE TABLE IF NOT EXISTS kandidat (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, telepon TEXT, posisi_dilamar TEXT, email TEXT, sumber TEXT, tanggal_lamar TEXT, status TEXT, catatan TEXT, tahapan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS lowongan (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, jumlah_dibutuhkan INTEGER, status TEXT DEFAULT 'Buka', deskripsi TEXT, tanggal_dibuka TEXT, tanggal_ditutup TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, alasan TEXT, jenis TEXT, clearance_status TEXT, kategori_penyebab TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS aset (id INTEGER PRIMARY KEY AUTOINCREMENT, kode TEXT UNIQUE, nama TEXT, kategori TEXT, lokasi TEXT, kondisi TEXT, nilai REAL, tanggal_perolehan TEXT, penanggung_jawab TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, id_pelanggan TEXT, label TEXT, nominal REAL, admin REAL, total_bayar REAL, metode TEXT, status TEXT, penanggung_jawab TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ruko (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, alamat TEXT, status TEXT, penyewa TEXT, nilai_sewa REAL, mulai_sewa TEXT, akhir_sewa TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS tenant (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lokasi TEXT, kamar TEXT, penghuni TEXT, biaya_bulanan REAL, status_ci TEXT, mulai TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT DEFAULT 'Menunggu', approved_by TEXT, approved_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, tunjangan_jabatan REAL, tunjangan_transport REAL, tunjangan_makan REAL, bpjs_kesehatan_karyawan REAL, bpjs_jht_karyawan REAL, pph21 REAL, total_penghasilan_bruto REAL, total_potongan REAL, gaji_bersih REAL, tanggal_proses TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT, periode TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, status TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS arsip_dokumen (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal_upload TEXT, nama_dokumen TEXT, kategori TEXT, keterangan TEXT, file_data BLOB, file_name TEXT, file_type TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS lampiran (id INTEGER PRIMARY KEY AUTOINCREMENT, ref_modul TEXT, ref_id TEXT, file_name TEXT, file_type TEXT, file_data BLOB, tanggal_upload TEXT, keterangan TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_wawancara (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, jabatan TEXT, usia TEXT, tanggal_wawancara TEXT, f1 TEXT, f2 TEXT, f3 TEXT, f4 TEXT, f5 TEXT, kelebihan TEXT, kekurangan TEXT, keputusan TEXT, pewawancara TEXT, nama_pewawancara TEXT, jabatan_pewawancara TEXT, data_fisik TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_coaching (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_karyawan TEXT, nik TEXT, tanggal_masuk TEXT, jabatan TEXT, status_karyawan TEXT, isu TEXT, observasi TEXT, langkah_perbaikan TEXT, komitmen TEXT, rekomendasi TEXT, hal_dilakukan TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_fpk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, divisi TEXT, jumlah INTEGER, penempatan TEXT, lokasi TEXT, tanggal_pengajuan TEXT, tujuan TEXT, alasan TEXT, magang TEXT, jangka_waktu TEXT, pendidikan TEXT, rentang_usia TEXT, jenis_kelamin TEXT, pengalaman TEXT, keahlian TEXT, bahasa TEXT, sertifikasi TEXT, persyaratan_tambahan TEXT, sumber_kandidat TEXT, proses_rekrutmen TEXT, technical_tes TEXT, deskripsi_pekerjaan TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_exit (id INTEGER PRIMARY KEY AUTOINCREMENT, jenis_form TEXT, nama TEXT, nik TEXT, posisi TEXT, departemen TEXT, data_json TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_izin (id INTEGER PRIMARY KEY AUTOINCREMENT, jenis_form TEXT, nama TEXT, jabatan TEXT, tanggal TEXT, alasan TEXT, pukul TEXT, keterangan TEXT, data_json TEXT, created_by TEXT, created_at TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS formulir_perubahan (id INTEGER PRIMARY KEY AUTOINCREMENT, no_urut TEXT, tanggal TEXT, data_json TEXT, pengaju TEXT, created_by TEXT, created_at TEXT)''')
conn.commit()
# ==================== SEEDING DATA DEFAULT ====================
c.execute("SELECT COUNT(*) FROM users")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hash_password("admin123"), "OKANAHARIANTO", "admin"))
    conn.commit()

c.execute("SELECT COUNT(*) FROM lowongan")
if c.fetchone()[0] == 0:
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka) VALUES (?,?,?,?,?,?)''', ("Mekanik 2 (M2)", "PRODUCT SUPPORT", 5, "Buka", "Pengganti: La Hajar dkk", str(date.today())))
    c.execute('''INSERT INTO lowongan (posisi, departemen, jumlah_dibutuhkan, status, deskripsi, tanggal_dibuka) VALUES (?,?,?,?,?,?)''', ("Mekanik 3 (M3)", "PRODUCT SUPPORT", 4, "Buka", "Pengganti: Indra S dkk", str(date.today())))
    conn.commit()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False; st.session_state.username = ""; st.session_state.nama = ""; st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS, GA AMOEY</h1></div>', unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                row = c.execute("SELECT username, password, nama_lengkap, role, aktif FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p) and row[4] == 1:
                    st.session_state.logged_in = True; st.session_state.username = row[0]; st.session_state.nama = row[2]; st.session_state.role = row[3]
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username / password salah")
        st.info("🔑 Default: **admin** / **admin123**")
    st.stop()

# ==================== SIDEBAR & FLYER ====================
with st.sidebar:
    st.markdown(f'<div style="text-align:center; padding: 15px 0;"><div style="font-size:3em;">👤</div><h3>{st.session_state.nama}</h3><p>Role: {st.session_state.role.upper()}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    menu = [
        "🏠 Dashboard HRIS", "🗂️ Filing Data Manpower", "👥 Data Karyawan", "📅 Absensi & Kehadiran", 
        "🏖️ Cuti & Izin", "💰 Payroll & Slip Gaji", "📋 Rekrutmen & CV", "📋 Jobdesk", "💡 CI Report", 
        "🏥 SKD", "📝 Internal Memo", "🔄 Mutasi & PKWT", "📉 Resign & Turnover", "⚠️ Disiplin & SP", 
        "📤 Exit Clearance", "📱 WhatsApp Reminder", "🚛 Aset & Properti", "🏪 Ruko & Tenant", 
        "💡 Utility Melak", "📁 Arsip Dokumen (E-Filing)", "📎 Lampiran / Attachment", 
        "📋 Formulir HRD (Official)", "📊 Laporan & Analitik", "📈 Manpower Report", "💾 Import, Export & Backup"
    ]
    if st.session_state.role == "admin": menu += ["👤 Manajemen User", "📝 Log Aktivitas"]
    
    pilihan = st.selectbox("📋 Menu Navigasi", menu)
    st.markdown("---")
    
    # Fitur Flyer Lowongan
    tampilkan_flyer = st.checkbox("📢 Tampilkan Flyer Lowongan", value=True)
    if tampilkan_flyer:
        df_loker = pd.read_sql_query("SELECT posisi, departemen, jumlah_dibutuhkan FROM lowongan WHERE status='Buka'", conn)
        st.markdown("### 📢 Lowongan Tersedia")
        if not df_loker.empty:
            for _, row in df_loker.iterrows():
                st.markdown(f"""
                <div class="flyer-card">
                    <div class="flyer-title">{row['posisi']}</div>
                    <div class="flyer-sub">Dept: {row['departemen']}</div>
                    <div class="flyer-sub">Butuh: {row['jumlah_dibutuhkan']} Orang</div>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("Belum ada lowongan buka.")
        
    st.markdown("---")
    if st.button("🚪 Logout"):
        log_aksi(st.session_state.username, "LOGOUT")
        for k in ["logged_in", "username", "nama", "role"]: st.session_state[k] = False if k == "logged_in" else ""
        st.rerun()

# ==================== KONTEN MENU: DASHBOARD ====================
if pilihan == "🏠 Dashboard HRIS":
    st.markdown('<div class="main-header"><h1>🏠 Dashboard HRIS</h1></div>', unsafe_allow_html=True)
    tk = c.execute("SELECT COUNT(*) FROM karyawan WHERE aktif=1").fetchone()[0]
    tc = c.execute("SELECT COUNT(*) FROM cuti WHERE status='Menunggu'").fetchone()[0]
    tr = c.execute("SELECT COUNT(*) FROM resign").fetchone()[0]
    ta = c.execute("SELECT COUNT(*) FROM aset").fetchone()[0]
    html = '<div class="metric-grid">'
    html += metric_card("👥 Karyawan Aktif", str(tk), "", "card-blue")
    html += metric_card("🏖️ Cuti Menunggu", str(tc), "", "card-orange")
    html += metric_card("📉 Resign", str(tr), "", "card-red")
    html += metric_card("🚛 Aset", str(ta), "", "card-teal")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
elif pilihan == "🗂️ Filing Data Manpower":
    st.markdown('<div class="main-header"><h1>🗂️ Filing Data Manpower</h1></div>', unsafe_allow_html=True)
    search = st.text_input("🔍 Cari (nama / employee ID)")
    q = "SELECT id, employee_id, full_name, divisi, job_position, status_employee FROM karyawan WHERE aktif=1"
    params = ()
    if search:
        q += " AND (full_name LIKE ? OR employee_id LIKE ?)"
        params = (f"%{search}%", f"%{search}%")
    st.dataframe(pd.read_sql_query(q, conn, params=params), use_container_width=True, hide_index=True)

elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    with st.expander("➕ Tambah Karyawan"):
        with st.form("add_kar"):
            col1, col2 = st.columns(2)
            emp_id = col1.text_input("Employee ID")
            full_name = col1.text_input("Nama Lengkap")
            div = col2.text_input("Divisi")
            pos = col2.text_input("Jabatan")
            if st.form_submit_button("Simpan"):
                c.execute("INSERT INTO karyawan (employee_id, full_name, divisi, job_position, aktif) VALUES (?,?,?,?,1)", (emp_id, full_name, div, pos))
                conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
    render_edit_delete_table("karyawan", "SELECT id, employee_id, full_name, divisi, job_position FROM karyawan", ["employee_id", "full_name", "divisi", "job_position"], ["id", "employee_id", "full_name", "divisi", "job_position"], "main")

elif pilihan == "📅 Absensi & Kehadiran":
    st.markdown('<div class="main-header"><h1>📅 Absensi</h1></div>', unsafe_allow_html=True)
    st.info("Modul Absensi harian siap digunakan.")

elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    df_cuti = pd.read_sql_query("SELECT c.id, k.full_name, c.jenis_cuti, c.tanggal_mulai, c.status FROM cuti c LEFT JOIN karyawan k ON c.karyawan_id=k.id", conn)
    st.dataframe(df_cuti, use_container_width=True, hide_index=True)

elif pilihan == "💰 Payroll & Slip Gaji":
    st.markdown('<div class="main-header"><h1>💰 Payroll</h1></div>', unsafe_allow_html=True)
    st.info("Modul Payroll sedang dalam tahap pengembangan.")

elif pilihan == "📋 Rekrutmen & CV":
    st.markdown('<div class="main-header"><h1>📋 Rekrutmen</h1></div>', unsafe_allow_html=True)
    df_k = pd.read_sql_query("SELECT id, nama, posisi_dilamar, status FROM kandidat", conn)
    st.dataframe(df_k, use_container_width=True)
elif pilihan == "📋 Jobdesk":
    st.markdown('<div class="main-header"><h1>📋 Jobdesk</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("jobdesk", "SELECT id, posisi, departemen, tugas_utama FROM jobdesk", ["posisi", "departemen", "tugas_utama"], ["id", "posisi", "departemen", "tugas_utama"], "jd")

elif pilihan == "💡 CI Report":
    st.markdown('<div class="main-header"><h1>💡 CI Report</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("ci", "SELECT id, tanggal, judul, departemen, status FROM ci", ["tanggal", "judul", "departemen", "status"], ["id", "tanggal", "judul", "departemen", "status"], "ci")

elif pilihan == "🏥 SKD":
    st.markdown('<div class="main-header"><h1>🏥 SKD</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("skd", "SELECT id, tanggal, no_surat, nama_karyawan FROM skd", ["tanggal", "no_surat", "nama_karyawan"], ["id", "tanggal", "no_surat", "nama_karyawan"], "skd")

elif pilihan == "📝 Internal Memo":
    st.markdown('<div class="main-header"><h1>📝 Internal Memo</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("im", "SELECT id, tanggal, no_memo, perihal FROM im", ["tanggal", "no_memo", "perihal"], ["id", "tanggal", "no_memo", "perihal"], "im")

elif pilihan == "🔄 Mutasi & PKWT":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi</h1></div>', unsafe_allow_html=True)
    df_mut = pd.read_sql_query("SELECT m.id, k.full_name, m.tanggal_mutasi, m.dari_divisi, m.ke_divisi FROM mutasi m LEFT JOIN karyawan k ON m.karyawan_id=k.id", conn)
    st.dataframe(df_mut, use_container_width=True)

elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign</h1></div>', unsafe_allow_html=True)
    df_r = pd.read_sql_query("SELECT r.id, k.full_name, r.tanggal_resign, r.alasan, r.jenis FROM resign r LEFT JOIN karyawan k ON r.karyawan_id=k.id", conn)
    st.dataframe(df_r, use_container_width=True)

elif pilihan == "⚠️ Disiplin & SP":
    st.markdown('<div class="main-header"><h1>⚠️ SP</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("disiplin", "SELECT id, jenis_sanksi, tanggal_mulai, rincian_pelanggaran, status FROM disiplin", ["jenis_sanksi", "tanggal_mulai", "rincian_pelanggaran", "status"], ["id", "jenis_sanksi", "tanggal_mulai", "rincian_pelanggaran", "status"], "sp")

elif pilihan == "📤 Exit Clearance":
    st.markdown('<div class="main-header"><h1>📤 Exit Clearance</h1></div>', unsafe_allow_html=True)
    st.info("Lihat menu Formulir HRD -> Tab Exit & Clearance.")

elif pilihan == "📱 WhatsApp Reminder":
    st.markdown('<div class="main-header"><h1>📱 WA Reminder</h1></div>', unsafe_allow_html=True)
    phone = st.text_input("No HP (62xxx)")
    msg = st.text_area("Pesan")
    if phone and msg: st.markdown(f"[Buka WhatsApp](https://wa.me/{phone}?text={quote(msg)})")
elif pilihan == "🚛 Aset & Properti":
    st.markdown('<div class="main-header"><h1>🚛 Aset & Properti</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("aset", "SELECT id, kode, nama, kategori, status FROM aset", ["kode", "nama", "kategori", "status"], ["id", "kode", "nama", "kategori", "status"], "aset")

elif pilihan == "🏪 Ruko & Tenant":
    st.markdown('<div class="main-header"><h1>🏪 Ruko & Tenant</h1></div>', unsafe_allow_html=True)
    tab_a, tab_b = st.tabs(["🏪 Ruko", "🏠 Tenant"])
    with tab_a: 
        render_edit_delete_table("ruko", "SELECT id, nama, penyewa, status FROM ruko", ["nama", "penyewa", "status"], ["id", "nama", "penyewa", "status"], "ruko")
    with tab_b: 
        render_edit_delete_table("tenant", "SELECT id, nama, penghuni, biaya_bulanan FROM tenant", ["nama", "penghuni", "biaya_bulanan"], ["id", "nama", "penghuni", "biaya_bulanan"], "tenant")

elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility</h1></div>', unsafe_allow_html=True)
    render_edit_delete_table("utility", "SELECT id, kategori, periode, total_bayar, status FROM utility", ["kategori", "periode", "total_bayar", "status"], ["id", "kategori", "periode", "total_bayar", "status"], "util")

elif pilihan == "📁 Arsip Dokumen (E-Filing)":
    st.markdown('<div class="main-header"><h1>📁 Arsip Dokumen</h1></div>', unsafe_allow_html=True)
    with st.form("arsip_form", clear_on_submit=True):
        st.subheader("📤 Upload Dokumen Baru")
        ar_nama = st.text_input("Nama Dokumen *")
        ar_kategori = st.selectbox("Kategori", ["Kontrak Kerja", "KTP", "NPWP", "Ijazah", "Sertifikat", "Lainnya"])
        ar_ket = st.text_area("Keterangan")
        ar_file = st.file_uploader("Upload File")
        if st.form_submit_button("💾 Upload Dokumen", type="primary"):
            if ar_nama and ar_file:
                file_data = ar_file.read()
                c.execute("INSERT INTO arsip_dokumen (tanggal_upload, nama_dokumen, kategori, keterangan, file_data, file_name, file_type) VALUES (?,?,?,?,?,?,?)",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ar_nama, ar_kategori, ar_ket, file_data, ar_file.name, ar_file.type))
                conn.commit(); st.success(f"✅ File {ar_file.name} tersimpan."); time.sleep(1); st.rerun()
    df_arsip = pd.read_sql_query("SELECT id, tanggal_upload, nama_dokumen, kategori FROM arsip_dokumen ORDER BY id DESC", conn)
    st.dataframe(df_arsip, use_container_width=True, hide_index=True)

elif pilihan == "📎 Lampiran / Attachment":
    st.markdown('<div class="main-header"><h1>📎 Lampiran</h1></div>', unsafe_allow_html=True)
    with st.form("lampiran_form", clear_on_submit=True):
        lm_modul = st.selectbox("Referensi Modul *", ["cuti", "kandidat", "karyawan", "resign", "disiplin", "payroll", "lainnya"])
        lm_id = st.text_input("Referensi ID (misal: 15) *")
        lm_ket = st.text_area("Keterangan")
        lm_file = st.file_uploader("Upload File")
        if st.form_submit_button("💾 Upload Lampiran", type="primary"):
            if lm_id and lm_file:
                file_data = lm_file.read()
                c.execute("INSERT INTO lampiran (ref_modul, ref_id, file_name, file_type, file_data, tanggal_upload, keterangan) VALUES (?,?,?,?,?,?,?)",
                          (lm_modul, lm_id, lm_file.name, lm_file.type, file_data, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lm_ket))
                conn.commit(); st.success(f"✅ File {lm_file.name} tersimpan."); time.sleep(1); st.rerun()
    df_lm = pd.read_sql_query("SELECT id, ref_modul, ref_id, file_name FROM lampiran ORDER BY id DESC", conn)
    st.dataframe(df_lm, use_container_width=True, hide_index=True)
elif pilihan == "📋 Formulir HRD (Official)":
    st.markdown('<div class="main-header"><h1>📋 Formulir HRD (Official)</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Wawancara & Coaching", "🌴 Permohonan Cuti", "🧑‍💼 Data Pelamar", "📋 Permintaan Karyawan (FPK)", "🚪 Exit & Clearance", "⏱️ Izin & Kehadiran"])
    
    with tab1:
        st.subheader("Formulir Laporan Wawancara")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR LAPORAN WAWANCARA</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.text_input("Nama", key="w_nama")
            with c2: st.text_input("Jabatan yang dilamar", key="w_jabatan")
            with c3: st.text_input("Usia", key="w_usia")
            with c4: st.date_input("Tanggal Wawancara", key="w_tgl")
            st.info("5 = Baik Sekali, 4 = Baik, 3 = Cukup, 2 = Kurang, 1 = Kurang Sekali")
            f1 = st.radio("1. KUALIFIKASI", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f1")
            f2 = st.radio("2. PENGALAMAN", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f2")
            f3 = st.radio("3. PENGETAHUAN & KETERAMPILAN", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f3")
            f4 = st.radio("4. KARAKTERISTIK KEPRIBADIAN", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f4")
            f5 = st.radio("5. KOMUNIKASI", ["5", "4", "3", "2", "1"], horizontal=True, key="w_f5")
            st.markdown("---")
            c_kiri, c_kanan = st.columns(2)
            with c_kiri:
                st.text_area("Kelebihan", height=100, key="w_kelebihan")
                st.text_area("Kekurangan", height=100, key="w_kekurangan")
            with c_kanan:
                st.markdown("**KEPUTUSAN**")
                st.checkbox("DITOLAK", key="w_dec_tolak"); st.checkbox("DIPERTIMBANGKAN", key="w_dec_pertimbangkan"); st.checkbox("DITERIMA", key="w_dec_terima")
                st.text_input("Pewawancara* (I / II / III / IV)", key="w_pewawancara"); st.text_input("Nama Pewawancara", key="w_nama_pewawancara"); st.text_input("Jabatan Pewawancara", key="w_jabatan_pewawancara")
            
            if st.button("📥 Cetak PDF Wawancara", key="pdf_wawancara"):
                data_pdf = {
                    "Nama": st.session_state.get("w_nama",""), "Jabatan Dilamar": st.session_state.get("w_jabatan",""),
                    "Usia": st.session_state.get("w_usia",""), "Tanggal": str(st.session_state.get("w_tgl","")),
                    "Kualifikasi": st.session_state.get("w_f1",""), "Pengalaman": st.session_state.get("w_f2",""),
                    "Pengetahuan": st.session_state.get("w_f3",""), "Karakteristik": st.session_state.get("w_f4",""),
                    "Komunikasi": st.session_state.get("w_f5",""), "Kelebihan": st.session_state.get("w_kelebihan",""),
                    "Kekurangan": st.session_state.get("w_kekurangan",""), "Pewawancara": st.session_state.get("w_pewawancara","") + " - " + st.session_state.get("w_nama_pewawancara","")
                }
                pdf_bytes = generate_pdf("Formulir Laporan Wawancara", data_pdf)
                st.download_button("💾 Download PDF Wawancara", data=pdf_bytes, file_name="Wawancara.pdf", mime="application/pdf")

        st.divider()
        st.subheader("2. Form Coaching & Counselling")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORM COACHING & COUNSELLING</div>', unsafe_allow_html=True)
            co_kid, co_emp_id, co_nama, co_jabatan, co_divisi = get_karyawan_dropdown("co_dropdown", "Pilih Karyawan yang di-Coaching")
            if co_nama:
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nama Karyawan", value=co_nama, disabled=True); st.text_input("NIK", value=co_emp_id, disabled=True)
                with c2: st.text_input("Tanggal Masuk", key="co_tgl_masuk"); st.text_input("Jabatan / Departemen", value=f"{co_jabatan} / {co_divisi}", disabled=True)
                st.radio("Status Karyawan", ["Tetap", "Kontrak (PKWT)", "Percobaan"], horizontal=True, key="co_status")
                st.text_area("Isu/Permasalahan & Penyebabnya", height=80, key="co_isu")
                st.text_area("Observasi/Kesaksian", height=80, key="co_obs")
                st.text_area("Langkah perbaikan yang akan dilakukan", height=80, key="co_langkah")
                st.text_area("Komitmen Karyawan akan sanksi", height=80, key="co_komit")
                st.markdown("**Rekomendasi (Atasan/HRD):**")
                r1 = st.checkbox("Diberi kesempatan melakukan perubahan", key="co_r1")
                r2 = st.checkbox("Direlokasi ke posisi lain", key="co_r2")
                r3 = st.checkbox("Mendapat sanksi", key="co_r3")
                r4 = st.checkbox("Masa kerja tidak dapat dilanjutkan (termination)", key="co_r4")
                st.text_area("Hal yang akan dilakukan (Atasan/HRD)", height=80, key="co_hal")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Simpan Coaching", type="primary"):
                        rekom = [x for x, v in [("Kesempatan", r1), ("Relokasi", r2), ("Sanksi", r3), ("Termination", r4)] if v]
                        c.execute("INSERT INTO formulir_coaching (nama_karyawan, nik, tanggal_masuk, jabatan, status_karyawan, isu, observasi, langkah_perbaikan, komitmen, rekomendasi, hal_dilakukan, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                  (co_nama, co_emp_id, st.session_state.get("co_tgl_masuk",""), co_jabatan, st.session_state.get("co_status",""), st.session_state.get("co_isu",""), st.session_state.get("co_obs",""), st.session_state.get("co_langkah",""), st.session_state.get("co_komit",""), ", ".join(rekom), st.session_state.get("co_hal",""), st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Coaching"):
                        data_pdf = {"Nama Karyawan": co_nama, "NIK": co_emp_id, "Jabatan": co_jabatan, "Tanggal Masuk": st.session_state.get("co_tgl_masuk",""), "Status": st.session_state.get("co_status",""), "Isu": st.session_state.get("co_isu",""), "Observasi": st.session_state.get("co_obs",""), "Langkah Perbaikan": st.session_state.get("co_langkah",""), "Komitmen": st.session_state.get("co_komit",""), "Hal Dilakukan": st.session_state.get("co_hal","")}
                        pdf_bytes = generate_pdf("Form Coaching & Counselling", data_pdf)
                        st.download_button("💾 Download PDF Coaching", data=pdf_bytes, file_name="Coaching.pdf", mime="application/pdf")

    with tab2:
        st.subheader("1. Surat Permohonan Cuti (Standard)")
        with st.container(border=True):
            st.markdown('<div class="form-title">SURAT PERMOHONAN CUTI</div>', unsafe_allow_html=True)
            c_kid, c_emp_id, c_nama_val, c_jabatan, c_divisi = get_karyawan_dropdown("c_dropdown", "Pilih Karyawan Pemohon")
            if c_nama_val:
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nama", value=c_nama_val, disabled=True)
                with c2: st.text_input("NIK / Divisi", value=f"{c_emp_id} / {c_divisi}", disabled=True)
                st.markdown("**Jenis Cuti:**")
                jc = []
                if st.checkbox("Tahunan", key="c_tahunan"): jc.append("Tahunan")
                if st.checkbox("Melahirkan", key="c_melahirkan"): jc.append("Melahirkan")
                if st.checkbox("Jobsite", key="c_jobsite"): jc.append("Jobsite")
                if st.checkbox("Mangkir", key="c_mangkir"): jc.append("Mangkir")
                c3, c4 = st.columns(2)
                with c3: c_lama = st.number_input("Lama Cuti (Hari)", min_value=1, step=1, key="c_lama")
                with c4: c_tgl = st.text_input("Mulai s/d", key="c_tgl")
                c_ket = st.text_area("Keterangan", key="c_ket")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Simpan Cuti Standard", type="primary"):
                        c.execute("INSERT INTO cuti (karyawan_id, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, status) VALUES (?,?,?,?,?,?,?)",
                                  (c_kid, ", ".join(jc), st.session_state.get("c_tgl",""), st.session_state.get("c_tgl",""), st.session_state.get("c_lama",1), st.session_state.get("c_ket",""), "Menunggu"))
                        conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Cuti Standard"):
                        data_pdf = {"Nama": c_nama_val, "NIK": c_emp_id, "Divisi": c_divisi, "Jenis Cuti": ", ".join(jc), "Lama Cuti": f"{st.session_state.get('c_lama',1)} Hari", "Mulai s/d": st.session_state.get("c_tgl",""), "Keterangan": st.session_state.get("c_ket","")}
                        pdf_bytes = generate_pdf("Surat Permohonan Cuti", data_pdf)
                        st.download_button("💾 Download PDF Cuti", data=pdf_bytes, file_name="Cuti_Standard.pdf", mime="application/pdf")

        st.divider()
        st.subheader("2. Permohonan Cuti Khusus")
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN CUTI KHUSUS</div>', unsafe_allow_html=True)
            ck_kid, ck_emp_id, ck_nama_val, ck_jabatan, ck_divisi = get_karyawan_dropdown("ck_dropdown", "Pilih Karyawan (Cuti Khusus)")
            if ck_nama_val:
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nama", value=ck_nama_val, disabled=True)
                with c2: st.text_input("NIK / Divisi", value=f"{ck_emp_id} / {ck_divisi}", disabled=True)
                
                ck_alasan = st.radio("Alasan Cuti Khusus", ["Menikah (3 Hari Kerja)", "Pernikahan anak (2 Hari Kerja)", "Mengkhitankan / membaptiskan anak (2 Hari Kerja)", "Istri Melahirkan / Gugur kandungan (2 Hari Kerja)", "Istri/ Suami/ Anak meninggal (2 Hari Kerja)", "Orang tua/ Mertua / Menantu meninggal (2 Hari Kerja)", "Anggota keluarga Karyawan yang serumah meninggal dunia (1 Hari Kerja)", "Melahirkan / Keguguran (45 hari sblm dan ssdh melahirkan)", "Ibadah Haji (40 hari, hanya 1 kali pengajuan)", "Bencana alam (Max. 2 Hari Kerja)"], key="ck_alasan")
                st.warning("Catatan: Setiap pengajuan cuti khusus ini harus melampirkan dokumen resmi sebagai pendukungnya.")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Simpan Cuti Khusus", type="primary"):
                        c.execute("INSERT INTO formulir_izin (jenis_form, nama, jabatan, tanggal, alasan, created_by, created_at) VALUES (?,?,?,?,?,?,?)",
                                  ("CUTI_KHUSUS", ck_nama_val, ck_jabatan, datetime.now().strftime("%Y-%m-%d"), st.session_state.get("ck_alasan",""), st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Cuti Khusus"):
                        data_pdf = {"Nama": ck_nama_val, "NIK": ck_emp_id, "Divisi": ck_divisi, "Alasan Cuti Khusus": st.session_state.get("ck_alasan",""), "Tanggal Pengajuan": datetime.now().strftime("%Y-%m-%d")}
                        pdf_bytes = generate_pdf("Permohonan Cuti Khusus", data_pdf)
                        st.download_button("💾 Download PDF Cuti Khusus", data=pdf_bytes, file_name="Cuti_Khusus.pdf", mime="application/pdf")
    with tab3:
        st.subheader("Formulir Data Pelamar")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR DATA PELAMAR</div>', unsafe_allow_html=True)
            with st.expander("A. DATA PRIBADI", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Pekerjaan yang Dilamar", key="dp_pekerjaan"); st.text_input("Nama Lengkap", key="dp_nama"); st.text_input("Nama Panggilan", key="dp_panggilan")
                    st.radio("Jenis Kelamin", ["Laki-Laki", "Perempuan"], horizontal=True, key="dp_jk")
                    st.text_area("Alamat Tempat Tinggal", key="dp_alamat_tinggal"); st.text_area("Alamat Sesuai KTP", key="dp_alamat_ktp")
                with c2:
                    st.text_input("Email", key="dp_email"); st.text_input("Tempat & Tanggal Lahir", key="dp_ttl")
                    st.selectbox("Agama", ["Islam", "Kristen", "Katholik", "Hindu", "Budha"], key="dp_agama")
                    st.selectbox("Status Perkawinan", ["Menikah", "Tidak Menikah", "Janda/Duda"], key="dp_status_perkawinan")
                    st.selectbox("Tempat Tinggal", ["Sendiri", "Ikut Orang Tua", "Kost/Kontrak"], key="dp_tempat_tinggal")
                    st.text_input("Nomor KTP", key="dp_no_ktp"); st.text_input("Nomor SIM", key="dp_no_sim")
            
            with st.expander("B. SUSUNAN KELUARGA"): df_keluarga = st.data_editor(pd.DataFrame(columns=["Hubungan", "Nama", "Pendidikan", "Pekerjaan", "Jabatan", "Perusahaan", "Telepon", "Keterangan"]), num_rows="dynamic", use_container_width=True, key="dp_de_keluarga")
            with st.expander("C. LATAR BELAKANG PENDIDIKAN"): df_pendidikan = st.data_editor(pd.DataFrame(columns=["Tingkat", "Nama Sekolah", "Tempat/Kota", "Jurusan", "Tahun Masuk", "Tahun Keluar", "Lulus/Tidak"]), num_rows="dynamic", use_container_width=True, key="dp_de_pendidikan")
            with st.expander("D. KURSUS / PELATIHAN"): df_kursus = st.data_editor(pd.DataFrame(columns=["Bidang/Jenis", "Lembaga", "Tempat/Kota", "Lama Kursus", "Tahun", "Dibiayai Oleh"]), num_rows="dynamic", use_container_width=True, key="dp_de_kursus")
            with st.expander("E. PENGETAHUAN BAHASA ASING"): df_bahasa = st.data_editor(pd.DataFrame(columns=["Bahasa", "Bicara", "Mendengar", "Membaca", "Menulis", "Pemakaian"]), num_rows="dynamic", use_container_width=True, key="dp_de_bahasa")
            with st.expander("F. KEGIATAN SOSIAL"): df_sosial = st.data_editor(pd.DataFrame(columns=["Tahun", "Nama Organisasi", "Jenis Kegiatan", "Jabatan"]), num_rows="dynamic", use_container_width=True, key="dp_de_sosial")
            with st.expander("G. HOBBY DAN KEGIATAN WAKTU LUANG"): st.text_area("Hobby", key="dp_hobby")
            with st.expander("H. RIWAYAT PEKERJAAN"): df_pekerjaan = st.data_editor(pd.DataFrame(columns=["Nama/Perusahaan", "Jabatan", "Awal", "Akhir", "Lama Kerja", "Jenis Usaha", "Alasan Berhenti", "Atasan Langsung", "Direktur", "Gaji Terakhir"]), num_rows="dynamic", use_container_width=True, key="dp_de_pekerjaan")
            with st.expander("I. REFERENSI"): df_referensi = st.data_editor(pd.DataFrame(columns=["Nama", "Alamat", "Telepon", "Pekerjaan", "Hubungan"]), num_rows="dynamic", use_container_width=True, key="dp_de_referensi")
            with st.expander("J. URAIAN TUGAS DAN TANGGUNG JAWAB"): st.text_area("Uraikan tugas dan tanggung jawab Anda pada jabatan terakhir Anda:", height=100, key="dp_uraian_tugas")
            with st.expander("K. HAL-HAL POSITIF & NEGATIF"): st.text_area("Hal-Hal Yang Positif", height=100, key="dp_positif"); st.text_area("Hal-Hal Yang Negatif", height=100, key="dp_negatif")
            with st.expander("PERTANYAAN 1 (Aset Pribadi)"): df_pertanyaan1 = st.data_editor(pd.DataFrame(columns=["Pertanyaan", "Ya", "Tidak", "Penjelasan"]), num_rows="dynamic", use_container_width=True, key="dp_de_pertanyaan1")
            with st.expander("PERTANYAAN 2"): df_pertanyaan2 = st.data_editor(pd.DataFrame(columns=["Pertanyaan", "Ya", "Tidak", "Penjelasan"]), num_rows="dynamic", use_container_width=True, key="dp_de_pertanyaan2")
                
            st.markdown("**Pernyataan:** DENGAN INI SAYA MENYATAKAN BAHWA KETERANGAN YANG SAYA BERIKAN DIATAS ADALAH BENAR. APABILA DIKEMUDIAN HARI DITEMUKAN KETIDAKSESUAIAN, SAYA BERTANGGUNG JAWAB PENUH ATAS AKIBATNYA.")
            st.text_input("JAKARTA, (Tanggal)", key="dp_tgl_pernyataan"); st.text_input("PELAMAR (Nama Terang)", key="dp_nama_terang")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("💾 Simpan Data Pelamar", type="primary", use_container_width=True):
                try:
                    data_json = json.dumps({"nama": st.session_state.get("dp_nama",""), "pekerjaan": st.session_state.get("dp_pekerjaan",""), "email": st.session_state.get("dp_email",""), "ttl": st.session_state.get("dp_ttl",""), "keluarga": df_keluarga.to_dict("records"), "pendidikan": df_pendidikan.to_dict("records"), "pekerjaan_riwayat": df_pekerjaan.to_dict("records")}, ensure_ascii=False, default=str)
                    c.execute("INSERT INTO formulir_exit (jenis_form, nama, posisi, data_json, created_by, created_at) VALUES (?,?,?,?,?,?)", ("DATA_PELAMAR", st.session_state.get("dp_nama",""), st.session_state.get("dp_pekerjaan",""), data_json, st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit(); st.success("✅ Data Pelamar tersimpan."); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Gagal: {e}")
        with c_btn2:
            if st.button("📥 Cetak PDF Data Pelamar", use_container_width=True):
                data_pdf = {"Nama Lengkap": st.session_state.get("dp_nama",""), "Pekerjaan Dilamar": st.session_state.get("dp_pekerjaan",""), "Email": st.session_state.get("dp_email",""), "TTL": st.session_state.get("dp_ttl",""), "Jenis Kelamin": st.session_state.get("dp_jk",""), "Agama": st.session_state.get("dp_agama",""), "Status Kawin": st.session_state.get("dp_status_perkawinan","")}
                pdf_bytes = generate_pdf("Formulir Data Pelamar", data_pdf)
                st.download_button("💾 Download PDF", data=pdf_bytes, file_name="Data_Pelamar.pdf", mime="application/pdf")

    with tab4:
        st.subheader("Formulir Permintaan Karyawan (FPK)")
        with st.container(border=True):
            st.markdown('<div class="form-title">FORMULIR PERMINTAAN KARYAWAN<br>UNTUK PEMENUHAN INTERNAL</div>', unsafe_allow_html=True)
            st.markdown("**I. POSISI KARYAWAN YANG DIAJUKAN**")
            c1, c2 = st.columns(2)
            with c1: st.text_input("Posisi", key="fpk_posisi"); st.text_input("Divisi/Departemen", key="fpk_divisi"); st.number_input("Jumlah", min_value=1, key="fpk_jumlah")
            with c2: st.radio("Penempatan", ["Head Office", "Cabang", "Site"], horizontal=True, key="fpk_penempatan"); st.text_input("Lokasi", key="fpk_lokasi"); st.date_input("Tanggal Pengajuan", key="fpk_tgl")
            st.markdown("**II. TUJUAN PERMINTAAN**"); st.checkbox("Penambahan", key="fpk_penambahan"); st.text_input("Alasan", key="fpk_alasan"); st.checkbox("Magang", key="fpk_magang"); st.text_input("Jangka Waktu (Bulan)", key="fpk_jangka_waktu")
            st.markdown("**III. PERSYARATAN JABATAN**"); st.text_input("1. Pendidikan", key="fpk_pendidikan"); st.text_input("2. Rentang Usia", key="fpk_rentang_usia"); st.radio("3. Jenis Kelamin", ["Laki-Laki", "Perempuan", "Tidak Spesifik"], horizontal=True, key="fpk_jk"); st.text_input("4. Pengalaman", key="fpk_pengalaman"); st.text_input("5. Keahlian Umum", key="fpk_keahlian"); st.text_input("6. Kemampuan Bahasa", key="fpk_bahasa"); st.text_input("7. Sertifikasi", key="fpk_sertifikasi"); st.text_input("8. Persyaratan Tambahan", key="fpk_persyaratan_tambahan")
            st.markdown("**IV. PROSES PENCARIAN KARYAWAN**"); st.radio("Sumber Kandidat", ["Internal Hiring", "External Hiring", "Labor Supply"], horizontal=True, key="fpk_sumber"); st.radio("Proses Rekrutmen", ["Publish", "Hide"], horizontal=True, key="fpk_proses"); st.radio("Technical Tes", ["Ya", "Tidak"], horizontal=True, key="fpk_tes")
            st.markdown("**V. URAIAN JABATAN**"); st.text_area("Deskripsi Pekerjaan & Tanggung Jawab", height=150, key="fpk_deskripsi")
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("💾 Simpan FPK", type="primary"):
                    c.execute("""INSERT INTO formulir_fpk (posisi, divisi, jumlah, penempatan, lokasi, tanggal_pengajuan, alasan, deskripsi_pekerjaan, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)""", (st.session_state.get("fpk_posisi",""), st.session_state.get("fpk_divisi",""), st.session_state.get("fpk_jumlah",1), st.session_state.get("fpk_penempatan",""), st.session_state.get("fpk_lokasi",""), str(st.session_state.get("fpk_tgl","")), st.session_state.get("fpk_alasan",""), st.session_state.get("fpk_deskripsi",""), st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit(); st.success("✅ FPK tersimpan."); time.sleep(1); st.rerun()
            with c_btn2:
                if st.button("📥 Cetak PDF FPK"):
                    data_pdf = {"Posisi": st.session_state.get("fpk_posisi",""), "Divisi": st.session_state.get("fpk_divisi",""), "Jumlah": st.session_state.get("fpk_jumlah",1), "Penempatan": st.session_state.get("fpk_penempatan",""), "Alasan": st.session_state.get("fpk_alasan",""), "Deskripsi": st.session_state.get("fpk_deskripsi","")}
                    pdf_bytes = generate_pdf("Formulir Permintaan Karyawan (FPK)", data_pdf)
                    st.download_button("💾 Download PDF FPK", data=pdf_bytes, file_name="FPK.pdf", mime="application/pdf")
       with tab5:
        st.subheader("Formulir Karyawan Keluar dari Perusahaan")
        with st.container(border=True):
            st.markdown('<div class="form-title">SERAH TERIMA INVENTARIS PERUSAHAAN</div>', unsafe_allow_html=True)
            e_kid, e_emp_id, e_nama_val, e_jab, e_div = get_karyawan_dropdown("e_inv_dropdown", "Pilih Karyawan (Yang Menyerahkan)")
            if e_nama_val:
                c1, c2 = st.columns(2)
                with c1: st.text_input("NAMA", value=e_nama_val, disabled=True); st.text_input("POSISI/JABATAN", value=e_jab, disabled=True)
                with c2: st.text_input("NIK", value=e_emp_id, disabled=True); st.text_input("DEPARTEMEN", value=e_div, disabled=True)
                st.write("Dengan ini menyerahkan inventaris kantor yang telah saya terima selama saya bekerja di PT.UNITED EQUIPMENT INDONESIA, berupa:")
                df_inv = st.data_editor(pd.DataFrame(columns=["No", "Nama Barang", "Jumlah", "Keterangan"]), num_rows="dynamic", use_container_width=True, key="e_inv")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Simpan Inventaris", type="primary"):
                        c.execute("INSERT INTO formulir_exit (jenis_form, nama, nik, posisi, departemen, data_json, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)", ("SERAH_TERIMA_INVENTARIS", e_nama_val, e_emp_id, e_jab, e_div, json.dumps(df_inv.to_dict("records")), st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Inventaris"):
                        items_str = "\n".join([f"{r['Nama Barang']} ({r['Jumlah']}) - {r['Keterangan']}" for _, r in df_inv.iterrows()])
                        data_pdf = {"Nama": e_nama_val, "NIK": e_emp_id, "Jabatan": e_jab, "Divisi": e_div, "Daftar Barang": items_str}
                        pdf_bytes = generate_pdf("Serah Terima Inventaris", data_pdf)
                        st.download_button("💾 Download PDF Inventaris", data=pdf_bytes, file_name="Inventaris.pdf", mime="application/pdf")

    with tab6:
        st.subheader("1. Permohonan Izin Pulang Cepat")
        with st.container(border=True):
            st.markdown('<div class="form-title">PERMOHONAN IZIN PULANG CEPAT</div>', unsafe_allow_html=True)
            pc_kid, pc_emp_id, pc_nama_val, pc_jab, pc_div = get_karyawan_dropdown("pc_dropdown", "Pilih Karyawan")
            if pc_nama_val:
                st.text_input("HRD No: /RCP-HR/ /20", key="pc_hrd")
                c1, c2 = st.columns(2)
                with c1: st.text_input("Nama Karyawan", value=pc_nama_val, disabled=True); st.text_input("Hari/Tanggal", key="pc_tgl"); st.text_area("Alasan", key="pc_alasan")
                with c2: st.text_input("Jabatan/Divisi", value=f"{pc_jab} / {pc_div}", disabled=True); st.text_input("Pukul (s/d)", key="pc_pukul")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Simpan Izin Pulang Cepat", type="primary"):
                        c.execute("INSERT INTO formulir_izin (jenis_form, nama, jabatan, tanggal, alasan, pukul, data_json, created_by, created_at) VALUES (?,?,?,?,?,?,?,?,?)", ("IZIN_PULANG_CEPAT", pc_nama_val, pc_jab, st.session_state.get("pc_tgl",""), st.session_state.get("pc_alasan",""), st.session_state.get("pc_pukul",""), json.dumps({"hrd_no": st.session_state.get("pc_hrd","")}), st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit(); st.success("Tersimpan"); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Izin"):
                        data_pdf = {"Nama": pc_nama_val, "Jabatan": pc_jab, "Divisi": pc_div, "Tanggal": st.session_state.get("pc_tgl",""), "Alasan": st.session_state.get("pc_alasan",""), "Pukul": st.session_state.get("pc_pukul","")}
                        pdf_bytes = generate_pdf("Permohonan Izin Pulang Cepat", data_pdf)
                        st.download_button("💾 Download PDF Izin", data=pdf_bytes, file_name="Izin_Pulang.pdf", mime="application/pdf")

    with st.expander("Form Perubahan Data Karyawan"):
        with st.container(border=True):
            st.markdown('<div class="form-title">FORM PERUBAHAN DATA KARYAWAN</div>', unsafe_allow_html=True)
            pd_kid, pd_emp_id, pd_nama_val, pd_jab, pd_div = get_karyawan_dropdown("pd_dropdown", "Pilih Karyawan")
            if pd_nama_val:
                st.text_input("Nama Karyawan", value=pd_nama_val, disabled=True)
                st.date_input("Tanggal Pengisian", key="pd_tgl")
                df_perubahan = st.data_editor(pd.DataFrame({"Keterangan": ["No. ID", "Nama", "No. REK BCA", "Alamat Tinggal Sebenarnya", "Kota", "Kode POS", "Alamat di KTP", "No Telp", "Pendidikan Terakhir", "Agama", "Jabatan", "Status Menikah", "Tanggungan"], "Data Sebelumnya": [""] * 13, "Data Sekarang": [""] * 13}), hide_index=True, use_container_width=True, disabled=["Keterangan"], key="pd_table")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("💾 Simpan Perubahan", type="primary"):
                        c.execute("INSERT INTO formulir_perubahan (no_urut, tanggal, data_json, pengaju, created_by, created_at) VALUES (?,?,?,?,?,?)", (pd_emp_id, str(st.session_state.get("pd_tgl","")), json.dumps(df_perubahan.to_dict("records")), pd_nama_val, st.session_state.username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit(); st.success("✅ Perubahan Data tersimpan."); time.sleep(1); st.rerun()
                with c_btn2:
                    if st.button("📥 Cetak PDF Perubahan Data"):
                        pdf_bytes = generate_pdf("Form Perubahan Data Karyawan", {"Nama": pd_nama_val, "NIK": pd_emp_id, "Tanggal": str(st.session_state.get("pd_tgl",""))})
                        st.download_button("💾 Download PDF Perubahan", data=pdf_bytes, file_name="Perubahan_Data.pdf", mime="application/pdf")

elif pilihan == "📊 Laporan & Analitik":
    st.markdown('<div class="main-header"><h1>📊 Laporan & Analitik</h1></div>', unsafe_allow_html=True)
    st.info("Fitur Analitik siap digunakan. Anda dapat menambahkan grafik Altair di sini.")

elif pilihan == "📈 Manpower Report":
    st.markdown('<div class="main-header"><h1>📈 Manpower Report</h1></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: 
        filter_div = st.selectbox("Filter Divisi", ["(Semua)"] + [r[0] for r in c.execute("SELECT DISTINCT divisi FROM karyawan WHERE divisi IS NOT NULL AND divisi != ''").fetchall()], key="mp_div")
    with col2: 
        filter_status = st.selectbox("Filter Status", ["(Semua)", "Contract", "Permanent", "Percobaan"], key="mp_stat")
        
    q = "SELECT * FROM karyawan WHERE 1=1"
    params = []
    if filter_div != "(Semua)": q += " AND divisi=?"; params.append(filter_div)
    if filter_status != "(Semua)": q += " AND status_employee=?"; params.append(filter_status)
    
    df_man = pd.read_sql_query(q, conn, params=tuple(params))
    st.markdown(f"**Total Data: {len(df_man)} Karyawan**")
    
    cols_tampil = ["employee_id", "full_name", "organization", "job_position", "job_level", "join_date", "resign_date", "status_employee", "email", "mobile_phone", "branch_name", "divisi"]
    cols_ada = [c for c in cols_tampil if c in df_man.columns]
    st.dataframe(df_man[cols_ada], use_container_width=True, hide_index=True)
    
    csv_man = df_man.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download Laporan (CSV)", data=csv_man, file_name=f"manpower_report.csv", mime="text/csv")

elif pilihan == "💾 Import, Export & Backup":
    st.markdown('<div class="main-header"><h1>💾 Import, Export & Backup</h1></div>', unsafe_allow_html=True)
    tab_e1, tab_e2, tab_e3 = st.tabs(["📤 Export CSV", "📦 Backup ZIP", "📥 Import Excel Karyawan"])
    
    with tab_e1:
        st.info("Export database ke CSV.")
        tables = ["karyawan", "kandidat", "lowongan", "absensi", "cuti", "payroll", "resign", "aset", "utility", "ruko", "tenant", "disiplin", "mutasi", "jobdesk", "ci", "skd", "im", "log_aktivitas"]
        pilih_tabel = st.selectbox("Pilih Tabel", tables)
        if st.button("📥 Download CSV"):
            df = pd.read_sql_query(f"SELECT * FROM {pilih_tabel}", conn)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(f"💾 {pilih_tabel}.csv", data=csv, file_name=f"{pilih_tabel}.csv", mime="text/csv")
    
    with tab_e2:
        if st.button("📦 Buat Backup ZIP"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.exists("hris_ga.db"): zf.write("hris_ga.db")
            buf.seek(0)
            st.download_button("💾 Download Backup", data=buf, file_name="backup.zip", mime="application/zip")
            
    with tab_e3:
        st.subheader("Import Data Karyawan dari Excel")
        st.info("Pastikan judul kolom di file Excel Anda sesuai format standar (Employee ID, Full Name, Job Position, dll).")
        uploaded_excel = st.file_uploader("Pilih File Excel", type=["xlsx", "xls"])
        
        if uploaded_excel is not None:
            df_excel = pd.read_excel(uploaded_excel)
            st.write(f"Total baris: {len(df_excel)}")
            
            if st.button("💾 Mulai Import", type="primary"):
                success = 0
                for _, row in df_excel.iterrows():
                    emp_id = str(row.get('Employee ID', '')).strip()
                    if not emp_id or emp_id == 'nan': continue
                    
                    c.execute("""INSERT OR REPLACE INTO karyawan 
                        (employee_id, full_name, barcode, organization, job_position, job_level, 
                         join_date, resign_date, status_employee, end_date, sign_date, email, 
                         birth_date, age, birth_place, citizen_id_address, residential_address, 
                         npwp, ptkp_status, employee_tax_status, tax_config, bank_name, 
                         bank_account, bank_account_holder, bpjs_ketenagakerjaan, bpjs_kesehatan, 
                         nik_npwp_16, mobile_phone, phone, branch_name, parent_branch_name, 
                         religion, gender, marital_status, blood_type, nationality_code, 
                         currency, length_of_service, payment_schedule, approval_line, 
                         manager, grade, class, profile_picture, cost_center, 
                         cost_center_category, sbu, npwp_16_new, passport, 
                         passport_expiration_date, jenis_dok_referensi_bukti_potong, 
                         nomor_dok_referensi_bukti_potong, tanggal_dok_referensi_bukti_potong, 
                         tin, divisi, keterangan, aktif) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                        (emp_id, clean(row.get('Full Name')), clean(row.get('Barcode')), 
                         clean(row.get('Organization')), clean(row.get('Job Position')), clean(row.get('Job Level')), 
                         clean_date(row.get('Join Date')), clean_date(row.get('Resign Date')), 
                         clean(row.get('Status Employee')), clean_date(row.get('End Date')), 
                         clean_date(row.get('Sign Date')), clean(row.get('Email')), 
                         clean_date(row.get('Birth Date')), clean(row.get('Age')), clean(row.get('Birth Place')), 
                         clean(row.get('Citizen ID Address')), clean(row.get('Residential Address')), clean(row.get('NPWP')), 
                         clean(row.get('PTKP Status')), clean(row.get('Employee Tax Status')), clean(row.get('Tax Config')), 
                         clean(row.get('Bank Name')), clean(row.get('Bank Account')), clean(row.get('Bank Account Holder')), 
                         clean(row.get('BPJS Ketenagakerjaan')), clean(row.get('BPJS Kesehatan')), 
                         clean(row.get('NIK (NPWP 16 Digit)')), clean(row.get('Mobile Phone')), clean(row.get('Phone')), 
                         clean(row.get('Branch Name')), clean(row.get('Parent Branch Name')), 
                         clean(row.get('Religion')), clean(row.get('Gender')), clean(row.get('Marital Status')), 
                         clean(row.get('Blood Type')), clean(row.get('Nationality Code')), clean(row.get('Currency')), 
                         clean(row.get('Length Of Service')), clean(row.get('Payment Schedule')), clean(row.get('Approval Line')), 
                         clean(row.get('Manager')), clean(row.get('Grade')), clean(row.get('Class')), 
                         clean(row.get('Profile Picture')), clean(row.get('Cost Center')), 
                         clean(row.get('Cost Center Category')), clean(row.get('SBU')), clean(row.get('NPWP 16 digit (new)')), 
                         clean(row.get('Passport')), clean_date(row.get('Passport Expiration Date')), 
                         clean(row.get('Jenis Dok. Referensi Bukti Potong')), clean(row.get('Nomor Dok. Referensi Bukti Potong')), 
                         clean_date(row.get('Tanggal Dok. Referensi Bukti Potong')), clean(row.get('TIN (Taxpayer Identification Number)')), 
                         clean(row.get('Divisi')), clean(row.get('Keterangan')))
                    )
                    success += 1
                conn.commit()
                st.success(f"✅ Berhasil import {success} data.")
                time.sleep(2); st.rerun()

elif pilihan == "👤 Manajemen User":
    st.markdown('<div class="main-header"><h1>👤 Manajemen User</h1></div>', unsafe_allow_html=True)
    df_u = pd.read_sql_query("SELECT id, username, nama_lengkap, role, aktif FROM users", conn)
    st.dataframe(df_u, use_container_width=True, hide_index=True)

elif pilihan == "📝 Log Aktivitas":
    st.markdown('<div class="main-header"><h1>📝 Log Aktivitas</h1></div>', unsafe_allow_html=True)
    df_log = pd.read_sql_query("SELECT * FROM log_aktivitas ORDER BY id DESC LIMIT 200", conn)
    st.dataframe(df_log, use_container_width=True, hide_index=True)

# ==================== FOOTER ====================
st.markdown(f"""
<div style="text-align:center; padding: 25px 0 15px 0; color: #64748b; font-size: 0.85em; border-top: 1px solid #cbd5e1; margin-top: 30px;">
    ⚡ <b>HRIS, GA & Amoey</b> — Sistem Manajemen SDM Terpadu<br>© {datetime.now().year} — All Rights Reserved
</div>
""", unsafe_allow_html=True)
