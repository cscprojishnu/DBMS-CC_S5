"""
Concurrency Control & Transaction Stress Engine
Implements:
- DBMS Unit 3: Concurrency Control, Lock-Based Protocols, 2-Phase Locking (2PL),
  Pessimistic Locking (SELECT ... FOR UPDATE), Optimistic Locking (OCC),
  and Uncontrolled Race Condition demonstration (Lost Updates & Overselling).
"""

import time
import threading
import pymysql
from database import get_connection
from real_time_sync import broadcast_event


def run_uncontrolled_sale(product_id, warehouse_id, qty_to_buy, buyer_name, thread_delay=0.05):
    """
    Demonstrates UNCONTROLLED CONCURRENCY (No Locking, Race Condition, Lost Update).
    
    Flaw:
    1. Reads stock into memory without a lock.
    2. Context switch / processing delay occurs.
    3. Writes back calculated stock.
    Result: When two users buy at the same time, both read the same initial stock,
    causing overselling and lost updates.
    """
    conn = get_connection()
    log = []
    t_start = time.time()
    try:
        with conn.cursor() as cursor:
            # 1. Read without lock
            cursor.execute("SELECT quantity FROM inventory WHERE product_id = %s AND warehouse_id = %s", (product_id, warehouse_id))
            row = cursor.fetchone()
            current_stock = row["quantity"] if row else 0
            log.append(f"[{buyer_name}] Read stock = {current_stock} (NO LOCK acquired)")

            # 2. Simulate processing delay
            time.sleep(thread_delay)

            # 3. Check condition in application memory (vulnerable to race condition)
            if current_stock >= qty_to_buy:
                new_stock = current_stock - qty_to_buy
                # 4. Blind write back
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = %s 
                    WHERE product_id = %s AND warehouse_id = %s
                """, (new_stock, product_id, warehouse_id))
                conn.commit()
                log.append(f"[{buyer_name}] SUCCESS: Deducted {qty_to_buy}, blind wrote new_stock = {new_stock}")
                status = "SUCCESS"
            else:
                conn.rollback()
                log.append(f"[{buyer_name}] REJECTED: Stock {current_stock} < {qty_to_buy}")
                status = "REJECTED_STOCK"
    except Exception as e:
        conn.rollback()
        log.append(f"[{buyer_name}] ERROR: {str(e)}")
        status = "ERROR"
    finally:
        conn.close()

    duration = round((time.time() - t_start) * 1000, 2)
    return {"buyer": buyer_name, "status": status, "duration_ms": duration, "log": log}


def run_pessimistic_sale(product_id, warehouse_id, qty_to_buy, buyer_name, lock_hold_delay=0.03):
    """
    Demonstrates PESSIMISTIC 2-PHASE LOCKING (2PL) using MySQL SELECT ... FOR UPDATE.
    
    DBMS Unit 3 Concepts:
    - Exclusive Lock (X-Lock) granted by MySQL InnoDB engine on the specific inventory row.
    - Other concurrent transactions trying to acquire X-Lock are placed in WAITING state.
    - Atomicity & Isolation guarantees zero overselling and 100% serializability.
    """
    conn = get_connection()
    log = []
    t_start = time.time()
    try:
        with conn.cursor() as cursor:
            # Start explicit transaction
            cursor.execute("START TRANSACTION")
            
            # Acquire Exclusive Row Lock (X-Lock)
            t_lock_req = time.time()
            cursor.execute("""
                SELECT quantity, version 
                FROM inventory 
                WHERE product_id = %s AND warehouse_id = %s 
                FOR UPDATE
            """, (product_id, warehouse_id))
            row = cursor.fetchone()
            lock_wait_ms = round((time.time() - t_lock_req) * 1000, 2)

            if not row:
                conn.rollback()
                log.append(f"[{buyer_name}] Product not found in warehouse.")
                return {"buyer": buyer_name, "status": "NOT_FOUND", "duration_ms": lock_wait_ms, "log": log}

            current_stock = row["quantity"]
            log.append(f"[{buyer_name}] X-LOCK GRANTED (wait: {lock_wait_ms}ms). Current stock = {current_stock}")

            # Hold lock briefly to demonstrate concurrency serialization
            if lock_hold_delay > 0:
                time.sleep(lock_hold_delay)

            # Strict inventory check inside lock
            if current_stock >= qty_to_buy:
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - %s, version = version + 1
                    WHERE product_id = %s AND warehouse_id = %s
                """, (qty_to_buy, product_id, warehouse_id))

                # Record in audit ledger
                cursor.execute("""
                    INSERT INTO inventory_transactions 
                    (product_id, warehouse_id, user_id, transaction_type, quantity, previous_quantity, new_quantity, notes)
                    VALUES (%s, %s, 1, 'Sale', %s, %s, %s, %s)
                """, (product_id, warehouse_id, qty_to_buy, current_stock, current_stock - qty_to_buy, f"Pessimistic Sale by {buyer_name}"))

                conn.commit()  # Lock released (Shrinking phase)
                log.append(f"[{buyer_name}] TRANSACTION COMMITTED. Stock reduced from {current_stock} to {current_stock - qty_to_buy}")
                status = "SUCCESS"
            else:
                conn.rollback()  # Lock released
                log.append(f"[{buyer_name}] ROLLBACK: Insufficient stock ({current_stock} available, {qty_to_buy} requested). Overselling prevented!")
                status = "REJECTED_STOCK"
    except Exception as e:
        conn.rollback()
        log.append(f"[{buyer_name}] TRANSACTION ABORTED: {str(e)}")
        status = "ERROR"
    finally:
        conn.close()

    duration = round((time.time() - t_start) * 1000, 2)
    return {"buyer": buyer_name, "status": status, "duration_ms": duration, "log": log}


def run_optimistic_sale(product_id, warehouse_id, qty_to_buy, buyer_name, max_retries=3):
    """
    Demonstrates OPTIMISTIC CONCURRENCY CONTROL (OCC).
    
    DBMS Unit 3 Concepts:
    - Assumes conflicts are rare. Does not block other transactions with X-locks.
    - Validates row version or quantity threshold atomically at commit/write phase:
      UPDATE inventory SET quantity = quantity - N, version = version + 1 
      WHERE product_id = ? AND warehouse_id = ? AND quantity >= N
    - If rows_affected == 0, conflict detected; transaction retries with backoff or safely aborts.
    """
    conn = get_connection()
    log = []
    t_start = time.time()
    status = "FAILED"
    
    try:
        with conn.cursor() as cursor:
            for attempt in range(1, max_retries + 1):
                # 1. Read phase (without lock)
                cursor.execute("SELECT quantity, version FROM inventory WHERE product_id = %s AND warehouse_id = %s", (product_id, warehouse_id))
                row = cursor.fetchone()
                if not row:
                    status = "NOT_FOUND"
                    break

                curr_qty = row["quantity"]
                curr_ver = row["version"]

                if curr_qty < qty_to_buy:
                    log.append(f"[{buyer_name}] Attempt {attempt}: Insufficient stock ({curr_qty} < {qty_to_buy}). Aborting.")
                    status = "REJECTED_STOCK"
                    break

                # 2. Validation & Write phase in single atomic compare-and-swap
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - %s, version = version + 1
                    WHERE product_id = %s AND warehouse_id = %s AND version = %s AND quantity >= %s
                """, (qty_to_buy, product_id, warehouse_id, curr_ver, qty_to_buy))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    log.append(f"[{buyer_name}] Attempt {attempt}: OCC VALIDATED. Stock updated to {curr_qty - qty_to_buy}")
                    status = "SUCCESS"
                    break
                else:
                    # Row was modified concurrently by another thread!
                    log.append(f"[{buyer_name}] Attempt {attempt}: Conflict detected (version changed). Retrying...")
                    time.sleep(0.02 * attempt)
            else:
                log.append(f"[{buyer_name}] Exceeded max retries due to heavy concurrency conflicts.")
                status = "CONFLICT_MAX_RETRIES"
    except Exception as e:
        conn.rollback()
        log.append(f"[{buyer_name}] ERROR: {str(e)}")
        status = "ERROR"
    finally:
        conn.close()

    duration = round((time.time() - t_start) * 1000, 2)
    return {"buyer": buyer_name, "status": status, "duration_ms": duration, "log": log}


def simulate_concurrent_load(product_id, warehouse_id, initial_stock, num_threads=5, qty_per_buyer=2, mode="pessimistic"):
    """
    Executes a multi-threaded concurrency stress simulation against MySQL.
    Synchronizes threads to start at the exact same microsecond using a Threading Barrier.
    """
    # 1. Reset baseline stock for this test
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO inventory (product_id, warehouse_id, quantity, version)
            VALUES (%s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE quantity = %s, version = 1
        """, (product_id, warehouse_id, initial_stock, initial_stock))
        conn.commit()
    conn.close()

    results = []
    barrier = threading.Barrier(num_threads)

    def worker(buyer_idx):
        buyer_name = f"Buyer-{buyer_idx}"
        barrier.wait()  # Synchronize all threads to launch simultaneously
        
        if mode == "pessimistic":
            res = run_pessimistic_sale(product_id, warehouse_id, qty_per_buyer, buyer_name)
        elif mode == "optimistic":
            res = run_optimistic_sale(product_id, warehouse_id, qty_per_buyer, buyer_name)
        else:
            res = run_uncontrolled_sale(product_id, warehouse_id, qty_per_buyer, buyer_name)
            
        results.append(res)

    threads = []
    for i in range(1, num_threads + 1):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify final stock in MySQL
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT quantity, version FROM inventory WHERE product_id = %s AND warehouse_id = %s", (product_id, warehouse_id))
        final_row = cursor.fetchone()
        final_stock = final_row["quantity"] if final_row else 0
    conn.close()

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    total_requested = num_threads * qty_per_buyer
    expected_safe_sales = min(initial_stock // qty_per_buyer, num_threads)
    oversold = (success_count * qty_per_buyer) > initial_stock

    # Trigger real-time broadcast to connected browsers
    broadcast_event("CONCURRENCY_TEST_COMPLETED", {
        "mode": mode,
        "initial_stock": initial_stock,
        "final_stock": final_stock,
        "success_count": success_count,
        "oversold": oversold
    })

    return {
        "mode": mode,
        "initial_stock": initial_stock,
        "final_stock": final_stock,
        "num_threads": num_threads,
        "qty_per_buyer": qty_per_buyer,
        "total_requested": total_requested,
        "success_count": success_count,
        "expected_safe_sales": expected_safe_sales,
        "oversold": oversold,
        "results": results
    }
