import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_option_menu import option_menu
import db
import styles
from lang import _
import base64

SVG_LOGO = '<svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;"><rect width="100" height="100" rx="20" fill="url(#ng1)"/><defs><linearGradient id="ng1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#c084fc"/></linearGradient></defs><path d="M25 75L25 25L75 75L75 25" fill="none" stroke="white" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/></svg>'

SVG_LOGO_SMALL = '<svg width="18" height="18" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle;"><rect width="100" height="100" rx="20" fill="url(#ng2)"/><defs><linearGradient id="ng2" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#c084fc"/></linearGradient></defs><path d="M25 75L25 25L75 75L75 25" fill="none" stroke="white" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/></svg>'

st.set_page_config(
    page_title="NexGen Inventory Pro",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(styles.CSS, unsafe_allow_html=True)
db.init_db()

def render_dashboard():
    account_id = st.session_state.get('account_id', 1)
    current_lang = st.session_state.get('lang', 'en')
    st.markdown(f'<div class="section-header"><h2>📊 {_("Executive Dashboard", current_lang)}</h2></div>', unsafe_allow_html=True)
    stats = db.get_dashboard_stats(account_id)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-icon">📦</div>
                <div class="kpi-value">{stats["total_products"]}</div>
                <div class="kpi-label">Total Products</div>
            </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-icon">💰</div>
                <div class="kpi-value">₹{stats["inventory_value"]:,.2f}</div>
                <div class="kpi-label">Inventory Value</div>
            </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-icon">⚠️</div>
                <div class="kpi-value">{stats["low_stock"]}</div>
                <div class="kpi-label">Low Stock Items</div>
            </div>
        ''', unsafe_allow_html=True)
    with col4:
        st.metric(label=_("Revenue Today", current_lang), value=f"₹{stats['revenue_today']:,.2f}", 
                  delta=f"₹{stats['revenue_today'] - stats['revenue_yesterday']:,.2f} " + _("from yesterday", current_lang),
                  delta_color="normal")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f'### 📈 {_("Daily Revenue Trend", current_lang)}')
        trend_df = db.get_sales_trend(account_id)
        if not trend_df.empty:
            fig = px.bar(trend_df, x='date', y='revenue', 
                         color_discrete_sequence=['#6366f1'],
                         template="plotly_dark",
                         labels={'revenue': 'Revenue (₹)', 'date': 'Date'})
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(_("No sales data available.", current_lang))

    with c2:
        st.markdown(f'### 🍩 {_("Category Value Distribution", current_lang)}')
        cat_df = db.get_category_stock_value(account_id)
        if not cat_df.empty:
            fig = px.pie(cat_df, values='value', names='category', hole=0.6,
                         color_discrete_sequence=px.colors.sequential.Purp,
                         template="plotly_dark")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available.")

    st.markdown(f'### ⚠️ {_("Action Required: Low Stock Alerts", current_lang)}')
    low_stock = db.get_low_stock(account_id)
    if not low_stock.empty:
        st.dataframe(low_stock[['name', 'sku', 'quantity', 'min_stock', 'category']], use_container_width=True, hide_index=True)
    else:
        st.success(_("All products are well stocked!", current_lang))
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'### 📝 {_("Recent Sales History", current_lang)}')
    recent_sales = db.get_recent_sales(account_id)
    if not recent_sales.empty:
        st.dataframe(recent_sales.head(10), use_container_width=True, hide_index=True)
    else:
        st.info(_("No sales data available.", current_lang))

@st.dialog("Create New Account")
def dialog_create_account(current_lang):
    st.write(_("Please enter the name of the new account to create.", current_lang))
    acc_name = st.text_input(_("Account Name", current_lang))
    if st.button(_("Create Account", current_lang), type="primary"):
        if acc_name:
            db.create_account(acc_name)
            st.session_state['show_toast'] = f"✅ Account '{acc_name}' created successfully!"
            st.rerun()
        else:
            st.error(_("Please enter an account name.", current_lang))

@st.dialog("Confirm Deletion")
def dialog_delete_account(account_id, account_name, current_lang):
    msg = _("Are you sure you want to completely delete '{account_name}'? All products, sales, and users attached to this account will be permanently lost.", current_lang)
    st.warning(msg.replace("{account_name}", account_name))
    if st.button(_("Delete Account", current_lang), type="primary"):
        db.delete_account(account_id)
        if st.session_state.get('account_id') == account_id:
            st.session_state['account_id'] = None
        st.session_state['show_toast'] = f"🗑️ Account '{account_name}' deleted completely."
        st.rerun()

def render_super_admin():
    current_lang = st.session_state.get('lang', 'en')
    st.markdown(f'<div class="section-header"><h2>🌍 {_("Super Admin", current_lang)}</h2></div>', unsafe_allow_html=True)
    
    # Show any pending toasts from dialogs
    if 'show_toast' in st.session_state:
        st.toast(st.session_state['show_toast'])
        del st.session_state['show_toast']
        
    st.markdown("### " + _("Manage Accounts", current_lang))
    
    col_btn, col_empty = st.columns([1, 4])
    with col_btn:
        if st.button("➕ " + _("Create New Account", current_lang), use_container_width=True):
            dialog_create_account(current_lang)
            
    st.markdown("<br>", unsafe_allow_html=True)
    accounts = db.get_all_accounts()
    if not accounts.empty:
        for idx, row in accounts.iterrows():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**🏢 {row['name']}** (ID: {row['id']})")
            with c2:
                if st.button("🗑️ " + _("Delete", current_lang), key=f"del_acc_{row['id']}"):
                    dialog_delete_account(row['id'], row['name'], current_lang)
            st.markdown("<hr style='margin:0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    else:
        st.info(_("No accounts exist yet.", current_lang))

def render_products():
    current_lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>📦 {_("Product Catalog", current_lang)}</h2></div>', unsafe_allow_html=True)
    
    role = st.session_state.get('role', 'read')
    tabs_list = [_("Browse Inventory", current_lang)]
    if role in ["write", "admin", "root"]:
        tabs_list.extend([_("Add Product", current_lang), _("Edit Product", current_lang)])
        
    tabs = st.tabs(tabs_list)
    
    with tabs[0]:
        df = db.get_products_full(account_id)
        if not df.empty:
            def clear_search():
                st.session_state.search_input = ""
                
            sc1, sc2 = st.columns([5, 1])
            with sc1:
                search = st.text_input("🔍 " + _("Search products by name, SKU, or category...", current_lang), key="search_input")
            with sc2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("✖ " + _("Clear", current_lang), use_container_width=True, on_click=clear_search)

            if search:
                mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
                df = df[mask]
                
            def style_qty(row):
                if row['quantity'] <= 0: return ['background-color: rgba(239,68,68,0.2)'] * len(row)
                if row['quantity'] <= row['min_stock']: return ['background-color: rgba(251,191,36,0.2)'] * len(row)
                return [''] * len(row)

            st.dataframe(
                df[['id', 'name', 'sku', 'category', 'quantity', 'min_stock', 'selling_price', 'stock_value', 'margin_pct']]
                .style.apply(style_qty, axis=1)
                .format({'selling_price': '₹{:.2f}', 'stock_value': '₹{:.2f}', 'margin_pct': '{:.1f}%'}),
                width='stretch', hide_index=True, height=400
            )
        else:
            st.info(_("Inventory is empty.", current_lang))

    if role in ["write", "admin", "root"]:
        with tabs[1]:
            with st.form("add_product_form"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Product Name*")
                sku = c2.text_input("SKU*")
                
                categories = db.get_categories(account_id)
                cat_opts = dict(zip(categories['name'], categories['id'])) if not categories.empty else {}
                
                c3, c4 = st.columns(2)
                cat_name = c3.selectbox("Category", options=list(cat_opts.keys()))
                
                c5, c6, c7 = st.columns(3)
                cost = c5.number_input("Cost Price (₹)", min_value=0.0, step=0.01)
                price = c6.number_input("Selling Price (₹)", min_value=0.0, step=0.01)
                qty = c7.number_input("Initial Quantity", min_value=0, step=1)
                
                if st.form_submit_button("➕ " + _("Add Product", current_lang)):
                    if not name or not sku:
                        st.error("Name and SKU are required!")
                    else:
                        try:
                            db.execute_query("""
                                INSERT INTO products (account_id, name, sku, category_id, supplier_id, cost_price, selling_price, quantity)
                                VALUES (?, ?, ?, ?, NULL, ?, ?, ?)
                            """, (account_id, name, sku, cat_opts.get(cat_name), cost, price, qty))
                            st.success(f"Product '{name}' added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with tabs[2]:
            products_df = db.fetch_df("SELECT id, name, sku, cost_price, selling_price, quantity, min_stock FROM products WHERE is_active=1 AND account_id=?", (account_id,))
            if not products_df.empty:
                prod_edit_sel = st.selectbox("Select Product to Edit", products_df['name'].tolist())
                selected_prod = products_df[products_df['name'] == prod_edit_sel].iloc[0]
                
                with st.form("edit_product_form"):
                    e_c1, e_c2 = st.columns(2)
                    new_name = e_c1.text_input("Product Name*", value=selected_prod['name'])
                    new_sku = e_c2.text_input("SKU*", value=selected_prod['sku'])
                    
                    e_c3, e_c4 = st.columns(2)
                    new_cost = e_c3.number_input("Cost Price (₹)", min_value=0.0, step=0.01, value=float(selected_prod['cost_price']))
                    new_price = e_c4.number_input("Selling Price (₹)", min_value=0.0, step=0.01, value=float(selected_prod['selling_price']))
                    
                    e_c5, e_c6 = st.columns(2)
                    new_qty = e_c5.number_input("Quantity", min_value=0, step=1, value=int(selected_prod['quantity']))
                    new_min = e_c6.number_input("Min Stock", min_value=0, step=1, value=int(selected_prod['min_stock']))
                    
                    st.markdown("<hr>", unsafe_allow_html=True)
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            if not new_name or not new_sku:
                                st.error("Name and SKU are required!")
                            else:
                                try:
                                    db.execute_query("""
                                        UPDATE products SET name=?, sku=?, cost_price=?, selling_price=?, quantity=?, min_stock=?, updated_at=datetime('now')
                                        WHERE id=? AND account_id=?
                                    """, (new_name, new_sku, new_cost, new_price, new_qty, new_min, int(selected_prod['id']), account_id))
                                    st.success(f"Product '{new_name}' updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                    with bc2:
                        if st.form_submit_button("🗑️ Delete Product", use_container_width=True, type="primary"):
                            db.soft_delete_product(int(selected_prod['id']))
                            st.success(f"Product '{new_name}' deleted.")
                            st.rerun()
            else:
                st.info("No products available to edit.")

def render_sales():
    current_lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>🛒 {_("Point of Sale", current_lang)}</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"### {_('Record New Sale', current_lang)}")
        with st.form("sale_form"):
            products = db.fetch_df("SELECT id, name, quantity, selling_price FROM products WHERE is_active=1 AND account_id=?", (account_id,))
            prod_dict = {f"{r['name']} (₹{r['selling_price']:.2f} | Stock: {r['quantity']})": (r['id'], r['selling_price'], r['quantity']) for idx, r in products.iterrows()}
            
            prod_sel = st.selectbox(_("Select Product", current_lang), list(prod_dict.keys()) if prod_dict else [_("No products available.", current_lang)])
            customer = st.text_input(_("Customer Name (Sold to whom?)", current_lang))
            
            custom_price = st.number_input(_("Custom Sold Price (₹) - Optional", current_lang), min_value=0.0, step=0.01, value=None, placeholder="Leave blank to use default price")
            qty = st.number_input(_("Quantity Sold", current_lang), min_value=1, step=1)
            notes = st.text_input(_("Additional Notes (Optional)", current_lang))
            
            if st.form_submit_button(_("Complete Sale", current_lang)):
                if prod_dict:
                    pid, default_price, max_qty = prod_dict[prod_sel]
                    final_price = custom_price if custom_price is not None else default_price
                    if not customer:
                        st.error("Please enter the customer name.")
                    elif qty > max_qty:
                        st.error(f"Cannot sell {qty}. Only {max_qty} in stock!")
                    else:
                        order_num = db.record_sale(account_id, pid, qty, final_price, customer, notes)
                        st.success(f"Sale recorded! Order: {order_num} | Total: ₹{qty * final_price:.2f}")
                        st.rerun()
                else:
                    st.error(_("No products available.", current_lang))
    
    with col2:
        st.markdown(f"### {_('Recent Sales History', current_lang)}")
        sales = db.get_recent_sales(account_id)
        if not sales.empty:
            st.dataframe(
                sales[['order_number', 'customer_name', 'product_name', 'quantity', 'unit_price', 'total', 'status', 'created_at']]
                .style.apply(lambda row: ['color: #ef4444' if row['status'] == 'revoked' else ''] * len(row), axis=1)
                .format({'unit_price': '₹{:.2f}', 'total': '₹{:.2f}'}),
                hide_index=True, use_container_width=True
            )
            
            st.markdown(f"### {_('Revoke a Sale', current_lang)}")
            valid_sales = sales[sales['status'] != 'revoked']
            if not valid_sales.empty:
                with st.form("revoke_form"):
                    revoke_opts = {f"{r['order_number']} - {r['product_name']} (Qty: {r['quantity']})": r['order_id'] for idx, r in valid_sales.iterrows()}
                    selected_revoke = st.selectbox("Select Order to Revoke", list(revoke_opts.keys()))
                    if st.form_submit_button("🚫 " + _("Revoke Selected Sale", current_lang)):
                        order_id = revoke_opts[selected_revoke]
                        db.revoke_sale(order_id)
                        st.success(_("Sale revoked! Stock has been returned and revenue deducted.", current_lang))
                        st.rerun()
            else:
                st.info(_("No active sales available to revoke.", current_lang))
        else:
            st.info(_("No sales yet.", current_lang))

def render_movements():
    st.markdown('<div class="section-header"><h2>🔄 Stock Movements</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Record Movement")
        with st.form("movement_form"):
            products = db.fetch_df("SELECT id, name, quantity FROM products WHERE is_active=1")
            prod_dict = {f"{r['name']} (Stock: {r['quantity']})": r['id'] for _, r in products.iterrows()}
            
            prod_sel = st.selectbox("Select Product", list(prod_dict.keys()) if prod_dict else ["No products"])
            m_type = st.selectbox("Movement Type", ["purchase", "sale", "adjustment_in", "adjustment_out", "damage", "return"])
            qty = st.number_input("Quantity", min_value=1, step=1)
            notes = st.text_input("Notes / Reference")
            
            if st.form_submit_button("Record Movement"):
                if prod_dict:
                    pid = prod_dict[prod_sel]
                    db.add_stock_movement(pid, m_type, qty, 0, "", notes)
                    st.success("Movement recorded!")
                    st.rerun()
                else:
                    st.error("No products available.")
    
    with col2:
        st.markdown("### Recent Activity")
        moves = db.get_stock_movements()
        if not moves.empty:
            st.dataframe(moves.head(20), width='stretch', hide_index=True)

def render_admin():
    current_lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>🛡️ {_("User Management", current_lang)}</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("create_user_form"):
            st.markdown(f"### {_('Create User', current_lang)}")
            new_user = st.text_input(_("Username", current_lang))
            new_pass = st.text_input(_("Password", current_lang), type="password")
            new_role = st.selectbox(_("Role", current_lang), ["read", "write", "admin"])
            
            if st.form_submit_button(_("Add User", current_lang)):
                if new_user and new_pass:
                    if db.get_user(new_user):
                        st.error("Username already exists!")
                    else:
                        db.create_user(new_user, new_pass, new_role, account_id)
                        st.success(f"User {new_user} created!")
                        st.rerun()
                else:
                    st.error("Please fill all fields.")
                    
    with col2:
        st.markdown(f"### {_('Existing Users', current_lang)}")
        users_df = db.get_all_users(account_id)
        if not users_df.empty:
            for idx, row in users_df.iterrows():
                with st.expander(f"👤 {row['username']} ({row['role']})"):
                    # Username update
                    u_col1, u_col2 = st.columns([3, 1])
                    new_u = u_col1.text_input("Edit Username", value=row['username'], key=f"uname_{row['id']}")
                    if u_col2.button("💾", key=f"btn_uname_{row['id']}"):
                        if new_u and new_u != row['username']:
                            if not db.get_user(new_u):
                                db.update_username(row['id'], new_u)
                                st.success("Username updated!")
                                st.rerun()
                            else:
                                st.error("Username exists!")
                    
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        new_r = st.selectbox("Change Role", ["read", "write", "admin"], index=["read", "write", "admin"].index(row['role']) if row['role'] in ["read", "write", "admin"] else 2, key=f"role_{row['id']}")
                        if st.button("Update Role", key=f"btn_role_{row['id']}"):
                            db.update_user_role(row['id'], new_r)
                            st.success("Role updated!")
                            st.rerun()
                    with uc2:
                        reset_pass = st.text_input("New Password", type="password", key=f"pass_{row['id']}")
                        if st.button("Reset Password", key=f"btn_pass_{row['id']}"):
                            if reset_pass:
                                db.update_user_password(row['username'], reset_pass)
                                st.success("Password reset!")
                            else:
                                st.error("Enter a password")
                    
                    if row['username'] != 'admin':
                        if st.button("🗑️ Delete User", key=f"del_{row['id']}", type="primary"):
                            db.delete_user(row['id'])
                            st.rerun()

def render_analytics():
    current_lang = st.session_state.get('lang', 'en')
    st.markdown(f'<div class="section-header"><h2>📊 Analytics (All Accounts)</h2></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    accounts = db.get_all_accounts()
    acc_filter = "All Accounts"
    if not accounts.empty:
        acc_filter = c1.selectbox("Filter by Account", ["All Accounts"] + list(accounts['name']))
        
    all_cats = db.fetch_df("SELECT DISTINCT name FROM categories ORDER BY name")
    cat_filter = "All Categories"
    if not all_cats.empty:
        cat_filter = c2.selectbox("Filter by Category", ["All Categories"] + list(all_cats['name']))
        
    sales = db.get_global_sales(cat_filter)
    
    if acc_filter != "All Accounts":
        sales = sales[sales['account_name'] == acc_filter]
        
    total_rev = sales['total_amount'][sales['status'] != 'revoked'].sum() if not sales.empty else 0.0
    
    st.markdown(f"""
        <div class="kpi-card" style="text-align:center; max-width: 400px; margin: 0 auto 30px auto;">
            <div class="kpi-icon">🌍</div>
            <div class="kpi-value">₹{total_rev:,.2f}</div>
            <div class="kpi-label">Revenue ({acc_filter})</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### All Sales Orders")
    if not sales.empty:
        st.dataframe(sales, use_container_width=True, hide_index=True)
    else:
        st.info("No sales data found.")

def render_auth():
    st.markdown('<div style="max-width: 400px; margin: 100px auto;">', unsafe_allow_html=True)
    
    # Render logo in the center
    st.markdown(f'<div style="display:flex; justify-content:center; align-items:center; gap:10px; margin-bottom: 2rem;">{SVG_LOGO}<h2 style="margin:0; background: linear-gradient(90deg, #a5b4fc, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NexGen Inventory</h2></div>', unsafe_allow_html=True)
        
    st.markdown('<div class="section-header" style="border-radius: 12px; text-align: center; margin-bottom: 2rem;"><h2>🔒 Portal Login</h2></div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            user = db.get_user(username)
            if user and db.verify_password(password, user['password_hash']):
                st.session_state['user'] = user['username']
                st.session_state['role'] = user['role']
                st.session_state['account_id'] = user['account_id']
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    with st.expander("Forgot Password? (Root Only)"):
        with st.form("recovery_form"):
            phrase = st.text_input("Please enter the Phrase", type="password")
            new_pwd = st.text_input("New Password", type="password")
            if st.form_submit_button("Reset Root Password"):
                if phrase == "9182776493":
                    if new_pwd:
                        # Update the root user's password
                        db.execute_query("UPDATE users SET password_hash=? WHERE role='root'", (db.hash_password(new_pwd),))
                        st.success("Root password reset successfully! You can now log in.")
                    else:
                        st.error("Enter a new password.")
                else:
                    st.error("Invalid phrase.")
                    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'en'
        
    if 'user' not in st.session_state:
        render_auth()
        return

    role = st.session_state.get('role', 'read')
    account_id = st.session_state.get('account_id', 1)
    
    with st.sidebar:
        st.markdown(f"""
        <div style='display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 10px; margin-bottom: 5px;'>
            {SVG_LOGO}
            <h2 style='margin: 0; padding: 0; font-size: 1.5rem; background: linear-gradient(90deg, #a5b4fc, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>NexGen</h2>
        </div>
        <div style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-bottom: 20px;'>Made by Ganesh Narapareddy</div>
        """, unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center; color:#a5b4fc; margin-bottom: 20px;'>{_('Welcome', st.session_state['lang'])}, {st.session_state['user']} ({role.upper()})</div>", unsafe_allow_html=True)
        
        # Language Toggle
        lang_idx = 0 if st.session_state['lang'] == 'en' else 1
        st.radio(_("Language", st.session_state['lang']), options=['en', 'te'], horizontal=True, format_func=lambda x: "English" if x == 'en' else "తెలుగు", index=lang_idx, key='lang')
            
        # Account Switcher for Root
        if role == 'root':
            accounts = db.get_all_accounts()
            if not accounts.empty:
                acc_opts = dict(zip(accounts['name'], accounts['id']))
                current_acc_name = [k for k, v in acc_opts.items() if v == account_id]
                sel_acc = st.selectbox(_("Active Account", st.session_state['lang']), list(acc_opts.keys()), index=list(acc_opts.keys()).index(current_acc_name[0]) if current_acc_name else 0)
                if acc_opts[sel_acc] != account_id:
                    st.session_state['account_id'] = acc_opts[sel_acc]
                    st.rerun()
            else:
                st.info("No accounts exist. Go to Super Admin (+) to create one.")
                st.session_state['account_id'] = None
        
        # Build menu based on role
        options = [_("Dashboard", st.session_state['lang']), _("Products", st.session_state['lang'])]
        icons = ["speedometer2", "box"]
        
        if role in ["write", "admin", "root"]:
            options.insert(1, _("Point of Sale", st.session_state['lang']))
            icons.insert(1, "cart-check")
            
        if role in ["admin", "root"]:
            options.append(_("User Management", st.session_state['lang']))
            icons.append("shield-lock")
            
        if role == 'root':
            options.append(_("Super Admin", st.session_state['lang']))
            icons.append("globe")
            options.append("Analytics")
            icons.append("graph-up")
            
        selected = option_menu(
            menu_title=None,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#a5b4fc", "font-size": "18px"}, 
                "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "rgba(99,102,241,0.2)", "color": "#e2e8f0"},
                "nav-link-selected": {"background-color": "rgba(99,102,241,0.3)", "border-left": "4px solid #6366f1", "color": "#ffffff", "font-weight": "bold"},
            }
        )
        
        st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        with st.expander("👤 " + _("Edit Profile", st.session_state['lang'])):
            with st.form("edit_profile_form"):
                new_u = st.text_input("Username", value=st.session_state['user'])
                new_p = st.text_input(_("New Password", st.session_state['lang']), type="password")
                if st.form_submit_button("Update"):
                    if new_u and new_u != st.session_state['user']:
                        if not db.get_user(new_u):
                            db.execute_query("UPDATE users SET username=? WHERE username=?", (new_u, st.session_state['user']))
                            st.session_state['user'] = new_u
                            st.success("Username updated!")
                        else:
                            st.error("Username already exists!")
                    if new_p:
                        db.update_user_password(st.session_state['user'], new_p)
                        st.success("Password updated!")
                    
        if st.button("🚪 " + _("Logout", st.session_state['lang']), use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("<div style='text-align:center; color:#64748b; font-size:0.8rem; margin-top: 20px;'>v2.0 SaaS Edition</div>", unsafe_allow_html=True)

    if selected == _("Dashboard", st.session_state['lang']):
        if st.session_state.get('account_id'):
            render_dashboard()
        else:
            st.warning("Please create or select an account first.")
    elif selected == _("Point of Sale", st.session_state['lang']):
        if st.session_state.get('account_id'):
            render_sales()
        else:
            st.warning("Please create or select an account first.")
    elif selected == _("Products", st.session_state['lang']):
        if st.session_state.get('account_id'):
            render_products()
        else:
            st.warning("Please create or select an account first.")
    elif selected == _("User Management", st.session_state['lang']):
        if st.session_state.get('account_id'):
            render_admin()
        else:
            st.warning("Please create or select an account first.")
    elif selected == _("Super Admin", st.session_state['lang']):
        render_super_admin()
    elif selected == "Analytics":
        render_analytics()

    # Footer Injection — scroll-triggered swipe-up animation
    footer_html = f"""
<div id="nexgen-footer" style="
    opacity: 0;
    transform: translateY(40px);
    transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    width: 100%;
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f1f3d 100%);
    border-top: 1px solid rgba(99,102,241,0.2);
    padding: 14px 0;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #94a3b8;
    margin-top: 40px;
">
    {SVG_LOGO_SMALL}
    <span style="color: white; font-weight: 600;">NexGen Inventory</span>
    <span style="color: rgba(99,102,241,0.4);">|</span>
    <span>Made by Ganesh Narapareddy</span>
</div>
<script>
    const footer = document.getElementById('nexgen-footer');
    if (footer) {{
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    footer.style.opacity = '1';
                    footer.style.transform = 'translateY(0)';
                }} else {{
                    footer.style.opacity = '0';
                    footer.style.transform = 'translateY(40px)';
                }}
            }});
        }}, {{ threshold: 0.1 }});
        observer.observe(footer);
    }}
</script>
"""
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
