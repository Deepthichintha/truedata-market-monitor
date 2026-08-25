import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function ProviderSelection() {
  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Market Data Provider Evaluation</h1>
          <p>Independent NSE + BSE live-data testing</p>
        </div>
      </header>

      <main className="container provider-selection">
        <section className="provider-hero">
          <h2>Select a Market Data Provider</h2>
          <p>
            The two providers are tested independently. TrueData remains on its
            existing implementation; Kite uses its own authentication,
            instrument mapping, WebSocket collector, storage, and API.
          </p>
        </section>

        <section className="provider-grid">
          <a className="provider-card" href="/?provider=truedata">
            <span className="provider-tag">EXISTING</span>
            <h3>TrueData</h3>
            <p>Open the existing TrueData NSE + BSE monitor.</p>
            <span className="provider-action">Open TrueData Test →</span>
          </a>

          <a className="provider-card kite" href="/?provider=kite">
            <span className="provider-tag">NEW EVALUATION</span>
            <h3>Kite</h3>
            <p>Run the independent Kite Connect NSE + BSE test.</p>
            <span className="provider-action">Open Kite Test →</span>
          </a>
        </section>

        <div className="provider-note">
          Backend: {API_BASE_URL} · Same test universe · Independent data paths
        </div>
      </main>
    </div>
  );
}
