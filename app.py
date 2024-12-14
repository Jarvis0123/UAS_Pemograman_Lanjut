from itertools import product
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
import urllib.parse
from flask_session import Session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'KUNCIRAHASIA'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Fungsi untuk menghash password menggunakan SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Membuat koneksi ke database SQLite
def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/', methods=['GET', 'POST'])

# Route untuk halaman register (pembuatan akun)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = 'user'  # Default role untuk pengguna biasa

        # Validasi password
        if password != confirm_password:
            flash('Password dan Konfirmasi Password tidak cocok! Pastikan kedua password sama.', 'danger')
            return redirect(url_for('register'))

        # Validasi panjang password (contoh: minimal 8 karakter)
        if len(password) < 8:
            flash('Password terlalu pendek! Pastikan panjang password minimal 8 karakter.', 'danger')
            return redirect(url_for('register'))

        # Menghash password
        hashed_password = hash_password(password)

        try:
            conn = get_db_connection()
            # Cek jika username sudah ada di database
            existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                flash('Username sudah ada. Silakan pilih username lain.', 'danger')
                return redirect(url_for('register'))

            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                         (username, hashed_password, role))
            conn.commit()
            conn.close()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Terjadi kesalahan dalam proses pendaftaran. Silakan coba lagi.', 'danger')

    return render_template('register.html')
# Route untuk halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and user['password'] == hashed_password:
            # Menyimpan data ke session
            session['username'] = user['username']
            session['role'] = user['role']  # Role: admin/user
            flash('Login berhasil! Selamat datang.', 'success')
            return redirect(url_for('dashboard' if session['role'] == 'user' else 'admin_dashboard'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

# Route untuk dashboard setelah berhasil login
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Harap login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))
    
    if session['role'] == 'user':
        # Data khusus untuk user
        return render_template('dashboard.html', username=session['username'])
    elif session['role'] == 'admin':
        # Alihkan ke dashboard admin
        return redirect(url_for('admin_dashboard'))

# Route untuk halaman produk dengan fitur pencarian dan filter
@app.route('/products', methods=['GET', 'POST'])
def products():
    search_query = request.args.get('search', '')
    filter_brand = request.args.get('brand', '')
    sort_by = request.args.get('sort', 'name')  # Menambahkan fitur sorting

    conn = get_db_connection()

    query = 'SELECT * FROM products WHERE 1=1'
    params = []

    if search_query:
        query += ' AND name LIKE ?'
        params.append('%' + search_query + '%')

    if filter_brand:
        query += ' AND brand = ?'
        params.append(filter_brand)

    query += f' ORDER BY {sort_by}'  # Sorting berdasarkan nama atau harga
    products = conn.execute(query, params).fetchall()

    brands = conn.execute('SELECT DISTINCT brand FROM products').fetchall()
    conn.close()

    return render_template('products.html', products=products, brands=brands, search_query=search_query, filter_brand=filter_brand, sort_by=sort_by)


# Route untuk detail produk
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if product:
        return render_template('product_detail.html', product=product)
    else:
        flash('Produk tidak ditemukan!', 'danger')
        return redirect(url_for('products'))

# Route untuk halaman pemesanan
@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        name = request.form['name']
        product_id = request.form['product_id']
        quantity = request.form['quantity']

        # Validasi input
        if not name or not product_id or not quantity.isdigit():
            flash('Data yang Anda masukkan tidak valid! Pastikan semua kolom terisi dengan benar.', 'danger')
            return redirect(url_for('order'))

        conn = get_db_connection()
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        conn.close()

        # Cek jika produk ditemukan
        if product:
            product_name = product['name']
            product_price = product['price']
            total_price = product_price * int(quantity)

            # Menyusun pesan untuk WhatsApp
            message = f"Pesanan Baru:\nNama: {name}\nProduk: {product_name}\nJumlah: {quantity}\nTotal Harga: Rp {total_price}"
            wa_phone_number = "+6285228820207"  # Ganti dengan nomor WhatsApp penjual
            wa_url = f"https://wa.me/{wa_phone_number}?text={urllib.parse.quote(message)}"

            flash('Pesanan berhasil dibuat! Mengarahkan ke WhatsApp...', 'success')
            return redirect(wa_url)
        else:
            flash('Produk tidak ditemukan! Pastikan ID produk benar.', 'danger')

    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('order.html', products=products)


@app.route('/about')
def about():
    return render_template('about.html')

# Decorator untuk memastikan hanya admin yang bisa mengakses halaman tertentu
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['role'] != 'admin':
            flash('Akses ditolak, hanya admin yang bisa mengakses halaman ini.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route untuk halaman dashboard admin
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

    # Route untuk menambah produk (Hanya Admin)
@app.route('/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        price = request.form['price']
        description = request.form['description']

        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, brand, price, description) VALUES (?, ?, ?, ?)', 
                     (name, brand, price, description))
        conn.commit()
        conn.close()
        flash('Produk berhasil ditambahkan!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html')

# Route untuk mengedit produk (Hanya Admin)
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        flash('Produk tidak ditemukan! Pastikan ID produk benar.', 'danger')
        conn.close()
        return redirect(url_for('products'))

    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        price = request.form['price']
        description = request.form['description']

        conn.execute('UPDATE products SET name = ?, brand = ?, price = ?, description = ? WHERE id = ?',
                     (name, brand, price, description, product_id))
        conn.commit()
        flash('Produk berhasil diupdate!', 'success')
        return redirect(url_for('products'))

    conn.close()
    return render_template('edit_product.html', product=product)


# Route untuk menghapus produk (Hanya Admin)
@app.route('/delete_product/<int:product_id>', methods=['GET'])
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if not product:
        flash('Produk tidak ditemukan! Tidak bisa menghapus produk yang tidak ada.', 'danger')
        conn.close()
        return redirect(url_for('products'))

    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    flash('Produk berhasil dihapus!', 'success')
    return redirect(url_for('products'))

@app.route('/logout')
def logout():
    session.pop('username', None)  # Menghapus data session
    return redirect(url_for('login'))  # Mengarahkan ke halaman login

if __name__ == '__main__':
    app.run(debug=True)
