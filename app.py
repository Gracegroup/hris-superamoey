import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import calendar
import altair as alt
from datetime import datetime, timedelta, date

# ==================== KONFIGURASI ====================
st.set_page_config(
    page_title="HRIS & GA SUPER v5.1",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("uploads", exist_ok=True)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #eef2f7 0%, #d9e4f5 100%); }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e57c2 100%);
        padding: 20px; border-radius: 15px; color: white; text-align: center;
        margin-bottom: 20px; box-shadow: 0 8px 25px rgba(30, 60, 114, 0.4);
    }
    .main-header h1 { color: white !important; margin: 0; font-size: 2em; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .metric-card { padding: 15px; border-radius: 15px; color: white; box-shadow: 0 6px 15px rgba(0,0,0,0.15); }
    .metric-card .label { font-size: 0.8em; opacity: 0.95; margin-bottom: 8px; text-transform: uppercase; }
    .metric-card .value { font-size: 1.5em; font-weight: bold; }
    .card-blue { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .card-red { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .card-green { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .card-orange { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .card-purple { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); }
    section[data-testid="stSidebar"] * { color: #ecf0f1 !important; }
    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #7e57c2 100%);
        color: white !important; border: none; border-radius: 8px; padding: 10px 15px; font-weight: 600;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 10px rgba(42,82,152,0.5); }
    /* Highlight box untuk instruksi */
    .instruction-box { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE SETUP ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, mobile_phone TEXT, gaji REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, total_penghasilan_bruto REAL, gaji_bersih REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, jenis TEXT, alasan TEXT, kategori_penyebab TEXT, clearance_status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, periode TEXT, label TEXT, nominal REAL, admin REAL, total_bayar REAL, metode TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
    conn.commit()

init_db()

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def format_rp(n): return f"Rp {float(n):,.0f}".replace(",", ".") if pd.notna(n) else "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def metric_card(label, value, sub="", warna="card-blue"):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    return f'<div class="metric-card {warna}"><div class="label">{label}</div><div class="value">{value}</div>{sub_html}</div>'

# --- FUNGSI UTAMA UNTUK SIMPAN (SAVE) DATA DARI TABEL ---
def save_dataframe_to_db(table_name, edited_df):
    """Menyimpan perubahan dari st.data_editor ke database SQLite"""
    cur = conn.cursor()
    old_df = pd.read_sql_query(f"SELECT id FROM {table_name}", conn)
    old_ids = set(old_df['id'].dropna().astype(int).tolist()) if not old_df.empty else set()
    
    # Pastikan ID berupa integer
    edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
    new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
    
    # 1. PROSES HAPUS (DELETE) -> Bandingkan ID lama dengan ID baru
    for did in (old_ids - new_ids):
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        
    # 2. PROSES TAMBAH (INSERT) & EDIT (UPDATE)
    cols = [col for col in edited_df.columns if col != 'id']
    for _, row in edited_df.iterrows():
        vals = [None if pd.isna(row[col]) else row[col] for col in cols]
        if row['id'] == 0:
            # Data Baru (Insert)
            ph = ", ".join(["?"] * len(cols))
            cur.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({ph})", tuple(vals))
        else:
            # Data Lama (Update)
            set_c = ", ".join([f"{col}=?" for col in cols])
            cur.execute(f"UPDATE {table_name} SET {set_c} WHERE id=?", tuple(vals) + (row['id'],))
    conn.commit()

def render_export_print(df, filename):
    c1, c2, c3 = st.columns(3)
    with c1: st.download_button("📥 Download CSV", df.to_csv(index=False).encode(), f"{filename}.csv", "text/csv", use_container_width=True)
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w, index=False)
        st.download_button("📥 Download Excel", buf.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c3:
        html_table = df.to_html(classes='table', index=False)
        html_full = f"<html><head><title>Print</title><style>table{{border-collapse: collapse; width:100%;}} th,td{{border:1px solid #ddd; padding:8px;}} th{{background-color:#f2f2f2;}}</style></head><body><h2>{filename.upper()}</h2>{html_table}</body></html>"
        st.download_button("🖨️ Cetak Form", html_full, f"{filename}_print.html", "text/html", use_container_width=True)

def render_import_ui(table_name):
    with st.expander("📥 Import Data (CSV/Excel)"):
        f = st.file_uploader(f"Upload file untuk {table_name}", type=["csv", "xlsx", "xls"], key=f"up_{table_name}")
        if f:
            try:
                df_imp = pd.read_csv(f) if f.name.endswith('csv') else pd.read_excel(f)
                df_imp.columns = [str(col).lower().replace(' ', '_') for col in df_imp.columns]
                st.dataframe(df_imp.head(3))
                if st.button("🚀 Proses Import", key=f"btn_imp_{table_name}"):
                    df_imp.to_sql(table_name, conn, if_exists='append', index=False)
                    st.success(f"Berhasil import {len(df_imp)} baris!"); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": "", "nama": "", "role": ""})

if not st.session_state.logged_in:
    st.markdown('<div class="main-header"><h1>⚡ HRIS & GA SUPER v5.1</h1></div>', unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            row = c.execute("SELECT username, password, nama_lengkap, role FROM users WHERE username=?", (u,)).fetchone()
            if row and row[1] == hash_password(p):
                st.session_state.update({"logged_in": True, "username": row[0], "nama": row[2], "role": row[3]})
                log_aksi(u, "LOGIN"); st.rerun()
            else: st.error("Username / Password salah!")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.nama}")
    menu = [
        "🏠 Dashboard", 
        "👥 Data Karyawan", 
        "📅 Absensi", 
        "🏖️ Cuti & Izin", 
        "💰 Payroll", 
        "📉 Resign & Turnover",
        "🔄 Mutasi, PKWT & SP",
        "💡 Utility Melak", 
        "⚙️ Pengaturan & Log"
    ]
    pilihan = st.radio("Navigasi", menu)
    if st.button("Logout"):
        st.session_state.clear(); st.rerun()

# ==================== KONTEN MENU ====================
if pilihan == "🏠 Dashboard":
    st.markdown('<div class="main-header"><h1>🏠 Dashboard</h1></div>', unsafe_allow_html=True)
    aktif = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date=''").fetchone()[0]
    
    html = '<div class="metric-grid">'
    html += metric_card("Karyawan Aktif", str(aktif), "", "card-blue")
    html += metric_card("Total Resign", str(c.execute("SELECT COUNT(*) FROM resign").fetchone()[0]), "", "card-red")
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ==================== RESIGN & TURNOVER (Sesuai Screenshot) ====================
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<div class="main-header"><h1>📉 Resign & Turnover</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Input", "📋 Daftar & Kelola", "📊 Turnover"])

    with tab2:
        st.markdown("""
        <div class="instruction-box">
            <b>💡 Panduan Edit, Delete & Save:</b><br>
            1. <b>EDIT</b>: Klik langsung pada teks di dalam sel tabel, lalu ubah datanya.<br>
            2. <b>DELETE</b>: Klik pada kotak kosong di ujung <b>paling kiri</b> baris (sebelah kolom id), lalu tekan tombol <code>Delete</code> di keyboard Anda.<br>
            3. <b>SAVE</b>: Setelah selesai mengedit/menghapus, klik tombol <b>💾 SIMPAN PERUBAHAN TABEL</b> di bawah ini.
        </div>
        """, unsafe_allow_html=True)

        # Fetch data Resign (Gabungan dengan nama karyawan)
        df_r = pd.read_sql_query("""
            SELECT r.id, k.employee_id, k.full_name, r.tanggal_resign, r.jenis, r.kategori_penyebab, r.clearance_status, r.alasan
            FROM resign r 
            LEFT JOIN karyawan k ON r.karyawan_id = k.id 
            ORDER BY r.id DESC
        """, conn)

        if df_r.empty:
            st.info("Belum ada data karyawan yang resign.")
        else:
            # Fitur Export & Print
            render_export_print(df_r, "data_resign")
            
            # Tabel Interaktif (st.data_editor)
            edited_df = st.data_editor(
                df_r, 
                num_rows="dynamic", 
                use_container_width=True,
                hide_index=True
            )
            
            # TOMBOL SAVE
            if st.button("💾 SIMPAN PERUBAHAN TABEL", type="primary", use_container_width=True):
                save_dataframe_to_db("resign", edited_df)
                st.success("✅ Perubahan pada tabel (Edit/Hapus) berhasil disimpan ke Database!")
                st.rerun()

    with tab1:
        st.subheader("Input Resign Baru")
        df_k = pd.read_sql_query("SELECT id, employee_id, full_name FROM karyawan WHERE resign_date IS NULL OR resign_date=''", conn)
        if not df_k.empty:
            opsi = {f"{r['employee_id']} - {r['full_name']}": r['id'] for _, r in df_k.iterrows()}
            with st.form("form_resign"):
                pilih = st.selectbox("Karyawan", list(opsi.keys()))
                tgl = st.date_input("Tgl Resign", date.today())
                jenis = st.selectbox("Jenis", ["Resign Sendiri","PHK","Pensiun","Kontrak Habis"])
                kategori = st.selectbox("Kategori Penyebab", ["Mengundurkan Diri","Gagal Induksi","Medical Unfit","Contract Complete","Pelanggaran Indisipliner"])
                alasan = st.text_area("Alasan")
                if st.form_submit_button("💾 Simpan Data Baru"):
                    kid = opsi[pilih]
                    c.execute('''INSERT INTO resign (karyawan_id,tanggal_resign,alasan,jenis,kategori_penyebab,clearance_status) VALUES (?,?,?,?,?,?)''',
                              (kid, str(tgl), alasan, jenis, kategori, "Proses"))
                    c.execute("UPDATE karyawan SET resign_date=? WHERE id=?", (str(tgl), kid))
                    conn.commit(); st.success("✅ Data resign berhasil ditambahkan!"); st.rerun()

# ==================== KARYAWAN ====================
elif pilihan == "👥 Data Karyawan":
    st.markdown('<div class="main-header"><h1>👥 Data Karyawan</h1></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="instruction-box">
        <b>💡 Panduan CRUD:</b> Klik sel untuk Edit • Pilih baris kiri + Delete untuk Hapus • Klik <b>Simpan</b> di bawah tabel.
    </div>
    """, unsafe_allow_html=True)
    
    render_import_ui("karyawan")
    df = pd.read_sql_query("SELECT * FROM karyawan ORDER BY id DESC", conn)
    render_export_print(df, "karyawan")
    
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Karyawan", type="primary", use_container_width=True):
        save_dataframe_to_db("karyawan", edited)
        st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== ABSENSI ====================
elif pilihan == "📅 Absensi":
    st.markdown('<div class="main-header"><h1>📅 Absensi</h1></div>', unsafe_allow_html=True)
    render_import_ui("absensi")
    df = pd.read_sql_query("SELECT a.*, k.full_name FROM absensi a LEFT JOIN karyawan k ON a.karyawan_id = k.id ORDER BY a.tanggal DESC LIMIT 100", conn)
    render_export_print(df, "absensi")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Absensi", type="primary", use_container_width=True):
        save_dataframe_to_db("absensi", edited); st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== CUTI ====================
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<div class="main-header"><h1>🏖️ Cuti & Izin</h1></div>', unsafe_allow_html=True)
    render_import_ui("cuti")
    df = pd.read_sql_query("SELECT c.*, k.full_name FROM cuti c LEFT JOIN karyawan k ON c.karyawan_id = k.id ORDER BY c.id DESC", conn)
    render_export_print(df, "cuti")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Cuti", type="primary", use_container_width=True):
        save_dataframe_to_db("cuti", edited); st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== PAYROLL ====================
elif pilihan == "💰 Payroll":
    st.markdown('<div class="main-header"><h1>💰 Payroll</h1></div>', unsafe_allow_html=True)
    render_import_ui("payroll")
    df = pd.read_sql_query("SELECT p.*, k.full_name FROM payroll p LEFT JOIN karyawan k ON p.karyawan_id = k.id ORDER BY p.periode DESC", conn)
    render_export_print(df, "payroll")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Payroll", type="primary", use_container_width=True):
        save_dataframe_to_db("payroll", edited); st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== MUTASI & SP ====================
elif pilihan == "🔄 Mutasi, PKWT & SP":
    st.markdown('<div class="main-header"><h1>🔄 Mutasi, PKWT & SP</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Mutasi", "Surat Peringatan (SP)"])
    
    with tab1:
        df_mut = pd.read_sql_query("SELECT * FROM mutasi ORDER BY id DESC", conn)
        render_export_print(df_mut, "mutasi")
        edited_mut = st.data_editor(df_mut, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan Mutasi", type="primary", use_container_width=True):
            save_dataframe_to_db("mutasi", edited_mut); st.success("✅ Perubahan tersimpan!"); st.rerun()
            
    with tab2:
        df_sp = pd.read_sql_query("SELECT * FROM disiplin ORDER BY id DESC", conn)
        render_export_print(df_sp, "disiplin")
        edited_sp = st.data_editor(df_sp, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan SP", type="primary", use_container_width=True):
            save_dataframe_to_db("disiplin", edited_sp); st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== UTILITY ====================
elif pilihan == "💡 Utility Melak":
    st.markdown('<div class="main-header"><h1>💡 Utility Melak</h1></div>', unsafe_allow_html=True)
    render_import_ui("utility")
    df_u = pd.read_sql_query("SELECT * FROM utility ORDER BY tanggal_bayar DESC", conn)
    render_export_print(df_u, "utility")
    edited_u = st.data_editor(df_u, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Utility", type="primary", use_container_width=True):
        save_dataframe_to_db("utility", edited_u); st.success("✅ Perubahan tersimpan!"); st.rerun()

# ==================== PENGATURAN ====================
elif pilihan == "⚙️ Pengaturan & Log":
    st.markdown('<div class="main-header"><h1>⚙️ Pengaturan & Log</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["User Management", "Log Aktivitas"])
    with tab1:
        df_usr = pd.read_sql_query("SELECT id, username, nama_lengkap, role FROM users", conn)
        render_export_print(df_usr, "users")
        edited_usr = st.data_editor(df_usr, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan User", type="primary"):
            save_dataframe_to_db("users", edited_usr); st.success("✅ Tersimpan!"); st.rerun()
    with tab2:
        df_log = pd.read_sql_query("SELECT * FROM log_aktivitas ORDER BY id DESC LIMIT 100", conn)
        st.dataframe(df_log, use_container_width=True, hide_index=True)
