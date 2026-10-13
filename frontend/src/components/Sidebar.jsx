import { NavLink } from "react-router-dom";
import Icon from "./Icon";
const groups = [
  [
    "WORKSPACE",
    [
      ["Monitoring", "/", "grid"],
      ["Analyst work queue", "/cases", "report"],
      ["Covenant register", "/covenants", "shield"],
      ["Data quality", "/data-quality", "layers"],
      ["Borrowers", "/borrowers", "users"],
    ],
  ],
  [
    "ANALYSIS & POLICY",
    [
      ["Portfolio analytics", "/portfolio", "portfolio"],
      ["Trajectory signals", "/interventions", "pulse"],
      ["Reports", "/reports", "report"],
      ["Historical validation", "/validation", "shield"],
      ["Monitoring policy", "/policy", "layers"],
    ],
  ],
];
export default function Sidebar({ health }) {
  return (
    <aside className="sidebar">
      <NavLink
        to="/"
        className="sidebar-brand"
        aria-label="RiskVision overview"
      >
        <div className="brand-mark">
          <Icon name="pulse" size={23} />
        </div>
        <div>
          <h2>
            RiskVision<span className="brand-dot">.</span>
          </h2>
          <span>CREDIT INTELLIGENCE</span>
        </div>
      </NavLink>
      <div className="workspace-label">
        <span className="workspace-avatar">RV</span>
        <div>
          Credit workspace<small>Portfolio monitoring</small>
        </div>
        <Icon name="layers" size={16} />
      </div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {groups.map(([title, items]) => (
          <div className="nav-group" key={title}>
            <p className="nav-caption">{title}</p>
            {items.map(([name, path, icon]) => (
              <NavLink
                key={path}
                to={path}
                end={path === "/"}
                className={({ isActive }) =>
                  `sidebar-link${isActive ? " active" : ""}`
                }
              >
                <Icon name={icon} />
                <span>{name}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-insight">
        <Icon name="shield" size={20} />
        <strong>Every signal, explained.</strong>
        <p>Trace priorities back to the underlying financial evidence.</p>
      </div>
      <div className="sidebar-footer">
        <span
          className={`status-dot ${health?.status === "ready" ? "ready" : ""}`}
        />
        <div>
          {health?.data_mode === "synthetic"
            ? "Sample portfolio"
            : health?.status === "ready"
              ? "Connected workspace"
              : "Service unavailable"}
          <small>
            {health?.data_mode === "synthetic"
              ? "Synthetic development data"
              : "Analyst decision support"}
          </small>
        </div>
      </div>
    </aside>
  );
}
