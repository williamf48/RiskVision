import { Suspense, useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import Icon from "./Icon";
import { getJson } from "../utils/api";
const titles = {
  "/": "Portfolio monitoring",
  "/cases": "Analyst work queue",
  "/covenants": "Covenant register",
  "/data-quality": "Data quality",
  "/policy": "Monitoring policy",
  "/portfolio": "Portfolio",
  "/borrowers": "Borrowers",
  "/interventions": "Interventions",
  "/alerts": "Alerts",
  "/reports": "Reports",
  "/validation": "Historical validation",
};
export default function DashboardLayout() {
  const [health, setHealth] = useState(null);
  const [search, setSearch] = useState("");
  const [fullScreenError, setFullScreenError] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    getJson("/health")
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active) setHealth({ status: "offline" });
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);
  async function fullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
      setFullScreenError("");
    } catch {
      setFullScreenError("Use F11 for full screen in this browser.");
    }
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <Sidebar health={health} />
      <div className="workspace-main">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace
            <Icon name="chevron" size={13} />
            <strong>
              {titles[location.pathname] || "Borrower intelligence"}
            </strong>
          </div>
          <form
            className="global-search"
            onSubmit={(event) => {
              event.preventDefault();
              navigate(`/borrowers?q=${encodeURIComponent(search.trim())}`);
              setSearch("");
            }}
          >
            <Icon name="search" size={16} />
            <input
              aria-label="Search all borrowers"
              placeholder="Find a borrower…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <kbd>↵</kbd>
          </form>
          <div className="topbar-actions">
            <span
              className={`connection-label ${health?.status === "ready" ? "" : "offline"}`}
            >
              <span className="status-dot" />
              {health === null
                ? "Connecting"
                : health.status !== "ready"
                  ? "API offline"
                  : health.data_mode === "synthetic"
                    ? "Sample data"
                    : "API connected"}
            </span>
            <button
              className="icon-button"
              title="Refresh data"
              aria-label="Refresh data"
              onClick={() => window.location.reload()}
            >
              <Icon name="refresh" size={17} />
            </button>
            <button
              className="icon-button fullscreen-button"
              title="Full screen"
              aria-label="Toggle full screen"
              onClick={fullscreen}
            >
              <Icon name="expand" size={17} />
            </button>
            <span className="profile-avatar" title="Analyst workspace">
              WF
            </span>
          </div>
        </header>
        {fullScreenError && (
          <p role="status" className="inline-notice">
            {fullScreenError}
          </p>
        )}
        <main id="main-content" className="app-content">
          {["/portfolio", "/interventions", "/reports", "/borrowers"].includes(location.pathname) && <p className="rv-model-context">Trajectory analysis view. The Monitoring workspace also includes covenant overrides and evidence-quality checks.</p>}
          <Suspense fallback={<div className="dashboard-state" role="status">Loading workspace…</div>}><Outlet key={location.pathname} context={{ health }} /></Suspense>
        </main>
        <footer className="workspace-footer">
          <span>RiskVision · Explainable credit monitoring</span>
          <span>
            {health?.data_mode === "synthetic"
              ? "Synthetic portfolio · Rules-based analysis"
              : "Rules-based analysis · Analyst review required"}
          </span>
        </footer>
      </div>
    </div>
  );
}
