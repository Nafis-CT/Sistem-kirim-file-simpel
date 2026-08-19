import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "kunci_rahasia_anda"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Buat folder uploads jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inisialisasi Database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Hapus tulisan PRIMARY KEY dari id
    c.execute('''CREATE TABLE IF NOT EXISTS uploads 
                 (id TEXT, nama TEXT, no_wa TEXT, filename TEXT, upload_date TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Fungsi Auto-Delete (4 Hari)
def delete_old_files():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    four_days_ago = datetime.now() - timedelta(days=4)
    c.execute("SELECT id, filename FROM uploads WHERE upload_date < ?", (four_days_ago,))
    old_files = c.fetchall()
    
    for file in old_files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file[1])
        if os.path.exists(file_path):
            os.remove(file_path)
        c.execute("DELETE FROM uploads WHERE id = ?", (file[0],))
    conn.commit()
    conn.close()

# Penjadwal berjalan setiap hari untuk mengecek file lama
scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_old_files, trigger="interval", days=1)
scheduler.start()

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Gunakan .strip() untuk menghilangkan spasi tidak sengaja di awal/akhir nama
        nama = request.form['nama'].strip() 
        no_wa = request.form.get('no_wa', '').strip()
        
        files = request.files.getlist('file') 
        
        if files and nama:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            
            # 1. CEK DATABASE: Apakah nama ini sudah ada sebelumnya?
            # Kita menggunakan lower() agar "Budi" dan "budi" dianggap orang yang sama
            c.execute("SELECT id FROM uploads WHERE LOWER(nama) = LOWER(?) LIMIT 1", (nama,))
            pengguna_lama = c.fetchone()
            
            if pengguna_lama:
                # Jika nama sudah ada, gunakan ID lama miliknya
                user_id = pengguna_lama[0]
            else:
                # Jika ini nama baru, buat ID unik baru
                user_id = str(uuid.uuid4())[:8]
            
            # 2. PROSES FILE: Simpan file dengan ID yang sudah ditentukan di atas
            for file in files:
                if file and file.filename: 
                    filename = secure_filename(file.filename)
                    
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    c.execute("INSERT INTO uploads VALUES (?, ?, ?, ?, ?)", 
                              (user_id, nama, no_wa, filename, datetime.now()))
            
            conn.commit()
            conn.close()
            
            return render_template('index.html', pesan="Semua file berhasil dikirim! Terima kasih.")
            
    return render_template('index.html')

@app.route('/admin')
def admin():
    # KODE BARU: Cek alamat IP pengunjung
    # 127.0.0.1 dan ::1 adalah alamat IP khusus untuk "komputer ini sendiri" (Localhost)
    
    if not request.host.startswith('localhost') and not request.host.startswith('127.0.0.1'):
        return "Akses Ditolak: Halaman ini hanya bisa diakses dari komputer server (Admin).", 403

    # Mengambil kata kunci pencarian dari URL (jika ada)
    kata_kunci = request.args.get('q', '')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
   # '%d-%m-%Y %H:%M' akan menghasilkan format: Hari-Bulan-Tahun Jam:Menit (Contoh: 28-06-2026 08:32)
    if kata_kunci:
        search_term = f"%{kata_kunci}%"
        c.execute('''SELECT id, nama, no_wa, filename, strftime('%d-%m-%Y %H:%M', upload_date) 
                     FROM uploads 
                     WHERE id LIKE ? OR nama LIKE ? OR no_wa LIKE ? 
                     ORDER BY upload_date DESC''', (search_term, search_term, search_term))
    else:
        c.execute('''SELECT id, nama, no_wa, filename, strftime('%d-%m-%Y %H:%M', upload_date) 
                     FROM uploads 
                     ORDER BY upload_date DESC''')
        
    data = c.fetchall()
    conn.close()
    
    return render_template('admin.html', data=data, q=kata_kunci)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete/<id>/<filename>')
def delete_file(id, filename):
    # Hapus file dari sistem komputer
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Hapus dari database (berdasarkan ID dan Filename)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM uploads WHERE id = ? AND filename = ?", (id, filename))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

@app.route('/delete_all')
def delete_all():
    # 1. KODE KEAMANAN: Pastikan hanya Admin yang bisa mengakses fitur ini
    if not request.host.startswith('localhost') and not request.host.startswith('127.0.0.1'):
        return "Akses Ditolak.", 403

    # 2. HAPUS SEMUA FILE FISIK: Looping untuk menghapus isi folder 'uploads'
    folder_path = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # 3. HAPUS SEMUA DATA DATABASE: Mengosongkan tabel uploads
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM uploads")
    conn.commit()
    conn.close()
    
    # 4. Kembali ke halaman admin
    return redirect(url_for('admin'))

@app.route('/open_folder')
def open_folder():
    # 1. Pastikan hanya Admin dari komputer server yang bisa menekan tombol ini
    if not request.host.startswith('localhost') and not request.host.startswith('127.0.0.1'):
        return "Akses Ditolak.", 403

    # 2. Dapatkan lokasi asli (path) dari folder uploads di Windows
    folder_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
    
    # 3. Perintah khusus Windows untuk membuka File Explorer
    try:
        os.startfile(folder_path)
    except Exception as e:
        print(f"Gagal membuka folder: {e}")
        
    # 4. Kembali ke halaman admin tanpa mengubah apa-apa di layar
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)