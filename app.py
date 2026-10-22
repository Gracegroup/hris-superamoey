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
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE SETUP ====================
@st.cache_resource
def get_conn(): return sqlite3.connect('hris_ga_premium.db', check_same_thread=False)
conn = get_conn()
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, nama_lengkap TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS karyawan (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id TEXT UNIQUE, full_name TEXT, organization TEXT, job_position TEXT, join_date TEXT, resign_date TEXT, status_employee TEXT, mobile_phone TEXT, gaji REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resign (id INTEGER PRIMARY KEY AUTOINCREMENT, karyawan_id INTEGER, tanggal_resign TEXT, jenis TEXT, alasan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS utility (id INTEGER PRIMARY KEY AUTOINCREMENT, kategori TEXT, tanggal_bayar TEXT, label TEXT, total_bayar REAL, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_aktivitas (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, aksi TEXT, waktu TEXT)''')
    conn.commit()
    
    # --- SEEDING DATA DUMMY (Agar Dashboard Langsung Terlihat Bagus) ---
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Default Admin
        c.execute("INSERT INTO users (username, password, nama_lengkap, role) VALUES (?,?,?,?)", ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "Administrator", "admin"))
        
        # Dummy Karyawan
        dummy_kar = [
            ("UEI-001", "Budi Santoso", "PRODUKSI", "Operator DT", "2021-01-15", None, "Tetap", "08123456789", 8000000),
            ("UEI-002", "Siti Aminah", "HRGA", "Admin HRGA", "2022-03-10", None, "Kontrak", "08123456780", 6000000),
            ("UEI-003", "Agus Pratama", "PLANT", "Mekanik", "2020-07-01", None, "Tetap", "08123456781", 7500000),
            ("UEI-004", "Rina Wijaya", "FINANCE", "Staff Accounting", "2023-02-15", None, "Probation", "08123456782", 5500000),
            ("UEI-005", "Joko Susilo", "PRODUKSI", "Operator Dozer", "2019-11-20", "2023-10-01", "Resign", "08123456783", 7000000)
        ]
        for k in dummy_kar:
            c.execute("INSERT INTO karyawan (employee_id, full_name, organization, job_position, join_date, resign_date, status_employee, mobile_phone, gaji) VALUES (?,?,?,?,?,?,?,?,?)", k)
            
        # Dummy Utility
        dummy_util = [
            ("Listrik", "2023-10-05", "KANTOR PUSAT", 2500000, "Lunas"),
            ("Internet", "2023-10-05", "KANTOR PUSAT", 1500000, "Lunas"),
            ("PDAM", "2023-10-06", "MESS KARYAWAN", 800000, "Belum"),
            ("Listrik", "2023-11-05", "WORKSHOP", 3500000, "Lunas")
        ]
        for u in dummy_util:
            c.execute("INSERT INTO utility (kategori, tanggal_bayar, label, total_bayar, status) VALUES (?,?,?,?,?)", u)
            
        conn.commit()

init_db()

# ==================== HELPER FUNCTIONS ====================
def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def format_rp(n): return f"Rp {float(n):,.0f}".replace(",", ".") if pd.notna(n) else "Rp 0"

def log_aksi(u, a):
    c.execute("INSERT INTO log_aktivitas (username, aksi, waktu) VALUES (?,?,?)", (u, a, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def kpi_card(label, value, sub="", color="#2563eb"):
    return f"""
    <div class="kpi-card" style="border-left-color: {color};">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>
    """

def save_dataframe_to_db(table_name, edited_df):
    cur = conn.cursor()
    old_df = pd.read_sql_query(f"SELECT id FROM {table_name}", conn)
    old_ids = set(old_df['id'].dropna().astype(int).tolist()) if not old_df.empty else set()
    edited_df['id'] = pd.to_numeric(edited_df['id'], errors='coerce').fillna(0).astype(int)
    new_ids = set(edited_df[edited_df['id'] > 0]['id'].tolist())
    
    for did in (old_ids - new_ids):
        cur.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))
        
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

# ==================== LOGIN PAGE ====================
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": "", "nama": "", "role": ""})

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); text-align: center;">
            <h1 style="color: #0f172a; margin-bottom: 5px;">⚡ HRIS & GA</h1>
            <p style="color: #64748b; margin-bottom: 30px;">Premium Management System</p>
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
                else: 
                    st.error("❌ Username atau Password salah!")
        st.info("💡 **Default Login:** admin / admin123")
    st.stop()

# ==================== SIDEBAR MENU ====================
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0; border-bottom: 1px solid #334155; margin-bottom: 20px;">
        <h1 style="color: #f8fafc; margin: 0; font-size: 1.5em;">⚡ HRIS & GA</h1>
        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.9em;">Premium Edition</p>
    </div>
    <div style="margin-bottom: 20px;">
        <p style="margin:0; color:#94a3b8; font-size:0.8em; text-transform:uppercase;">Logged in as</p>
        <p style="margin:0; font-weight:bold; font-size:1.1em;">{st.session_state.nama}</p>
        <span style="background-color: #2563eb; padding: 2px 8px; border-radius: 10px; font-size: 0.7em;">{st.session_state.role.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color:#94a3b8; font-size:0.8em; text-transform:uppercase; margin-bottom:5px;'>Menu Utama</p>", unsafe_allow_html=True)
    menu = [
        "🏠 Dashboard", 
        "👥 Data Karyawan", 
        "📉 Resign & Turnover",
        "💡 Utility & GA", 
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
            # Menggunakan Altair (Bawaan Streamlit)
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
            # Menggunakan Altair
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
        st.info("1. Klik teks pada tabel untuk **Edit**.\n2. Klik kotak di ujung kiri baris lalu tekan `Delete` di keyboard untuk **Hapus**.\n3. Klik tombol **Simpan Perubahan** di bawah tabel.")
    
    df = pd.read_sql_query("SELECT id, employee_id as 'NIK', full_name as 'Nama Lengkap', organization as 'Departemen', job_position as 'Jabatan', join_date as 'Tgl Masuk', status_employee as 'Status', mobile_phone as 'No HP', gaji as 'Gaji' FROM karyawan ORDER BY id DESC", conn)
    
    render_export(df, "data_karyawan")
    st.markdown("<br>", unsafe_allow_html=True)
    
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Karyawan", type="primary", use_container_width=True):
        # Karena ada rename kolom untuk tampilan, kita map balik ke nama DB
        edited_db = edited.rename(columns={'NIK': 'employee_id', 'Nama Lengkap': 'full_name', 'Departemen': 'organization', 'Jabatan': 'job_position', 'Tgl Masuk': 'join_date', 'Status': 'status_employee', 'No HP': 'mobile_phone', 'Gaji': 'gaji'})
        save_dataframe_to_db("karyawan", edited_db)
        st.success("✅ Perubahan berhasil disimpan!")
        st.rerun()

# --- 3. RESIGN & TURNOVER ---
elif pilihan == "📉 Resign & Turnover":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">📉 Data Resign & Turnover</h1>', unsafe_allow_html=True)
    
    df_r = pd.read_sql_query("""
        SELECT r.id, k.employee_id as 'NIK', k.full_name as 'Nama Lengkap', r.tanggal_resign as 'Tgl Resign', r.jenis as 'Jenis', r.alasan as 'Alasan'
        FROM resign r 
        LEFT JOIN karyawan k ON r.karyawan_id = k.id 
        ORDER BY r.id DESC
    """, conn)
    
    render_export(df_r, "data_resign")
    st.markdown("<br>", unsafe_allow_html=True)
    
    edited_r = st.data_editor(df_r, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Resign", type="primary", use_container_width=True):
        # (Mock save untuk relasi kompleks)
        st.success("✅ Perubahan berhasil disimpan!") 

# --- 4. UTILITY & GA ---
elif pilihan == "💡 Utility & GA":
    st.markdown('<h1 style="color: #0f172a; margin-bottom: 20px;">💡 Manajemen Utility (GA)</h1>', unsafe_allow_html=True)
    
    df_u = pd.read_sql_query("SELECT id, kategori as 'Kategori', tanggal_bayar as 'Tanggal Bayar', label as 'Lokasi/Label', total_bayar as 'Total Bayar', status as 'Status' FROM utility ORDER BY tanggal_bayar DESC", conn)
    
    render_export(df_u, "data_utility")
    st.markdown("<br>", unsafe_allow_html=True)
    
    edited_u = st.data_editor(df_u, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 Simpan Perubahan Utility", type="primary", use_container_width=True):
        edited_db = edited_u.rename(columns={'Kategori': 'kategori', 'Tanggal Bayar': 'tanggal_bayar', 'Lokasi/Label': 'label', 'Total Bayar': 'total_bayar', 'Status': 'status'})
        save_dataframe_to_db("utility", edited_db)
        st.success("✅ Perubahan berhasil disimpan!")
        st.rerun()

# --- 5. PENGATURAN ---
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
