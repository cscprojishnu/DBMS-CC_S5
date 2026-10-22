-- =========================================================================
-- Initial Database Schema for Docker Container Initialization
-- Cloud Computing & DBMS Unit 1, 2, 3
-- =========================================================================

CREATE DATABASE IF NOT EXISTS `warehouse_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `warehouse_db`;

-- Users
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Warehouse Manager', 'Warehouse Staff', 'Sales Executive') NOT NULL DEFAULT 'Sales Executive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Suppliers
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

-- Products
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
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Warehouses
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_name VARCHAR(150) NOT NULL UNIQUE,
    location VARCHAR(255) NOT NULL,
    manager_name VARCHAR(100),
    contact_number VARCHAR(20),
    capacity_sqft INT DEFAULT 10000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Inventory
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    version INT NOT NULL DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (product_id, warehouse_id),
    CHECK (quantity >= 0)
) ENGINE=InnoDB;

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Sales
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE,
    customer_id INT NOT NULL,
    user_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    payment_status ENUM('Paid', 'Pending', 'Credit') NOT NULL DEFAULT 'Paid',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Sale Items
CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_order_id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE,
    supplier_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Pending', 'Approved', 'Received', 'Cancelled') NOT NULL DEFAULT 'Pending',
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    auto_generated BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    purchase_order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(purchase_order_id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Inventory Transactions (Audit Ledger)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    user_id INT NOT NULL,
    transaction_type ENUM('Purchase', 'Sale', 'Return', 'Adjustment', 'Transfer_Out', 'Transfer_In') NOT NULL,
    quantity INT NOT NULL,
    previous_quantity INT NOT NULL,
    new_quantity INT NOT NULL,
    notes VARCHAR(255),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;
