/**
 * Real-Time Synchronization Client (Server-Sent Events)
 * Coordinates live state sync across multiple laptops, tablets, and phones on the network.
 */

// Web Audio API Synthesizer for subtle notification chimes
function playChime(type = "info") {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === "success") {
      osc.frequency.setValueAtTime(523.25, audioCtx.currentTime); // C5
      osc.frequency.setValueAtTime(659.25, audioCtx.currentTime + 0.1); // E5
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.35);
    } else if (type === "warning") {
      osc.frequency.setValueAtTime(440, audioCtx.currentTime); // A4
      osc.frequency.setValueAtTime(349.23, audioCtx.currentTime + 0.12); // F4
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.4);
    }
  } catch (e) {
    // Audio context may require user interaction first
  }
}

// Toast Notification Manager
function showToast(title, message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const icons = {
    success: "✓",
    warning: "⚠",
    danger: "✕",
    info: "ℹ"
  };

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || "ℹ"}</div>
    <div class="toast-content">
      <h4>${title}</h4>
      <p>${message}</p>
    </div>
  `;

  container.appendChild(toast);
  playChime(type);

  // Auto remove
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Initialize Real-Time SSE Stream
function initRealTimeStream() {
  const statusEl = document.getElementById("live-status-indicator");

  if (!window.EventSource) {
    console.warn("EventSource not supported by browser. Falling back to polling.");
    return;
  }

  const evtSource = new EventSource("/api/realtime/stream");

  evtSource.onopen = function () {
    if (statusEl) {
      statusEl.innerHTML = `<span class="pulse-dot"></span> Real-Time Live`;
      statusEl.style.color = "var(--accent-emerald)";
    }
    console.log("[SSE] Connected to real-time warehouse stream.");
  };

  evtSource.onmessage = function (e) {
    try {
      const data = JSON.parse(e.data);
      handleRealtimeEvent(data);
    } catch (err) {
      console.error("[SSE] Error parsing event:", err);
    }
  };

  evtSource.onerror = function () {
    if (statusEl) {
      statusEl.innerHTML = `<span style="background:var(--accent-amber);" class="pulse-dot"></span> Reconnecting...`;
      statusEl.style.color = "var(--accent-amber)";
    }
    console.warn("[SSE] Connection lost. Auto-reconnecting in 3s...");
  };
}

// Event Dispatcher
function handleRealtimeEvent(data) {
  const { event, timestamp, payload } = data;
  console.log(`[SSE Event: ${event}]`, payload);

  switch (event) {
    case "STOCK_TRANSFER":
      showToast(
        "Stock Transferred Across Warehouses",
        `Product #${payload.product_id} (${payload.quantity} units) moved from WH #${payload.from_warehouse_id} to WH #${payload.to_warehouse_id}`,
        "info"
      );
      highlightRow(`inv-row-${payload.product_id}-${payload.from_warehouse_id}`);
      highlightRow(`inv-row-${payload.product_id}-${payload.to_warehouse_id}`);
      break;

    case "SALE_COMPLETED":
      showToast(
        "Real-Time Sale Processed",
        `Order ${payload.reference_no} confirmed (₹${payload.total_amount}). Stock deducted.`,
        "success"
      );
      break;

    case "PO_CREATED":
      showToast(
        "Purchase Order Generated",
        `PO ${payload.po_number} created for ${payload.supplier_name}.`,
        "info"
      );
      break;

    case "PO_RECEIVED":
      showToast(
        "Stock Received & Restocked",
        `PO ${payload.po_number} received. Inventory credited across warehouse.`,
        "success"
      );
      break;

    case "LOW_STOCK_ALERT":
      showToast(
        "Low Stock Critical Warning",
        `Product '${payload.product_name}' at WH '${payload.warehouse_name}' is below safety threshold!`,
        "warning"
      );
      break;

    case "STOCK_ADJUSTMENT":
      showToast(
        "Inventory Adjusted",
        `Product #${payload.product_id} stock updated to ${payload.new_quantity}.`,
        "info"
      );
      break;

    default:
      break;
  }
}

function highlightRow(rowId) {
  const row = document.getElementById(rowId);
  if (row) {
    row.style.transition = "background-color 0.4s ease";
    row.style.backgroundColor = "rgba(56, 189, 248, 0.25)";
    setTimeout(() => {
      row.style.backgroundColor = "";
    }, 1800);
  }
}

// Auto start on page load
document.addEventListener("DOMContentLoaded", () => {
  initRealTimeStream();
});
