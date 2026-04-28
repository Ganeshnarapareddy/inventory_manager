import toml
import libsql_client

with open(".streamlit/secrets.toml", "r") as f:
    secrets = toml.load(f)

url = secrets['database']['url']
auth_token = secrets['database'].get('auth_token', '')

client = libsql_client.create_client_sync(url=url, auth_token=auth_token)

tables = ['sale_items', 'sales_orders', 'po_items', 'purchase_orders', 'stock_movements', 'adjustments', 'products', 'categories', 'suppliers', 'users']

for t in tables:
    try:
        client.execute(f"DROP TABLE IF EXISTS {t}")
        print(f"Dropped {t}")
    except Exception as e:
        print(f"Error dropping {t}: {e}")

client.close()
print("Turso Database completely wiped.")
