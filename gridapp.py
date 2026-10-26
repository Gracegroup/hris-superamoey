from flask import Flask, render_template, request, jsonify
from scraper_uniquip import scrape_uniquip
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def do_scrape():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username dan Password wajib diisi!"}), 400

    try:
        # Panggil fungsi scraper
        df = scrape_uniquip(username, password)
        
        # Ubah DataFrame menjadi format JSON untuk dikirim ke frontend
        # (Kita batasi 100 baris agar tidak berat di browser)
        hasil_json = df.head(100).to_dict(orient='records')
        
        return jsonify({
            "status": "success",
            "total_data": len(df),
            "data": hasil_json
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Aplikasi berjalan di http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
