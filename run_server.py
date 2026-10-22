"""
Application Server Launcher & Network Deployment Initializer
Smart Warehouse & Inventory Management System

Automatically:
1. Validates MySQL database connectivity
2. Ensures all tables, views, stored procedures and seed data exist
3. Detects your primary LAN IPv4 address (for multi-device access)
4. Displays formatted connection URLs and firewall instructions
5. Starts the production-capable multi-threaded web server
"""

import sys
import socket
from config import config
from database import test_connection


def print_banner():
    ip = config.LOCAL_IP
    port = config.PORT

    print("*" * 75)
    print("  📦 CLOUD-BASED SMART WAREHOUSE & INVENTORY MANAGEMENT SYSTEM")
    print("     Real-Time Multi-Warehouse Synchronization using MySQL (ACID)")
    print("*" * 75)
    print("  STATUS: Production-Ready Local Cloud Node Active")
    print()
    print("  🔗 ACCESS URLS:")
    print(f"     ► This Laptop (Localhost):     http://localhost:{port}")
    print(f"     ► Other Laptops / Mobiles:     http://{ip}:{port}")
    print()
    print("  📲 HOW TO USE FROM ANOTHER LAPTOP / PHONE (REAL-TIME DEMO):")
    print("     1. Connect the 2nd laptop or phone to the SAME Wi-Fi or Mobile Hotspot.")
    print(f"     2. Open any browser (Chrome, Edge, Safari) and go to: http://{ip}:{port}")
    print("     3. Open Sales or Transfer on Laptop 1, and watch Laptop 2 update in real time!")
    print()
    print("  🛡️ WINDOWS FIREWALL NOTE (If 2nd laptop cannot connect):")
    print("     Run this one command in PowerShell (Run as Administrator):")
    print('     New-NetFirewallRule -DisplayName "SmartWarehouse5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow')
    print("*" * 75)
    print("  Press Ctrl+C to stop the server at any time.")
    print("*" * 75)
    print()


def main():
    # 1. Test database connection
    print("Verifying MySQL database connection...")
    db_ok, info = test_connection()
    if not db_ok:
        print(f"⚠ Warning: Could not connect to MySQL: {info}")
        print("Attempting to run database setup script...")
        from setup_database import initialize_database
        if not initialize_database():
            print("❌ Error: Failed to initialize database. Please check MySQL service is running.")
            sys.exit(1)
    else:
        # Check if tables are populated
        from setup_database import initialize_database
        initialize_database()

    # 2. Print network deployment banner
    print_banner()

    # 3. Start Flask app
    from app import app
    app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
