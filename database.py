import pyodbc
import pandas as pd

SERVER = r'(local)\SQLEXPRESS'
DATABASE = 'CanteenDB'

def get_connection():
    conn_str = (
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={SERVER};'
        f'DATABASE={DATABASE};'
        f'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

def run_query(sql, params=None):
    conn = get_connection()
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df

def run_action(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    conn.commit()
    conn.close()

# ── Dashboard queries ──────────────────────────────────────────

def get_summary():
    return run_query("""
        SELECT
            (SELECT COUNT(*) FROM Products) AS total_products,
            (SELECT ISNULL(SUM(stock_qty * price),0) FROM Products) AS stock_value,
            (SELECT COUNT(*) FROM Products WHERE stock_qty <= reorder_level) AS low_stock_count,
            (SELECT COUNT(*) FROM Suppliers) AS total_suppliers
    """)

def get_stock_levels():
    return run_query("""
        SELECT name, stock_qty, reorder_level,
            CASE
                WHEN stock_qty = 0 THEN 'Out of Stock'
                WHEN stock_qty <= reorder_level THEN 'Low Stock'
                ELSE 'OK'
            END AS status
        FROM Products
        ORDER BY stock_qty ASC
    """)

def get_recent_movements():
    return run_query("""
        SELECT TOP 8
            p.name AS product,
            sm.type,
            sm.quantity,
            CAST(sm.quantity * p.price AS DECIMAL(10,2)) AS total_price,
            CONVERT(varchar, sm.movement_date, 23) AS date,
            sm.note
        FROM StockMovements sm
        JOIN Products p ON sm.product_id = p.id
        ORDER BY sm.id DESC
    """)

def get_weekly_revenue():
    return run_query("""
        SELECT
            CONVERT(varchar, sale_date, 23) AS sale_date,
            SUM(total_price) AS revenue
        FROM Sales
        WHERE sale_date >= DATEADD(day, -30, GETDATE())
        GROUP BY sale_date
        ORDER BY sale_date
    """)

def get_top_sellers():
    return run_query("""
        SELECT TOP 5
            p.name,
            SUM(s.quantity) AS total_sold,
            SUM(s.total_price) AS total_revenue
        FROM Sales s
        JOIN Products p ON s.product_id = p.id
        GROUP BY p.name
        ORDER BY total_sold DESC
    """)

# ── Products ───────────────────────────────────────────────────

def get_products():
    return run_query("""
        SELECT p.id, p.name, p.category, p.price,
               p.stock_qty, p.reorder_level,
               s.name AS supplier,
               CASE
                   WHEN p.stock_qty = 0 THEN 'Out of Stock'
                   WHEN p.stock_qty <= p.reorder_level THEN 'Low Stock'
                   ELSE 'OK'
               END AS status
        FROM Products p
        LEFT JOIN Suppliers s ON p.supplier_id = s.id
        ORDER BY p.name
    """)

def add_product(name, category, price, stock_qty, reorder_level, supplier_id):
    run_action("""
        INSERT INTO Products (name, category, price, stock_qty, reorder_level, supplier_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, category, price, stock_qty, reorder_level, supplier_id))

def delete_product(product_id):
    run_action("DELETE FROM Products WHERE id = ?", (product_id,))

# ── Stock Movements ────────────────────────────────────────────

def get_movements():
    return run_query("""
        SELECT
            p.name AS product,
            sm.type,
            sm.quantity,
            CAST(sm.quantity * p.price AS DECIMAL(10,2)) AS total_price,
            CONVERT(varchar, sm.movement_date, 23) AS date,
            sm.note
        FROM StockMovements sm
        JOIN Products p ON sm.product_id = p.id
        ORDER BY sm.id DESC
    """)

def add_movement(product_id, mov_type, quantity, note):
    if mov_type == 'OUT':
        df = run_query("SELECT stock_qty FROM Products WHERE id = ?", params=(product_id,))
        if df.empty or df['stock_qty'].iloc[0] < quantity:
            return False, "Not enough stock"

    run_action("""
        INSERT INTO StockMovements (product_id, type, quantity, movement_date, note)
        VALUES (?, ?, ?, GETDATE(), ?)
    """, (product_id, mov_type, quantity, note))

    if mov_type == 'IN':
        run_action("UPDATE Products SET stock_qty = stock_qty + ? WHERE id = ?", (quantity, product_id))
    else:
        run_action("UPDATE Products SET stock_qty = stock_qty - ? WHERE id = ?", (quantity, product_id))

    return True, "OK"

# ── Sales ──────────────────────────────────────────────────────

def get_sales():
    return run_query("""
        SELECT
            p.name AS product,
            s.quantity,
            s.total_price,
            CONVERT(varchar, s.sale_date, 23) AS date
        FROM Sales s
        JOIN Products p ON s.product_id = p.id
        ORDER BY s.id DESC
    """)

def add_sale(product_id, quantity):
    df = run_query("SELECT stock_qty, price FROM Products WHERE id = ?", params=(product_id,))
    if df.empty or df['stock_qty'].iloc[0] < quantity:
        return False, "Not enough stock"
    price = df['price'].iloc[0]
    total = round(price * quantity, 2)
    run_action("""
        INSERT INTO Sales (product_id, quantity, sale_date, total_price)
        VALUES (?, ?, GETDATE(), ?)
    """, (product_id, quantity, total))
    run_action("UPDATE Products SET stock_qty = stock_qty - ? WHERE id = ?", (quantity, product_id))
    return True, "OK"

# ── Reorder ────────────────────────────────────────────────────

def get_reorder_list():
    return run_query("""
        SELECT
            p.name,
            p.stock_qty,
            p.reorder_level,
            (p.reorder_level * 2 - p.stock_qty) AS order_qty,
            ((p.reorder_level * 2 - p.stock_qty) * p.price) AS est_cost,
            s.name AS supplier,
            s.phone,
            CASE WHEN p.stock_qty = 0 THEN 'Out of Stock' ELSE 'Low Stock' END AS status
        FROM Products p
        LEFT JOIN Suppliers s ON p.supplier_id = s.id
        WHERE p.stock_qty <= p.reorder_level
        ORDER BY p.stock_qty ASC
    """)

# ── Suppliers ──────────────────────────────────────────────────

def get_suppliers():
    return run_query("""
        SELECT
            s.id,
            s.name,
            s.contact,
            s.phone,
            s.email,
            COUNT(DISTINCT p.id) AS product_count,
            CAST(ISNULL(SUM(p.stock_qty * p.price), 0) AS DECIMAL(10,2)) AS total_stock_value,
            CONVERT(varchar,
                (SELECT MAX(sm.movement_date)
                 FROM StockMovements sm
                 JOIN Products p2 ON sm.product_id = p2.id
                 WHERE p2.supplier_id = s.id), 23
            ) AS last_movement
        FROM Suppliers s
        LEFT JOIN Products p ON p.supplier_id = s.id
        GROUP BY s.id, s.name, s.contact, s.phone, s.email
        ORDER BY s.name
    """)

def add_supplier(name, contact, phone, email):
    run_action("""
        INSERT INTO Suppliers (name, contact, phone, email)
        VALUES (?, ?, ?, ?)
    """, (name, contact, phone, email))

def delete_supplier(supplier_id):
    run_action("DELETE FROM Suppliers WHERE id = ?", (supplier_id,))

def get_supplier_options():
    return run_query("SELECT id, name FROM Suppliers ORDER BY name")
