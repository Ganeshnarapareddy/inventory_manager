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
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'read',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
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
            account_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sku TEXT NOT NULL,
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
            account_id INTEGER NOT NULL,
            po_number TEXT NOT NULL,
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
            account_id INTEGER NOT NULL,
            order_number TEXT NOT NULL,
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
            
        # Migrations for existing tables
        migrations = [
            "ALTER TABLE categories ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN account_id INTEGER DEFAULT 1",
            "ALTER TABLE suppliers ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE products ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE purchase_orders ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE sales_orders ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1"
        ]
        for m in migrations:
            try:
                conn.execute(m)
            except Exception:
                pass # Column already exists
                
        # Force admin user to root
        conn.execute("UPDATE users SET role='root' WHERE username='admin'")
    else:
        c = conn.cursor()
        c.executescript(script)
        
        # Migrations for sqlite
        migrations = [
            "ALTER TABLE categories ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE users ADD COLUMN account_id INTEGER DEFAULT 1",
            "ALTER TABLE suppliers ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE products ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE purchase_orders ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE sales_orders ADD COLUMN account_id INTEGER NOT NULL DEFAULT 1"
        ]
        for m in migrations:
            try:
                c.execute(m)
            except Exception:
                pass
                
        # Force admin user to root
        c.execute("UPDATE users SET role='root' WHERE username='admin'")
        conn.commit()
    
    # Initialize root user if no users exist
    df_users = fetch_df("SELECT COUNT(*) as cnt FROM users")
    if df_users.empty or df_users['cnt'].iloc[0] == 0:
        hashed = hash_password("admin123")
        execute_query("INSERT INTO users(username, password_hash, role, account_id) VALUES('admin', ?, 'root', NULL)", (hashed,))

# ── Auth & User helpers ───────────────────────────────────────────────────────
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(username, password, role="read", account_id=1):
    hashed = hash_password(password)
    execute_query("INSERT INTO users(username, password_hash, role, account_id) VALUES(?, ?, ?, ?)", (username, hashed, role, account_id))

def get_user(username):
    df = fetch_df("SELECT * FROM users WHERE username=?", (username,))
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def get_all_users(account_id=None):
    if account_id:
        return fetch_df("SELECT id, username, role, created_at, account_id FROM users WHERE account_id=? ORDER BY created_at", (account_id,))
    return fetch_df("SELECT id, username, role, created_at, account_id FROM users ORDER BY created_at")

def update_user_password(username, new_password):
    hashed = hash_password(new_password)
    execute_query("UPDATE users SET password_hash=? WHERE username=?", (hashed, username))

def update_username(user_id, new_username):
    execute_query("UPDATE users SET username=? WHERE id=?", (new_username, user_id))

def delete_user(user_id):
    execute_query("DELETE FROM users WHERE id=?", (user_id,))

def update_user_role(user_id, role):
    execute_query("UPDATE users SET role=? WHERE id=?", (role, user_id))

# ── Account helpers ───────────────────────────────────────────────────────────
def get_all_accounts():
    return fetch_df("SELECT id, name, created_at FROM accounts ORDER BY name")

def create_account(name):
    execute_query("INSERT INTO accounts(name) VALUES(?)", (name,))

# ── Product helpers ───────────────────────────────────────────────────────────
def get_products_full(account_id):
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
        WHERE p.is_active = 1 AND p.account_id = ?
        ORDER BY p.name
    """, (account_id,))

def soft_delete_product(product_id):
    execute_query("UPDATE products SET is_active=0 WHERE id=?", (product_id,))

def get_low_stock(account_id):
    return fetch_df("""
        SELECT p.id, p.name, p.sku, p.quantity, p.min_stock,
               c.name as category, s.name as supplier
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.quantity <= p.min_stock AND p.is_active=1 AND p.account_id = ?
        ORDER BY p.quantity ASC
    """, (account_id,))

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

def record_sale(account_id, product_id, quantity, unit_price, customer_name, notes=""):
    order_num = generate_order_number(account_id)
    total = quantity * unit_price
    
    order_id = execute_query("""
        INSERT INTO sales_orders(account_id, order_number, customer_name, total_amount, notes, status, order_date)
        VALUES(?, ?, ?, ?, ?, 'completed', datetime('now'))
    """, (account_id, order_num, customer_name, total, notes))
    
    execute_query("""
        INSERT INTO sale_items(order_id, product_id, quantity, unit_price)
        VALUES(?, ?, ?, ?)
    """, (order_id, product_id, quantity, unit_price))
    
    add_stock_movement(product_id, "sale", quantity, unit_price, f"SO: {order_num}", f"Sold to: {customer_name}. {notes}")
    return order_num

def get_recent_sales(account_id):
    return fetch_df("""
        SELECT so.id as order_id, so.order_number, so.customer_name, p.name as product_name,
               si.quantity, si.unit_price, (si.quantity * si.unit_price) as total,
               so.created_at, so.status
        FROM sales_orders so
        JOIN sale_items si ON so.id = si.order_id
        JOIN products p ON si.product_id = p.id
        WHERE so.account_id = ?
        ORDER BY so.created_at DESC
    """, (account_id,))

def revoke_sale(order_id):
    # Fetch all items in the order
    items = fetch_df("SELECT product_id, quantity FROM sale_items WHERE order_id=?", (order_id,))
    
    # Restore quantities via stock movement (which automatically updates product quantity)
    for _, row in items.iterrows():
        add_stock_movement(int(row['product_id']), "adjustment_in", int(row['quantity']), 0, f"Revoke Order {order_id}", "Sale Revoked")
        
    # Mark order as revoked
    execute_query("UPDATE sales_orders SET status='revoked' WHERE id=?", (order_id,))

def get_dashboard_stats(account_id):
    query = """
    SELECT 
        (SELECT COUNT(*) FROM products WHERE is_active=1 AND account_id=?) as total_products,
        (SELECT COUNT(*) FROM products WHERE quantity<=min_stock AND is_active=1 AND account_id=?) as low_stock,
        (SELECT COALESCE(SUM(quantity*cost_price),0) FROM products WHERE is_active=1 AND account_id=?) as inventory_value,
        (SELECT COUNT(*) FROM sales_orders WHERE date(created_at)=date('now') AND status!='revoked' AND account_id=?) as sales_today,
        (SELECT COALESCE(SUM(total_amount),0) FROM sales_orders WHERE date(created_at)=date('now') AND status!='revoked' AND account_id=?) as revenue_today,
        (SELECT COALESCE(SUM(total_amount),0) FROM sales_orders WHERE date(created_at)=date('now', '-1 day') AND status!='revoked' AND account_id=?) as revenue_yesterday,
        (SELECT COUNT(*) FROM purchase_orders WHERE status='pending' AND account_id=?) as pending_po,
        (SELECT COUNT(*) FROM products WHERE quantity=0 AND is_active=1 AND account_id=?) as out_of_stock
    """
    df = fetch_df(query, (account_id, account_id, account_id, account_id, account_id, account_id, account_id, account_id))
    
    if df.empty:
        return {"total_products": 0, "low_stock": 0, "inventory_value": 0, "sales_today": 0, 
                "revenue_today": 0, "revenue_yesterday": 0, "pending_po": 0, "out_of_stock": 0}
                
    row = df.iloc[0]
    return {
        "total_products": int(row['total_products']),
        "low_stock": int(row['low_stock']),
        "inventory_value": float(row['inventory_value']),
        "sales_today": int(row['sales_today']),
        "revenue_today": float(row['revenue_today']),
        "revenue_yesterday": float(row['revenue_yesterday']),
        "pending_po": int(row['pending_po']),
        "out_of_stock": int(row['out_of_stock'])
    }

def get_category_stock_value(account_id):
    return fetch_df("""
        SELECT c.name as category, SUM(p.quantity*p.cost_price) as value,
               COUNT(p.id) as products, SUM(p.quantity) as total_qty
        FROM products p JOIN categories c ON p.category_id=c.id
        WHERE p.is_active=1 AND p.account_id=?
        GROUP BY c.name ORDER BY value DESC
    """, (account_id,))

def get_sales_trend(account_id, days=30):
    return fetch_df(f"""
        SELECT date(created_at) as date, COUNT(*) as orders,
               SUM(total_amount) as revenue
        FROM sales_orders
        WHERE created_at >= datetime('now','-{days} days') AND status!='revoked' AND account_id=?
        GROUP BY date(created_at) ORDER BY date
    """, (account_id,))

def generate_po_number(account_id):
    df = fetch_df("SELECT COUNT(*) as c FROM purchase_orders WHERE account_id=?", (account_id,))
    n = df['c'].iloc[0] + 1 if not df.empty else 1
    return f"PO-{datetime.now().strftime('%Y%m')}-{n:04d}"

def generate_order_number(account_id):
    df = fetch_df("SELECT COUNT(*) as c FROM sales_orders WHERE account_id=?", (account_id,))
    n = df['c'].iloc[0] + 1 if not df.empty else 1
    return f"SO-{datetime.now().strftime('%Y%m')}-{n:04d}"

def get_global_sales():
    return fetch_df("""
        SELECT so.id as order_id, so.order_number, so.customer_name, so.total_amount, so.status, so.created_at, a.name as account_name
        FROM sales_orders so
        JOIN accounts a ON so.account_id = a.id
        ORDER BY so.created_at DESC
    """)
    
def get_global_revenue():
    df = fetch_df("SELECT SUM(total_amount) as total FROM sales_orders WHERE status!='revoked'")
    if not df.empty and pd.notna(df['total'].iloc[0]):
        return float(df['total'].iloc[0])
    return 0.0
