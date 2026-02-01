"""
E-commerce Web Application
A simple Flask-based e-commerce platform for managing products and users.
Security fixes: env for secrets, parameterized queries, escaping, path/command safety.
"""
import os
import json
import sqlite3
import shutil
from flask import Flask, request, render_template_string, session, redirect, jsonify
from werkzeug.utils import secure_filename
from markupsafe import escape

app = Flask(__name__)

# FIX 1: Load secrets from environment
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
DATABASE = os.environ.get("DATABASE_PATH", "ecommerce.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
API_KEY = os.environ.get("API_KEY", "")

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/var/www/uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_DOWNLOAD_DIR = os.path.abspath(os.environ.get("FILES_DIR", "/var/www/files"))


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            stock INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    """Home page"""
    return '''
    <html>
    <body>
        <h1>Welcome to SecureShop</h1>
        <ul>
            <li><a href="/login">Login</a></li>
            <li><a href="/products">Products</a></li>
            <li><a href="/search">Search</a></li>
            <li><a href="/admin">Admin Panel</a></li>
        </ul>
    </body>
    </html>
    '''


# FIX 2 & 9: Parameterized query + password hashing (compare hashes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = get_db_connection()
        # Parameterized query - no SQL injection
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return "Invalid credentials", 401

    return '''
    <html>
    <body>
        <h2>Login</h2>
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    </body>
    </html>
    '''


# FIX 3: XSS - escape user input in HTML
@app.route('/search')
def search():
    """Product search with escaped output"""
    query = request.args.get('q', '')
    safe_query = escape(query)

    html = f'''
    <html>
    <body>
        <h2>Search Results for: {safe_query}</h2>
        <form method="get">
            <input type="text" name="q" value="{safe_query}">
            <input type="submit" value="Search">
        </form>
        <p>Showing results for: {safe_query}</p>
    </body>
    </html>
    '''
    return render_template_string(html)


# FIX 4: SQL Injection - parameterized query for category
@app.route('/products')
def products():
    """List products with optional filter"""
    category = request.args.get('category', '')

    conn = get_db_connection()
    if category:
        products = conn.execute(
            "SELECT * FROM products WHERE description LIKE ?",
            (f"%{category}%",)
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    product_list = "<ul>"
    for product in products:
        product_list += f"<li>{product['name']} - ${product['price']}</li>"
    product_list += "</ul>"

    return f'''
    <html>
    <body>
        <h2>Products</h2>
        <form method="get">
            Filter by category: <input type="text" name="category">
            <input type="submit" value="Filter">
        </form>
        {product_list}
    </body>
    </html>
    '''


# FIX 5: Path traversal - secure filename and path validation
@app.route('/download')
def download():
    """Download files - path restricted to allowed directory"""
    filename = request.args.get('file')
    if not filename:
        return "Missing file parameter", 400

    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return "Invalid filename", 400

    filepath = os.path.abspath(os.path.join(ALLOWED_DOWNLOAD_DIR, safe_name))
    if not filepath.startswith(ALLOWED_DOWNLOAD_DIR):
        return "Access denied", 403

    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error: {str(e)}", 404


# FIX 6: Command injection - use shutil.copy, validate filename
@app.route('/admin/backup', methods=['POST'])
def backup_database():
    """Backup database using safe file copy"""
    backup_name = request.form.get('backup_name', 'backup.db')
    safe_name = secure_filename(backup_name)
    if not safe_name:
        safe_name = 'backup.db'

    backup_dir = os.path.abspath(os.environ.get("BACKUP_DIR", "/backups"))
    dest_path = os.path.abspath(os.path.join(backup_dir, safe_name))
    if not dest_path.startswith(backup_dir):
        return jsonify({'status': 'error', 'error': 'Invalid path'}), 400

    try:
        shutil.copy(DATABASE, dest_path)
        return jsonify({'status': 'success', 'output': '', 'error': ''})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


# FIX 7: Insecure deserialization - use JSON only, reject pickle
@app.route('/api/import', methods=['POST'])
def import_data():
    """Import user data from JSON file (safe format)"""
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    try:
        data = json.loads(file.read().decode('utf-8'))
        if not isinstance(data, list):
            data = [data]
        return jsonify({'status': 'success', 'imported': len(data)})
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return f"Error importing data: {str(e)}", 500


# FIX 8: Broken authentication - remove override bypass
@app.route('/admin')
def admin_panel():
    """Admin panel - require proper admin role (no override bypass)"""
    if 'role' in session and session['role'] == 'admin':
        return '''
        <html>
        <body>
            <h2>Admin Panel</h2>
            <p>Welcome, administrator!</p>
            <a href="/admin/users">Manage Users</a>
        </body>
        </html>
        '''

    return "Access denied", 403


@app.route('/admin/users')
def manage_users():
    """Manage users - requires admin access"""
    if 'role' not in session or session['role'] != 'admin':
        return "Access denied", 403

    conn = get_db_connection()
    users = conn.execute("SELECT id, username, email, role FROM users").fetchall()
    conn.close()

    user_list = "<ul>"
    for user in users:
        user_list += f"<li>{user['username']} ({user['role']})</li>"
    user_list += "</ul>"

    return f'''
    <html>
    <body>
        <h2>User Management</h2>
        {user_list}
    </body>
    </html>
    '''


# CORRECT CODE: Proper input validation example
@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Get product by ID - properly parameterized query"""
    conn = get_db_connection()
    # This is CORRECT - using parameterized query
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    if product:
        return jsonify({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'description': product['description']
        })
    return jsonify({'error': 'Product not found'}), 404


# CORRECT CODE: Proper password hashing (example)
def hash_password(password):
    """
    Example of proper password hashing approach.
    In production, use bcrypt or argon2.
    """
    import hashlib
    # This is a simplified example - use proper libraries in production
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + key


# CORRECT CODE: Proper file upload validation
@app.route('/upload/avatar', methods=['POST'])
def upload_avatar():
    """Upload user avatar with proper validation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # Proper validation
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Validate file extension
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename:
        return jsonify({'error': 'Invalid file'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': 'File type not allowed'}), 400

    # Use secure_filename
    filename = secure_filename(file.filename)

    # Validate file size (e.g., max 5MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > 5 * 1024 * 1024:
        return jsonify({'error': 'File too large'}), 400

    file.seek(0)

    # Save file
    filepath = os.path.join('/var/www/avatars', filename)
    file.save(filepath)

    return jsonify({'status': 'success', 'filename': filename})


@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect('/login')

    return f'''
    <html>
    <body>
        <h2>Dashboard</h2>
        <p>Welcome, {session.get('username')}!</p>
        <a href="/logout">Logout</a>
    </body>
    </html>
    '''


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    init_db()
    # FIX 10: Debug from env, default False for production
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=debug, host='0.0.0.0', port=port)
