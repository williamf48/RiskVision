import { downloadFile, money, label } from "./api";
const escape = (value) =>
  String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
export function exportBorrowerBrief({
  borrower,
  deterioration,
  covenants,
  history,
  review,
  mode,
}) {
  const e = escape;
  const list = (items) =>
    (items || []).map((item) => `<li>${e(item)}</li>`).join("");
  const rows = (deterioration.metric_results || [])
    .map(
      (m) =>
        `<tr><td>${e(label(m.metric_code))}</td><td>${e(m.current_value)}</td><td>${e(label(m.condition))}</td><td>${e(label(m.direction))}</td><td>${e(history?.metrics?.[m.metric_code]?.at(-1)?.date)}</td></tr>`,
    )
    .join("");
  const content = `<!doctype html><html lang="en"><meta charset="utf-8"><title>RiskVision — ${e(borrower.borrower_name)}</title><style>body{font:15px/1.65 system-ui,sans-serif;color:#17273b;max-width:850px;margin:48px auto;padding:0 24px}header{border-bottom:3px solid #157f72;padding-bottom:18px}h1{font-size:28px;margin:10px 0}h2{font-size:18px;margin-top:28px}small{color:#5b697d}table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:10px;text-align:left;border-bottom:1px solid #dfe5eb}th{background:#f4f6f8}pre{white-space:pre-wrap;font:inherit;background:#f4f6f8;padding:18px}.meta{display:flex;gap:24px;flex-wrap:wrap}footer{margin-top:36px;border-top:1px solid #dfe5eb;padding-top:14px;font-size:12px}@media print{body{margin:0}h2,table{break-inside:avoid}}</style><header><small>RISKVISION · ANALYST BRIEF · ${mode === "synthetic" ? "SYNTHETIC SAMPLE PORTFOLIO" : "CONNECTED WORKSPACE"}</small><h1>${e(borrower.borrower_name)}</h1><div class="meta"><span>${e(borrower.sector)}</span><span>${e(money(borrower.loan_amount))} Cr exposure</span><strong>${e(label(deterioration.intervention_priority))} priority</strong></div></header><p><small>Exported ${e(new Date().toLocaleString())}. Metrics retain their own observation dates.</small></p><h2>Assessment</h2><p>${e(deterioration.deteriorating_signals)} of ${e(deterioration.metrics_analyzed)} analyzed indicators are deteriorating. Signal convergence: ${e(deterioration.convergence_percentage)}%. ${e(covenants?.breached_covenants || 0)} breached covenant(s).</p><h2>Evidence</h2><table><thead><tr><th>Metric</th><th>Latest value</th><th>Condition</th><th>Direction</th><th>Observed</th></tr></thead><tbody>${rows || '<tr><td colspan="5">Insufficient historical data.</td></tr>'}</tbody></table><h2>Why this priority</h2><ul>${list(deterioration.explanations)}</ul><h2>Recommended investigation</h2><ol>${list(deterioration.recommended_investigations)}</ol><h2>Saved analyst review</h2><p>Status: ${e(review.status)}${review.savedAt ? " · Saved " + e(new Date(review.savedAt).toLocaleString()) : ""}</p><pre>${e(review.note || "No saved analyst note.")}</pre><footer>Transparent deterministic analytical rules; not a probability-of-default forecast. Analyst notes are stored in this browser, without a shared audit trail. ${mode === "synthetic" ? "All borrower data in this export is synthetic and intended for demonstration." : "Analyst review is required before action."}</footer></html>`;
  downloadFile(
    `riskvision-${borrower.borrower_name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-brief.html`,
    content,
    "text/html;charset=utf-8",
  );
}
