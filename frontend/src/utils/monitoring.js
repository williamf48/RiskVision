import { useEffect, useState } from "react";
import { downloadFile, getJson, label } from "./api";

export function useResource(path) {
  const [resource, setResource] = useState({ path: null, data: null, error: "" });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true;
    getJson(path).then((data) => { if (active) setResource({ path, data, error: "" }); })
      .catch((error) => { if (active) setResource({ path, data: null, error: error.message }); });
    return () => { active = false; };
  }, [path, revision]);
  return { data: resource.path === path ? resource.data : null,
    error: resource.path === path ? resource.error : "", refresh: () => setRevision((v) => v + 1),
    updateData: (transform) => setResource((current) => current.path === path ? { ...current, data: transform(current.data) } : current) };
}
export const names = { DATA_REVIEW: "Data review", NOT_ASSESSED: "Not assessed", ROUTINE: "Routine",
  IN_REVIEW: "In review", OPEN: "Open", RESOLVED: "Resolved", ESCALATED: "Escalated",
  UNASSIGNED: "Not started", VALID: "Current", MISSING: "Missing", COMPLETE: "Complete",
  NEAR_BREACH: "Near limit", COMPLIANT: "Compliant", UNTESTED: "Untested" };
export const title = (value) => names[value] || label(value);
export const dateText = (value) => value ? new Date(`${value.slice(0, 10)}T12:00:00`).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—";
export const metricValue = (value, unit = "") => value == null ? "—" : `${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })}${unit === "days" ? " d" : unit}`;
export function exportQueue(rows, asOf) {
  const csv = (value) => {
    const raw = String(value ?? "");
    const safe = /^[=+@\-\t\r\n]/.test(raw) ? `'${raw}` : raw;
    return `"${safe.replaceAll('"', '""')}"`;
  };
  const data = [["Observation cutoff", "Borrower", "Sector", "Exposure INR Cr", "Review priority", "Current metrics / 4", "Driver", "Case status", "Owner", "Case due date", "Data exceptions"],
    ...rows.map((b) => [asOf, b.borrower_name, b.sector, b.exposure, title(b.priority), b.fresh_metrics,
      b.drivers.join("; "), title(b.case?.status || "UNASSIGNED"), b.case?.owner || "Unassigned",
      b.case?.due_date || "", b.data_issues.join("; ")])];
  downloadFile(`riskvision-monitoring-${asOf}.csv`, "\ufeff" + data.map((row) => row.map(csv).join(",")).join("\r\n"), "text/csv;charset=utf-8");
}
export function exportMonitoringBrief(b) {
  const e = (value) => String(value ?? "—").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
  const tr = (cells) => `<tr>${cells.map((c) => `<td>${e(c)}</td>`).join("")}</tr>`;
  const note = b.case;
  const content = `<!doctype html><html lang="en"><meta charset="utf-8"><title>RiskVision review — ${e(b.borrower_name)}</title><style>body{font:14px/1.7 system-ui,sans-serif;color:#203447;max-width:920px;margin:40px auto;padding:24px}header{border-bottom:3px solid #147d70;padding-bottom:16px}h1{font-size:30px}h2{font-size:18px;margin-top:30px}small{color:#65768b}table{width:100%;border-collapse:collapse;font-size:12px}td,th{border-bottom:1px solid #dfe5eb;padding:9px;text-align:left}th{background:#f1f5f8}pre{white-space:pre-wrap;font:inherit;background:#f1f5f8;padding:16px}footer{margin-top:30px;font-size:11px;color:#5e7083}@media print{body{margin:0;padding:0}h2{break-after:avoid}tr{break-inside:avoid}}</style><header><small>RISKVISION · CREDIT REVIEW · ${b.mode === "synthetic" ? "SYNTHETIC SAMPLE PORTFOLIO" : "CONNECTED WORKSPACE"}</small><h1>${e(b.borrower_name)}</h1><p>${e(b.sector)} · ₹${e(b.exposure)} Cr · ${e(title(b.priority))} priority</p><small>Observation cutoff ${e(b.as_of)} · Policy ${e(b.policy_version)} · Exported ${e(new Date().toISOString())}</small></header><h2>Review rationale</h2><ul>${b.drivers.map((d) => `<li>${e(d)}</li>`).join("")}</ul><h2>Financial evidence</h2><table><thead><tr><th>Indicator</th><th>Value</th><th>Evidence</th><th>Trend</th><th>Observed</th><th>Source</th></tr></thead><tbody>${b.metrics.map((m) => tr([m.name, metricValue(m.value, m.unit), title(m.freshness), title(m.direction), m.observed_at, m.source])).join("")}</tbody></table><h2>Covenant register</h2><table><thead><tr><th>Facility</th><th>Covenant</th><th>Actual</th><th>Threshold</th><th>Headroom</th><th>Test / evidence</th></tr></thead><tbody>${b.covenants.map((c) => tr([c.facility_code, c.covenant_name, c.actual, `${c.threshold_direction} ${c.threshold_value}`, c.headroom_pct == null ? "—" : c.headroom_pct.toFixed(2) + "%", `${title(c.result)} / ${title(c.freshness)} / ${c.test_date || "untested"}`])).join("") || tr(["No covenants configured"] )}</tbody></table><h2>Evidence exceptions</h2><ul>${b.data_issues.map((d) => `<li>${e(d)}</li>`).join("") || "<li>No evidence exceptions under this policy.</li>"}</ul><h2>Saved analyst case</h2><p>${e(title(note?.status || "UNASSIGNED"))} · Owner: ${e(note?.owner || "Unassigned")} · Due: ${e(note?.due_date)} · Version ${e(note?.version || 0)}</p><p>Next action: ${e(note?.next_action || b.next_action)}</p><pre>${e(note?.note || "No analyst decision recorded.")}</pre><h2>Decision history</h2>${(b.events || []).map((v) => `<p><strong>v${e(v.version)} · ${e(title(v.after.status))}</strong> · ${e(v.actor)} · ${e(v.recorded_at)}<br>${e(v.after.note)}</p>`).join("") || "<p>No saved activity.</p>"}<footer>Deterministic demonstration policy, not a default forecast, investment recommendation, or regulatory classification. Observation cutoffs do not reconstruct historical contract versions or publication times. Case closure does not clear a credit signal. The case journal persists in the workspace database; actor names are user-entered and not authenticated.</footer></html>`;
  downloadFile(`riskvision-${b.borrower_name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-credit-review.html`, content, "text/html;charset=utf-8");
}
