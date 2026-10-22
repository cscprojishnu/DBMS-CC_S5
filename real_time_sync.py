"""
Real-Time Event Synchronization Module (Server-Sent Events / SSE)
Supports cross-device real-time inventory updates across multiple laptops & clients on local network or cloud.

Cloud Computing Concepts:
- Unit 1: Cloud-Native event-driven architecture, stateless pub/sub, real-time telemetry
- Real-time inventory synchronization across multi-user web clients
"""

import json
import queue
import time
from datetime import datetime

# In-memory thread-safe pub/sub event listeners
_listeners = []


def register_listener():
    """Registers a new client queue for Server-Sent Events."""
    q = queue.Queue(maxsize=50)
    _listeners.append(q)
    return q


def unregister_listener(q):
    """Removes a disconnected client queue."""
    if q in _listeners:
        _listeners.remove(q)


def broadcast_event(event_type, payload):
    """
    Broadcasts an inventory/transaction event to all connected browsers/devices in real time.
    
    event_type: 'STOCK_UPDATE', 'SALE_COMPLETED', 'STOCK_TRANSFER', 'LOW_STOCK_ALERT', 'PO_CREATED', 'PO_RECEIVED'
    """
    event_data = {
        "event": event_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": payload
    }
    
    dead_queues = []
    for q in list(_listeners):
        try:
            q.put_nowait(event_data)
        except queue.Full:
            # Drop slowest listener or discard
            dead_queues.append(q)
        except Exception:
            dead_queues.append(q)
            
    for q in dead_queues:
        unregister_listener(q)


def get_active_listeners_count():
    """Returns number of active real-time connected client sessions."""
    return len(_listeners)


def format_sse(data: str, event=None) -> str:
    """Formats payload according to the W3C Server-Sent Events specification."""
    msg = f"data: {data}\n"
    if event:
        msg = f"event: {event}\n{msg}"
    return f"{msg}\n"
