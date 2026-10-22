/**
 * Interactive Concurrency Control Lab Client
 * Demonstrates DBMS Unit 3 Concurrency Protocols (2PL, OCC, Lost Updates)
 */

async function runConcurrencySimulation() {
  const form = document.getElementById("concurrency-form");
  const btn = document.getElementById("run-sim-btn");
  const terminal = document.getElementById("sim-terminal-output");
  const summaryBox = document.getElementById("sim-summary-box");

  const productId = document.getElementById("sim-product-id").value;
  const warehouseId = document.getElementById("sim-warehouse-id").value;
  const initialStock = parseInt(document.getElementById("sim-initial-stock").value);
  const numThreads = parseInt(document.getElementById("sim-threads").value);
  const qtyPerBuyer = parseInt(document.getElementById("sim-qty-per-buyer").value);
  const mode = document.querySelector('input[name="sim-mode"]:checked').value;

  btn.disabled = true;
  btn.innerHTML = `<span class="pulse-dot"></span> Running Concurrent Threads...`;
  terminal.innerHTML = `<div class="terminal-line log-time">> Initializing ${numThreads} concurrent buyer threads at barrier...</div>`;
  summaryBox.style.display = "none";

  try {
    const response = await fetch("/api/concurrency/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: productId,
        warehouse_id: warehouseId,
        initial_stock: initialStock,
        num_threads: numThreads,
        qty_per_buyer: qtyPerBuyer,
        mode: mode
      })
    });

    const data = await response.json();

    if (!data.success) {
      terminal.innerHTML += `<div class="terminal-line log-error">> Error: ${data.error}</div>`;
      btn.disabled = false;
      btn.innerHTML = `Execute Concurrency Benchmark`;
      return;
    }

    const sim = data.simulation;
    terminal.innerHTML += `<div class="terminal-line log-lock">> All threads released simultaneously via Threading Barrier!</div>`;
    terminal.innerHTML += `<div class="terminal-line">> Selected Concurrency Control Mode: <strong>${sim.mode.toUpperCase()}</strong></div>`;
    terminal.innerHTML += `<div class="terminal-line">> Baseline Stock reset to: <strong>${sim.initial_stock}</strong> units</div>`;
    terminal.innerHTML += `<div class="terminal-line">> Total Requested across threads: ${sim.total_requested} units (${sim.num_threads} buyers × ${sim.qty_per_buyer} units)</div>`;
    terminal.innerHTML += `<div class="terminal-line">-----------------------------------------------------------</div>`;

    // Print individual thread traces
    sim.results.forEach((res) => {
      res.log.forEach((line) => {
        let cls = "terminal-line";
        if (line.includes("X-LOCK") || line.includes("LOCK")) cls += " log-lock";
        else if (line.includes("SUCCESS") || line.includes("COMMITTED")) cls += " log-success";
        else if (line.includes("ROLLBACK") || line.includes("REJECTED") || line.includes("Conflict")) cls += " log-warning";
        else if (line.includes("ERROR") || line.includes("ABORTED")) cls += " log-error";

        terminal.innerHTML += `<div class="${cls}">[${res.duration_ms}ms] ${escapeHtml(line)}</div>`;
      });
    });

    terminal.innerHTML += `<div class="terminal-line">-----------------------------------------------------------</div>`;
    terminal.innerHTML += `<div class="terminal-line log-time">> Simulation finished in ${data.total_elapsed_ms}ms. Verifying database state...</div>`;

    // Render Summary Card
    document.getElementById("res-mode").innerText = sim.mode.toUpperCase();
    document.getElementById("res-initial").innerText = sim.initial_stock;
    document.getElementById("res-final").innerText = sim.final_stock;
    document.getElementById("res-sales").innerText = `${sim.success_count} / ${sim.num_threads} Successful`;

    const anomalyBadge = document.getElementById("res-anomaly");
    if (sim.oversold) {
      anomalyBadge.className = "status-badge out_of_stock";
      anomalyBadge.innerText = "⚠ ANOMALY: OVERSELLING OCCURRED! (Lost Update Anomaly)";
      terminal.innerHTML += `<div class="terminal-line log-error font-bold">> CRITICAL ANOMALY: Overselling occurred! DBMS locking was bypassed.</div>`;
    } else {
      anomalyBadge.className = "status-badge healthy";
      anomalyBadge.innerText = "✓ ZERO OVERSELLING - SERIALIZABILITY PRESERVED (ACID Compliant)";
      terminal.innerHTML += `<div class="terminal-line log-success font-bold">> VERIFIED: Concurrency control successfully protected inventory consistency!</div>`;
    }

    summaryBox.style.display = "block";
    terminal.scrollTop = terminal.scrollHeight;

  } catch (err) {
    terminal.innerHTML += `<div class="terminal-line log-error">> Network/Server exception: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `Execute Concurrency Benchmark`;
  }
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}
