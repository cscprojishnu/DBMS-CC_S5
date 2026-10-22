"""
Database Connection & Transaction Management Module
Implements:
- DBMS Unit 3: ACID Transaction Management (Atomicity, Consistency, Isolation, Durability)
- Transaction Isolation Levels (READ COMMITTED, REPEATABLE READ, SERIALIZABLE)
- Concurrency Control & Row-Level Locking Helper
- Automatic Rollback on Exceptions
"""

import time
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config import config


def get_connection(isolation_level=None):
    """
    Returns a new PyMySQL connection configured with DictCursor.
    Optionally sets the transaction isolation level for this session.
    """
    conn = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=config.DB_CONNECT_TIMEOUT,
        autocommit=False  # Crucial for explicit transaction control (ACID)
    )

    if isolation_level:
        with conn.cursor() as cursor:
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation_level}")

    return conn


@contextmanager
def db_transaction(isolation_level=None):
    """
    Context manager for atomic database transactions.
    
    DBMS Unit 3 Concepts Implemented:
    - Atomicity: All operations in the block succeed or all are rolled back.
    - Consistency: Constraints are validated before commit.
    - Isolation: Configurable session isolation level.
    - Durability: Changes persisted to disk on commit.
    """
    conn = get_connection(isolation_level=isolation_level)
    cursor = conn.cursor()
    try:
        # Explicitly begin transaction
        cursor.execute("START TRANSACTION")
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def test_connection():
    """Tests MySQL connectivity and returns status information."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version, DATABASE() AS db, @@transaction_isolation AS isolation")
            result = cursor.fetchone()
        conn.close()
        return True, result
    except Exception as e:
        return False, str(e)


def execute_with_retry(func, max_retries=3, delay=0.1):
    """
    Executes a transaction function with automatic retry on deadlock
    (Error 1213: Deadlock found when trying to get lock).
    
    DBMS Unit 3: Deadlock Detection & Recovery
    """
    attempt = 0
    while attempt < max_retries:
        try:
            return func()
        except pymysql.err.OperationalError as e:
            # 1213 = Deadlock, 1205 = Lock wait timeout exceeded
            if e.args[0] in (1213, 1205):
                attempt += 1
                if attempt >= max_retries:
                    raise e
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise e
