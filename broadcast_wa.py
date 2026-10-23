import csv
import os
import re
import time
import random
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ================== KONFIGURASI ==================
CSV_FILE = "kandidat_baru.csv"
LOG_FILE = "broadcast_log.csv"
# Sesuaikan path Chrome profile Anda (Windows contoh di bawah)
CHROME_PROFILE = os.path.expandvars(
    r"%LOCALAPPDATA%\Google\Chrome\User Data"
)
PROFILE_DIR = "Default"

TEMPLATE = """Selamat siang Bapak {nama},

Perkenalkan saya Okana dari PT. UNITED EQUIPMENT INDONESIA – Melak Reps.

Kami informasikan bahwa data Bapak tercatat dalam proses rekrutmen posisi {posisi} dengan status Baru. Sehubungan dengan proses administrasi dan pencocokan jadwal interview, kami memerlukan alamat domisili terbaru Bapak.

Mohon kesediaannya untuk membalas pesan ini dengan format berikut:

Nama | Kota | Kecamatan | Alamat lengkap

Contoh:
Alvin Willynata | Samarinda | Samarinda Ulu | Jl. Contoh No. 10, RT 01/RW 02

Balasan Bapak akan kami gunakan untuk keperluan administrasi rekrutmen dan pencocokan jadwal interview. Terima kasih atas perhatian dan kerja samanya.

Hormat saya,
Okana
PT. UNITED EQUIPMENT INDONESIA – Melak Reps."""

DELAY_MIN = 25   # detik
DELAY_MAX = 45   # detik
# =================================================

def normalize_phone(raw: str) -> str:
    """Ubah nomor Indonesia ke format 62xxx, ambil nomor pertama jika ada '/'."""
    if not raw:
        return ""
    raw = raw.split("/")[0].strip()           # ambil nomor pertama
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    elif not digits.startswith("62"):
        digits = "62" + digits
    return digits

def load_contacts(path):
    seen, out = set(), []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (r["nama"].strip().lower(), r["telepon"].strip())
            if key in seen:
                continue
            seen.add(key)
            phone = normalize_phone(r["telepon"])
            if not phone:
                print(f"  SKIP (tanpa nomor): {r['nama']}")
                continue
            out.append({
                "nama": r["nama"].strip(),
                "telepon": phone,
                "posisi": (r["posisi"].strip()
                           or "Mechanic Alat Berat Area Kalimantan"),
            })
    return out

def main():
    opts = Options()
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    opts.add_argument(f"--profile-directory={PROFILE_DIR}")
    opts.add_experimental_option("detach", True)
    opts.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=opts)
    driver.get("https://web.whatsapp.com")
    input(">>> Login WhatsApp Web, tunggu sampai muncul chat, lalu tekan ENTER...")

    contacts = load_contacts(CSV_FILE)
    print(f"Total kandidat akan dikirimi: {len(contacts)}\n")

    log = []
    for i, c in enumerate(contacts, 1):
        nama, phone, posisi = c["nama"], c["telepon"], c["posisi"]
        pesan = TEMPLATE.format(nama=nama, posisi=posisi)

        url = (
            f"https://web.whatsapp.com/send?phone={phone}"
            f"&text={urllib.parse.quote(pesan)}"
        )
        driver.get(url)
        time.sleep(5)   # beri waktu load

        try:
            # Tombol kirim dengan data-icon="send"
            send_btn = WebDriverWait(driver, 40).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'span[data-icon="send"]')
                )
            )
            time.sleep(random.uniform(1.5, 3))
            send_btn.click()
            print(f"[{i}/{len(contacts)}] ✓ TERKIRIM → {nama} ({phone})")
            log.append([nama, phone, "TERKIRIM", datetime.now().isoformat()])
        except Exception as e:
            print(f"[{i}/{len(contacts)}] ✗ GAGAL → {nama} ({phone}): {e}")
            log.append([nama, phone, f"GAGAL: {e}", datetime.now().isoformat()])

        if i < len(contacts):
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"     tunggu {delay:.0f} detik...")
            time.sleep(delay)

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nama", "telepon", "status", "waktu"])
        w.writerows(log)

    print(f"\nSelesai. Log tersimpan di {LOG_FILE}")
    driver.quit()

if __name__ == "__main__":
    main()
