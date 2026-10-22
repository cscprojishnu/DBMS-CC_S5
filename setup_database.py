"""
Database Setup & Seed Data Script
Smart Warehouse & Inventory Management System

DBMS Syllabus Concepts Embedded:
- Unit 1: Relational Data Model, Constraints, Primary & Foreign Keys, 1:N & N:M Reductions
- Unit 2: Good Relational Design (3NF/BCNF), Integrity Constraints, Advanced SQL (Views, Stored Procedures, Indexes)
- Unit 3: Transactional consistency, Lock-friendly indexing, Audit ledger
"""

import pymysql
from config import config


def initialize_database():
    print(f"Connecting to MySQL server at {config.DB_HOST}:{config.DB_PORT} as '{config.DB_USER}'...")
    try:
        connection = pymysql.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = connection.cursor()
        print("Connected to MySQL server.")
    except Exception as e:
        print(f"ERROR: Could not connect to MySQL server: {e}")
        return False

    # 1. Create Database
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE `{config.DB_NAME}`")
    print(f"Database '{config.DB_NAME}' initialized and selected.")

    # 2. Define Tables with full Relational Schema & Constraints
    tables = {}

    tables["users"] = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role ENUM('Admin', 'Warehouse Manager', 'Warehouse Staff', 'Sales Executive') 
            NOT NULL DEFAULT 'Sales Executive',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    tables["categories"] = """
    CREATE TABLE IF NOT EXISTS categories (
        category_id INT AUTO_INCREMENT PRIMARY KEY,
        category_name VARCHAR(100) NOT NULL UNIQUE,
        description VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    tables["suppliers"] = """
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INT AUTO_INCREMENT PRIMARY KEY,
        supplier_name VARCHAR(150) NOT NULL,
        contact_person VARCHAR(100),
        phone VARCHAR(20),
        email VARCHAR(100),
        address VARCHAR(255),
        gst_number VARCHAR(30) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    tables["products"] = """
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(150) NOT NULL,
        category_id INT NOT NULL,
        supplier_id INT NOT NULL,
        barcode VARCHAR(100) UNIQUE,
        price DECIMAL(10,2) NOT NULL,
        minimum_stock INT NOT NULL DEFAULT 10,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_product_category
            FOREIGN KEY (category_id)
            REFERENCES categories(category_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_product_supplier
            FOREIGN KEY (supplier_id)
            REFERENCES suppliers(supplier_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT chk_product_price CHECK (price >= 0),
        CONSTRAINT chk_product_min_stock CHECK (minimum_stock >= 0)
    ) ENGINE=InnoDB;
    """

    tables["warehouses"] = """
    CREATE TABLE IF NOT EXISTS warehouses (
        warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
        warehouse_name VARCHAR(150) NOT NULL UNIQUE,
        location VARCHAR(255) NOT NULL,
        manager_name VARCHAR(100),
        contact_number VARCHAR(20),
        capacity_sqft INT DEFAULT 10000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    tables["inventory"] = """
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        warehouse_id INT NOT NULL,
        quantity INT NOT NULL DEFAULT 0,
        version INT NOT NULL DEFAULT 1,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP,

        CONSTRAINT fk_inventory_product
            FOREIGN KEY (product_id)
            REFERENCES products(product_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_inventory_warehouse
            FOREIGN KEY (warehouse_id)
            REFERENCES warehouses(warehouse_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT unique_product_warehouse
            UNIQUE (product_id, warehouse_id),

        CONSTRAINT chk_inventory_quantity
            CHECK (quantity >= 0)
    ) ENGINE=InnoDB;
    """

    tables["customers"] = """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT AUTO_INCREMENT PRIMARY KEY,
        customer_name VARCHAR(150) NOT NULL,
        phone VARCHAR(20),
        email VARCHAR(100),
        address VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    tables["sales"] = """
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INT AUTO_INCREMENT PRIMARY KEY,
        reference_no VARCHAR(50) UNIQUE,
        customer_id INT NOT NULL,
        user_id INT NOT NULL,
        warehouse_id INT NOT NULL,
        sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
        payment_status ENUM('Paid', 'Pending', 'Credit') NOT NULL DEFAULT 'Paid',

        CONSTRAINT fk_sale_customer
            FOREIGN KEY (customer_id)
            REFERENCES customers(customer_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_sale_user
            FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_sale_warehouse
            FOREIGN KEY (warehouse_id)
            REFERENCES warehouses(warehouse_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """

    tables["sale_items"] = """
    CREATE TABLE IF NOT EXISTS sale_items (
        sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
        sale_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        subtotal DECIMAL(12,2) NOT NULL,

        CONSTRAINT fk_sale_item_sale
            FOREIGN KEY (sale_id)
            REFERENCES sales(sale_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        CONSTRAINT fk_sale_item_product
            FOREIGN KEY (product_id)
            REFERENCES products(product_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT chk_sale_quantity
            CHECK (quantity > 0)
    ) ENGINE=InnoDB;
    """

    tables["purchase_orders"] = """
    CREATE TABLE IF NOT EXISTS purchase_orders (
        purchase_order_id INT AUTO_INCREMENT PRIMARY KEY,
        po_number VARCHAR(50) UNIQUE,
        supplier_id INT NOT NULL,
        warehouse_id INT NOT NULL,
        user_id INT NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('Pending', 'Approved', 'Received', 'Cancelled')
            NOT NULL DEFAULT 'Pending',
        total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
        auto_generated BOOLEAN DEFAULT FALSE,

        CONSTRAINT fk_po_supplier
            FOREIGN KEY (supplier_id)
            REFERENCES suppliers(supplier_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_po_warehouse
            FOREIGN KEY (warehouse_id)
            REFERENCES warehouses(warehouse_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_po_user
            FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """

    tables["purchase_order_items"] = """
    CREATE TABLE IF NOT EXISTS purchase_order_items (
        purchase_order_item_id INT AUTO_INCREMENT PRIMARY KEY,
        purchase_order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        subtotal DECIMAL(12,2) NOT NULL,

        CONSTRAINT fk_po_item_order
            FOREIGN KEY (purchase_order_id)
            REFERENCES purchase_orders(purchase_order_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,

        CONSTRAINT fk_po_item_product
            FOREIGN KEY (product_id)
            REFERENCES products(product_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT chk_po_quantity
            CHECK (quantity > 0)
    ) ENGINE=InnoDB;
    """

    tables["inventory_transactions"] = """
    CREATE TABLE IF NOT EXISTS inventory_transactions (
        transaction_id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        warehouse_id INT NOT NULL,
        user_id INT NOT NULL,
        transaction_type ENUM(
            'Purchase',
            'Sale',
            'Return',
            'Adjustment',
            'Transfer_Out',
            'Transfer_In'
        ) NOT NULL,
        quantity INT NOT NULL,
        previous_quantity INT NOT NULL,
        new_quantity INT NOT NULL,
        notes VARCHAR(255),
        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_transaction_product
            FOREIGN KEY (product_id)
            REFERENCES products(product_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_transaction_warehouse
            FOREIGN KEY (warehouse_id)
            REFERENCES warehouses(warehouse_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        CONSTRAINT fk_transaction_user
            FOREIGN KEY (user_id)
            REFERENCES users(user_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """

    for name, ddl in tables.items():
        try:
            cursor.execute(ddl)
            print(f"Table '{name}' verified/created.")
        except Exception as e:
            print(f"Warning on table {name}: {e}")

    # Schema Migrations: Safely add columns if tables already existed previously
    migrations = [
        "ALTER TABLE warehouses ADD COLUMN capacity_sqft INT DEFAULT 10000",
        "ALTER TABLE inventory ADD COLUMN version INT NOT NULL DEFAULT 1",
        "ALTER TABLE products ADD COLUMN description TEXT",
        "ALTER TABLE sales ADD COLUMN reference_no VARCHAR(50) UNIQUE",
        "ALTER TABLE sales ADD COLUMN payment_status ENUM('Paid', 'Pending', 'Credit') NOT NULL DEFAULT 'Paid'",
        "ALTER TABLE purchase_orders ADD COLUMN po_number VARCHAR(50) UNIQUE",
        "ALTER TABLE purchase_orders ADD COLUMN auto_generated BOOLEAN DEFAULT FALSE",
        "ALTER TABLE inventory_transactions ADD COLUMN notes VARCHAR(255)",
        "ALTER TABLE inventory_transactions MODIFY COLUMN transaction_type ENUM('Purchase', 'Sale', 'Return', 'Adjustment', 'Transfer', 'Transfer_Out', 'Transfer_In') NOT NULL"
    ]
    for mig in migrations:
        try:
            cursor.execute(mig)
        except Exception:
            pass  # Already applied or column exists

    # 3. Create Performance Indexes for Relational Queries (Unit 1 & 2 DBMS)
    indexes = [
        "CREATE INDEX idx_inv_prod_wh ON inventory(product_id, warehouse_id)",
        "CREATE INDEX idx_sales_date ON sales(sale_date)",
        "CREATE INDEX idx_po_status ON purchase_orders(status)",
        "CREATE INDEX idx_tx_date ON inventory_transactions(transaction_date)",
        "CREATE INDEX idx_prod_cat ON products(category_id)"
    ]
    for idx in indexes:
        try:
            cursor.execute(idx)
        except Exception:
            pass  # Index already exists

    # 4. Create Advanced SQL Database Views (Unit 2 DBMS)
    views = {}

    views["v_inventory_summary"] = """
    CREATE OR REPLACE VIEW v_inventory_summary AS
    SELECT 
        i.inventory_id,
        p.product_id,
        p.product_name,
        p.barcode,
        p.price,
        p.minimum_stock,
        c.category_name,
        w.warehouse_id,
        w.warehouse_name,
        w.location,
        i.quantity,
        (i.quantity * p.price) AS total_valuation,
        CASE 
            WHEN i.quantity = 0 THEN 'OUT_OF_STOCK'
            WHEN i.quantity <= p.minimum_stock THEN 'LOW_STOCK'
            WHEN i.quantity > p.minimum_stock * 3 THEN 'SURPLUS'
            ELSE 'HEALTHY'
        END AS stock_status,
        i.last_updated
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    JOIN categories c ON p.category_id = c.category_id
    JOIN warehouses w ON i.warehouse_id = w.warehouse_id;
    """

    views["v_low_stock_alerts"] = """
    CREATE OR REPLACE VIEW v_low_stock_alerts AS
    SELECT 
        p.product_id,
        p.product_name,
        p.minimum_stock,
        w.warehouse_id,
        w.warehouse_name,
        i.quantity AS current_stock,
        (p.minimum_stock * 2 - i.quantity) AS suggested_reorder_qty,
        s.supplier_id,
        s.supplier_name,
        s.contact_person,
        s.phone AS supplier_phone,
        s.email AS supplier_email,
        p.price AS unit_price
    FROM inventory i
    JOIN products p ON i.product_id = p.product_id
    JOIN warehouses w ON i.warehouse_id = w.warehouse_id
    JOIN suppliers s ON p.supplier_id = s.supplier_id
    WHERE i.quantity <= p.minimum_stock;
    """

    views["v_warehouse_performance"] = """
    CREATE OR REPLACE VIEW v_warehouse_performance AS
    SELECT 
        w.warehouse_id,
        w.warehouse_name,
        w.location,
        COUNT(DISTINCT i.product_id) AS total_skus,
        COALESCE(SUM(i.quantity), 0) AS total_units_stored,
        COALESCE(SUM(i.quantity * p.price), 0.00) AS total_inventory_valuation
    FROM warehouses w
    LEFT JOIN inventory i ON w.warehouse_id = i.warehouse_id
    LEFT JOIN products p ON i.product_id = p.product_id
    GROUP BY w.warehouse_id, w.warehouse_name, w.location;
    """

    for view_name, view_ddl in views.items():
        try:
            cursor.execute(view_ddl)
            print(f"SQL View '{view_name}' registered.")
        except Exception as e:
            print(f"Warning on view {view_name}: {e}")

    # 5. Stored Procedures (Unit 2 & 3 DBMS - Advanced SQL & 2PL Concurrency)
    try:
        cursor.execute("DROP PROCEDURE IF EXISTS sp_transfer_inventory")
        cursor.execute("""
        CREATE PROCEDURE sp_transfer_inventory(
            IN p_product_id INT,
            IN p_from_warehouse_id INT,
            IN p_to_warehouse_id INT,
            IN p_quantity INT,
            IN p_user_id INT,
            OUT p_status VARCHAR(50)
        )
        proc: BEGIN
            DECLARE v_src_stock INT DEFAULT 0;
            DECLARE v_dst_stock INT DEFAULT 0;
            DECLARE v_first_wh INT;
            DECLARE v_second_wh INT;

            -- Validation
            IF p_from_warehouse_id = p_to_warehouse_id THEN
                SET p_status = 'ERROR_SAME_WAREHOUSE';
                LEAVE proc;
            END IF;

            IF p_quantity <= 0 THEN
                SET p_status = 'ERROR_INVALID_QUANTITY';
                LEAVE proc;
            END IF;

            -- Deadlock Prevention Protocol: Canonical Resource Ordering (DBMS Unit 3)
            -- Always acquire row locks in deterministic ascending order of warehouse_id
            IF p_from_warehouse_id < p_to_warehouse_id THEN
                SET v_first_wh = p_from_warehouse_id;
                SET v_second_wh = p_to_warehouse_id;
            ELSE
                SET v_first_wh = p_to_warehouse_id;
                SET v_second_wh = p_from_warehouse_id;
            END IF;

            -- Lock in strict order (Pessimistic X-Lock via SELECT ... FOR UPDATE)
            SELECT quantity INTO v_src_stock FROM inventory 
            WHERE product_id = p_product_id AND warehouse_id = p_from_warehouse_id FOR UPDATE;

            -- Check if source has sufficient stock
            IF v_src_stock IS NULL OR v_src_stock < p_quantity THEN
                SET p_status = 'ERROR_INSUFFICIENT_STOCK';
                LEAVE proc;
            END IF;

            -- Ensure destination inventory row exists
            INSERT IGNORE INTO inventory (product_id, warehouse_id, quantity)
            VALUES (p_product_id, p_to_warehouse_id, 0);

            SELECT quantity INTO v_dst_stock FROM inventory 
            WHERE product_id = p_product_id AND warehouse_id = p_to_warehouse_id FOR UPDATE;

            -- Atomic Debit & Credit (2-Phase Update)
            UPDATE inventory 
            SET quantity = quantity - p_quantity, version = version + 1
            WHERE product_id = p_product_id AND warehouse_id = p_from_warehouse_id;

            UPDATE inventory 
            SET quantity = quantity + p_quantity, version = version + 1
            WHERE product_id = p_product_id AND warehouse_id = p_to_warehouse_id;

            -- Immutable Audit Ledger Entries
            INSERT INTO inventory_transactions 
            (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
            VALUES 
            (p_product_id, p_from_warehouse_id, p_user_id, 'Transfer_Out', p_quantity, v_src_stock, v_src_stock - p_quantity, CONCAT('Transfer to WH #', p_to_warehouse_id)),
            (p_product_id, p_to_warehouse_id, p_user_id, 'Transfer_In', p_quantity, v_dst_stock, v_dst_stock + p_quantity, CONCAT('Transfer from WH #', p_from_warehouse_id));

            SET p_status = 'SUCCESS';
        END;
        """)
        print("Stored Procedure 'sp_transfer_inventory' registered.")
    except Exception as e:
        print(f"Note on stored procedure: {e}")

    # 6. Seed Realistic Initial Demonstration Data if tables are empty
    seed_data(cursor)

    cursor.close()
    connection.close()
    print("Database setup and initialization completed successfully.")
    return True


def seed_data(cursor):
    """Populates realistic multi-warehouse enterprise data for evaluation & live testing."""
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] > 0:
        print("Existing data detected. Ensuring minimum demo records are present...")
    else:
        print("Empty database detected. Seeding comprehensive warehouse dataset...")

    # Users
    users = [
        ("System Administrator", "admin@warehouse.com", "admin123", "Admin"),
        ("Sarah Jenkins (Bangalore Manager)", "sarah.mgr@warehouse.com", "manager123", "Warehouse Manager"),
        ("Rahul Verma (Inventory Specialist)", "rahul.inv@warehouse.com", "staff123", "Warehouse Staff"),
        ("Priya Nair (Sales Lead)", "priya.sales@warehouse.com", "sales123", "Sales Executive")
    ]
    cursor.executemany("""
        INSERT IGNORE INTO users (full_name, email, password, role)
        VALUES (%s, %s, %s, %s)
    """, users)

    # Categories
    categories = [
        ("Enterprise Electronics", "High-value computing, sensors, barcode scanners, and wireless network gear"),
        ("Industrial Hardware", "Heavy equipment, hydraulic jacks, power tools, and racking systems"),
        ("Storage & Packaging", "Poly wrap, heavy-duty cardboard boxes, pallet bands, strapping kits"),
        ("Safety & PPE", "High-visibility vests, steel-toe boots, hardhats, hazardous material kits"),
        ("Office & Dispatch Supplies", "Thermal label rolls, adhesive tape, packing slips, manifest printers")
    ]
    cursor.executemany("""
        INSERT IGNORE INTO categories (category_name, description)
        VALUES (%s, %s)
    """, categories)

    # Suppliers
    suppliers = [
        ("Apex Logistics Supplies Ltd", "Vikram Malhotra", "+91-9845012345", "orders@apexsupplies.com", "Plot 42, Electronic City Phase 1, Bangalore", "29AAAAA0000A1Z5"),
        ("Global Tech Distribution", "Anita Desai", "+91-9820067890", "supply@globaltech.in", "Bandra-Kurla Complex, Mumbai", "27BBBBB1111B2Z6"),
        ("Delta Heavy Industrial Tools", "Robert Chen", "+91-9811154321", "sales@deltatools.com", "Okhla Industrial Area Phase 3, New Delhi", "07CCCCC2222C3Z7"),
        ("EcoPack Manufacturing Corp", "Deepak Rao", "+91-9444087654", "dispatch@ecopack.co", "Ambattur Industrial Estate, Chennai", "33DDDDD3333D4Z8")
    ]
    cursor.executemany("""
        INSERT IGNORE INTO suppliers (supplier_name, contact_person, phone, email, address, gst_number)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, suppliers)

    # Warehouses
    warehouses = [
        ("WH-South (Bangalore Central DC)", "Hosur Main Road, Electronic City, Bangalore", "Sarah Jenkins", "+91-80-28520001", 35000),
        ("WH-Coastal (Chennai Cargo Hub)", "GNT Road, Puzhal Logistics Park, Chennai", "Murugan K.", "+91-44-26590002", 28000),
        ("WH-West (Mumbai Inland Port)", "Taloja MIDC, Navi Mumbai", "Kishore Kadam", "+91-22-27410003", 42000),
        ("WH-North (Delhi Freight Terminal)", "Samalkha Logistics Zone, New Delhi", "Amitabh Singh", "+91-11-25650004", 30000)
    ]
    cursor.executemany("""
        INSERT IGNORE INTO warehouses (warehouse_name, location, manager_name, contact_number, capacity_sqft)
        VALUES (%s, %s, %s, %s, %s)
    """, warehouses)

    # Fetch IDs to create dependent relationships
    cursor.execute("SELECT category_id, category_name FROM categories")
    cat_map = {name: cid for cid, name in cursor.fetchall()}

    cursor.execute("SELECT supplier_id, supplier_name FROM suppliers")
    sup_map = {name: sid for sid, name in cursor.fetchall()}

    cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses")
    wh_map = {name: wid for wid, name in cursor.fetchall()}

    # Products (Diverse SKU catalog with minimum stock limits)
    products = [
        ("Zebra Industrial 2D Barcode Scanner", cat_map.get("Enterprise Electronics", 1), sup_map.get("Global Tech Distribution", 2), "BAR-ZEB-001", 12500.00, 15, "Rugged IP65 cordless barcode reader with Bluetooth link"),
        ("Cisco Catalyst 24-Port Gigabit Switch", cat_map.get("Enterprise Electronics", 1), sup_map.get("Global Tech Distribution", 2), "NET-CIS-024", 45000.00, 8, "Managed rackmount switch with PoE+ for warehouse IoT"),
        ("Raspberry Pi 5 IoT Dock Sensor Gateway", cat_map.get("Enterprise Electronics", 1), sup_map.get("Global Tech Distribution", 2), "IOT-RPI-005", 6800.00, 20, "Edge computing gateway for bay sensors and RFID telemetry"),
        ("Heavy Duty 2.5T Hydraulic Pallet Jack", cat_map.get("Industrial Hardware", 2), sup_map.get("Delta Heavy Industrial Tools", 3), "EQU-PAL-250", 18500.00, 5, "Polyurethane roller fork truck for standard Euro pallets"),
        ("Bosch Professional Cordless Impact Wrench", cat_map.get("Industrial Hardware", 2), sup_map.get("Delta Heavy Industrial Tools", 3), "TLS-BSH-018", 9200.00, 10, "18V brushless motor tool with 300Nm breakaway torque"),
        ("Industrial Heavy Duty Storage Bins (Pack of 10)", cat_map.get("Storage & Packaging", 3), sup_map.get("EcoPack Manufacturing Corp", 4), "STG-BIN-P10", 3400.00, 25, "Stackable polypropylene organizer bins for small parts"),
        ("Automated Stretch Wrap Film Roll (500mm x 300m)", cat_map.get("Storage & Packaging", 3), sup_map.get("EcoPack Manufacturing Corp", 4), "PKG-STR-500", 1450.00, 40, "23-micron puncture resistant cast pallet stretch film"),
        ("Reflective ANSI Class 3 Safety Vest (XL)", cat_map.get("Safety & PPE", 4), sup_map.get("Apex Logistics Supplies Ltd", 1), "PPE-VST-003", 650.00, 30, "High visibility neon yellow with 3M reflective tape"),
        ("Thermal Shipping Label Roll (4x6 inch, 500/roll)", cat_map.get("Office & Dispatch Supplies", 5), sup_map.get("Apex Logistics Supplies Ltd", 1), "LBL-THM-4X6", 420.00, 50, "Direct thermal adhesive labels for Zebra and TSC printers"),
        ("Honeywell RFID Handheld Reader Terminal", cat_map.get("Enterprise Electronics", 1), sup_map.get("Global Tech Distribution", 2), "RFD-HON-099", 58000.00, 6, "Long-range UHF RFID scanner with Android 13 OS")
    ]

    for p in products:
        cursor.execute("""
            INSERT IGNORE INTO products (product_name, category_id, supplier_id, barcode, price, minimum_stock, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, p)

    # Customers
    customers = [
        ("CloudScale Retail Solutions", "+91-9988776655", "procure@cloudscaleretail.com", "Whitefield Main Rd, Bangalore"),
        ("Metro Express 3PL Logistics", "+91-9876543210", "operations@metroexpress.in", "JNPT Port Road, Navi Mumbai"),
        ("Titan Distribution Hubs", "+91-9765432109", "titan.warehouse@titan.com", "Sriperumbudur Industrial Corridor, Chennai"),
        ("Alpha Omni Logistics", "+91-9654321098", "buyer@alphaomni.net", "NH-8 Logistics Belt, Gurugram")
    ]
    cursor.executemany("""
        INSERT IGNORE INTO customers (customer_name, phone, email, address)
        VALUES (%s, %s, %s, %s)
    """, customers)

    # Distribute Inventory across Warehouses
    cursor.execute("SELECT product_id, barcode, minimum_stock FROM products")
    db_products = cursor.fetchall()

    cursor.execute("SELECT warehouse_id FROM warehouses")
    wh_ids = [row[0] for row in cursor.fetchall()]

    if wh_ids and db_products:
        # Create a realistic distribution:
        # - WH-1 (Bangalore): Primary stock hub, healthy quantities
        # - WH-2 (Chennai): Moderate quantities, one item intentionally LOW_STOCK for immediate alert showcase!
        # - WH-3 (Mumbai): High quantities
        # - WH-4 (Delhi): Critically low stock on 2 items to trigger Automated PO generation!
        for pid, barcode, min_stock in db_products:
            for wid in wh_ids:
                if wid == wh_ids[0]:
                    qty = min_stock * 4 + 10  # Healthy
                elif wid == wh_ids[1]:
                    # Make one product low stock
                    qty = (min_stock - 2) if "BAR-ZEB" in barcode else (min_stock * 2)
                elif wid == wh_ids[2]:
                    qty = min_stock * 3 + 5
                else:
                    # Delhi: Trigger low stock condition for auto-PO demonstration
                    qty = (min_stock - 3) if ("NET-CIS" in barcode or "RFD-HON" in barcode) else (min_stock + 4)
                
                qty = max(2, qty)

                cursor.execute("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE quantity = VALUES(quantity)
                """, (pid, wid, qty))

    # Add initial seed transaction in audit ledger
    cursor.execute("SELECT COUNT(*) FROM inventory_transactions")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO inventory_transactions 
            (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
            SELECT product_id, warehouse_id, 1, 'Purchase', quantity, 0, quantity, 'Initial Warehouse Opening Stock Baseline'
            FROM inventory
            LIMIT 15;
        """)

    print("Seed data loaded successfully.")


if __name__ == "__main__":
    initialize_database()
