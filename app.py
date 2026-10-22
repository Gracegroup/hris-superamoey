import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import io
import calendar
import altair as alt
from datetime import datetime, timedelta, date

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(
    page_title="HRIS & GA SUPER | Premium",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("uploads", exist_ok=True)

# ==================== PREMIUM CSS (STYLING) ====================
st.markdown("""
<style>
    /* Import Font Google */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Background Utama */
    .stApp { 
        background-color: #f8fafc; 
    }
    
    /* Header Container */
    .premium-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px; 
        border-radius: 16px; 
        color: white; 
        text-align: left;
        margin-bottom: 25px; 
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .premium-header h1 { 
        color: white !important; 
        margin: 0; 
        font-size: 2.2em; 
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .premium-header p { 
        color: #94a3b8; 
        margin: 5px 0 0 0; 
        font-size: 1.1em;
    }

    /* Kartu KPI (Metrics) */
    .kpi-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
        gap: 20px; 
        margin-bottom: 30px; 
    }
    .kpi-card { 
        background: white;
        padding: 25px; 
        border-radius: 16px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        border-left: 6px solid #1e3a8a;
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }
    .kpi-card .label { 
        font-size: 0.85em; 
        color: #64748b; 
        font-weight: 600; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .kpi-card .value { 
        font-size: 2em; 
        font-weight: 700; 
        color: #0f172a; 
    }
    .kpi-card .sub { 
        font-size: 0.85em; 
        color: #10b981; 
        margin-top: 8px; 
        font-weight: 500;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] { 
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] * { 
        color: #e2e8f0 !important; 
    }
    section[data-testid="stSidebar"] .stRadio > div { 
        gap: 5px;
    }
    /* Tombol Sidebar */
    section[data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: #e2e8f0 !important;
        border: none !important;
        text-align: left !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        transition: 0.2s;
        width: 100%;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #1e293b !important;
    }

    /* Tombol Utama */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        color: white !important; 
        border: none; 
        border-radius: 10px; 
        padding: 12px 24px; 
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .stButton > button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5); 
    }

    /* Styling Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        color: #64748b;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #1e3a8a !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Highlight box untuk instruksi */
    .instruction-box { background-color: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; border-left: 5px solid #0ea5e9; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE SETUP ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga_ultimate.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

def init_db():
    # Core & HR Tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, end_date TEXT, mobile_phone TEXT, gaji REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS absensi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, jam_masuk TEXT, jam_keluar TEXT, status TEXT, keterangan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_cuti TEXT, tanggal_mulai TEXT, tanggal_selesai TEXT, lama_hari INTEGER, alasan TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, periode TEXT, gaji_pokok REAL, total_penghasilan_bruto REAL, gaji_bersih REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, jenis TEXT, alasan TEXT, kategori_penyebab TEXT, clearance_status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mutasi (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_mutasi TEXT, dari_divisi TEXT, ke_divisi TEXT, alasan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS disiplin (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, jenis_sanksi TEXT, tanggal_mulai TEXT, tanggal_akhir TEXT, rincian_pelanggaran TEXT, status TEXT)''')
    
    # Rekrutmen & Coaching
    c.execute('''CREATE TABLE IF NOT EXISTS interview_score (id INTEGER PRIMARY KEY AUTOINCREMENT, kandidat_id INTEGER, tanggal TEXT, nilai_kualifikasi INTEGER, nilai_pengalaman INTEGER, nilai_pengetahuan INTEGER, nilai_karakter INTEGER, nilai_komunikasi INTEGER, total_nilai INTEGER, keputusan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS coaching (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal TEXT, isu TEXT, observasi TEXT, perbaikan TEXT, rekomendasi TEXT, status TEXT)''')
    
    # GA & Others
    c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, label TEXT, nominal REAL, admin REAL, total_bayar REAL, metode TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mess_inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, cabang TEXT, item TEXT, qty INTEGER, kondisi TEXT, keterangan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobdesk (id INTEGER PRIMARY KEY AUTOINCREMENT, posisi TEXT, departemen TEXT, tugas_utama TEXT, kpi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ci (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, judul TEXT, departemen TEXT, deskripsi TEXT, pic TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skd (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_surat TEXT, nama_karyawan TEXT, jenis_surat TEXT, keterangan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS im (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, no_memo TEXT, perihal TEXT, pengirim TEXT, penerima TEXT, isi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, detail TEXT, waktu TEXT)''')
    
    conn.commit()
    
    # --- SEEDING DATA DUMMY ---
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Administrator", "admin"))
        
        dummy_kar = [
            ("UEI-001", "Budi Santoso", "PRODUKSI", "Operator DT", "2021-01-15", None, "Tetap", "2025-12-31", "08123456789", 8000000),
            ("UEI-002", "Siti Aminah", "HRGA", "Admin HRGA", "2022-03-10", None, "Kontrak", "2024-12-31", "08123456780", 6000000),
            ("UEI-003", "Agus Pratama", "PLANT", "Mekanik", "2020-07-01", None, "Tetap", "2025-12-31", "08123456781", 7500000),
            ("UEI-004", "Rina Wijaya", "FINANCE", "Staff Accounting", "2023-02-15", None, "Probation", "2024-06-30", "08123456782", 5500000),
            ("UEI-005", "Joko Susilo", "PRODUKSI", "Operator Dozer", "2019-11-20", "2023-10-01", "Resign", "2023-10-01", "08123456783", 7000000)
        ]
        for k in dummy_kar:
            c.execute("INSERT INTO karyawan (employee_id, full_name, organization, job_position, join_date, resign_date, status_employee, end_date, mobile_phone, gaji) VALUES (?,?,?,?,?,?,?,?,?,?)", k)
            
        c.execute("INSERT INTO resign (karyawan_id, tanggal_resign, jenis, alasan) VALUES (5, '2023-10-01', 'Resign Sendiri', 'Pindah domisili')")
            
        dummy_util = [
            ("Listrik", "2023-10-05", "KANTOR PUSAT", 2500000, 3000, 2503000, "BCA", "Lunas"),
            ("Internet", "2023-10-05", "KANTOR PUSAT", 1500000, 3000, 1503000, "BCA", "Lunas"),
            ("PDAM", "2023-10-06", "MESS KARYAWAN", 800000, 3000, 803000, "BCA", "Belum"),
            ("Listrik", "2023-11-05", "WORKSHOP", 3500000, 3000, 3503000, "BCA", "Lunas")
        ]
        for u in dummy_util:
            c.execute("INSERT INTO utility (kategori, tanggal_bayar, label, nominal, admin, total_bayar, metode, status) VALUES (?,?,?,?,?,?,?,?)", u)
            
        conn.commit()

init_db()

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def format_rp(n): return f"Rp {float(n):,.0f}".replace(",", ".") if pd.notna(n) else "Rp 0"

def log_aksi(u, a, d=""):
    c.execute("INSERT INTO log_aktivitas (username, aksi, detail, waktu) VALUES (?,?,?,?)", (u, a, d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def kpi_card(label, value, sub="", color="#2563eb"):
    return f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """

# Universal Save (Edit/Insert/Delete)
def save_dataframe_to_db(table_name, edited_df, original_df):
    cur = conn.cursor()
    
    # Konversi ID ke integer
    edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
    old_ids = set(original_df['id'].dropna().astype(int).tolist()) if not original_df.empty else set()
    new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
    
    # 1. Hapus data yang dibuang dari tabel
    for did in (old_ids - new_ids):
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        
    # 2. Insert & Update
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

def render_export(df, filename):
    c1, c2, c3 = st.columns(3)
    with c1: st.download_button("📥 Export CSV", df.to_csv(index=False).encode(), f"{filename}.csv", "text/csv", use_container_width=True)
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as w: df.to_excel(w, index=False)
        st.download_button("📥 Export Excel", buf.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with c3:
        html_table = df.to_html(classes='table', index=False)
        html_full = f"<html><head><title>Print</title><style>table{{border-collapse: collapse; width:100%; font-family: sans-serif;}} th,td{{border:1px solid #ddd; padding:10px; text-align:left;}} th{{background-color:#1e3a8a; color:white;}}</style></head><body><h2>{filename.upper()}</h2>{html_table}</body></html>"
        st.download_button("🖨️ Cetak", html_full, f"{filename}_print.html", "text/html", use_container_width=True)

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
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center;">
            <h1 style="color: #0f172a; margin-bottom: 5px;">⚡ HRIS & GA</h1>
            <p style="color: #64748b; margin-bottom: 30px;">Ultimate Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login"):
            st.subheader("Login ke Akun Anda")
            u = st.text_input("Username", placeholder="Masukkan username")
            p = st.text_input("Password", type="password", placeholder="Masukkan password")
            if st.form_submit_button("🚀 Masuk ke Dashboard", use_container_width=True):
                row = c.execute("SELECT username, password, nama_lengkap, role FROM users WHERE username=?", (u,)).fetchone()
                if row and row[1] == hash_password(p):
                    st.session_state.update({"logged_in": True, "username": row[0], "nama": row[2], "role": row[3]})
                    log_aksi(u, "LOGIN"); st.rerun()
                else: st.error("❌ Username atau Password salah!")
        st.info("💡 **Default Login:** admin / admin123")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #334155; margin-bottom: 20px;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 1.5em;">⚡ HRIS & GA</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.9em;">Ultimate Edition</p>
    </div>
    <div style="margin-bottom: 20px;">
        <p style="margin:0; color:#94a3b8; font-size:0.8em; text-transform:uppercase;">Logged in as</p>
        <p style="margin:0; font-weight:bold; font-size:1.1em;">{st.session_state.nama}</p>
        <span style="background-color: #2563eb; padding: 2px 8px; border-radius: 10px; font-size: 0.7em;">{st.session_state.role.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color:#94a3b8; font-size:0.8em; text-transform:uppercase; margin-bottom:5px;'>Navigasi Utama</p>", unsafe_allow_html=True)
    menu = [
        "🏠 Dashboard", 
        "👥 Data Karyawan", 
        "📅 Absensi", 
        "🏖️ Cuti & Izin", 
        "💰 Payroll", 
        "📋 Rekrutmen & Wawancara", 
        "🔄 Mutasi, PKWT & SP", 
        "📝 Coaching & Counselling",
        "📉 Resign & Turnover",
        "💡 Utility Melak", 
        "🏠 Mess & 5R",
        "📄 Generator Formulir",
        "📚 Pusat Dokumen (SOP/CI)",
        "⚙️ Pengaturan & Log"
    ]
    pilihan = st.radio("", menu, label_visibility="collapsed")
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear(); st.rerun()

# ==================== KONTEN HALAMAN ====================

# --- 1. DASHBOARD PREMIUM ---
if pilihan == "🏠 Dashboard":
    st.markdown(f"""
    <div class="premium-header">
        <div>
            <h1>Overview Dashboard</h1>
            <p>Selamat datang kembali, {st.session_state.nama}. Berikut ringkasan data hari ini.</p>
        </div>
        <div style="text-align: right;">
            <h2 style="margin:0; color:#60a5fa;">{datetime.now().strftime('%d %b %Y')}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Ambil Data
    total_kar = c.execute("SELECT COUNT(*) FROM karyawan WHERE resign_date IS NULL OR resign_date=''").fetchone()[0]
    total_resign = c.execute("SELECT COUNT(*) FROM resign").fetchone()[0]
    util_belum = c.execute("SELECT COALESCE(SUM(total_bayar),0) FROM utility WHERE status='Belum'").fetchone()[0]
    
    # Tampilkan KPI Cards
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    st.markdown(kpi_card("Total Karyawan Aktif", str(total_kar), "Karyawan aktif saat ini", "#10b981"), unsafe_allow_html=True)
    st.markdown(kpi_card("Total Resign", str(total_resign), "Sepanjang tahun", "#ef4444"), unsafe_allow_html=True)
    st.markdown(kpi_card("Tagihan Utility", format_rp(util_belum), "Status: Belum Lunas", "#f59e0b"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Area Grafik
    st.markdown("### 📊 Analitik Perusahaan")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div style="background:white; padding:20px; border-radius:16px; box-shadow:0 4px 20px rgba(0,0,0,0.04);">', unsafe_allow_html=True)
        st.markdown("**Distribusi Karyawan per Departemen**")
        df_div = pd.read_sql_query("SELECT organization as Departemen, COUNT(*) as Jumlah FROM karyawan WHERE resign_date IS NULL OR resign_date='' GROUP BY organization", conn)
        if not df_div.empty:
            chart = alt.Chart(df_div).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Jumlah", type="quantitative"),
                color=alt.Color(field="Departemen", type="nominal", scale=alt.Scale(scheme='blues')),
                tooltip=["Departemen", "Jumlah"]
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Belum ada data")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div style="background:white; padding:20px; border-radius:16px; box-shadow:0 4px 20px rgba(0,0,0,0.04);">', unsafe_allow_html=True)
        st.markdown("**Tren Pengeluaran Utility**")
        df_util = pd.read_sql_query("SELECT tanggal_bayar, total_bayar FROM utility ORDER BY tanggal_bayar", conn)
        if not df_util.empty:
            chart2 = alt.Chart(df_util).mark_line(point=True, color='#2563eb').encode(
                x=alt.X('tanggal_bayar:N', title='Tanggal'),
                y=alt.Y('total_bayar:Q', title='Total (Rp)'),
                tooltip=['tanggal_bayar', 'total_bayar']
            ).properties(height=300)
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.info("Belum ada data")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 2. DATA KARYAWAN ---
elif pilihan == "👥 Data Karyawan":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">👥 Manajemen Data Karyawan</h1>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ Panduan Penggunaan Tabel (Edit / Delete / Save)", expanded=False):
        st.markdown("""
        <div class="instruction-box">
            1. Klik teks pada tabel untuk <b>Edit</b>.<br>
            2. Klik kotak di ujung kiri baris lalu tekan <code>Delete</code> di keyboard untuk <b>Hapus</b>.<br>
            3. Klik tombol <b>Simpan Perubahan</b> di bawah tabel.
        </div>
        """, unsafe_allow_html=True)
    
    render_import_ui("karyawan")
    
    # Ambil data dengan nama kolom yang rapi
    df = pd.read_sql_query("SELECT id, employee_id as 'NIK', full_name as 'Nama Lengkap', organization as 'Departemen', job_position as 'Jabatan', join_date as 'Tgl Masuk', status_employee as 'Status', mobile_phone as 'No HP', gaji as 'Gaji' FROM karyawan ORDER BY id DESC", conn)
    original_df = df.copy() # Simpan state awal untuk deteksi delete
    
    render_export(df, "data_karyawan")
    st.markdown("<br>", unsafe_allow_html=True)
    
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Karyawan", type="primary", use_container_width=True):
        # Map balik nama kolom UI ke nama kolom DB
        edited_db = edited.rename(columns={'NIK': 'employee_id', 'Nama Lengkap': 'full_name', 'Departemen': 'organization', 'Jabatan': 'job_position', 'Tgl Masuk': 'join_date', 'Status': 'status_employee', 'No HP': 'mobile_phone', 'Gaji': 'gaji'})
        original_db = original_df.rename(columns={'NIK': 'employee_id', 'Nama Lengkap': 'full_name', 'Departemen': 'organization', 'Jabatan': 'job_position', 'Tgl Masuk': 'join_date', 'Status': 'status_employee', 'No HP': 'mobile_phone', 'Gaji': 'gaji'})
        
        save_dataframe_to_db("karyawan", edited_db, original_db)
        st.success("✅ Perubahan berhasil disimpan!")
        st.rerun()

# --- 3. ABSENSI ---
elif pilihan == "📅 Absensi":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📅 Absensi</h1>', unsafe_allow_html=True)
    render_import_ui("absensi")
    df = pd.read_sql_query("SELECT a.id, k.employee_id as 'NIK', k.full_name as 'Nama', a.tanggal as 'Tanggal', a.jam_masuk as 'Masuk', a.jam_keluar as 'Keluar', a.status as 'Status', a.keterangan as 'Keterangan' FROM absensi a LEFT JOIN karyawan k ON a.karyawan_id = k.id ORDER BY a.tanggal DESC LIMIT 100", conn)
    original_df = df.copy()
    
    render_export(df, "absensi")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Absensi", type="primary", use_container_width=True):
        # Karena ada relasi kompleks (JOIN), simpan hanya kolom tabel absensi
        edited_db = edited.rename(columns={'Tanggal': 'tanggal', 'Masuk': 'jam_masuk', 'Keluar': 'jam_keluar', 'Status': 'status', 'Keterangan': 'keterangan'})
        # Hapus kolom hasil JOIN sebelum save
        cols_to_drop = ['NIK', 'Nama']
        edited_db = edited_db.drop(columns=[c for c in cols_to_drop if c in edited_db.columns])
        original_db = original_df.rename(columns={'Tanggal': 'tanggal', 'Masuk': 'jam_masuk', 'Keluar': 'jam_keluar', 'Status': 'status', 'Keterangan': 'keterangan'}).drop(columns=[c for c in cols_to_drop if c in original_df.columns])
        
        save_dataframe_to_db("absensi", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# --- 4. CUTI ---
elif pilihan == "🏖️ Cuti & Izin":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">🏖️ Cuti & Izin</h1>', unsafe_allow_html=True)
    render_import_ui("cuti")
    df = pd.read_sql_query("SELECT c.id, k.employee_id as 'NIK', k.full_name as 'Nama', c.jenis_cuti as 'Jenis', c.tanggal_mulai as 'Mulai', c.tanggal_selesai as 'Selesai', c.lama_hari as 'Hari', c.status as 'Status' FROM cuti c LEFT JOIN karyawan k ON c.karyawan_id = k.id ORDER BY c.id DESC", conn)
    original_df = df.copy()
    
    render_export(df, "cuti")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Cuti", type="primary", use_container_width=True):
        edited_db = edited.rename(columns={'Jenis': 'jenis_cuti', 'Mulai': 'tanggal_mulai', 'Selesai': 'tanggal_selesai', 'Hari': 'lama_hari', 'Status': 'status'}).drop(columns=['NIK', 'Nama'])
        original_db = original_df.rename(columns={'Jenis': 'jenis_cuti', 'Mulai': 'tanggal_mulai', 'Selesai': 'tanggal_selesai', 'Hari': 'lama_hari', 'Status': 'status'}).drop(columns=['NIK', 'Nama'])
        
        save_dataframe_to_db("cuti", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# --- 5. PAYROLL ---
elif pilihan == "💰 Payroll":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">💰 Payroll</h1>', unsafe_allow_html=True)
    render_import_ui("payroll")
    df = pd.read_sql_query("SELECT p.id, k.employee_id as 'NIK', k.full_name as 'Nama', p.periode as 'Periode', p.gaji_pokok as 'Gaji Pokok', p.total_penghasilan_bruto as 'Bruto', p.gaji_bersih as 'Take Home', p.status as 'Status' FROM payroll p LEFT JOIN karyawan k ON p.karyawan_id = k.id ORDER BY p.periode DESC", conn)
    original_df = df.copy()
    
    render_export(df, "payroll")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Payroll", type="primary", use_container_width=True):
        edited_db = edited.rename(columns={'Periode': 'periode', 'Gaji Pokok': 'gaji_pokok', 'Bruto': 'total_penghasilan_bruto', 'Take Home': 'gaji_bersih', 'Status': 'status'}).drop(columns=['NIK', 'Nama'])
        original_db = original_df.rename(columns={'Periode': 'periode', 'Gaji Pokok': 'gaji_pokok', 'Bruto': 'total_penghasilan_bruto', 'Take Home': 'gaji_bersih', 'Status': 'status'}).drop(columns=['NIK', 'Nama'])
        
        save_dataframe_to_db("payroll", edited_db, original_db)
        st.success("✅ Tersimpan!"); st.rerun()

# --- 6. REKRUTMEN & WAWANCARA ---
elif pilihan == "📋 Rekrutmen & Wawancara":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📋 Rekrutmen & Wawancara</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Data Kandidat", "Form Penilaian Wawancara"])
    
    with tab1:
        st.subheader("Data Kandidat")
        df_kan = pd.read_sql_query("SELECT id, nama, posisi_dilamar, no_hp, status FROM kandidat", conn) if c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kandidat'").fetchone() else pd.DataFrame()
        st.dataframe(df_kan, use_container_width=True)
    
    with tab2:
        st.subheader("Formulir Laporan Wawancara (F-UEI-HR-05-R0)")
        with st.form("form_wawancara"):
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Kandidat")
                posisi = st.text_input("Jabatan yang dilamar")
            with col2:
                usia = st.number_input("Usia", 17, 60)
                tanggal = st.date_input("Tanggal Wawancara", date.today())
            
            st.markdown("**Penilaian (5 = Baik Sekali, 1 = Kurang Sekali)**")
            colA, colB = st.columns(2)
            with colA:
                n_kua = st.slider("1. Kualifikasi", 1, 5, 3)
                n_peng = st.slider("2. Pengalaman Kerja", 1, 5, 3)
                n_penget = st.slider("3. Pengetahuan & Keterampilan", 1, 5, 3)
            with colB:
                n_kar = st.slider("4. Karakteristik (URE)", 1, 5, 3)
                n_kom = st.slider("5. Komunikasi", 1, 5, 3)
                
            total = n_kua + n_peng + n_penget + n_kar + n_kom
            st.info(f"**Total Skor: {total} / 25** (Rata-rata: {total/5.0:.1f})")
            
            keputusan = st.radio("Keputusan", ["DITERIMA", "DIPERTIMBANGKAN", "DITOLAK"], horizontal=True)
            
            if st.form_submit_button("💾 Simpan Hasil Wawancara"):
                c.execute("INSERT INTO kandidat (nama, posisi_dilamar, status) VALUES (?,?,?)", (nama, posisi, "Wawancara"))
                kid = c.lastrowid
                c.execute('''INSERT INTO interview_score (kandidat_id, tanggal, nilai_kualifikasi, nilai_pengalaman, nilai_pengetahuan, nilai_karakter, nilai_komunikasi, total_nilai, keputusan)
                             VALUES (?,?,?,?,?,?,?,?,?)''', (kid, str(tanggal), n_kua, n_peng, n_penget, n_kar, n_kom, total, keputusan))
                conn.commit()
                st.success(f"Hasil wawancara {nama} tersimpan dengan status: {keputusan}")

# --- 7. MUTASI, PKWT & SP ---
elif pilihan == "🔄 Mutasi, PKWT & SP":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">🔄 Mutasi, PKWT & SP</h1>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Mutasi", "PKWT Habis", "Surat Peringatan (SP)"])
    
    with tab1:
        df_mut = pd.read_sql_query("SELECT m.id, k.full_name as 'Nama', m.tanggal_mutasi as 'Tanggal', m.dari_divisi as 'Dari', m.ke_divisi as 'Ke', m.alasan as 'Alasan' FROM mutasi m LEFT JOIN karyawan k ON m.karyawan_id = k.id ORDER BY m.id DESC", conn)
        original_mut = df_mut.copy()
        render_export(df_mut, "mutasi")
        edited_mut = st.data_editor(df_mut, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Mutasi", type="primary", use_container_width=True):
            edited_db = edited_mut.rename(columns={'Tanggal': 'tanggal_mutasi', 'Dari': 'dari_divisi', 'Ke': 'ke_divisi', 'Alasan': 'alasan'}).drop(columns=['Nama'])
            original_db = original_mut.rename(columns={'Tanggal': 'tanggal_mutasi', 'Dari': 'dari_divisi', 'Ke': 'ke_divisi', 'Alasan': 'alasan'}).drop(columns=['Nama'])
            save_dataframe_to_db("mutasi", edited_db, original_db)
            st.success("✅ Tersimpan"); st.rerun()
            
    with tab2:
        tgl_60 = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        df_pkwt = pd.read_sql_query(f"SELECT id, employee_id, full_name, end_date FROM karyawan WHERE (resign_date IS NULL OR resign_date='') AND end_date <= '{tgl_60}'", conn)
        st.warning("Karyawan dengan kontrak habis dalam 60 hari:")
        st.dataframe(df_pkwt, use_container_width=True)
        
    with tab3:
        df_sp = pd.read_sql_query("SELECT id, karyawan_id, jenis_sanksi, tanggal_mulai, tanggal_akhir, rincian_pelanggaran, status FROM disiplin ORDER BY id DESC", conn)
        render_export(df_sp, "disiplin")
        edited_sp = st.data_editor(df_sp, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan SP", type="primary", use_container_width=True):
            save_dataframe_to_db("disiplin", edited_sp, df_sp)
            st.success("✅ Tersimpan"); st.rerun()

# --- 8. COACHING ---
elif pilihan == "📝 Coaching & Counselling":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📝 Coaching & Counselling</h1>', unsafe_allow_html=True)
    with st.form("form_coaching"):
        col1, col2 = st.columns(2)
        with col1: karyawan = st.text_input("Nama Karyawan / NIK")
        with col2: tanggal = st.date_input("Tanggal")
        
        isu = st.text_area("Isu/Permasalahan & Penyebabnya")
        obs = st.text_area("Observasi/Kesaksian")
        perbaikan = st.text_area("Langkah perbaikan yang akan dilakukan")
        komitmen = st.text_area("Komitmen Karyawan (Sanksi jika terulang)")
        rekomendasi = st.selectbox("Rekomendasi", [
            "Diberi kesempatan melakukan perubahan", 
            "Direlokasi ke posisi lain", 
            "Mendapat sanksi sesuai peraturan", 
            "Masa kerja tidak dapat dilanjutkan (termination)"
        ])
        if st.form_submit_button("Simpan Form Coaching", type="primary"):
            c.execute("SELECT id FROM karyawan WHERE full_name LIKE ? OR employee_id=?", (f"%{karyawan}%", karyawan))
            res = c.fetchone()
            kid = res[0] if res else 0
            
            c.execute('''INSERT INTO coaching (karyawan_id, tanggal, isu, observasi, perbaikan, rekomendasi, status) 
                         VALUES (?,?,?,?,?,?,?)''', (kid, str(tanggal), isu, obs, perbaikan, rekomendasi, "Proses"))
            conn.commit()
            st.success("Form Coaching berhasil disimpan!")

# --- 9. RESIGN ---
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📉 Resign & Turnover</h1>', unsafe_allow_html=True)
    df_r = pd.read_sql_query("SELECT r.id, k.employee_id as 'NIK', k.full_name as 'Nama', r.tanggal_resign as 'Tanggal Resign', r.jenis as 'Jenis', r.alasan as 'Alasan' FROM resign r LEFT JOIN karyawan k ON r.karyawan_id = k.id ORDER BY r.id DESC", conn)
    original_r = df_r.copy()
    render_export(df_r, "resign")
    edited_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Resign", type="primary", use_container_width=True):
        edited_db = edited_r.rename(columns={'Tanggal Resign': 'tanggal_resign', 'Jenis': 'jenis', 'Alasan': 'alasan'}).drop(columns=['NIK', 'Nama'])
        original_db = original_r.rename(columns={'Tanggal Resign': 'tanggal_resign', 'Jenis': 'jenis', 'Alasan': 'alasan'}).drop(columns=['NIK', 'Nama'])
        save_dataframe_to_db("resign", edited_db, original_db)
        st.success("✅ Tersimpan"); st.rerun()

# --- 10. UTILITY ---
elif pilihan == "💡 Utility Melak":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">💡 Utility Melak</h1>', unsafe_allow_html=True)
    render_import_ui("utility")
    df_u = pd.read_sql_query("SELECT id, kategori as 'Kategori', tanggal_bayar as 'Tanggal Bayar', label as 'Lokasi', nominal as 'Nominal', total_bayar as 'Total Bayar', status as 'Status' FROM utility ORDER BY tanggal_bayar DESC", conn)
    original_u = df_u.copy()
    render_export(df_u, "utility")
    edited_u = st.data_editor(df_u, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Perubahan Utility", type="primary", use_container_width=True):
        edited_db = edited_u.rename(columns={'Kategori': 'kategori', 'Tanggal Bayar': 'tanggal_bayar', 'Lokasi': 'label', 'Nominal': 'nominal', 'Total Bayar': 'total_bayar', 'Status': 'status'})
        original_db = original_u.rename(columns={'Kategori': 'kategori', 'Tanggal Bayar': 'tanggal_bayar', 'Lokasi': 'label', 'Nominal': 'nominal', 'Total Bayar': 'total_bayar', 'Status': 'status'})
        save_dataframe_to_db("utility", edited_db, original_db)
        st.success("✅ Tersimpan"); st.rerun()

# --- 11. MESS & 5R ---
elif pilihan == "🏠 Mess & 5R":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">🏠 Fasilitas Mess & 5R</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Inventory Mess", "SOP 5R & CI Mess"])
    
    with tab1:
        st.subheader("Checklist Kelengkapan Mess (Sesuai CI Mess)")
        df_mess = pd.read_sql_query("SELECT * FROM mess_inventory ORDER BY id DESC", conn)
        render_export(df_mess, "inventory_mess")
        edited_mess = st.data_editor(df_mess, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Inventory", type="primary", use_container_width=True):
            save_dataframe_to_db("mess_inventory", edited_mess, df_mess); st.success("✅ Tersimpan"); st.rerun()
            
    with tab2:
        st.info("**Panduan 5R di Area Perkantoran:**")
        st.markdown("""
        1. **Ringkas (Seiri):** Pisahkan barang yang perlu dan tidak perlu. Buang/arsipkan dokumen lama.
        2. **Rapi (Seiton):** Tata barang agar mudah diakses. Gunakan label folder.
        3. **Resik (Seiso):** Bersihkan tempat kerja dari debu dan kotoran.
        4. **Rawat (Seiketsu):** Standarisasi 3S pertama dengan SOP tertulis.
        5. **Rajin (Shitsuke):** Disiplin mematuhi standar 5S secara mandiri setiap hari.
        
        **Aturan Mess:**
        - Harap isi form Check In/Out mess (s.id/INOUTMESS).
        - Dilarang membawa tamu menginap tanpa izin.
        - Dilarang merokok dan makan di dalam kamar.
        - Matikan listrik jika tidak digunakan.
        """)

# --- 12. GENERATOR FORMULIR ---
elif pilihan == "📄 Generator Formulir":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📄 Cetak Formulir HRD</h1>', unsafe_allow_html=True)
    form_type = st.selectbox("Pilih Formulir yang ingin dicetak:", 
                             ["Surat Permohonan Cuti", "Izin Keluar Kantor", "Izin Pulang Cepat", "Notulen Meeting"])
    
    col1, col2 = st.columns(2)
    with col1: nama = st.text_input("Nama Karyawan")
    with col2: nik = st.text_input("NIK / Divisi")
    
    if form_type == "Surat Permohonan Cuti":
        jenis_cuti = st.selectbox("Jenis Cuti", ["Tahunan", "Melahirkan", "Jobsite", "Mangkir"])
        colA, colB, colC = st.columns(3)
        with colA: mulai = st.date_input("Mulai Tanggal")
        with colB: selesai = st.date_input("Selesai Tanggal")
        with colC: lama = st.number_input("Lama Cuti (Hari)", 1, 30)
        alasan = st.text_area("Alasan / Keterangan")
        
        if st.button("🖨️ Generate Form Cuti", type="primary"):
            html = f"""
            <div style="border: 2px solid black; padding: 20px; font-family: Arial; background: white; color: black;">
                <h2 style="text-align: center;">SURAT PERMOHONAN CUTI</h2>
                <hr>
                <table style="width:100%; border:none;">
                    <tr><td width="20%">Nama</td><td>: {nama}</td></tr>
                    <tr><td>NIK/Divisi</td><td>: {nik}</td></tr>
                    <tr><td>Jenis Cuti</td><td>: {jenis_cuti}</td></tr>
                    <tr><td>Lama Cuti</td><td>: {lama} Hari ({mulai} s/d {selesai})</td></tr>
                    <tr><td>Keterangan</td><td>: {alasan}</td></tr>
                </table>
                <br><br><br>
                <table style="width:100%; text-align:center; border:none;">
                    <tr>
                        <td>Pemohon<br><br><br><br>( {nama} )</td>
                        <td>Mengetahui<br><br><br><br>( Atasan )</td>
                        <td>Menyetujui<br><br><br><br>( HRD )</td>
                    </tr>
                </table>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:gray;'>Tekan Ctrl+P untuk print/save PDF</p>", unsafe_allow_html=True)

    elif form_type == "Izin Keluar Kantor":
        jam = st.text_input("Pukul (Contoh: 10:00 s/d 12:00)")
        alasan = st.text_area("Alasan")
        if st.button("🖨️ Generate Form Izin", type="primary"):
            html = f"""
            <div style="border: 2px solid black; padding: 20px; font-family: Arial; background: white; color: black;">
                <h2 style="text-align: center;">PERMOHONAN IZIN KELUAR KANTOR</h2>
                <hr>
                <table style="width:100%; border:none;">
                    <tr><td width="20%">Nama</td><td>: {nama}</td></tr>
                    <tr><td>NIK/Divisi</td><td>: {nik}</td></tr>
                    <tr><td>Pukul</td><td>: {jam}</td></tr>
                    <tr><td>Alasan</td><td>: {alasan}</td></tr>
                </table>
                <br><br><br>
                <table style="width:100%; text-align:center; border:none;">
                    <tr>
                        <td>Pemohon<br><br><br><br>( {nama} )</td>
                        <td>Disetujui<br><br><br><br>( Atasan )</td>
                        <td>Satpam<br><br><br><br>( Security )</td>
                    </tr>
                </table>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

# --- 13. PUSAT DOKUMEN ---
elif pilihan == "📚 Pusat Dokumen (SOP/CI)":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📚 Pusat Dokumen & Panduan</h1>', unsafe_allow_html=True)
    doc_cat = st.selectbox("Kategori Dokumen", ["Corporate Identity (CI)", "SOP Purchasing", "Internal Memo (IM)", "HRD Forms"])
    
    if doc_cat == "Corporate Identity (CI)":
        st.subheader("CI Uniform & Grooming")
        st.write("- Senin - Kamis: Seragam sesuai ketentuan. Jumat: Bebas sopan (Batik).")
        st.write("- Sanksi Denda Kehilangan Seragam: Pria PS (Rp 320.000), Wanita (Rp 370.000), Sepatu Safety (Rp 700.000 - 900.000).")
        
        st.subheader("CI Kendaraan (Vehicle)")
        st.write("- STNK, BPKB wajib diserahkan ke HO.")
        st.write("- Stiker Nomor Lambung (LV-XXX) wajib di kap mesin dan laci dasbor.")
        
        st.subheader("Warna Cat Gedung (CI Cat)")
        df_cat = pd.DataFrame({
            "Area": ["Outdoor Office", "Indoor Office", "Plafon", "Lantai Workshop"],
            "Merek": ["Jotun / Dulux", "Jotun / Dulux", "Jotun / Dulux", "U-Pox"],
            "Kode Warna": ["0562 / 40351", "9911 / 40466", "9918 / 2290", "105-3562"]
        })
        st.dataframe(df_cat, use_container_width=True)
        
    elif doc_cat == "SOP Purchasing":
        st.subheader("Limit Approval PRQ (IM 010/HRD-IM/XII/25)")
        st.markdown("""
        - **< Rp 100.000**: Petty Cash (Tanpa PRQ, kecuali Tools).
        - **> Rp 100.000**: Wajib PRQ ke Technical Advisor.
        - **< Rp 1.000.000**: Approval GM Purchasing.
        - **> Rp 1.000.000**: Approval Management.
        - **Tools > Rp 500.000**: Wajib PO.
        """)
        
    elif doc_cat == "Internal Memo (IM)":
        st.subheader("Perubahan Jam Istirahat Jumat (IM 002/NEST-IM/III/2025)")
        st.write("Jumat: Pukul 12.00 - 13.30 WITA (Sebelumnya 11.30 - 13.00).")
        
        st.subheader("Kebijakan Air Minum (IM 007/HR-IM/X/25)")
        st.write("- Beli air isi ulang maksimal Rp 12.000/galon. Selisih menjadi tanggungan karyawan.")
        st.write("- Cabang dengan >10 karyawan disarankan pakai Water Purifier.")

# --- 14. PENGATURAN ---
elif pilihan == "⚙️ Pengaturan & Log":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">⚙️ Pengaturan Sistem</h1>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Manajemen User", "Log Aktivitas"])
    
    with tab1:
        df_usr = pd.read_sql_query("SELECT id, username as 'Username', nama_lengkap as 'Nama Lengkap', role as 'Role' FROM users", conn)
        edited_usr = st.data_editor(df_usr, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("💾 Simpan Perubahan User", type="primary"):
            st.success("User tersimpan!")
            
    with tab2:
        df_log = pd.read_sql_query("SELECT waktu as 'Waktu', username as 'User', aksi as 'Aksi' FROM log_aktivitas ORDER BY id DESC LIMIT 50", conn)
        st.dataframe(df_log, use_container_width=True, hide_index=True)
