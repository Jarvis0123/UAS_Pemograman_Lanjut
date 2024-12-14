import sqlite3
import hashlib

# Fungsi untuk meng-hash password menggunakan SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Membuat koneksi ke database SQLite
def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# Membuat database dan tabel
def create_db():
    conn = get_db_connection()
    
    # Membuat tabel users
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    ''')

    # Membuat tabel products
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL
        );
    ''')

    # Membuat tabel orders
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
    ''')

    # Menambahkan data pengguna (admin dan user)
    hashed_admin_password = hash_password('adminpassword')  # password = "adminpassword"
    hashed_user_password = hash_password('userpassword')    # password = "userpassword"
    
    conn.execute('''
        INSERT OR IGNORE INTO users (username, password, role) 
        VALUES 
        ('admin', ?, 'admin'),
        ('user', ?, 'user');
    ''', (hashed_admin_password, hashed_user_password))

    # Menambahkan data produk
    conn.execute('''
        INSERT OR IGNORE INTO products (name, brand, price, description) 
        VALUES
        ('Las Mesin MIG', 'WeldMaster', 3500.00, 'Mesin las MIG serbaguna, mudah digunakan untuk proyek industri.'),
        ('Las Mesin TIG', 'WeldCraft', 4200.00, 'Mesin las TIG dengan presisi tinggi, cocok untuk las logam tipis.'),
        ('Las Stick', 'PowerWeld', 2500.00, 'Mesin las stick, ideal untuk pekerjaan las sederhana dan terjangkau.');
    ''')

    # Menambahkan data pesanan
    conn.execute('''
        INSERT OR IGNORE INTO orders (name, product_id, quantity) 
        VALUES 
        ('John Doe', 1, 2),
        ('Jane Smith', 2, 1);
    ''')

    # Commit dan tutup koneksi
    conn.commit()
    conn.close()

    print("Database telah dibuat dan data awal telah ditambahkan.")

if __name__ == '__main__':
    create_db()
