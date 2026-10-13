import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Icon from "../components/Icon";
import { Badge, CaseHistory, CovenantTable, EvidenceDots, LoadState } from "../components/MonitoringUI";
import { CaseDialog } from "../components/CasePanel";
import { useResource, dateText, exportQueue, metricValue, title } from "../utils/monitoring";
import { money } from "../utils/api";

const creditPriorities = ["URGENT", "HIGH", "WATCH"];
const pageTitles = { monitoring: "Portfolio monitoring", cases: "Analyst work queue", covenants: "Covenant register", quality: "Data coverage & quality" };
const descriptions = {
  monitoring: "A clear view of credit exceptions, supporting evidence, and the next action.",
  cases: "Assign a review, document the decision, and keep every follow-up visible.",
  covenants: "Contractual limits and test evidence, organized by borrower and facility.",
  quality: "See what is current, what is missing, and where monitoring needs better evidence.",
};

export default function MonitoringPage({ view = "monitoring" }) {
  const [params, setParams] = useSearchParams();
  const [cutoff, setCutoff] = useState("");
  const { data, error, refresh } = useResource(`/monitoring${cutoff ? `?as_of=${cutoff}` : ""}`);
  const [tab, setTab] = useState(view === "monitoring" ? "attention" : "all");
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("all");
  const [priority, setPriority] = useState("all");
  const [caseStatus, setCaseStatus] = useState("all");
  const contractStatus = params.get("status") || "all";
  function setContractStatus(value) {
    const next = new URLSearchParams(params);
    if (value === "all") next.delete("status");
    else next.set("status", value);
    setParams(next, { replace: true });
  }
  const [selected, setSelected] = useState(null);
  const [sort, setSort] = useState("priority");
  const [page, setPage] = useState(1);
  if (!data) return <LoadState error={error} retry={refresh} />;
  const { summary, borrowers, as_of: asOf } = data;
  const allContracts = borrowers.flatMap((b) => b.covenants.map((c) => ({ ...c, borrower_name: b.borrower_name, sector: b.sector })));
  const tabs = view === "cases" ? [["all", "All borrowers", borrowers.length], ["active", "Active cases", summary.open_cases], ["unassigned", "Not started", borrowers.filter((b) => !b.case).length], ["overdue", "Overdue", summary.overdue_cases], ["resolved", "Resolved", borrowers.filter((b) => b.case?.status === "RESOLVED").length]]
    : [["attention", "Credit exceptions", summary.attention_count], ["data", "Evidence exceptions", summary.data_exceptions], ["all", "All borrowers", borrowers.length], ["routine", "Routine", summary.counts.ROUTINE]];
  function resetPage(setter, value) { setter(value); setPage(1); }
  const matches = (b) => b.borrower_name.toLowerCase().includes(search.toLowerCase()) && (sector === "all" || b.sector === sector);
  let rows = borrowers.filter((b) => matches(b) && (priority === "all" || b.priority === priority) && (caseStatus === "all" || (b.case?.status || "UNASSIGNED") === caseStatus));
  if (view !== "quality" && view !== "covenants") rows = rows.filter((b) => tab === "all" || (tab === "attention" && creditPriorities.includes(b.priority)) || (tab === "data" && b.data_issues.length > 0)
    || (tab === "routine" && b.priority === "ROUTINE") || (tab === "active" && b.case && b.case.status !== "RESOLVED") || (tab === "unassigned" && !b.case)
    || (tab === "overdue" && b.case_overdue) || (tab === "resolved" && b.case?.status === "RESOLVED"));
  rows.sort((a, b) => sort === "exposure" ? b.exposure - a.exposure : sort === "name" ? a.borrower_name.localeCompare(b.borrower_name) : b.rank - a.rank || b.exposure - a.exposure);
  const contractRows = allContracts.filter((c) => matches(c) && (contractStatus === "all" || (contractStatus === "EVIDENCE" && c.freshness !== "VALID") || (contractStatus === "BREACHED" ? c.in_scope && c.unresolved_breach : c.result === contractStatus)));
  const visibleRows = rows.slice((page - 1) * 10, page * 10);
  const pages = Math.max(1, Math.ceil(rows.length / 10));
  const total = summary.exposure;
  return <div className="rv-workspace">
    <div className="rv-page-heading"><div><p className="eyebrow">CREDIT OPERATIONS / {view === "monitoring" ? "OVERVIEW" : view.toUpperCase()}</p><h1>{pageTitles[view]}</h1><p>{descriptions[view]}</p></div>
      <div className="rv-heading-actions"><Link className="secondary-button" to="/policy"><Icon name="shield" size={15} />Monitoring policy</Link>
        {view !== "covenants" && <button className="primary-button" onClick={() => exportQueue(rows, asOf)}><Icon name="download" size={15} />Export queue</button>}
      </div></div>
    <div className="rv-context-bar"><div><span className="status-dot ready" />{data.mode === "synthetic" ? "Sample portfolio" : "Connected portfolio"}<span className="rv-context-divider" />INR · Exposure in crore<span className="rv-context-divider" /><span>{data.policy_version}</span></div>
      <label>Observation cutoff<input aria-label="Observation cutoff" type="date" value={cutoff || asOf} max={new Date().toISOString().slice(0, 10)} onChange={(e) => { if (e.target.value) { setCutoff(e.target.value); setPage(1); } }} /></label>
    </div>
    <div className="rv-kpis">
      <Link to="/portfolio" className="rv-kpi"><div><span>Total portfolio exposure</span><Icon name="portfolio" size={18} /></div><strong>{money(total)}<small> Cr</small></strong><p>{summary.borrowers} borrowers <span>Borrower exposure basis</span></p></Link>
      <Link to="/" className="rv-kpi" onClick={() => { resetPage(setTab, "attention"); setPriority("all"); }}><div><span>Credit exceptions</span><Icon name="pulse" size={18} /></div><strong>{summary.attention_count}<small> borrowers</small></strong><p><b className="rv-red">{summary.urgent} urgent</b><span>{money(summary.attention_exposure)} Cr flagged exposure</span></p></Link>
      <Link to="/covenants?status=BREACHED" className="rv-kpi"><div><span>Confirmed covenant breaches</span><Icon name="shield" size={18} /></div><strong className={summary.breaches ? "rv-red" : ""}>{summary.breaches}<small> / {summary.covenants}</small></strong><p>Active contractual tests<span>{summary.overdue_tests} overdue tests</span></p></Link>
      <Link to="/data-quality" className="rv-kpi"><div><span>Current indicator coverage</span><Icon name="layers" size={18} /></div><strong>{summary.coverage_pct}<small>%</small></strong><p>{summary.complete_borrowers} complete borrower files<span>{summary.data_exceptions} need evidence</span></p></Link>
    </div>
    {view === "monitoring" && <div className="rv-briefing"><div className="rv-briefing-icon"><Icon name="pulse" size={21} /></div><div><strong>{summary.urgent ? `${summary.urgent} borrowers need an urgent review.` : "Your current review priorities are ready."}</strong><p>Confirmed contract breaches take precedence. Evidence gaps remain separate from the credit assessment.</p></div><Link to="/cases">Open work queue <Icon name="arrow" size={16} /></Link></div>}
    {view === "quality" && <div className="rv-briefing rv-data-briefing"><div className="rv-briefing-icon"><Icon name="info" size={21} /></div><div><strong>Missing evidence is not a low-risk signal.</strong><p>Freshness follows each metric’s reporting frequency. Estimated, conflicting, stale, and invalid readings do not drive current credit signals.</p></div><Link to="/policy">View data policy <Icon name="arrow" size={16} /></Link></div>}
    {view === "cases" && <div className="rv-workflow-strip">{[["OPEN", "Open"], ["IN_REVIEW", "In review"], ["ESCALATED", "Escalated"], ["RESOLVED", "Resolved"]].map(([value, name], i) => <button key={value} className={caseStatus === value ? "selected" : ""} onClick={() => { resetPage(setCaseStatus, caseStatus === value ? "all" : value); setTab("all"); }}><span>{String(i + 1).padStart(2, "0")}</span><div>{name}<strong>{borrowers.filter((b) => b.case?.status === value).length}</strong></div><Icon name="chevron" size={15} /></button>)}</div>}
    <section className="rv-panel">
      {!["quality", "covenants"].includes(view) ? <div className="rv-tabs" role="group" aria-label="Queue views">{tabs.map(([value, name, count]) => <button key={value} aria-pressed={tab === value} className={tab === value ? "active" : ""} onClick={() => { resetPage(setTab, value); setCaseStatus("all"); setPriority("all"); }}>{name}<span>{count}</span></button>)}</div>
        : <div className="rv-panel-title"><div><h2>{view === "quality" ? "Evidence coverage matrix" : "Facility covenant tests"}</h2><p>{view === "quality" ? "Four configured indicators per borrower. Hover for source and observation date." : `${allContracts.length} configured covenants · Headroom recalculated from each recorded test`}</p></div><Badge value="OPEN">{view === "quality" ? "4 indicators" : "Contract terms"}</Badge></div>}
      <div className="rv-toolbar"><label className="rv-search"><Icon name="search" size={16} /><input aria-label="Search monitoring borrowers" placeholder="Search borrowers…" value={search} onChange={(e) => resetPage(setSearch, e.target.value)} /></label>
        <select aria-label="Filter by sector" value={sector} onChange={(e) => resetPage(setSector, e.target.value)}><option value="all">All sectors</option>{data.sectors.map((s) => <option key={s.sector}>{s.sector}</option>)}</select>
        {view === "covenants" ? <select aria-label="Filter covenant status" value={contractStatus} onChange={(e) => setContractStatus(e.target.value)}><option value="all">All test results</option>{["BREACHED", "NEAR_BREACH", "TIGHT", "COMPLIANT", "UNTESTED", "EVIDENCE"].map((s) => <option key={s} value={s}>{s === "EVIDENCE" ? "Evidence exceptions" : title(s)}</option>)}</select>
          : <><select aria-label="Filter review priority" value={priority} onChange={(e) => { resetPage(setPriority, e.target.value); setTab("all"); }}><option value="all">All priorities</option>{[...creditPriorities, "DATA_REVIEW", "ROUTINE"].map((s) => <option key={s} value={s}>{title(s)}</option>)}</select>
            <select aria-label="Sort monitoring queue" value={sort} onChange={(e) => resetPage(setSort, e.target.value)}><option value="priority">Priority first</option><option value="exposure">Largest exposure</option><option value="name">Borrower A–Z</option></select></>}
        <button className="rv-reset" onClick={() => { setSearch(""); setSector("all"); setPriority("all"); setContractStatus("all"); setCaseStatus("all"); setTab("all"); setPage(1); }}>Clear filters</button>
      </div>
      {view === "covenants" ? <CovenantTable rows={contractRows} onReview={setSelected} asOf={asOf} /> : <div className="table-scroll"><table className={`rv-table ${view === "quality" ? "rv-quality-table" : ""}`}>
        <thead><tr><th>Borrower / sector</th><th className="rv-number">Exposure</th>{view === "quality" ? ["DSCR", "Bounce rate", "Receivables", "Debt / EBITDA"].map((m) => <th key={m}>{m}</th>) : <><th>Priority</th><th>Evidence</th><th>Primary driver</th></>}<th>{view === "quality" ? "Assessment" : "Owner / due"}</th><th>Case</th><th><span className="sr-only">Open review</span></th></tr></thead>
        <tbody>{visibleRows.map((b) => <tr key={b.borrower_id}>
          <td><Link className="rv-borrower-name" to={`/borrower/${b.borrower_id}?as_of=${asOf}`}>{b.borrower_name}</Link><small>{b.sector} <span className="rv-record-id">· RV-{b.borrower_id}</span></small></td>
          <td className="rv-number rv-mono">{money(b.exposure)}<small>Cr</small></td>
          {view === "quality" ? b.metrics.map((m) => <td key={m.code} title={`${m.name} · ${m.source || "No source"} · Observed ${m.observed_at || "not received"}`}><Badge value={m.freshness} /><small>{m.value == null ? "No valid value" : `${metricValue(m.value, m.unit)} · ${m.age_days}d old`}</small></td>)
            : <><td><Badge value={b.priority} /></td><td><EvidenceDots metrics={b.metrics} /><small>{b.data_issues.length ? "Needs attention" : "Current evidence"}</small></td><td className="rv-driver"><span>{b.drivers[0]}</span><small>{b.deteriorating_metrics}/4 indicators deteriorating</small></td></>}
          <td>{view === "quality" ? <Badge value={b.priority} /> : <><span className={b.case?.owner ? "" : "rv-muted"}>{b.case?.owner || "Unassigned"}</span><small className={b.case_overdue ? "rv-red" : ""}>{b.case?.due_date ? `${b.case_overdue ? "Overdue · " : "Due "}${dateText(b.case.due_date)}` : `Suggested ${dateText(b.suggested_due_date)}`}</small></>}</td>
          <td><Badge value={b.case?.status || "UNASSIGNED"} /></td>
          <td><button className="rv-row-action" aria-label={`Open review for ${b.borrower_name}`} onClick={() => setSelected(b.borrower_id)}><Icon name="arrow" size={17} /></button></td>
        </tr>)}</tbody></table>
        {!rows.length && <div className="rv-empty"><Icon name="search" size={27} /><h3>No borrowers in this view</h3><p>Change a filter or choose another queue to continue.</p></div>}
      </div>}
      {view !== "covenants" && <div className="rv-table-footer"><span>{rows.length ? `${(page - 1) * 10 + 1}–${Math.min(page * 10, rows.length)} of ${rows.length}` : "0"} borrowers <span className="rv-footnote-sep">·</span> {money(rows.reduce((sum, b) => sum + b.exposure, 0))} Cr in this view</span><div><button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} aria-label="Previous page">‹</button><span>{page} / {pages}</span><button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} aria-label="Next page">›</button></div></div>}
    </section>
    {view === "monitoring" && <div className="rv-bottom-grid"><section className="rv-panel"><div className="rv-panel-title"><div><p className="eyebrow">EXPOSURE CONTEXT</p><h2>Sector concentration</h2></div><Link className="rv-inline-link" to="/portfolio">Portfolio analysis <Icon name="arrow" size={14} /></Link></div><div className="rv-sector-bars">{data.sectors.slice(0, 5).map((s) => <button key={s.sector} onClick={() => { resetPage(setSector, s.sector); setTab("all"); }}><span>{s.sector}</span><div><i style={{ width: `${s.share_pct / 25 * 100}%` }} className={s.over_limit ? "rv-limit-breach" : ""} /></div><strong>{s.share_pct}%</strong><small>{money(s.exposure)} Cr</small></button>)}</div><p className="rv-panel-footnote">Top five sectors · 25% demonstration limit · Based on borrower exposure</p></section>
      <section className="rv-panel"><div className="rv-panel-title"><div><p className="eyebrow">FOLLOW THROUGH</p><h2>Review operations</h2></div><Icon name="report" size={20} /></div><div className="rv-operations-stats"><Link to="/cases"><strong>{summary.open_cases}</strong><span>Active cases</span></Link><Link to="/cases"><strong className={summary.overdue_cases ? "rv-red" : ""}>{summary.overdue_cases}</strong><span>Overdue reviews</span></Link><Link to="/data-quality"><strong>{summary.data_exceptions}</strong><span>Evidence exceptions</span></Link></div><div className="rv-next-action"><Icon name="clock" size={19} /><p><strong>From signal to a recorded decision</strong>Open a review to assign an owner, set the next action, and save the supporting rationale.</p></div><Link className="rv-panel-link" to="/cases">Manage analyst cases <Icon name="arrow" size={15} /></Link></section></div>}
    {view === "cases" && <ActivityPanel key={borrowers.map((b) => b.case?.version || 0).join("-")} borrowers={borrowers} />}
    {view === "covenants" && <div className="rv-explainer-grid"><div><Icon name="shield" size={18} /><h3>Contract terms first</h3><p>Minimum limits use actual − threshold. Maximum limits use threshold − actual. Negative headroom is a breach; equality is at the limit.</p></div><div><Icon name="clock" size={18} /><h3>Test result and evidence age</h3><p>A stale compliant test does not establish current compliance. A last confirmed breach remains flagged until later valid evidence resolves it.</p></div><div><Icon name="layers" size={18} /><h3>Scope stays explicit</h3><p>Waived, expired, and inactive-facility covenants do not generate active credit triggers. This sample contains a partial facility register.</p></div></div>}
    <p className="rv-page-note">{data.mode === "synthetic" ? "Synthetic demonstration portfolio. " : ""}Observation cutoffs apply to financial evidence and tests; contract terms and analyst cases use their current stored versions.</p>
    {selected !== null && <CaseDialog borrowerId={selected} asOf={asOf} onClose={() => setSelected(null)} onSaved={refresh} />}
  </div>;
}

function ActivityPanel({ borrowers }) {
  const { data, error } = useResource("/monitoring/activity");
  return <section className="rv-panel rv-activity-panel"><div className="rv-panel-title"><div><p className="eyebrow">WORKSPACE JOURNAL</p><h2>Recent decisions</h2></div><span className="rv-muted">Latest 8 entries</span></div><div className="rv-activity-content">{error ? <p role="alert">{error}</p> : !data ? <p>Loading decision history…</p> : !data.length ? <div className="rv-empty"><Icon name="report" size={25} /><h3>Your review history starts here</h3><p>Open a borrower above and save a decision to create a workspace entry.</p></div> : data.slice(0, 8).map((event) => <div key={event.id}><Link className="rv-borrower-name" to={`/borrower/${event.borrower_id}`}>{borrowers.find((b) => b.borrower_id === event.borrower_id)?.borrower_name || `RV-${event.borrower_id}`}</Link><CaseHistory events={[event]} /></div>)}</div></section>;
}
