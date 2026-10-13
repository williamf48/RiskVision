import { useEffect, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import Icon from "./Icon";
import { getJson, money, label } from "../utils/api";
const priorityColors = {
  URGENT: "#df4b55",
  HIGH: "#e79d43",
  MEDIUM: "#6387ce",
  LOW: "#279a7a",
  INSUFFICIENT_DATA: "#d8dfe8",
};
export default function MainDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const { health } = useOutletContext();
  useEffect(() => {
    let active = true;
    Promise.all(
      [
        "/portfolio_summary",
        "/intervention_watchlist",
        "/borrowers",
        "/covenant_summary",
      ].map((path) => getJson(path)),
    )
      .then(([summary, watchlist, borrowers, covenants]) => {
        if (active) setData({ summary, watchlist, borrowers, covenants });
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  if (error)
    return (
      <div className="dashboard-state error" role="alert">
        <Icon name="info" size={28} />
        <h2>Let's reconnect your workspace</h2>
        <p>{error}</p>
        <button
          className="primary-button"
          onClick={() => {
            setError("");
            setAttempt((a) => a + 1);
          }}
        >
          Try again
        </button>
      </div>
    );
  if (!data)
    return (
      <div
        className="dashboard-skeleton"
        role="status"
        aria-label="Loading portfolio"
      >
        <div />
        <div />
        <div />
        <div />
        <section />
        <section />
      </div>
    );
  const { summary, watchlist, borrowers, covenants } = data;
  const assessable = watchlist.filter(
    (a) => a.intervention_priority !== "INSUFFICIENT_DATA",
  );
  const actionable = assessable.filter(
    (a) => a.intervention_priority !== "LOW",
  );
  const counts = Object.fromEntries(
    Object.keys(priorityColors).map((p) => [
      p,
      watchlist.filter((a) => a.intervention_priority === p).length,
    ]),
  );
  const top = assessable[0];
  const coverage = borrowers.length
    ? Math.round((assessable.length / borrowers.length) * 100)
    : 0;
  const borrowersById = Object.fromEntries(borrowers.map((b) => [b.id, b]));
  const reviewExposure = actionable.reduce(
    (sum, a) => sum + Number(borrowersById[a.borrower_id]?.loan_amount || 0),
    0,
  );
  const dataThrough = health?.latest_observation
    ? new Date(
        `${health.latest_observation.slice(0, 10)}T00:00:00`,
      ).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Not available";
  return (
    <div className="overview">
      <div className="overview-heading">
        <div>
          <p className="eyebrow">PORTFOLIO INTELLIGENCE</p>
          <h1>A clearer view of credit risk.</h1>
          <p>
            Spot deterioration. Understand the evidence. Prioritize your next
            action.
          </p>
        </div>
        <Link className="primary-button" to="/reports">
          <Icon name="report" size={16} />
          Open reports
        </Link>
      </div>
      <div className="overview-meta">
        <span>
          <Icon name="clock" size={14} />
          Latest observation · {dataThrough}
        </span>
        <span>
          {health?.data_mode === "synthetic"
            ? "SYNTHETIC PORTFOLIO"
            : "CREDIT MONITORING"}
        </span>
      </div>
      <div className="kpi-row">
        {[
          {
            name: "Total exposure",
            value: money(summary.total_exposure),
            unit: "Cr",
            note: `${borrowers.length} corporate borrowers`,
            icon: "portfolio",
            path: "/portfolio",
          },
          {
            name: "Prioritized for review",
            value: actionable.length.toString().padStart(2, "0"),
            note: `${money(reviewExposure)} Cr exposure under review`,
            icon: "pulse",
            path: "/interventions",
            accent: "amber",
          },
          {
            name: "Urgent interventions",
            value: counts.URGENT.toString().padStart(2, "0"),
            note: "Highest priority for investigation",
            icon: "bell",
            path: "/interventions",
            accent: "red",
          },
          {
            name: "Historical coverage",
            value: `${coverage}%`,
            note: `${assessable.length} of ${borrowers.length} borrowers assessable`,
            icon: "layers",
            path: "/portfolio",
          },
        ].map((k) => (
          <Link
            className={`kpi-tile ${k.accent || ""}`}
            to={k.path}
            key={k.name}
          >
            <div className="kpi-label">
              {k.name}
              <span>
                <Icon name={k.icon} size={17} />
              </span>
            </div>
            <strong>
              {k.value}
              <small>{k.unit}</small>
            </strong>
            <div className="kpi-bottom">
              {k.note}
              <Icon name="chevron" size={14} />
            </div>
          </Link>
        ))}
      </div>
      <div className="overview-grid">
        <section className="panel priority-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">FOCUS YOUR ATTENTION</p>
              <h2>Intervention priorities</h2>
            </div>
            <Link to="/interventions" className="text-action">
              View queue
              <Icon name="arrow" size={15} />
            </Link>
          </div>
          <div className="table-scroll">
            <table className="data-table priority-table">
              <thead>
                <tr>
                  <th>Borrower</th>
                  <th>Priority</th>
                  <th>Signals worsening</th>
                  <th>Exposure</th>
                  <th>
                    <span className="sr-only">Open borrower</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {assessable.slice(0, 5).map((a, i) => (
                  <tr key={a.borrower_id}>
                    <td>
                      <Link
                        to={`/borrower/${a.borrower_id}`}
                        className="account-cell"
                      >
                        <span className={`account-monogram monogram-${i}`}>
                          {a.borrower_name
                            .split(" ")
                            .slice(0, 2)
                            .map((n) => n[0])
                            .join("")}
                        </span>
                        <span>
                          <strong>{a.borrower_name}</strong>
                          <small>{borrowersById[a.borrower_id]?.sector}</small>
                        </span>
                      </Link>
                    </td>
                    <td>
                      <span
                        className={`priority-badge ${a.intervention_priority.toLowerCase()}`}
                      >
                        <i />
                        {label(a.intervention_priority)}
                      </span>
                    </td>
                    <td>
                      <div className="signal-count">
                        <strong>
                          {a.deteriorating_signals}
                          <span> / {a.metrics_analyzed}</span>
                        </strong>
                        <div>
                          {Array.from(
                            { length: a.metrics_analyzed },
                            (_, j) => (
                              <i
                                key={j}
                                className={
                                  j < a.deteriorating_signals ? "worsening" : ""
                                }
                              />
                            ),
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="numeric">
                      {money(borrowersById[a.borrower_id]?.loan_amount)}{" "}
                      <small>Cr</small>
                    </td>
                    <td>
                      <Link
                        to={`/borrower/${a.borrower_id}`}
                        className="row-arrow"
                        aria-label={`Review ${a.borrower_name}`}
                      >
                        <Icon name="arrow" size={16} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!assessable.length && (
            <p className="empty-state">
              No borrowers have sufficient history for a trajectory assessment.
            </p>
          )}
          <div className="panel-footnote">
            <Icon name="info" size={14} />
            Priority reflects financial condition, trend persistence and signal
            convergence.
          </div>
        </section>
        <section className="briefing-panel">
          <div className="briefing-top">
            <span className="briefing-symbol">
              <Icon name="pulse" size={19} />
            </span>
            <span>PRIORITY BRIEFING</span>
            <span className="briefing-live">RULES-BASED</span>
          </div>
          {top ? (
            <>
              <span
                className={`priority-badge ${top.intervention_priority.toLowerCase()}`}
              >
                {label(top.intervention_priority)} priority
              </span>
              <h2>{top.borrower_name}</h2>
              <p>
                {top.deteriorating_signals} of {top.metrics_analyzed} indicators
                are deteriorating, with {top.convergence_percentage}% signal
                convergence.
              </p>
              <div className="briefing-stat-grid">
                <div>
                  <strong>{top.persistent_deterioration_signals}</strong>
                  <span>Persistent trends</span>
                </div>
                <div>
                  <strong>{top.critical_condition_signals}</strong>
                  <span>Critical signals</span>
                </div>
              </div>
              <div className="briefing-reason">
                <span>NEXT INVESTIGATION</span>
                <p>
                  {top.recommended_investigations?.[0] ||
                    "Review the underlying financial observations."}
                </p>
              </div>
              <Link
                to={`/borrower/${top.borrower_id}`}
                className="briefing-button"
              >
                Review borrower
                <Icon name="arrow" size={17} />
              </Link>
            </>
          ) : (
            <>
              <h2>No ranked cases yet</h2>
              <p>
                Add historical observations to assess changes in borrower
                conditions.
              </p>
            </>
          )}
        </section>
        <section className="panel distribution-panel">
          <div className="panel-heading">
            <div>
              <h2>Portfolio assessment</h2>
              <p>
                Coverage and intervention mix across {borrowers.length}{" "}
                borrowers.
              </p>
            </div>
            <Icon name="layers" size={20} />
          </div>
          <div
            className="distribution-bar"
            role="img"
            aria-label={Object.entries(counts)
              .map(([p, count]) => `${label(p)}: ${count}`)
              .join(", ")}
          >
            {Object.entries(counts)
              .filter(([, n]) => n > 0)
              .map(([p, count]) => (
                <span
                  key={p}
                  style={{ flex: count, background: priorityColors[p] }}
                  title={`${label(p)}: ${count}`}
                />
              ))}
          </div>
          <div className="distribution-legend">
            {Object.entries(counts).map(([p, count]) => (
              <div key={p}>
                <span>
                  <i style={{ background: priorityColors[p] }} />
                  {p === "INSUFFICIENT_DATA" ? "Missing history" : label(p)}
                </span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
          <div className="coverage-note">
            <Icon name="info" size={16} />
            <span>
              <strong>
                {counts.INSUFFICIENT_DATA} borrowers need more historical data.
              </strong>{" "}
              Insufficient history is kept separate from low risk.
            </span>
            <Link to="/borrowers" aria-label="Review borrower coverage">
              <Icon name="arrow" size={18} />
            </Link>
          </div>
        </section>
        <section className="panel covenant-compact">
          <div className="panel-heading">
            <div>
              <h2>Covenant monitoring</h2>
              <p>Latest facility-level tests.</p>
            </div>
            <Icon name="shield" size={20} />
          </div>
          <div className="covenant-numbers">
            <div>
              <strong className="text-red">
                {covenants.breached_covenants ?? 0}
              </strong>
              <span>Breached</span>
            </div>
            <div>
              <strong className="text-amber">
                {covenants.near_breach_covenants ?? 0}
              </strong>
              <span>Near breach</span>
            </div>
            <div>
              <strong>{covenants.healthy_covenants ?? 0}</strong>
              <span>Healthy</span>
            </div>
          </div>
          <Link to="/portfolio" className="covenant-link">
            Explore covenant pressure
            <Icon name="arrow" size={17} />
          </Link>
        </section>
      </div>
    </div>
  );
}
