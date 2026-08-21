import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";


function formatNumber(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
}


function formatVolume(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  const number = Number(value);

  if (number >= 10000000) {
    return `${(number / 10000000).toFixed(2)} Cr`;
  }

  if (number >= 100000) {
    return `${(number / 100000).toFixed(2)} L`;
  }

  if (number >= 1000) {
    return `${(number / 1000).toFixed(2)} K`;
  }

  return number.toString();
}


function formatTimestamp(value) {
  if (!value) {
    return "-";
  }

  return value.replace("T", " ");
}


function getStatusLabel(status, error) {
  if (error) {
    return "Backend Offline";
  }

  if (status === "LIVE") {
    return "Live";
  }

  if (status === "STALE") {
    return "Feed Stale";
  }

  if (status === "CLOSED") {
    return "Market Closed";
  }

  if (status === "PRE_MARKET") {
    return "Pre-Market";
  }

  return "Checking...";
}


function getStatusClass(status, error) {
  if (error) {
    return "offline";
  }

  if (status === "LIVE") {
    return "online";
  }

  if (status === "STALE") {
    return "stale";
  }

  if (status === "CLOSED") {
    return "closed";
  }

  if (status === "PRE_MARKET") {
    return "checking";
  }

  return "checking";
}


function App() {
  const [marketData, setMarketData] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");
  const [exchangeFilter, setExchangeFilter] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [error, setError] = useState("");

  const [marketStatus, setMarketStatus] = useState("CHECKING");
  const [latestTick, setLatestTick] = useState(null);
  const [tickAge, setTickAge] = useState(null);


  async function loadMarketData() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/market/live`
      );

      if (!response.ok) {
        throw new Error(
          `Backend returned ${response.status}`
        );
      }

      const result = await response.json();

      setMarketData(result.data || []);
      setError("");
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }


  async function loadMarketStatus() {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/market/status`
      );

      if (!response.ok) {
        throw new Error(
          `Status request failed: ${response.status}`
        );
      }

      const result = await response.json();

      setMarketStatus(result.status || "CHECKING");
      setLatestTick(result.latest_tick || null);
      setTickAge(result.age_seconds ?? null);

      setError("");
    } catch (err) {
      console.error(err);

      setMarketStatus("OFFLINE");
      setLatestTick(null);
      setTickAge(null);

      setError(
        "Unable to connect to backend. Make sure FastAPI is running on port 8000."
      );
    }
  }


  async function refreshDashboard() {
    await Promise.all([
      loadMarketData(),
      loadMarketStatus(),
    ]);
  }


  async function loadHistory(symbol) {
    setSelectedSymbol(symbol);
    setHistoryLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/market/${symbol}/history?limit=200`
      );

      if (!response.ok) {
        throw new Error(
          `History request failed: ${response.status}`
        );
      }

      const result = await response.json();

      setHistory(result.data || []);
    } catch (err) {
      console.error(err);
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }


  useEffect(() => {
    refreshDashboard();

    const interval = setInterval(() => {
      refreshDashboard();
    }, 1000);

    return () => clearInterval(interval);
  }, []);


  const exchangeCounts = useMemo(() => {
    return {
      all: marketData.length,
      nse: marketData.filter(
        (item) => item.exchange === "NSE"
      ).length,
      bse: marketData.filter(
        (item) => item.exchange === "BSE"
      ).length,
    };
  }, [marketData]);


  const filteredData = useMemo(() => {
    const searchText = search.trim().toUpperCase();

    return marketData.filter((item) => {
      const matchesExchange =
        exchangeFilter === "ALL" ||
        item.exchange === exchangeFilter;

      const matchesSearch =
        !searchText ||
        item.symbol?.toUpperCase().includes(searchText);

      return matchesExchange && matchesSearch;
    });
  }, [
    marketData,
    search,
    exchangeFilter,
  ]);


  const statusLabel = getStatusLabel(
    marketStatus,
    error
  );


  const statusClass = getStatusClass(
    marketStatus,
    error
  );


  return (
    <div className="app">

      <header className="topbar">
        <div>
          <h1>TrueData Market Monitor</h1>

          <p>
            Real-time NSE &amp; BSE market monitoring
          </p>
        </div>

        <div className="status-area">
          <span
            className={`status-dot ${statusClass}`}
          />

          <span>{statusLabel}</span>

          {latestTick && (
            <span className="refresh-time">
              Last tick {formatTimestamp(latestTick)}
            </span>
          )}

          {tickAge !== null &&
            marketStatus === "LIVE" && (
              <span className="refresh-time">
                ({Math.round(tickAge)}s ago)
              </span>
            )}
        </div>
      </header>


      {error && (
        <div className="error-banner">
          ⚠ {error}
        </div>
      )}


      <main className="container">

        <section className="summary-grid">

          <div className="summary-card">
            <span className="summary-label">
              Active Symbols
            </span>

            <strong>
              {exchangeCounts.all}
            </strong>

            <small>
              NSE + BSE market symbols
            </small>
          </div>


          <div className="summary-card">
            <span className="summary-label">
              Market Status
            </span>

            <strong>
              {marketStatus === "LIVE"
                ? "LIVE"
                : marketStatus === "STALE"
                  ? "STALE"
                  : marketStatus === "CLOSED"
                    ? "CLOSED"
                    : marketStatus === "PRE_MARKET"
                      ? "PRE-MARKET"
                      : "WAITING"}
            </strong>

            <small>
              NSE &amp; BSE market
            </small>
          </div>


          <div className="summary-card">
            <span className="summary-label">
              Dashboard Refresh
            </span>

            <strong>
              1 sec
            </strong>

            <small>
              Automatic polling
            </small>
          </div>


          <div className="summary-card">
            <span className="summary-label">
              Exchanges
            </span>

            <strong>
              NSE + BSE
            </strong>

            <small>
              {exchangeCounts.nse} NSE •{" "}
              {exchangeCounts.bse} BSE
            </small>
          </div>

        </section>


        <section className="toolbar">

          <div>
            <h2>Live Market</h2>

            <p>
              Showing {filteredData.length} of{" "}
              {marketData.length} symbols
            </p>
          </div>


          <div className="toolbar-actions">

            <div className="exchange-filters">
              <button
                className={
                  exchangeFilter === "ALL"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setExchangeFilter("ALL")
                }
              >
                ALL ({exchangeCounts.all})
              </button>

              <button
                className={
                  exchangeFilter === "NSE"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setExchangeFilter("NSE")
                }
              >
                NSE ({exchangeCounts.nse})
              </button>

              <button
                className={
                  exchangeFilter === "BSE"
                    ? "active"
                    : ""
                }
                onClick={() =>
                  setExchangeFilter("BSE")
                }
              >
                BSE ({exchangeCounts.bse})
              </button>
            </div>


            <input
              type="text"
              placeholder="Search symbol..."
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />


            <button onClick={refreshDashboard}>
              Refresh
            </button>

          </div>

        </section>


        {loading ? (

          <div className="loading">
            Loading market data...
          </div>

        ) : (

          <section className="table-card">

            <div className="table-wrapper">

              <table>

                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Exchange</th>
                    <th>LTP</th>
                    <th>ATP</th>
                    <th>Volume</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Prev Close</th>
                    <th>Bid</th>
                    <th>Ask</th>
                    <th>Updated</th>
                  </tr>
                </thead>


                <tbody>

                  {filteredData.map((item) => (

                    <tr
                      key={`${item.exchange}-${item.symbol}`}
                      onClick={() =>
                        loadHistory(item.symbol)
                      }
                      className={
                        selectedSymbol === item.symbol
                          ? "selected-row"
                          : ""
                      }
                    >

                      <td className="symbol-cell">

                        <strong>
                          {item.symbol}
                        </strong>

                        <small>
                          {item.truedata_symbol_id}
                        </small>

                      </td>


                      <td>
                        <span
                          className={`exchange-badge ${
                            item.exchange?.toLowerCase()
                          }`}
                        >
                          {item.exchange || "-"}
                        </span>
                      </td>


                      <td className="ltp">
                        ₹{formatNumber(item.ltp)}
                      </td>


                      <td>
                        ₹{formatNumber(item.atp)}
                      </td>


                      <td>
                        {formatVolume(
                          item.total_volume
                        )}
                      </td>


                      <td>
                        ₹{formatNumber(item.open)}
                      </td>


                      <td className="high">
                        ₹{formatNumber(item.high)}
                      </td>


                      <td className="low">
                        ₹{formatNumber(item.low)}
                      </td>


                      <td>
                        ₹{formatNumber(
                          item.prev_close
                        )}
                      </td>


                      <td>
                        {item.bid !== null
                          ? `₹${formatNumber(item.bid)}`
                          : "-"}
                      </td>


                      <td>
                        {item.ask !== null
                          ? `₹${formatNumber(item.ask)}`
                          : "-"}
                      </td>


                      <td>
                        {formatTimestamp(
                          item.timestamp
                        )}
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>


              {filteredData.length === 0 && (
                <div className="empty">
                  No market data found.
                </div>
              )}

            </div>

          </section>

        )}


        {selectedSymbol && (

          <section className="history-section">

            <div className="history-header">

              <div>

                <h2>
                  {selectedSymbol} Historical Data
                </h2>

                <p>
                  Last 6 months of completed EOD market data
                </p>

              </div>


              <button
                className="close-button"
                onClick={() => {
                  setSelectedSymbol(null);
                  setHistory([]);
                }}
              >
                Close
              </button>

            </div>


            {historyLoading ? (

              <div className="loading">
                Loading historical data...
              </div>

            ) : (

              <div className="history-table-wrapper">

                <table>

                  <thead>

                    <tr>
                      <th>Date</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      <th>Volume</th>
                      <th>OI</th>
                    </tr>

                  </thead>


                  <tbody>

                    {history.map(
                      (item, index) => (

                        <tr
                          key={`${item.timestamp}-${index}`}
                        >

                          <td>
                            {formatTimestamp(
                              item.timestamp
                            )}
                          </td>


                          <td>
                            ₹{formatNumber(item.open)}
                          </td>


                          <td className="high">
                            ₹{formatNumber(item.high)}
                          </td>


                          <td className="low">
                            ₹{formatNumber(item.low)}
                          </td>


                          <td>
                            ₹{formatNumber(item.close)}
                          </td>


                          <td>
                            {formatVolume(item.volume)}
                          </td>


                          <td>
                            {formatNumber(item.oi)}
                          </td>

                        </tr>
                      )
                    )}

                  </tbody>

                </table>


                {history.length === 0 && (
                  <div className="empty">
                    No historical data available for{" "}
                    {selectedSymbol}.
                  </div>
                )}

              </div>

            )}

          </section>

        )}

      </main>


      <footer>
        TrueData Market Monitor • Local Development
      </footer>

    </div>
  );
}


export default App;
