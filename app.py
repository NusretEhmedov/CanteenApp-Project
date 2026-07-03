import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import (
    get_summary, get_stock_levels, get_recent_movements,
    get_weekly_revenue, get_top_sellers,
    get_products, add_product, delete_product,
    get_movements, add_movement,
    get_sales, add_sale,
    get_reorder_list,
    get_suppliers, add_supplier, delete_supplier,
    get_supplier_options
)

st.set_page_config(
    page_title="Canteen Inventory",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── helper: colour the status column ──────────────────────────
def style_status(val):
    if val == 'Out of Stock': return 'color: #A32D2D; font-weight: bold'
    if val == 'Low Stock':    return 'color: #BA7517; font-weight: bold'
    if val == 'OK':           return 'color: #1D9E75; font-weight: bold'
    return ''

# ── Sidebar navigation ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏪 StockWise")
    st.markdown("**Canteen Inventory Manager**")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📦 Products", "🔄 Stock Movements",
         "💰 Sales", "🚨 Reorder Alerts", "🚚 Suppliers"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("School Canteen Management System")
    st.caption("Built with Python + MS SQL + Streamlit")

# ══════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    try:
        summary = get_summary()
        s = summary.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Products",  int(s['total_products']))
        col2.metric("Stock Value",     f"${float(s['stock_value']):.2f}")
        col3.metric("⚠ Low / Out",    int(s['low_stock_count']),
                    delta=None if s['low_stock_count'] == 0 else "Needs attention",
                    delta_color="inverse")
        col4.metric("Suppliers",       int(s['total_suppliers']))

        st.markdown("---")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Stock Levels")
            stock_df = get_stock_levels()
            color_map = {'OK': '#1D9E75', 'Low Stock': '#EF9F27', 'Out of Stock': '#E24B4A'}
            fig = px.bar(
                stock_df, x='stock_qty', y='name', orientation='h',
                color='status', color_discrete_map=color_map,
                labels={'stock_qty': 'Quantity', 'name': ''},
                height=380
            )
            fig.update_layout(showlegend=True, margin=dict(l=0, r=0, t=10, b=0),
                              plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Revenue (Last 30 Days)")
            rev_df = get_weekly_revenue()
            if not rev_df.empty:
                fig2 = px.bar(rev_df, x='sale_date', y='revenue',
                              labels={'sale_date': 'Date', 'revenue': 'Revenue ($)'},
                              color_discrete_sequence=['#1D9E75'], height=200)
                fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                                   plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No sales data yet.")

            st.subheader("Top 5 Best Sellers")
            top_df = get_top_sellers()
            if not top_df.empty:
                fig3 = px.pie(top_df, values='total_sold', names='name',
                              color_discrete_sequence=px.colors.sequential.Teal,
                              height=170)
                fig3.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                                   showlegend=True, legend=dict(font=dict(size=10)))
                st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Recent Stock Movements")
        mov_df = get_recent_movements()
        # format total_price as currency string
        mov_df['total_price'] = mov_df['total_price'].apply(lambda x: f"${x:.2f}")
        st.dataframe(mov_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Make sure MS SQL Server is running and CanteenDB exists.")

# ══════════════════════════════════════════════════════════════
# PAGE 2 — PRODUCTS
# ══════════════════════════════════════════════════════════════
elif page == "📦 Products":
    st.title("📦 Products")

    with st.expander("➕ Add New Product", expanded=False):
        with st.form("add_product_form"):
            c1, c2 = st.columns(2)
            p_name     = c1.text_input("Product Name")
            p_category = c2.selectbox("Category", ["Bakery","Beverages","Fresh Food",
                                                    "Fruit","Snacks","Dairy","Grains","Other"])
            c3, c4 = st.columns(2)
            p_price    = c3.number_input("Price ($)", min_value=0.0, step=0.10, format="%.2f")
            p_qty      = c4.number_input("Initial Stock Qty", min_value=0, step=1)
            c5, c6 = st.columns(2)
            p_reorder  = c5.number_input("Reorder Level", min_value=0, step=1, value=10)
            sup_df     = get_supplier_options()
            sup_dict   = dict(zip(sup_df['name'], sup_df['id']))
            p_supplier = c6.selectbox("Supplier", list(sup_dict.keys()))
            submitted  = st.form_submit_button("Add Product", type="primary")
            if submitted:
                if not p_name:
                    st.error("Please enter a product name.")
                else:
                    add_product(p_name, p_category, p_price, p_qty, p_reorder, sup_dict[p_supplier])
                    st.success(f"✅ '{p_name}' added successfully!")
                    st.rerun()

    st.subheader("All Products")
    try:
        prod_df = get_products()
        # use .map() instead of .applymap() — works on all pandas versions
        styled = prod_df.drop(columns=['id']).style.map(style_status, subset=['status'])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Remove a Product")
        prod_dict = dict(zip(prod_df['name'], prod_df['id']))
        del_name  = st.selectbox("Select product to remove", list(prod_dict.keys()))
        if st.button("🗑 Remove Product", type="secondary"):
            delete_product(prod_dict[del_name])
            st.success(f"Removed '{del_name}'.")
            st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE 3 — STOCK MOVEMENTS
# ══════════════════════════════════════════════════════════════
elif page == "🔄 Stock Movements":
    st.title("🔄 Stock Movements")

    with st.expander("➕ Record New Movement", expanded=True):
        with st.form("movement_form"):
            prod_df   = get_products()
            prod_dict = dict(zip(prod_df['name'], prod_df['id']))
            c1, c2 = st.columns(2)
            m_product = c1.selectbox("Product", list(prod_dict.keys()))
            m_type    = c2.selectbox("Type", ["IN — Stock received", "OUT — Sold / Used / Damaged"])
            c3, c4 = st.columns(2)
            m_qty  = c3.number_input("Quantity", min_value=1, step=1)
            m_note = c4.text_input("Note", placeholder="e.g. Morning delivery")
            submitted = st.form_submit_button("Record Movement", type="primary")
            if submitted:
                mov_type = "IN" if m_type.startswith("IN") else "OUT"
                ok, msg  = add_movement(prod_dict[m_product], mov_type, m_qty, m_note)
                if ok:
                    st.success(f"✅ Movement recorded for '{m_product}'.")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    st.subheader("Movement History")
    try:
        mov_df = get_movements()
        mov_df['total_price'] = mov_df['total_price'].apply(lambda x: f"${x:.2f}")
        st.dataframe(mov_df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE 4 — SALES
# ══════════════════════════════════════════════════════════════
elif page == "💰 Sales":
    st.title("💰 Sales")

    with st.expander("➕ Record New Sale", expanded=True):
        with st.form("sale_form"):
            prod_df   = get_products()
            prod_dict = dict(zip(prod_df['name'], prod_df['id']))
            c1, c2   = st.columns(2)
            s_product = c1.selectbox("Product", list(prod_dict.keys()))
            s_qty     = c2.number_input("Quantity Sold", min_value=1, step=1)
            submitted = st.form_submit_button("Record Sale", type="primary")
            if submitted:
                ok, msg = add_sale(prod_dict[s_product], s_qty)
                if ok:
                    st.success(f"✅ Sale recorded for '{s_product}'.")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sales History")
        try:
            sales_df = get_sales()
            st.dataframe(sales_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error: {e}")

    with col2:
        st.subheader("Top Sellers")
        try:
            top_df = get_top_sellers()
            if not top_df.empty:
                fig = px.bar(top_df, x='name', y='total_sold',
                             color_discrete_sequence=['#1D9E75'],
                             labels={'name': 'Product', 'total_sold': 'Units Sold'})
                fig.update_layout(margin=dict(l=0, r=0, t=10, b=0),
                                  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE 5 — REORDER ALERTS
# ══════════════════════════════════════════════════════════════
elif page == "🚨 Reorder Alerts":
    st.title("🚨 Reorder Alerts")

    try:
        reorder_df = get_reorder_list()
        if reorder_df.empty:
            st.success("✅ All products are sufficiently stocked. No reorders needed!")
        else:
            total_cost = reorder_df['est_cost'].sum()
            st.error(f"⚠ {len(reorder_df)} product(s) need restocking — "
                     f"Estimated total cost: **${total_cost:.2f}**")
            styled = reorder_df.style.map(style_status, subset=['status'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
            st.caption("Order quantity brings stock to 2× the reorder level.")

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE 6 — SUPPLIERS
# ══════════════════════════════════════════════════════════════
elif page == "🚚 Suppliers":
    st.title("🚚 Suppliers")

    with st.expander("➕ Add New Supplier", expanded=False):
        with st.form("supplier_form"):
            c1, c2 = st.columns(2)
            s_name    = c1.text_input("Company Name")
            s_contact = c2.text_input("Contact Person")
            c3, c4 = st.columns(2)
            s_phone = c3.text_input("Phone")
            s_email = c4.text_input("Email")
            submitted = st.form_submit_button("Add Supplier", type="primary")
            if submitted:
                if not s_name:
                    st.error("Please enter a company name.")
                else:
                    add_supplier(s_name, s_contact, s_phone, s_email)
                    st.success(f"✅ '{s_name}' added successfully!")
                    st.rerun()

    st.subheader("All Suppliers")
    try:
        sup_df = get_suppliers()
        # format total_stock_value as currency
        sup_df['total_stock_value'] = sup_df['total_stock_value'].apply(lambda x: f"${x:.2f}")
        sup_df['last_movement'] = sup_df['last_movement'].fillna('No movements yet')
        st.dataframe(sup_df.drop(columns=['id']), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Remove a Supplier")
        sup_dict = dict(zip(sup_df['name'], get_suppliers()['id']))
        del_name = st.selectbox("Select supplier to remove", list(sup_dict.keys()))
        if st.button("🗑 Remove Supplier", type="secondary"):
            try:
                delete_supplier(sup_dict[del_name])
                st.success(f"Removed '{del_name}'.")
                st.rerun()
            except Exception as ex:
                st.error(f"Cannot remove: supplier may have linked products. ({ex})")

    except Exception as e:
        st.error(f"Error: {e}")
