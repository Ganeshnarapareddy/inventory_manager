import sqlite3
import pandas as pd
from datetime import datetime, date
import streamlit as st
import bcrypt

# Check if Turso secrets are available
try:
    USE_TURSO = 'database' in st.secrets and 'url' in st.secrets['database']
except Exception:
    USE_TURSO = False

if USE_TURSO:
    import libsql_client

DB_PATH = "inventory.db"

@st.cache_resource
def get_connection():
    if USE_TURSO:
        return libsql_client.create_client_sync(
            url=st.secrets['database']['url'],
            auth_token=st.secrets['database'].get('auth_token', '')
        )
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=()):
    conn = get_connection()
    if USE_TURSO:
        result = conn.execute(query, params)
        return result.last_insert_rowid
    else:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()
        return c.lastrowid

def execute_many(query, data):
    conn = get_connection()
    if USE_TURSO:
        for d in data:
            conn.execute(query, d)
    else:
        c = conn.cursor()
        c.executemany(query, data)
        conn.commit()

def fetch_df(query, params=()):
    conn = get_connection()
    if USE_TURSO:
        result = conn.execute(query, params)
        return pd.DataFrame([r.astuple() for r in result.rows], columns=result.columns)
    else:
        return pd.read_sql_query(query, conn, params=params)

def init_db():
    script = """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'read',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            country TEXT,
            payment_terms TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            category_id INTEGER,
            supplier_id INTEGER,
            description TEXT,
            unit TEXT DEFAULT 'pcs',
            cost_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            max_stock INTEGER DEFAULT 1000,
            location TEXT,
            barcode TEXT,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(category_id) REFERENCES categories(id),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL DEFAULT 0,
            reference TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER,
            status TEXT DEFAULT 'pending',
            order_date TEXT,
            expected_date TEXT,
            received_date TEXT,
            total_amount REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        );
        CREATE TABLE IF NOT EXISTS po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity_ordered INTEGER DEFAULT 0,
            quantity_received INTEGER DEFAULT 0,
            unit_cost REAL DEFAULT 0,
            FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS sales_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            status TEXT DEFAULT 'pending',
            order_date TEXT,
            shipped_date TEXT,
            total_amount REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 0,
            unit_price REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            FOREIGN KEY(order_id) REFERENCES sales_orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            adjustment_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reason TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    """
    conn = get_connection()
    if USE_TURSO:
        statements = [s.strip() for s in script.split(';') if s.strip()]
        for s in statements:
            conn.execute(s)
    else:
        c = conn.cursor()
        c.executescript(script)
        conn.commit()
    
    # Initialize admin user if no users exist
    df = fetch_df("SELECT COUNT(*) as cnt FROM users")
    if df.empty or df['cnt'].iloc[0] == 0:
        create_user("admin", "admin123", "admin")

# ── Auth & User helpers ───────────────────────────────────────────────────────
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(username, password, role="read"):
    hashed = hash_password(password)
    execute_query("INSERT INTO users(username, password_hash, role) VALUES(?, ?, ?)", (username, hashed, role))

def get_user(username):
    df = fetch_df("SELECT * FROM users WHERE username=?", (username,))
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_all_users():
    return fetch_df("SELECT id, username, role, created_at FROM users ORDER BY created_at")

def update_user_password(username, new_password):
    hashed = hash_password(new_password)
    execute_query("UPDATE users SET password_hash=? WHERE username=?", (hashed, username))

def delete_user(user_id):
    execute_query("DELETE FROM users WHERE id=?", (user_id,))

def update_user_role(user_id, role):
    execute_query("UPDATE users SET role=? WHERE id=?", (role, user_id))

# ── Product helpers ───────────────────────────────────────────────────────────
def get_products_full():
    return fetch_df("""
        SELECT p.id, p.name, p.sku, c.name as category, s.name as supplier,
               p.unit, p.cost_price, p.selling_price, p.quantity, p.min_stock,
               p.max_stock, p.location, p.barcode, p.is_active,
               p.created_at, p.updated_at,
               ROUND((p.selling_price - p.cost_price)/NULLIF(p.selling_price,0)*100,1) as margin_pct,
               ROUND(p.quantity * p.cost_price, 2) as stock_value
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.is_active = 1
        ORDER BY p.name
    """)

def soft_delete_product(product_id):
    execute_query("UPDATE products SET is_active=0 WHERE id=?", (product_id,))

def get_low_stock():
    return fetch_df("""
        SELECT p.id, p.name, p.sku, p.quantity, p.min_stock,
               c.name as category, s.name as supplier
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.quantity <= p.min_stock AND p.is_active=1
        ORDER BY p.quantity ASC
    """)

def get_stock_movements():
    return fetch_df("""
        SELECT sm.id, p.name as product, p.sku, sm.movement_type, sm.quantity,
               sm.unit_cost, sm.reference, sm.notes, sm.created_at
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.id
        ORDER BY sm.created_at DESC
    """)

def add_stock_movement(product_id, mtype, qty, unit_cost, ref, notes):
    execute_query("""INSERT INTO stock_movements(product_id,movement_type,quantity,unit_cost,reference,notes)
                     VALUES(?,?,?,?,?,?)""", (product_id, mtype, qty, unit_cost, ref, notes))
    if mtype in ("purchase","adjustment_in","return"):
        execute_query("UPDATE products SET quantity=quantity+?, updated_at=datetime('now') WHERE id=?", (qty, product_id))
    elif mtype in ("sale","adjustment_out","damage"):
        execute_query("UPDATE products SET quantity=MAX(0,quantity-?), updated_at=datetime('now') WHERE id=?", (qty, product_id))

def record_sale(product_id, quantity, unit_price, customer_name, notes=""):
    order_num = generate_order_number()
    total = quantity * unit_price
    
    order_id = execute_query("""
        INSERT INTO sales_orders(order_number, customer_name, total_amount, notes, status, order_date)
        VALUES(?, ?, ?, ?, 'completed', datetime('now'))
    """, (order_num, customer_name, total, notes))
    
    execute_query("""
        INSERT INTO sale_items(order_id, product_id, quantity, unit_price)
        VALUES(?, ?, ?, ?)
    """, (order_id, product_id, quantity, unit_price))
    
    add_stock_movement(product_id, "sale", quantity, unit_price, f"SO: {order_num}", f"Sold to: {customer_name}. {notes}")
    return order_num

def get_recent_sales():
    return fetch_df("""
        SELECT so.order_number, so.customer_name, p.name as product_name,
               si.quantity, si.unit_price, (si.quantity * si.unit_price) as total,
               so.created_at
        FROM sales_orders so
        JOIN sale_items si ON so.id = si.order_id
        JOIN products p ON si.product_id = p.id
        ORDER BY so.created_at DESC
    """)

def get_dashboard_stats():
    df1 = fetch_df("SELECT COUNT(*) as c FROM products WHERE is_active=1")
    df2 = fetch_df("SELECT COUNT(*) as c FROM products WHERE quantity<=min_stock AND is_active=1")
    df3 = fetch_df("SELECT COALESCE(SUM(quantity*cost_price),0) as c FROM products WHERE is_active=1")
    df4 = fetch_df("SELECT COUNT(*) as c FROM suppliers")
    df5 = fetch_df("SELECT COUNT(*) as c FROM sales_orders WHERE date(created_at)=date('now')")
    df6 = fetch_df("SELECT COALESCE(SUM(total_amount),0) as c FROM sales_orders WHERE date(created_at)=date('now')")
    df7 = fetch_df("SELECT COUNT(*) as c FROM purchase_orders WHERE status='pending'")
    df8 = fetch_df("SELECT COUNT(*) as c FROM products WHERE quantity=0 AND is_active=1")
    
    return {
        "total_products": df1['c'].iloc[0] if not df1.empty else 0,
        "low_stock": df2['c'].iloc[0] if not df2.empty else 0,
        "inventory_value": round(df3['c'].iloc[0], 2) if not df3.empty else 0,
        "total_suppliers": df4['c'].iloc[0] if not df4.empty else 0,
        "sales_today": df5['c'].iloc[0] if not df5.empty else 0,
        "revenue_today": round(df6['c'].iloc[0], 2) if not df6.empty else 0,
        "pending_po": df7['c'].iloc[0] if not df7.empty else 0,
        "out_of_stock": df8['c'].iloc[0] if not df8.empty else 0
    }

def get_category_stock_value():
    return fetch_df("""
        SELECT c.name as category, SUM(p.quantity*p.cost_price) as value,
               COUNT(p.id) as products, SUM(p.quantity) as total_qty
        FROM products p JOIN categories c ON p.category_id=c.id
        WHERE p.is_active=1
        GROUP BY c.name ORDER BY value DESC
    """)

def get_movement_trend(days=30):
    return fetch_df(f"""
        SELECT date(created_at) as date,
               SUM(CASE WHEN movement_type='purchase' THEN quantity ELSE 0 END) as stock_in,
               SUM(CASE WHEN movement_type='sale' THEN quantity ELSE 0 END) as stock_out
        FROM stock_movements
        WHERE created_at >= datetime('now', '-{days} days')
        GROUP BY date(created_at) ORDER BY date
    """)

def get_sales_trend(days=30):
    return fetch_df(f"""
        SELECT date(created_at) as date, COUNT(*) as orders,
               SUM(total_amount) as revenue
        FROM sales_orders
        WHERE created_at >= datetime('now','-{days} days')
        GROUP BY date(created_at) ORDER BY date
    """)

def generate_po_number():
    df = fetch_df("SELECT COUNT(*) as c FROM purchase_orders")
    n = df['c'].iloc[0] + 1 if not df.empty else 1
    return f"PO-{datetime.now().strftime('%Y%m')}-{n:04d}"

def generate_order_number():
    df = fetch_df("SELECT COUNT(*) as c FROM sales_orders")
    n = df['c'].iloc[0] + 1 if not df.empty else 1
    return f"SO-{datetime.now().strftime('%Y%m')}-{n:04d}"
