"""
Cloud-Based Smart Warehouse & Inventory Management System
With Real-Time Inventory Synchronization using MySQL

Core Capabilities:
- DBMS Unit 1: Relational Data Model, Constraints, Foreign Keys
- DBMS Unit 2: Good Relational Design (3NF/BCNF), Database Views, Stored Procedures
- DBMS Unit 3: ACID Transactions, Concurrency Control (2PL with SELECT ... FOR UPDATE), Deadlock Prevention
- Cloud Computing Unit 1: Cloud-Native Architecture, Stateless Web Tier, Real-Time SSE Event-Driven Sync
- Cloud Computing Unit 2: Public Cloud Compute & Block/Object Storage Design
- Cloud Computing Unit 3: Docker Multi-Container Architecture & Kubernetes (K8s) Orchestration
"""

import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, stream_with_context
from config import config
from database import get_connection, db_transaction
from concurrency_engine import simulate_concurrent_load
from real_time_sync import register_listener, unregister_listener, broadcast_event, format_sse, get_active_listeners_count

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ============================================================
# CONTEXT PROCESSORS & GLOBAL TEMPLATE VARIABLES
# ============================================================

@app.context_processor
def inject_global_data():
    """Injects real-time configuration and low-stock notification counts into all templates."""
    low_stock_count = 0
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS cnt 
                FROM inventory i 
                JOIN products p ON i.product_id = p.product_id 
                WHERE i.quantity <= p.minimum_stock
            """)
            row = cursor.fetchone()
            if row:
                low_stock_count = row["cnt"]
        conn.close()
    except Exception:
        low_stock_count = 0

    return {
        "config": config,
        "low_stock_count": low_stock_count,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# ============================================================
# REAL-TIME SERVER-SENT EVENTS (SSE) STREAM
# ============================================================

@app.route("/api/realtime/stream")
def realtime_stream():
    """
    Server-Sent Events endpoint.
    Maintains persistent HTTP connection with browsers on local network or cloud.
    Pushes real-time stock mutations, sales, and transfer events instantly.
    """
    def event_stream():
        q = register_listener()
        try:
            # Send initial handshake
            init_data = json_dump({
                "status": "connected",
                "lan_ip": config.LOCAL_IP,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            yield format_sse(init_data, event="INIT")

            while True:
                try:
                    # Block waiting for broadcast event with timeout for keep-alive ping
                    event = q.get(timeout=25)
                    yield format_sse(json_dump(event))
                except Exception:
                    # Send periodic keep-alive comment so browser connection remains open
                    yield ": ping\n\n"
        finally:
            unregister_listener(q)

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


def json_dump(obj):
    import json
    return json.dumps(obj)


# ============================================================
# EXECUTIVE DASHBOARD
# ============================================================

@app.route("/")
def index():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Total Inventory Valuation & Units
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(i.quantity * p.price), 0.00) AS total_valuation,
                    COALESCE(SUM(i.quantity), 0) AS total_units,
                    COUNT(DISTINCT i.product_id) AS distinct_skus
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
            """)
            inv_stats = cursor.fetchone()
            total_valuation = float(inv_stats["total_valuation"])
            total_units = int(inv_stats["total_units"])
            product_count = int(inv_stats["distinct_skus"])

            # 2. Warehouses Count
            cursor.execute("SELECT COUNT(*) AS cnt FROM warehouses")
            warehouse_count = cursor.fetchone()["cnt"]

            # 3. Sales Count & Revenue
            cursor.execute("""
                SELECT 
                    COUNT(*) AS sales_count,
                    COALESCE(SUM(total_amount), 0.00) AS total_revenue
                FROM sales
            """)
            sales_stats = cursor.fetchone()
            sales_count = sales_stats["sales_count"]
            total_sales_revenue = float(sales_stats["total_revenue"])

            # 4. Low Stock Alerts View (Unit 2 DBMS SQL View)
            cursor.execute("SELECT * FROM v_low_stock_alerts LIMIT 8")
            low_stock_items = cursor.fetchall()
            low_stock_count = len(low_stock_items)

            # 5. Warehouse Performance View
            cursor.execute("SELECT * FROM v_warehouse_performance")
            warehouse_stats = cursor.fetchall()

            # 6. Recent Audit Ledger Transactions
            cursor.execute("""
                SELECT 
                    t.transaction_id,
                    t.transaction_type,
                    p.product_name,
                    w.warehouse_name,
                    t.quantity,
                    t.previous_quantity,
                    t.new_quantity,
                    t.notes,
                    DATE_FORMAT(t.transaction_date, '%%Y-%%m-%%d %%H:%%i:%%s') AS transaction_date
                FROM inventory_transactions t
                JOIN products p ON t.product_id = p.product_id
                JOIN warehouses w ON t.warehouse_id = w.warehouse_id
                ORDER BY t.transaction_id DESC
                LIMIT 8
            """)
            recent_transactions = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        total_valuation=total_valuation,
        total_units=total_units,
        product_count=product_count,
        warehouse_count=warehouse_count,
        sales_count=sales_count,
        total_sales_revenue=total_sales_revenue,
        low_stock_items=low_stock_items,
        low_stock_count=low_stock_count,
        warehouse_stats=warehouse_stats,
        recent_transactions=recent_transactions
    )


# ============================================================
# INVENTORY MODULE (STOCK CATALOG, ADJUSTMENT & TRANSFERS)
# ============================================================

@app.route("/inventory")
def inventory_list():
    warehouse_id = request.args.get("warehouse_id", "")
    category_id = request.args.get("category_id", "")
    status = request.args.get("status", "")

    query = "SELECT * FROM v_inventory_summary WHERE 1=1"
    params = []

    if warehouse_id:
        query += " AND warehouse_id = %s"
        params.append(warehouse_id)

    if category_id:
        query += " AND category_id = %s"
        params.append(category_id)

    if status:
        query += " AND stock_status = %s"
        params.append(status)

    query += " ORDER BY warehouse_name, product_name"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            items = cursor.fetchall()

            cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()

            cursor.execute("SELECT category_id, category_name FROM categories ORDER BY category_name")
            categories = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "inventory/list.html",
        items=items,
        warehouses=warehouses,
        categories=categories,
        selected_warehouse=warehouse_id,
        selected_category=category_id,
        selected_status=status
    )


@app.route("/inventory/add", methods=["GET", "POST"])
def inventory_add():
    if request.method == "POST":
        product_id = request.form["product_id"]
        warehouse_id = request.form["warehouse_id"]
        quantity = int(request.form.get("quantity", 0))
        notes = request.form.get("notes", "Initial Stock Allocation")

        with db_transaction() as (conn, cursor):
            cursor.execute("""
                INSERT INTO inventory (product_id, warehouse_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + %s
            """, (product_id, warehouse_id, quantity, quantity))

            cursor.execute("""
                INSERT INTO inventory_transactions 
                (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                VALUES (%s, %s, 1, 'Purchase', %s, 0, %s, %s)
            """, (product_id, warehouse_id, quantity, quantity, notes))

        broadcast_event("STOCK_UPDATE", {
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "new_quantity": quantity
        })

        flash("Inventory row added and logged in audit ledger.", "success")
        return redirect(url_for("inventory_list"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, product_name, barcode FROM products ORDER BY product_name")
            products = cursor.fetchall()
            cursor.execute("SELECT warehouse_id, warehouse_name, location FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
    finally:
        conn.close()

    return render_template("inventory/add.html", products=products, warehouses=warehouses)


@app.route("/inventory/edit/<int:inventory_id>", methods=["GET", "POST"])
def inventory_edit(inventory_id):
    if request.method == "POST":
        new_quantity = int(request.form["quantity"])
        notes = request.form.get("notes", "Manual Physical Stock Audit Adjustment")

        with db_transaction() as (conn, cursor):
            # Lock row for update
            cursor.execute("""
                SELECT inventory_id, product_id, warehouse_id, quantity 
                FROM inventory 
                WHERE inventory_id = %s 
                FOR UPDATE
            """, (inventory_id,))
            current = cursor.fetchone()

            if not current:
                flash("Inventory record not found.", "danger")
                return redirect(url_for("inventory_list"))

            prev_qty = current["quantity"]
            diff = new_quantity - prev_qty

            cursor.execute("""
                UPDATE inventory 
                SET quantity = %s, version = version + 1 
                WHERE inventory_id = %s
            """, (new_quantity, inventory_id))

            cursor.execute("""
                INSERT INTO inventory_transactions 
                (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                VALUES (%s, %s, 1, 'Adjustment', %s, %s, %s, %s)
            """, (current["product_id"], current["warehouse_id"], abs(diff), prev_qty, new_quantity, notes))

        broadcast_event("STOCK_ADJUSTMENT", {
            "inventory_id": inventory_id,
            "product_id": current["product_id"],
            "new_quantity": new_quantity
        })

        flash(f"Stock quantity successfully adjusted from {prev_qty} to {new_quantity}.", "success")
        return redirect(url_for("inventory_list"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT i.*, p.product_name, p.barcode, w.warehouse_name 
                FROM inventory i
                JOIN products p ON i.product_id = p.product_id
                JOIN warehouses w ON i.warehouse_id = w.warehouse_id
                WHERE i.inventory_id = %s
            """, (inventory_id,))
            item = cursor.fetchone()
    finally:
        conn.close()

    if not item:
        flash("Inventory row not found.", "danger")
        return redirect(url_for("inventory_list"))

    return render_template("inventory/edit.html", item=item)


@app.route("/inventory/transfer", methods=["GET", "POST"])
def stock_transfer():
    """
    Executes Inter-Warehouse Stock Transfer.
    Demonstrates DBMS Unit 3 Concurrency Control & Deadlock Prevention:
    - Row-level Exclusive Locks (SELECT ... FOR UPDATE) acquired in canonical ascending ID order.
    - Two-Phase Commit ensures atomic debit and credit.
    - Automatic rollback if source has insufficient stock.
    """
    if request.method == "POST":
        product_id = int(request.form["product_id"])
        from_wh_id = int(request.form["from_warehouse_id"])
        to_wh_id = int(request.form["to_warehouse_id"])
        quantity = int(request.form["quantity"])
        user_id = int(request.form.get("user_id", 1))
        notes = request.form.get("notes", "Inter-Warehouse Rebalancing Transfer")

        if from_wh_id == to_wh_id:
            flash("Source and destination warehouses cannot be the same.", "danger")
            return redirect(url_for("stock_transfer"))

        if quantity <= 0:
            flash("Transfer quantity must be greater than zero.", "danger")
            return redirect(url_for("stock_transfer"))

        try:
            with db_transaction() as (conn, cursor):
                # Deadlock Prevention: Acquire row locks in canonical ascending warehouse_id order
                wh_first = min(from_wh_id, to_wh_id)
                wh_second = max(from_wh_id, to_wh_id)

                # Ensure destination inventory row exists
                cursor.execute("""
                    INSERT IGNORE INTO inventory (product_id, warehouse_id, quantity)
                    VALUES (%s, %s, 0)
                """, (product_id, to_wh_id))

                # Lock first warehouse row
                cursor.execute("""
                    SELECT quantity FROM inventory 
                    WHERE product_id = %s AND warehouse_id = %s 
                    FOR UPDATE
                """, (product_id, wh_first))
                row_first = cursor.fetchone()

                # Lock second warehouse row
                cursor.execute("""
                    SELECT quantity FROM inventory 
                    WHERE product_id = %s AND warehouse_id = %s 
                    FOR UPDATE
                """, (product_id, wh_second))
                row_second = cursor.fetchone()

                # Determine source and destination stock from acquired locks
                src_stock = (row_first["quantity"] if wh_first == from_wh_id else row_second["quantity"]) if (row_first and row_second) else 0
                dst_stock = (row_first["quantity"] if wh_first == to_wh_id else row_second["quantity"]) if (row_first and row_second) else 0

                if src_stock < quantity:
                    raise ValueError(f"Insufficient stock in source warehouse ({src_stock} available, {quantity} requested).")

                # Debit Source
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - %s, version = version + 1 
                    WHERE product_id = %s AND warehouse_id = %s
                """, (quantity, product_id, from_wh_id))

                # Credit Destination
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity + %s, version = version + 1 
                    WHERE product_id = %s AND warehouse_id = %s
                """, (quantity, product_id, to_wh_id))

                # Record 2 Immutable Audit Ledger Entries
                cursor.execute("""
                    INSERT INTO inventory_transactions 
                    (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                    VALUES 
                    (%s, %s, %s, 'Transfer_Out', %s, %s, %s, %s),
                    (%s, %s, %s, 'Transfer_In', %s, %s, %s, %s)
                """, (
                    product_id, from_wh_id, user_id, quantity, src_stock, src_stock - quantity, f"{notes} (To WH #{to_wh_id})",
                    product_id, to_wh_id, user_id, quantity, dst_stock, dst_stock + quantity, f"{notes} (From WH #{from_wh_id})"
                ))

            # Broadcast real-time update to all connected laptops/clients
            broadcast_event("STOCK_TRANSFER", {
                "product_id": product_id,
                "from_warehouse_id": from_wh_id,
                "to_warehouse_id": to_wh_id,
                "quantity": quantity
            })

            flash(f"Successfully transferred {quantity} units atomically from Warehouse #{from_wh_id} to #{to_wh_id}.", "success")
            return redirect(url_for("inventory_list"))

        except Exception as e:
            flash(f"Transfer failed and rolled back: {str(e)}", "danger")
            return redirect(url_for("stock_transfer"))

    # GET Request
    product_id = request.args.get("product_id", "")
    from_wh_id = request.args.get("from_warehouse_id", "")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, product_name, barcode FROM products ORDER BY product_name")
            products = cursor.fetchall()
            cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
            cursor.execute("SELECT user_id, full_name, role FROM users ORDER BY full_name")
            users = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "inventory/transfer.html",
        products=products,
        warehouses=warehouses,
        users=users,
        selected_product_id=product_id,
        selected_from_wh=from_wh_id
    )


# ============================================================
# SALES & OUTBOUND DISPATCH MODULE (ACID POS CHECKOUT)
# ============================================================

@app.route("/sales")
def sales_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.sale_id,
                    s.reference_no,
                    c.customer_name,
                    w.warehouse_name,
                    u.full_name,
                    s.total_amount,
                    s.payment_status,
                    DATE_FORMAT(s.sale_date, '%%Y-%%m-%%d %%H:%%i') AS sale_date
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                JOIN warehouses w ON s.warehouse_id = w.warehouse_id
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.sale_id DESC
            """)
            sales = cursor.fetchall()
    finally:
        conn.close()

    return render_template("sales/list.html", sales=sales)


@app.route("/sales/new", methods=["GET", "POST"])
def sales_new():
    """
    Creates an Outbound Sale Order.
    DBMS Unit 3 ACID Transaction Guarantee:
    - Locks all requested inventory rows with SELECT ... FOR UPDATE.
    - Prevents overselling if multiple sales occur concurrently.
    - Inserts sale, sale items, deducts inventory, and writes audit trail atomically.
    """
    if request.method == "POST":
        customer_id = int(request.form["customer_id"])
        warehouse_id = int(request.form["warehouse_id"])
        user_id = int(request.form.get("user_id", 1))
        payment_status = request.form.get("payment_status", "Paid")
        product_ids = request.form.getlist("product_ids[]")
        quantities = request.form.getlist("quantities[]")

        if not product_ids:
            flash("Sale must contain at least one product.", "danger")
            return redirect(url_for("sales_new"))

        # Aggregate quantities if same product selected multiple times
        items_map = {}
        for pid_str, qty_str in zip(product_ids, quantities):
            pid = int(pid_str)
            qty = int(qty_str)
            if qty > 0:
                items_map[pid] = items_map.get(pid, 0) + qty

        if not items_map:
            flash("Please enter valid quantities for items.", "danger")
            return redirect(url_for("sales_new"))

        ref_no = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"

        try:
            with db_transaction() as (conn, cursor):
                total_sale_amount = 0.0
                sale_items_data = []

                # Deadlock Prevention: Sort product IDs before acquiring row locks
                sorted_pids = sorted(items_map.keys())

                for pid in sorted_pids:
                    req_qty = items_map[pid]

                    # 1. Acquire Exclusive Row Lock (X-Lock)
                    cursor.execute("""
                        SELECT i.quantity, p.product_name, p.price 
                        FROM inventory i
                        JOIN products p ON i.product_id = p.product_id
                        WHERE i.product_id = %s AND i.warehouse_id = %s
                        FOR UPDATE
                    """, (pid, warehouse_id))
                    inv_row = cursor.fetchone()

                    if not inv_row:
                        raise ValueError(f"Product #{pid} is not stocked at selected warehouse.")

                    current_stock = inv_row["quantity"]
                    unit_price = float(inv_row["price"])
                    subtotal = unit_price * req_qty

                    # 2. Strict Check Constraint Validation
                    if current_stock < req_qty:
                        raise ValueError(f"Overselling Prevented! Product '{inv_row['product_name']}' has only {current_stock} units available, but {req_qty} requested.")

                    # 3. Deduct Inventory Stock
                    cursor.execute("""
                        UPDATE inventory 
                        SET quantity = quantity - %s, version = version + 1 
                        WHERE product_id = %s AND warehouse_id = %s
                    """, (req_qty, pid, warehouse_id))

                    # 4. Record Audit Ledger Entry
                    cursor.execute("""
                        INSERT INTO inventory_transactions 
                        (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                        VALUES (%s, %s, %s, 'Sale', %s, %s, %s, %s)
                    """, (pid, warehouse_id, user_id, req_qty, current_stock, current_stock - req_qty, f"Outbound Sale {ref_no}"))

                    total_sale_amount += subtotal
                    sale_items_data.append((pid, req_qty, unit_price, subtotal))

                # 5. Insert Sale Master Record
                cursor.execute("""
                    INSERT INTO sales (reference_no, customer_id, user_id, warehouse_id, total_amount, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (ref_no, customer_id, user_id, warehouse_id, total_sale_amount, payment_status))
                sale_id = cursor.lastrowid

                # 6. Insert Sale Detail Items
                for pid, req_qty, unit_price, subtotal in sale_items_data:
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (sale_id, pid, req_qty, unit_price, subtotal))

            # Broadcast Real-Time SSE Notification
            broadcast_event("SALE_COMPLETED", {
                "sale_id": sale_id,
                "reference_no": ref_no,
                "warehouse_id": warehouse_id,
                "total_amount": total_sale_amount
            })

            flash(f"Sale order {ref_no} processed and committed successfully (Total: ₹{total_sale_amount:,.2f}).", "success")
            return redirect(url_for("sales_detail", sale_id=sale_id))

        except Exception as e:
            flash(f"Transaction Aborted & Rolled Back: {str(e)}", "danger")
            return redirect(url_for("sales_new"))

    # GET Request
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT customer_id, customer_name, phone FROM customers ORDER BY customer_name")
            customers = cursor.fetchall()
            cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
            cursor.execute("SELECT product_id, product_name, price, barcode FROM products ORDER BY product_name")
            products = cursor.fetchall()
            cursor.execute("SELECT user_id, full_name, role FROM users ORDER BY full_name")
            users = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "sales/new.html",
        customers=customers,
        warehouses=warehouses,
        products=products,
        users=users
    )


@app.route("/sales/<int:sale_id>")
def sales_detail(sale_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.*,
                    c.customer_name,
                    c.phone,
                    c.email,
                    c.address,
                    w.warehouse_name,
                    u.full_name,
                    DATE_FORMAT(s.sale_date, '%%Y-%%m-%%d %%H:%%i:%%s') AS sale_date
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                JOIN warehouses w ON s.warehouse_id = w.warehouse_id
                JOIN users u ON s.user_id = u.user_id
                WHERE s.sale_id = %s
            """, (sale_id,))
            sale = cursor.fetchone()

            if not sale:
                flash("Sale record not found.", "danger")
                return redirect(url_for("sales_list"))

            cursor.execute("""
                SELECT si.*, p.product_name, p.barcode 
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                WHERE si.sale_id = %s
            """, (sale_id,))
            items = cursor.fetchall()
    finally:
        conn.close()

    return render_template("sales/detail.html", sale=sale, items=items)


# ============================================================
# PURCHASE ORDERS & INBOUND REPLENISHMENT
# ============================================================

@app.route("/purchases")
def purchases_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    po.*,
                    s.supplier_name,
                    w.warehouse_name,
                    u.full_name,
                    DATE_FORMAT(po.order_date, '%%Y-%%m-%%d %%H:%%i') AS order_date
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.supplier_id
                JOIN warehouses w ON po.warehouse_id = w.warehouse_id
                JOIN users u ON po.user_id = u.user_id
                ORDER BY po.purchase_order_id DESC
            """)
            purchase_orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template("purchases/list.html", purchase_orders=purchase_orders)


@app.route("/purchases/new", methods=["GET", "POST"])
def purchases_new():
    if request.method == "POST":
        supplier_id = int(request.form["supplier_id"])
        warehouse_id = int(request.form["warehouse_id"])
        user_id = int(request.form.get("user_id", 1))
        product_id = int(request.form["product_id"])
        quantity = int(request.form["quantity"])

        po_num = f"PO-2026-{uuid.uuid4().hex[:6].upper()}"

        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT price FROM products WHERE product_id = %s", (product_id,))
            price_row = cursor.fetchone()
            unit_price = float(price_row["price"]) if price_row else 1000.0
            total_amount = unit_price * quantity

            cursor.execute("""
                INSERT INTO purchase_orders (po_number, supplier_id, warehouse_id, user_id, total_amount, status)
                VALUES (%s, %s, %s, %s, %s, 'Pending')
            """, (po_num, supplier_id, warehouse_id, user_id, total_amount))
            po_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (po_id, product_id, quantity, unit_price, total_amount))

        broadcast_event("PO_CREATED", {
            "po_id": po_id,
            "po_number": po_num,
            "supplier_id": supplier_id
        })

        flash(f"Purchase Order {po_num} created successfully.", "success")
        return redirect(url_for("purchases_detail", po_id=po_id))

    # Prepopulate if from low stock trigger
    supplier_id = request.args.get("supplier_id", "")
    warehouse_id = request.args.get("warehouse_id", "")
    product_id = request.args.get("product_id", "")
    quantity = request.args.get("quantity", "")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT supplier_id, supplier_name, gst_number FROM suppliers ORDER BY supplier_name")
            suppliers = cursor.fetchall()
            cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
            cursor.execute("SELECT product_id, product_name, price FROM products ORDER BY product_name")
            products = cursor.fetchall()
            cursor.execute("SELECT user_id, full_name, role FROM users ORDER BY full_name")
            users = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "purchases/new.html",
        suppliers=suppliers,
        warehouses=warehouses,
        products=products,
        users=users,
        pre_supplier_id=supplier_id,
        pre_warehouse_id=warehouse_id,
        pre_product_id=product_id,
        pre_quantity=quantity
    )


@app.route("/purchases/auto-generate", methods=["POST"])
def auto_generate_pos():
    """
    Automated Low-Stock Replenishment Engine.
    Scans v_low_stock_alerts view and batches reorders by supplier into draft purchase orders.
    """
    created_count = 0
    with db_transaction() as (conn, cursor):
        cursor.execute("SELECT * FROM v_low_stock_alerts")
        low_items = cursor.fetchall()

        # Group by (supplier_id, warehouse_id)
        grouped = {}
        for item in low_items:
            key = (item["supplier_id"], item["warehouse_id"])
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)

        for (sup_id, wh_id), items in grouped.items():
            po_num = f"PO-AUTO-{uuid.uuid4().hex[:6].upper()}"
            po_total = sum(float(it["unit_price"]) * int(it["suggested_reorder_qty"]) for it in items)

            cursor.execute("""
                INSERT INTO purchase_orders (po_number, supplier_id, warehouse_id, user_id, total_amount, status, auto_generated)
                VALUES (%s, %s, %s, 1, %s, 'Pending', TRUE)
            """, (po_num, sup_id, wh_id, po_total))
            po_id = cursor.lastrowid

            for it in items:
                qty = int(it["suggested_reorder_qty"])
                price = float(it["unit_price"])
                cursor.execute("""
                    INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                """, (po_id, it["product_id"], qty, price, price * qty))

            created_count += 1

    broadcast_event("PO_CREATED", {
        "auto_generated": True,
        "count": created_count
    })

    flash(f"Successfully auto-generated {created_count} replenishment Purchase Orders for depleted inventory.", "success")
    return redirect(url_for("purchases_list"))


@app.route("/purchases/<int:po_id>")
def purchases_detail(po_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    po.*,
                    s.supplier_name,
                    s.contact_person,
                    s.phone,
                    s.gst_number,
                    s.address,
                    w.warehouse_name,
                    w.location,
                    w.manager_name,
                    u.full_name,
                    DATE_FORMAT(po.order_date, '%%Y-%%m-%%d %%H:%%i') AS order_date
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.supplier_id
                JOIN warehouses w ON po.warehouse_id = w.warehouse_id
                JOIN users u ON po.user_id = u.user_id
                WHERE po.purchase_order_id = %s
            """, (po_id,))
            po = cursor.fetchone()

            if not po:
                flash("Purchase Order not found.", "danger")
                return redirect(url_for("purchases_list"))

            cursor.execute("""
                SELECT poi.*, p.product_name, p.barcode 
                FROM purchase_order_items poi
                JOIN products p ON poi.product_id = p.product_id
                WHERE poi.purchase_order_id = %s
            """, (po_id,))
            items = cursor.fetchall()
    finally:
        conn.close()

    return render_template("purchases/detail.html", po=po, items=items)


@app.route("/purchases/<int:po_id>/receive", methods=["POST"])
def purchases_receive(po_id):
    """
    Receives an inbound Purchase Order shipment.
    Atomically updates PO status to 'Received', credits inventory quantities,
    and writes audit trail records inside a single ACID transaction.
    """
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("SELECT * FROM purchase_orders WHERE purchase_order_id = %s FOR UPDATE", (po_id,))
            po = cursor.fetchone()

            if not po or po["status"] == "Received":
                flash("Purchase order is already received or does not exist.", "warning")
                return redirect(url_for("purchases_detail", po_id=po_id))

            cursor.execute("SELECT * FROM purchase_order_items WHERE purchase_order_id = %s", (po_id,))
            po_items = cursor.fetchall()

            for item in po_items:
                pid = item["product_id"]
                wh_id = po["warehouse_id"]
                qty = item["quantity"]

                # Lock inventory row
                cursor.execute("""
                    SELECT quantity FROM inventory 
                    WHERE product_id = %s AND warehouse_id = %s 
                    FOR UPDATE
                """, (pid, wh_id))
                curr_inv = cursor.fetchone()
                prev_qty = curr_inv["quantity"] if curr_inv else 0

                # Credit inventory
                cursor.execute("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE quantity = quantity + %s, version = version + 1
                """, (pid, wh_id, qty, qty))

                # Log Transaction
                cursor.execute("""
                    INSERT INTO inventory_transactions 
                    (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                    VALUES (%s, %s, %s, 'Purchase', %s, %s, %s, %s)
                """, (pid, wh_id, po["user_id"], qty, prev_qty, prev_qty + qty, f"Inbound PO Receipt {po['po_number']}"))

            # Update PO status
            cursor.execute("UPDATE purchase_orders SET status = 'Received' WHERE purchase_order_id = %s", (po_id,))

        broadcast_event("PO_RECEIVED", {
            "po_id": po_id,
            "po_number": po["po_number"],
            "warehouse_id": po["warehouse_id"]
        })

        flash(f"Shipment for PO {po['po_number']} received and stock credited successfully.", "success")
    except Exception as e:
        flash(f"Error receiving shipment: {str(e)}", "danger")

    return redirect(url_for("purchases_detail", po_id=po_id))


# ============================================================
# AUDIT LEDGER MODULE
# ============================================================

@app.route("/transactions")
def transactions_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.transaction_id,
                    t.transaction_type,
                    p.product_name,
                    w.warehouse_name,
                    u.full_name,
                    t.quantity,
                    t.previous_quantity,
                    t.new_quantity,
                    t.notes,
                    DATE_FORMAT(t.transaction_date, '%%Y-%%m-%%d %%H:%%i:%%s') AS transaction_date
                FROM inventory_transactions t
                JOIN products p ON t.product_id = p.product_id
                JOIN warehouses w ON t.warehouse_id = w.warehouse_id
                JOIN users u ON t.user_id = u.user_id
                ORDER BY t.transaction_id DESC
                LIMIT 100
            """)
            transactions = cursor.fetchall()
    finally:
        conn.close()

    return render_template("transactions/list.html", transactions=transactions)


# ============================================================
# MASTER DATA CRUD (PRODUCTS, WAREHOUSES, SUPPLIERS, CATEGORIES, CUSTOMERS)
# ============================================================

# Products
@app.route("/products")
def products_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.*, c.category_name, s.supplier_name 
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                JOIN suppliers s ON p.supplier_id = s.supplier_id
                ORDER BY p.product_name
            """)
            products = cursor.fetchall()
            cursor.execute("SELECT * FROM categories ORDER BY category_name")
            categories = cursor.fetchall()
            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_name")
            suppliers = cursor.fetchall()
    finally:
        conn.close()

    return render_template("master/products.html", products=products, categories=categories, suppliers=suppliers)


@app.route("/products/add", methods=["POST"])
def products_add():
    name = request.form["product_name"]
    cat_id = request.form["category_id"]
    sup_id = request.form["supplier_id"]
    barcode = request.form["barcode"]
    price = request.form["price"]
    min_stock = request.form.get("minimum_stock", 10)
    desc = request.form.get("description", "")

    with db_transaction() as (conn, cursor):
        cursor.execute("""
            INSERT INTO products (product_name, category_id, supplier_id, barcode, price, minimum_stock, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, cat_id, sup_id, barcode, price, min_stock, desc))

    flash(f"Product '{name}' added to catalog.", "success")
    return redirect(url_for("products_list"))


@app.route("/products/delete/<int:product_id>")
def products_delete(product_id):
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        flash("Product deleted successfully.", "success")
    except Exception as e:
        flash(f"Cannot delete product (Referential Integrity Constraint in effect): {e}", "danger")
    return redirect(url_for("products_list"))


# Warehouses
@app.route("/warehouses")
def warehouses_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
    finally:
        conn.close()

    return render_template("master/warehouses.html", warehouses=warehouses)


@app.route("/warehouses/add", methods=["POST"])
def warehouses_add():
    name = request.form["warehouse_name"]
    loc = request.form["location"]
    mgr = request.form.get("manager_name", "")
    phone = request.form.get("contact_number", "")
    cap = request.form.get("capacity_sqft", 10000)

    with db_transaction() as (conn, cursor):
        cursor.execute("""
            INSERT INTO warehouses (warehouse_name, location, manager_name, contact_number, capacity_sqft)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, loc, mgr, phone, cap))

    flash(f"Warehouse '{name}' added successfully.", "success")
    return redirect(url_for("warehouses_list"))


@app.route("/warehouses/delete/<int:warehouse_id>")
def warehouses_delete(warehouse_id):
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("DELETE FROM warehouses WHERE warehouse_id = %s", (warehouse_id,))
        flash("Warehouse facility deleted successfully.", "success")
    except Exception as e:
        flash(f"Cannot delete warehouse (Contains inventory / active references): {e}", "danger")
    return redirect(url_for("warehouses_list"))


# Suppliers
@app.route("/suppliers")
def suppliers_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM suppliers ORDER BY supplier_name")
            suppliers = cursor.fetchall()
    finally:
        conn.close()

    return render_template("master/suppliers.html", suppliers=suppliers)


@app.route("/suppliers/add", methods=["POST"])
def suppliers_add():
    name = request.form["supplier_name"]
    contact = request.form.get("contact_person", "")
    phone = request.form.get("phone", "")
    email = request.form.get("email", "")
    gst = request.form.get("gst_number", "")
    addr = request.form.get("address", "")

    with db_transaction() as (conn, cursor):
        cursor.execute("""
            INSERT INTO suppliers (supplier_name, contact_person, phone, email, gst_number, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, contact, phone, email, gst, addr))

    flash(f"Supplier '{name}' registered.", "success")
    return redirect(url_for("suppliers_list"))


@app.route("/suppliers/delete/<int:supplier_id>")
def suppliers_delete(supplier_id):
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("DELETE FROM suppliers WHERE supplier_id = %s", (supplier_id,))
        flash("Supplier deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete supplier (Foreign Key constraint active): {e}", "danger")
    return redirect(url_for("suppliers_list"))


# Categories
@app.route("/categories")
def categories_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM categories ORDER BY category_name")
            categories = cursor.fetchall()
    finally:
        conn.close()

    return render_template("master/categories.html", categories=categories)


@app.route("/categories/add", methods=["POST"])
def categories_add():
    name = request.form["category_name"]
    desc = request.form.get("description", "")

    with db_transaction() as (conn, cursor):
        cursor.execute("INSERT INTO categories (category_name, description) VALUES (%s, %s)", (name, desc))

    flash(f"Category '{name}' added.", "success")
    return redirect(url_for("categories_list"))


@app.route("/categories/delete/<int:category_id>")
def categories_delete(category_id):
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
        flash("Category deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete category: {e}", "danger")
    return redirect(url_for("categories_list"))


# Customers
@app.route("/customers")
def customers_list():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM customers ORDER BY customer_name")
            customers = cursor.fetchall()
    finally:
        conn.close()

    return render_template("master/customers.html", customers=customers)


@app.route("/customers/add", methods=["POST"])
def customers_add():
    name = request.form["customer_name"]
    phone = request.form.get("phone", "")
    email = request.form.get("email", "")
    addr = request.form.get("address", "")

    with db_transaction() as (conn, cursor):
        cursor.execute("""
            INSERT INTO customers (customer_name, phone, email, address)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, addr))

    flash(f"Customer '{name}' registered.", "success")
    return redirect(url_for("customers_list"))


@app.route("/customers/delete/<int:customer_id>")
def customers_delete(customer_id):
    try:
        with db_transaction() as (conn, cursor):
            cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
        flash("Customer deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete customer: {e}", "danger")
    return redirect(url_for("customers_list"))


# ============================================================
# CONCURRENCY CONTROL & STRESS TESTING LAB
# ============================================================

@app.route("/concurrency-lab")
def concurrency_lab():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT product_id, product_name, barcode FROM products ORDER BY product_name")
            products = cursor.fetchall()
            cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses ORDER BY warehouse_name")
            warehouses = cursor.fetchall()
    finally:
        conn.close()

    return render_template("concurrency_lab.html", products=products, warehouses=warehouses)


@app.route("/api/concurrency/simulate", methods=["POST"])
def api_concurrency_simulate():
    data = request.get_json() or {}
    product_id = int(data.get("product_id", 1))
    warehouse_id = int(data.get("warehouse_id", 1))
    initial_stock = int(data.get("initial_stock", 5))
    num_threads = int(data.get("num_threads", 3))
    qty_per_buyer = int(data.get("qty_per_buyer", 2))
    mode = data.get("mode", "pessimistic")

    t_start = time.time()
    try:
        simulation_res = simulate_concurrent_load(
            product_id=product_id,
            warehouse_id=warehouse_id,
            initial_stock=initial_stock,
            num_threads=num_threads,
            qty_per_buyer=qty_per_buyer,
            mode=mode
        )
        elapsed = round((time.time() - t_start) * 1000, 2)
        return jsonify({
            "success": True,
            "total_elapsed_ms": elapsed,
            "simulation": simulation_res
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/network-status")
def network_status():
    return render_template(
        "network_status.html",
        active_listeners=get_active_listeners_count()
    )


# ============================================================
# HEALTH CHECK (FOR DOCKER & KUBERNETES LIVENESS PROBES)
# ============================================================

@app.route("/health")
def health_check():
    """Cloud-Native Liveness & Readiness Probe for Docker & Kubernetes."""
    from database import test_connection
    db_ok, db_info = test_connection()
    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "healthy" if db_ok else "unhealthy",
        "app_version": config.APP_VERSION,
        "environment": config.ENVIRONMENT,
        "database_connected": db_ok,
        "database_meta": db_info if db_ok else str(db_info),
        "timestamp": datetime.now().isoformat()
    }), status_code


if __name__ == "__main__":
    print("=" * 65)
    print(f"  {config.SYSTEM_NAME}")
    print("=" * 65)
    print(f"  Local Access:   http://localhost:{config.PORT}")
    print(f"  Network (LAN):  http://{config.LOCAL_IP}:{config.PORT}")
    print("=" * 65)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)
