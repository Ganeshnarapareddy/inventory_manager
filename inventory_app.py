import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_option_menu import option_menu
import db
import styles
from lang import _

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
    lang = st.session_state.get('lang', 'en')
    st.markdown(f'<div class="section-header"><h2>📊 {_("Executive Dashboard", lang)}</h2></div>', unsafe_allow_html=True)
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
        st.metric(label=_("Revenue Today", lang), value=f"₹{stats['revenue_today']:,.2f}", 
                  delta=f"₹{stats['revenue_today'] - stats['revenue_yesterday']:,.2f} " + _("from yesterday", lang),
                  delta_color="normal")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f'### 📈 {_("Daily Revenue Trend", lang)}')
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
            st.info(_("No sales data available.", lang))

    with c2:
        st.markdown(f'### 🍩 {_("Category Value Distribution", lang)}')
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

    st.markdown(f'### ⚠️ {_("Action Required: Low Stock Alerts", lang)}')
    low_stock = db.get_low_stock(account_id)
    if not low_stock.empty:
        st.dataframe(low_stock[['name', 'sku', 'quantity', 'min_stock', 'category']], use_container_width=True, hide_index=True)
    else:
        st.success(_("All products are well stocked!", lang))

def render_super_admin():
    lang = st.session_state.get('lang', 'en')
    st.markdown(f'<div class="section-header"><h2>🌍 {_("Super Admin", lang)}</h2></div>', unsafe_allow_html=True)
    
    st.markdown("### " + _("Create New Account", lang))
    with st.form("new_account_form"):
        acc_name = st.text_input("Account Name")
        if st.form_submit_button("Create Account"):
            db.create_account(acc_name)
            st.success(f"Account {acc_name} created!")
            st.rerun()

def render_products():
    lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>📦 {_("Product Catalog", lang)}</h2></div>', unsafe_allow_html=True)
    
    role = st.session_state.get('role', 'read')
    tabs_list = [_("Browse Inventory", lang)]
    if role in ["write", "admin", "root"]:
        tabs_list.extend([_("Add Product", lang), _("Edit Product", lang)])
        
    tabs = st.tabs(tabs_list)
    
    with tabs[0]:
        df = db.get_products_full(account_id)
        if not df.empty:
            def clear_search():
                st.session_state.search_input = ""
                
            sc1, sc2 = st.columns([5, 1])
            with sc1:
                search = st.text_input("🔍 " + _("Search products by name, SKU, or category...", lang), key="search_input")
            with sc2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("✖ " + _("Clear", lang), use_container_width=True, on_click=clear_search)

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
            st.info(_("Inventory is empty.", lang))

    if role in ["write", "admin", "root"]:
        with tabs[1]:
            with st.form("add_product_form"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Product Name*")
                sku = c2.text_input("SKU*")
                
                categories = db.fetch_df("SELECT id, name FROM categories WHERE account_id=?", (account_id,))
                cat_opts = dict(zip(categories['name'], categories['id'])) if not categories.empty else {}
                
                c3, c4 = st.columns(2)
                cat_name = c3.selectbox("Category", options=list(cat_opts.keys()))
                
                c5, c6, c7 = st.columns(3)
                cost = c5.number_input("Cost Price (₹)", min_value=0.0, step=0.01)
                price = c6.number_input("Selling Price (₹)", min_value=0.0, step=0.01)
                qty = c7.number_input("Initial Quantity", min_value=0, step=1)
                
                if st.form_submit_button("➕ " + _("Add Product", lang)):
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
    lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>🛒 {_("Point of Sale", lang)}</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"### {_('Record New Sale', lang)}")
        with st.form("sale_form"):
            products = db.fetch_df("SELECT id, name, quantity, selling_price FROM products WHERE is_active=1 AND account_id=?", (account_id,))
            prod_dict = {f"{r['name']} (₹{r['selling_price']:.2f} | Stock: {r['quantity']})": (r['id'], r['selling_price'], r['quantity']) for _, r in products.iterrows()}
            
            prod_sel = st.selectbox(_("Select Product", lang), list(prod_dict.keys()) if prod_dict else [_("No products available.", lang)])
            customer = st.text_input(_("Customer Name (Sold to whom?)", lang))
            
            custom_price = st.number_input(_("Custom Sold Price (₹) - Optional", lang), min_value=0.0, step=0.01, value=None, placeholder="Leave blank to use default price")
            qty = st.number_input(_("Quantity Sold", lang), min_value=1, step=1)
            notes = st.text_input(_("Additional Notes (Optional)", lang))
            
            if st.form_submit_button(_("Complete Sale", lang)):
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
                    st.error(_("No products available.", lang))
    
    with col2:
        st.markdown(f"### {_('Recent Sales History', lang)}")
        sales = db.get_recent_sales(account_id)
        if not sales.empty:
            st.dataframe(
                sales[['order_number', 'customer_name', 'product_name', 'quantity', 'unit_price', 'total', 'status', 'created_at']]
                .style.apply(lambda row: ['color: #ef4444' if row['status'] == 'revoked' else ''] * len(row), axis=1)
                .format({'unit_price': '₹{:.2f}', 'total': '₹{:.2f}'}),
                hide_index=True, use_container_width=True
            )
            
            st.markdown(f"### {_('Revoke a Sale', lang)}")
            valid_sales = sales[sales['status'] != 'revoked']
            if not valid_sales.empty:
                with st.form("revoke_form"):
                    revoke_opts = {f"{r['order_number']} - {r['product_name']} (Qty: {r['quantity']})": r['order_id'] for _, r in valid_sales.iterrows()}
                    selected_revoke = st.selectbox("Select Order to Revoke", list(revoke_opts.keys()))
                    if st.form_submit_button("🚫 " + _("Revoke Selected Sale", lang)):
                        order_id = revoke_opts[selected_revoke]
                        db.revoke_sale(order_id)
                        st.success(_("Sale revoked! Stock has been returned and revenue deducted.", lang))
                        st.rerun()
            else:
                st.info(_("No active sales available to revoke.", lang))
        else:
            st.info(_("No sales yet.", lang))

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
    lang = st.session_state.get('lang', 'en')
    account_id = st.session_state.get('account_id', 1)
    st.markdown(f'<div class="section-header"><h2>🛡️ {_("User Management", lang)}</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        with st.form("create_user_form"):
            st.markdown(f"### {_('Create User', lang)}")
            new_user = st.text_input(_("Username", lang))
            new_pass = st.text_input(_("Password", lang), type="password")
            new_role = st.selectbox(_("Role", lang), ["read", "write", "admin"])
            
            if st.form_submit_button(_("Add User", lang)):
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
        st.markdown(f"### {_('Existing Users', lang)}")
        users_df = db.get_all_users(account_id)
        if not users_df.empty:
            for _, row in users_df.iterrows():
                with st.expander(f"👤 {row['username']} ({row['role']})"):
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        new_r = st.selectbox("Change Role", ["read", "write", "admin"], index=["read", "write", "admin"].index(row['role']), key=f"role_{row['id']}")
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

def render_auth():
    st.markdown('<div style="max-width: 400px; margin: 100px auto;">', unsafe_allow_html=True)
    st.markdown('<div class="section-header" style="border-radius: 12px; text-align: center; margin-bottom: 2rem;"><h2>🔒 NexGen Login</h2></div>', unsafe_allow_html=True)
    
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
        st.markdown(f"<h1>NexGen Inventory</h1><div style='text-align:center; color:#a5b4fc; margin-bottom: 20px;'>{_('Welcome', st.session_state['lang'])}, {st.session_state['user']} ({role.upper()})</div>", unsafe_allow_html=True)
        
        # Language Toggle
        new_lang = st.radio(_("Language", st.session_state['lang']), options=['en', 'te'], horizontal=True, format_func=lambda x: "English" if x == 'en' else "తెలుగు")
        if new_lang != st.session_state['lang']:
            st.session_state['lang'] = new_lang
            st.rerun()
            
        # Account Switcher for Root
        if role == 'root':
            accounts = db.get_all_accounts()
            acc_opts = dict(zip(accounts['name'], accounts['id']))
            current_acc_name = [k for k, v in acc_opts.items() if v == account_id]
            sel_acc = st.selectbox(_("Active Account", st.session_state['lang']), list(acc_opts.keys()), index=list(acc_opts.keys()).index(current_acc_name[0]) if current_acc_name else 0)
            if acc_opts[sel_acc] != account_id:
                st.session_state['account_id'] = acc_opts[sel_acc]
                st.rerun()
        
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
        with st.expander("🔑 " + _("Change Password", st.session_state['lang'])):
            with st.form("change_pass_form"):
                new_p = st.text_input(_("Password", st.session_state['lang']), type="password")
                if st.form_submit_button("Update"):
                    if new_p:
                        db.update_user_password(st.session_state['user'], new_p)
                        st.success("Updated!")
                    
        if st.button("🚪 " + _("Logout", st.session_state['lang']), use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("<div style='text-align:center; color:#64748b; font-size:0.8rem; margin-top: 20px;'>v2.0 SaaS Edition</div>", unsafe_allow_html=True)

    if selected == _("Dashboard", st.session_state['lang']):
        render_dashboard()
    elif selected == _("Point of Sale", st.session_state['lang']):
        render_sales()
    elif selected == _("Products", st.session_state['lang']):
        render_products()
    elif selected == _("User Management", st.session_state['lang']):
        render_admin()
    elif selected == _("Super Admin", st.session_state['lang']):
        render_super_admin()

if __name__ == "__main__":
    main()
