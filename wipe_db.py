import db
tables = ['sale_items', 'sales_orders', 'po_items', 'purchase_orders', 'stock_movements', 'adjustments', 'products', 'categories', 'suppliers', 'users']
conn = db.get_connection()
if db.USE_TURSO:
    for t in tables:
        try:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        except Exception as e:
            print(f"Error dropping {t}: {e}")
    conn.close()
else:
    c = conn.cursor()
    for t in tables:
        c.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()
print("Database wiped.")
