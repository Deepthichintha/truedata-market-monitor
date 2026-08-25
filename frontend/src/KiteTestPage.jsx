import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function money(value) {
  if (value === null || value === undefined) return "-";
  return `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}

function time(value) {
  if (!value) return "-";
  return String(value).replace("T", " ");
}

export default function KiteTestPage() {
  const [auth, setAuth] = useState(null);
  const [collector, setCollector] = useState(null);
  const [mapping, setMapping] = useState(null);
  const [data, setData] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadStatus() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/kite-test/status`);
      const result = await response.json();
      setAuth(result.auth);
      setCollector(result.collector);
    } catch (err) {
      setError("Kite backend is unavailable. Start FastAPI on port 8000.");
    }
  }

  async function loadLive() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/kite-test/live`);
      const result = await response.json();
      setData(result.data || []);
    } catch (err) {
      // Status polling displays the primary error.
    }
  }

  async function prepareMapping() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/kite-test/mapping`, {
        method: "POST",
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Mapping failed");
      setMapping(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function startCollector() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/kite-test/start`, {
        method: "POST",
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Collector start failed");
      setCollector(result.collector);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function stopCollector() {
    await fetch(`${API_BASE_URL}/api/kite-test/stop`, { method: "POST" });
    await loadStatus();
  }

  useEffect(() => {
    loadStatus();
    loadLive();
    const interval = setInterval(() => {
      loadStatus();
      loadLive();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const counts = useMemo(
    () => ({
      nse: data.filter((row) => row.exchange === "NSE").length,
      bse: data.filter((row) => row.exchange === "BSE").length,
    }),
    [data],
  );

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Kite Live Market Test</h1>
          <p>Independent Kite Connect NSE + BSE evaluation</p>
        </div>
        <div className="status-area">
          <span className={`status-dot ${collector?.connected ? "online" : "closed"}`} />
          <span>{collector?.connected ? "Kite Connected" : "Kite Not Connected"}</span>
        </div>
      </header>

      {error && <div className="error-banner">⚠ {error}</div>}

      <main className="container">
        <section className="summary-grid">
          <div className="summary-card">
            <span className="summary-label">Authentication</span>
            <strong>{auth?.authenticated ? "READY" : "LOGIN REQUIRED"}</strong>
            <small>Kite access token stays server-side</small>
          </div>
          <div className="summary-card">
            <span className="summary-label">Subscription</span>
            <strong>{collector?.subscribed_instruments || 0}</strong>
            <small>NSE + BSE instruments</small>
          </div>
          <div className="summary-card">
            <span className="summary-label">NSE</span>
            <strong>{counts.nse}</strong>
            <small>Live Kite instruments</small>
          </div>
          <div className="summary-card">
            <span className="summary-label">BSE</span>
            <strong>{counts.bse}</strong>
            <small>Live Kite instruments</small>
          </div>
        </section>

        <section className="toolbar">
          <div>
            <h2>Kite Test Controls</h2>
            <p>Same 10-stock NSE + 10-stock BSE evaluation universe.</p>
          </div>
          <div className="toolbar-actions">
            {!auth?.authenticated && (
              <a className="button-link" href={`${API_BASE_URL}/api/kite-test/login`}>
                Login with Kite
              </a>
            )}
            <button disabled={busy || !auth?.authenticated} onClick={prepareMapping}>
              Refresh Kite Mapping
            </button>
            <button disabled={busy || !auth?.authenticated} onClick={startCollector}>
              Start Kite Collector
            </button>
            <button disabled={!collector?.running} onClick={stopCollector}>
              Stop
            </button>
            <a className="button-link secondary" href="/">
              Provider Selection
            </a>
          </div>
        </section>

        {mapping && (
          <section className="table-card mapping-card">
            <div className="mapping-status">
              Mapping: {mapping.validation?.found}/{mapping.validation?.expected} ·
              {mapping.validation?.complete ? " complete" : " incomplete"}
            </div>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr><th>Exchange</th><th>Symbol</th><th>Kite Instrument Token</th><th>Tick Size</th></tr>
                </thead>
                <tbody>
                  {(mapping.instruments || []).map((row) => (
                    <tr key={`${row.exchange}-${row.symbol}`}>
                      <td>{row.exchange}</td><td>{row.symbol}</td>
                      <td>{row.instrument_token}</td><td>{row.tick_size || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <section className="table-card">
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th><th>Exchange</th><th>LTP</th><th>ATP</th><th>Volume</th>
                  <th>Open</th><th>High</th><th>Low</th><th>Prev Close</th>
                  <th>Bid</th><th>Ask</th><th>Last Trade</th><th>Exchange Time</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={`${item.exchange}-${item.symbol}`}>
                    <td><strong>{item.symbol}</strong><small>Kite {item.instrument_token}</small></td>
                    <td><span className={`exchange-badge ${item.exchange.toLowerCase()}`}>{item.exchange}</span></td>
                    <td className="ltp">{money(item.ltp)}</td><td>{money(item.atp)}</td>
                    <td>{item.total_volume?.toLocaleString("en-IN") || "-"}</td>
                    <td>{money(item.open)}</td><td className="high">{money(item.high)}</td>
                    <td className="low">{money(item.low)}</td><td>{money(item.prev_close)}</td>
                    <td>{money(item.bid)} {item.bid_qty ? `(${item.bid_qty})` : ""}</td>
                    <td>{money(item.ask)} {item.ask_qty ? `(${item.ask_qty})` : ""}</td>
                    <td>{time(item.last_trade_time)}</td><td>{time(item.exchange_timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!data.length && <div className="empty">No Kite ticks received yet. Authenticate and start the collector during live market hours.</div>}
          </div>
        </section>
      </main>

      <footer>Kite Provider Evaluation • TrueData implementation untouched</footer>
    </div>
  );
}
