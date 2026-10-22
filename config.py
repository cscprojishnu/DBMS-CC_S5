"""
Application Configuration
Supports Local Development, Local Network (Multi-Laptop) Deployment,
Docker Containers, Kubernetes, and Cloud Platforms.
"""

import os
import socket


def get_local_ip():
    """Detects the primary LAN IPv4 address for multi-device network deployment."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable, just initiates route lookup
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


class Config:
    # Flask Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-warehouse-secret-key-cloud-dbms-2026")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    # MySQL Database Settings (Fallbacks to local MySQL default root:root)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "warehouse_db")
    DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", 10))

    # Concurrency and Transaction Settings (Unit 3 DBMS)
    DEFAULT_ISOLATION_LEVEL = os.getenv("ISOLATION_LEVEL", "READ COMMITTED")
    DEADLOCK_MAX_RETRIES = int(os.getenv("DEADLOCK_MAX_RETRIES", 3))
    DEADLOCK_RETRY_DELAY = float(os.getenv("DEADLOCK_RETRY_DELAY", 0.15))

    # Cloud & Deployment Metadata
    ENVIRONMENT = os.getenv("ENVIRONMENT", "Local-LAN")  # 'Local-LAN', 'Docker', 'Kubernetes', 'Cloud'
    LOCAL_IP = get_local_ip()
    APP_VERSION = "2.0.0-CloudNative"
    SYSTEM_NAME = "Smart Warehouse Cloud & Inventory Management System"


config = Config()
