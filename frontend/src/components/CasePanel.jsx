import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { getJson } from "../utils/api";
import { useResource, dateText, exportMonitoringBrief, title } from "../utils/monitoring";
import { Badge, CaseHistory, LoadState } from "./MonitoringUI";
import Icon from "./Icon";
import { loadReview, reviewKey } from "../utils/reviews";

export function CaseEditor({ borrower, onSaved }) {
  const saved = borrower.case;
  const [status, setStatus] = useState(saved?.status || "OPEN");
  const [owner, setOwner] = useState(saved?.owner || "");
  const [actor, setActor] = useState("William Fernandes");
  const [due, setDue] = useState(saved?.due_date || borrower.suggested_due_date);
  const [action, setAction] = useState(saved?.next_action || borrower.next_action);
  const legacyNote = !saved ? loadReview(reviewKey(borrower.borrower_id, borrower.mode)).note : "";
  const [note, setNote] = useState(legacyNote || "");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  async function save(event) {
    event.preventDefault();
    setError(""); setSaving(true);
    try {
      const result = await getJson(`/monitoring/borrowers/${borrower.borrower_id}/case?as_of=${borrower.as_of}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expected_version: saved?.version || 0, status, owner, actor, due_date: due || null, next_action: action, note }),
      });
      onSaved(result);
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }
  return <form className="rv-case-form" onSubmit={save}>
    {legacyNote && <p className="rv-callout">Your previous browser note is included below. Save this decision to add it to the workspace journal.</p>}
    <div className="rv-form-row"><label>Case status<select value={status} onChange={(e) => setStatus(e.target.value)}>{["OPEN", "IN_REVIEW", "ESCALATED", "RESOLVED"].map((s) => <option key={s} value={s}>{title(s)}</option>)}</select></label>
      <label>Review owner<input placeholder="Assign an analyst" value={owner} maxLength={80} required={status !== "OPEN"} onChange={(e) => setOwner(e.target.value)} /></label></div>
    <div className="rv-form-row"><label>Review due date<input type="date" value={due || ""} required={["IN_REVIEW", "ESCALATED"].includes(status)} onChange={(e) => setDue(e.target.value)} /></label>
      <label>Recorded by<input value={actor} minLength={2} maxLength={80} required onChange={(e) => setActor(e.target.value)} /></label></div>
    <label>Next action<textarea rows={2} placeholder="What needs to happen next?" value={action} minLength={["IN_REVIEW", "ESCALATED"].includes(status) ? 5 : undefined} maxLength={500} required={["IN_REVIEW", "ESCALATED"].includes(status)} onChange={(e) => setAction(e.target.value)} /></label>
    <label>{status === "RESOLVED" ? "Resolution rationale" : "Decision note"}<textarea rows={4} minLength={10} maxLength={5000} required placeholder={status === "RESOLVED" ? "Explain the review outcome and remaining monitoring requirements…" : "Record your assessment, evidence requested, or reason for escalation…"} value={note} onChange={(e) => setNote(e.target.value)} /></label>
    {status === "RESOLVED" && <p className="rv-callout">Resolving the case records your decision. Active credit and covenant signals remain visible.</p>}
    {error && <p className="rv-form-error" role="alert">{error}</p>}
    <button className="primary-button" disabled={saving}><Icon name="check" size={16} />{saving ? "Saving decision…" : "Save decision"}</button>
    <small className="rv-storage-note">Saved to the workspace database with a dated assessment. “Recorded by” is a user-entered name.</small>
  </form>;
}

export default function CasePanel({ borrowerId, asOf, onSaved }) {
  const path = `/monitoring/borrowers/${borrowerId}${asOf ? `?as_of=${asOf}` : ""}`;
  const { data, error, refresh, updateData } = useResource(path);
  const [message, setMessage] = useState("");
  if (!data) return <LoadState error={error} retry={refresh} />;
  return <div className="rv-case-content">
    <div className="rv-case-heading"><div><p className="eyebrow">CREDIT REVIEW · RV-{borrowerId}</p><h2>{data.borrower_name}</h2><p>{data.sector} · ₹{data.exposure} Cr exposure</p></div><Badge value={data.priority} /></div>
    <div className="rv-case-evidence"><strong>Why this review matters</strong>{data.drivers.map((driver) => <p key={driver}>{driver}</p>)}<small>{data.fresh_metrics}/4 current indicators · Observation cutoff {dateText(data.as_of)}</small></div>
    {data.data_issues.length > 0 && <details className="rv-case-quality"><summary>{data.data_issues.length} evidence exceptions to resolve</summary><ul>{data.data_issues.map((issue) => <li key={issue}>{issue}</li>)}</ul></details>}
    <div className="rv-case-actions"><Link className="rv-inline-link" to={`/borrower/${borrowerId}?as_of=${data.as_of}`}>Open borrower analysis <Icon name="arrow" size={14} /></Link><button className="secondary-button" onClick={() => exportMonitoringBrief(data)}><Icon name="download" size={14} />Export review</button></div>
    <div role="status" className="rv-save-feedback">{message}</div>
    <CaseEditor key={`${data.borrower_id}-${data.case?.version || 0}`} borrower={data} onSaved={(result) => { updateData((current) => ({ ...current, ...result })); setMessage("Decision saved. The case and its assessment are recorded."); onSaved?.(); }} />
    <div className="rv-case-history"><h3>Decision history <span>{data.events.length}</span></h3><CaseHistory events={data.events} /></div>
  </div>;
}

export function CaseDialog({ borrowerId, asOf, onClose, onSaved }) {
  const dialog = useRef(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  return <dialog className="rv-case-dialog" ref={dialog} aria-label="Borrower case review" onCancel={(event) => { event.preventDefault(); onClose(); }}>
    <div className="rv-drawer-top"><span><Icon name="report" size={16} /> Analyst workspace</span><button className="icon-button" aria-label="Close case review" onClick={onClose}>✕</button></div>
    <CasePanel borrowerId={borrowerId} asOf={asOf} onSaved={onSaved} />
  </dialog>;
}
