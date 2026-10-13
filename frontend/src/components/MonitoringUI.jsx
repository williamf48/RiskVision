import { Link } from "react-router-dom";
import { title, metricValue, dateText } from "../utils/monitoring";
import Icon from "./Icon";

export function Badge({ value, children }) {
  return <span className={`rv-badge rv-${(value || "missing").toLowerCase()}`}>{children || title(value)}</span>;
}
export function LoadState({ error, retry }) {
  return <section className="dashboard-state" role={error ? "alert" : "status"}>
    <Icon name={error ? "info" : "layers"} size={28} />
    <h2>{error ? "The workspace could not load" : "Preparing your monitoring workspace"}</h2>
    <p>{error || "Checking financial evidence and covenant tests…"}</p>
    {error && <button className="primary-button" onClick={retry}>Try again</button>}
  </section>;
}
export function EvidenceDots({ metrics }) {
  return <div className="rv-evidence-dots" aria-label={`${metrics.filter((m) => m.eligible).length} of 4 current indicators`}>
    {metrics.map((m) => <span key={m.code} title={`${m.name}: ${title(m.freshness)}`} className={m.eligible ? "valid" : m.freshness.toLowerCase()} />)}
    <small>{metrics.filter((m) => m.eligible).length}/4</small>
  </div>;
}
export function CovenantTable({ rows, onReview, showBorrower = true, asOf }) {
  return <div className="table-scroll"><table className="rv-table covenant-register">
    <thead><tr>{showBorrower && <th>Borrower / facility</th>}<th>Covenant</th><th>Actual / limit</th><th>Headroom</th><th>Last test</th><th>Evidence</th><th>Next test</th>{onReview && <th><span className="sr-only">Review</span></th>}</tr></thead>
    <tbody>{rows.map((c) => <tr key={c.covenant_id}>
      {showBorrower && <td><Link className="rv-borrower-name" to={`/borrower/${c.borrower_id}${asOf ? `?as_of=${asOf}` : ""}`}>{c.borrower_name}</Link><small>{c.facility_code} · {title(c.facility_type)}</small></td>}
      <td><strong>{c.covenant_name}</strong><small>{!showBorrower && `${c.facility_code} · `}{title(c.testing_frequency)}{!c.in_scope ? ` · ${title(c.covenant_status)}` : ""}</small></td>
      <td><strong className="rv-mono">{metricValue(c.actual, ["DSCR", "DEBT_EBITDA"].includes(c.metric_code) ? "×" : "")}</strong><small>{c.threshold_direction === "MINIMUM" ? "≥" : "≤"} {c.threshold_value}{["DSCR", "DEBT_EBITDA"].includes(c.metric_code) ? "×" : ""} required</small></td>
      <td><strong className={c.headroom_absolute < 0 ? "rv-red rv-mono" : "rv-mono"}>{c.headroom_pct == null ? c.headroom_absolute == null ? "—" : `${c.headroom_absolute.toFixed(2)} absolute` : `${c.headroom_pct > 0 ? "+" : ""}${c.headroom_pct.toFixed(1)}%`}</strong>
        <small className="rv-headroom-track"><i style={{ width: `${Math.min(100, Math.max(5, c.headroom_pct == null ? 0 : Math.abs(c.headroom_pct) * 2))}%`, background: c.headroom_absolute < 0 ? "#ce5360" : "#218b7b" }} /></small></td>
      <td><Badge value={c.in_scope && c.unresolved_breach ? "BREACHED" : c.confirmed && c.in_scope ? c.result : "UNVERIFIED"}>{c.unresolved_breach && c.in_scope && c.result !== "BREACHED" ? "Breach unresolved" : title(c.result)}</Badge><small>{dateText(c.test_date)}</small>{c.unresolved_breach && c.result !== "BREACHED" && <small>Last valid breach: {dateText(c.last_valid_test_date)}</small>}</td>
      <td><Badge value={c.freshness} /><small>{c.source || "No test received"}</small></td>
      <td><span className={c.overdue ? "rv-red" : ""}>{dateText(c.next_test_date)}</span><small>{c.overdue ? "Overdue" : c.days_to_test == null ? "Not scheduled" : c.days_to_test >= 0 ? `In ${c.days_to_test} days` : "Schedule needs refresh"}</small></td>
      {onReview && <td><button className="rv-row-action" aria-label={`Review ${c.borrower_name} ${c.covenant_name}`} onClick={() => onReview(c.borrower_id)}><Icon name="arrow" size={16} /></button></td>}
    </tr>)}</tbody>
  </table>{rows.length === 0 && <div className="rv-empty"><Icon name="shield" size={24} /><h3>No matching covenants</h3><p>Change the filters or configure facility covenants to monitor them here.</p></div>}</div>;
}

export function CaseHistory({ events = [] }) {
  return <div className="rv-history">
    {!events.length && <p className="rv-muted">No decision has been recorded. Save a case to start its history.</p>}
    {events.map((event) => <article key={event.id} className="rv-history-event">
      <div className="rv-history-mark"><Icon name="check" size={13} /></div>
      <div><div className="rv-history-heading"><strong>{title(event.after.status)}</strong><span>v{event.version}</span><time>{new Date(event.recorded_at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</time></div>
        <small>{event.actor} · {event.after.owner || "Unassigned"}{event.after.due_date ? ` · Due ${dateText(event.after.due_date)}` : ""}</small>
        <p>{event.after.note}</p>
        <details><summary>Assessment recorded with this decision</summary>
          <p>{event.evidence.policy_version} · Observation cutoff {dateText(event.evidence.as_of)} · {title(event.evidence.priority)} priority</p>
          <p>{event.evidence.drivers.join(" · ")}</p>
          <p>Change: {title(event.before.status || "UNASSIGNED")} → {title(event.after.status)}. Action: {event.after.next_action || "No action recorded"}.</p>
        </details>
      </div>
    </article>)}
  </div>;
}
