import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Icon from "./Icon";
import { label } from "../utils/api";
import { reviewKey, loadReview } from "../utils/reviews";
import { exportBorrowerBrief } from "../utils/brief";
const metrics = [
  ["DSCR", "Debt-service coverage", "×"],
  ["BOUNCE_RATE", "Payment bounce rate", "%"],
  ["RECEIVABLE_DAYS", "Receivable days", " days"],
  ["DEBT_EBITDA", "Debt / EBITDA", "×"],
];
function ReviewPanel({ storageKey }) {
  const [saved, setSaved] = useState(() => loadReview(storageKey));
  const [status, setStatus] = useState(saved.status);
  const [note, setNote] = useState(saved.note);
  const [message, setMessage] = useState("");
  const dirty = note !== saved.note || status !== saved.status;
  function save(event) {
    event.preventDefault();
    const next = {
      status,
      note: note.trim(),
      savedAt: new Date().toISOString(),
    };
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
      setSaved(next);
      setNote(next.note);
      setMessage("Review saved in this browser.");
    } catch {
      setMessage(
        "This browser could not save the review. Copy your note before leaving.",
      );
    }
  }
  return (
    <form className="panel analyst-panel" onSubmit={save}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FROM INSIGHT TO ACTION</p>
          <h2>Analyst review</h2>
        </div>
        <Icon name="report" size={20} />
      </div>
      <label htmlFor="review-status">Review status</label>
      <select
        id="review-status"
        value={status}
        onChange={(event) => {
          setStatus(event.target.value);
          setMessage("");
        }}
      >
        {["Not reviewed", "In review", "Escalated", "Reviewed"].map((s) => (
          <option key={s}>{s}</option>
        ))}
      </select>
      <label htmlFor="review-note">Investigation note</label>
      <textarea
        id="review-note"
        placeholder="Record what needs to be investigated and your next step…"
        value={note}
        maxLength={5000}
        onChange={(event) => {
          setNote(event.target.value);
          setMessage("");
        }}
        rows={4}
      />
      <button type="submit" className="primary-button" disabled={!dirty}>
        <Icon name="check" size={16} />
        Save review
      </button>
      <p className="review-feedback" role="status">
        {message ||
          (saved.savedAt
            ? `Last saved ${new Date(saved.savedAt).toLocaleString()}`
            : "No review recorded yet.")}
        {dirty && !message ? " · Unsaved changes" : ""}
      </p>
      <small className="local-note">
        <Icon name="info" size={13} />
        Stored in this browser. No notification is sent.
      </small>
    </form>
  );
}
export default function BorrowerOverview({
  borrower,
  deterioration,
  history,
  covenants,
}) {
  const { health } = useOutletContext();
  const storageKey = reviewKey(borrower.borrower_id, health?.data_mode);
  const analyzed = deterioration.metrics_analyzed > 0;
  const workspaceReady = health?.status === "ready";
  return (
    <div className="borrower-overview">
      <div className="evidence-heading">
        <div>
          <h2>Follow the evidence.</h2>
          <p>
            {analyzed
              ? `${deterioration.deteriorating_signals} of ${deterioration.metrics_analyzed} signals worsening · ${deterioration.convergence_percentage}% convergence`
              : "Historical observations are needed before a trajectory can be assessed."}
          </p>
        </div>
        <button
          className="secondary-button"
          disabled={!workspaceReady}
          onClick={() =>
            exportBorrowerBrief({
              borrower,
              deterioration,
              history,
              covenants,
              review: loadReview(storageKey),
              mode: health?.data_mode,
            })
          }
        >
          <Icon name="download" size={16} />
          Export brief
        </button>
      </div>
      <div className="signal-grid">
        {metrics.map(([code, name, unit]) => {
          const observations = history?.metrics?.[code] || [];
          const metric = deterioration.metric_results?.find(
            (m) => m.metric_code === code,
          );
          const bad = metric?.direction === "DETERIORATING";
          const color = bad ? "#d55d65" : "#168672";
          const first = observations[0],
            last = observations.at(-1);
          return (
            <section className="signal-card" key={code}>
              <div className="signal-card-top">
                <span>{name}</span>
                <span
                  className={`signal-condition ${metric?.condition?.toLowerCase() || ""}`}
                >
                  {metric?.condition ? label(metric.condition) : "No history"}
                </span>
              </div>
              <strong className="signal-value">
                {last ? last.value : "—"}
                <small>{last ? unit : ""}</small>
              </strong>
              <div
                className="signal-sparkline"
                role="img"
                aria-label={`${name}: ${observations.map((o) => o.value).join(" to ") || "no data"}`}
              >
                {observations.length > 1 ? (
                  <ResponsiveContainer width="100%" height={58}>
                    <LineChart
                      data={observations}
                      margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
                    >
                      <XAxis dataKey="date" hide />
                      <YAxis domain={["dataMin", "dataMax"]} hide />
                      <Tooltip
                        contentStyle={{ fontSize: 12, borderRadius: 8 }}
                        formatter={(value) => [`${value}${unit}`, name]}
                      />
                      <Line
                        type="linear"
                        dataKey="value"
                        stroke={color}
                        strokeWidth={2.4}
                        dot={{ r: 3, fill: "#fff", strokeWidth: 2 }}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <span className="muted-text">Insufficient history</span>
                )}
              </div>
              <div className="signal-period">
                <span>{first?.date || "No observations"}</span>
                <span>{last?.date || ""}</span>
              </div>
              <p className={bad ? "text-red" : ""}>
                {metric?.direction ? label(metric.direction) : "Not assessed"}
                {metric?.persistence > 0
                  ? ` · ${metric.persistence} consecutive changes`
                  : ""}
              </p>
            </section>
          );
        })}
      </div>
      <div className="evidence-grid">
        <section className="panel explanation-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">EXPLAINABLE ASSESSMENT</p>
              <h2>Why this borrower needs attention</h2>
            </div>
            <Icon name="pulse" size={20} />
          </div>
          {analyzed ? (
            <>
              <div className="explanation-points">
                {(deterioration.explanations || [])
                  .slice(0, 4)
                  .map((reason, i) => (
                    <div key={reason}>
                      <span>{String(i + 1).padStart(2, "0")}</span>
                      <p>{reason}</p>
                    </div>
                  ))}
              </div>
              <div className="next-steps">
                <h3>Recommended investigation</h3>
                {(deterioration.recommended_investigations || [])
                  .slice(0, 3)
                  .map((reason) => (
                    <p key={reason}>
                      <Icon name="arrow" size={15} />
                      {reason}
                    </p>
                  ))}
              </div>
            </>
          ) : (
            <div className="insufficient-state">
              <h3>Insufficient historical data</h3>
              <p>
                A financial snapshot alone cannot establish deterioration.
                Collect at least two valid observations per metric before
                assigning a trajectory priority.
              </p>
            </div>
          )}
        </section>
        {workspaceReady ? (
          <ReviewPanel key={storageKey} storageKey={storageKey} />
        ) : (
          <section className="panel analyst-panel" role="status">
            {health?.status === "offline"
              ? "Workspace connection unavailable. Refresh to load saved reviews."
              : "Loading workspace settings…"}
          </section>
        )}
      </div>
      <section className="panel snapshot-panel">
        <div className="panel-heading">
          <div>
            <h2>Financial snapshot</h2>
            <p>
              Current stored values, separate from historical trajectory
              analysis.
            </p>
          </div>
        </div>
        <div className="snapshot-grid">
          {[
            ["Days past due", borrower.dpd],
            ["Snapshot DSCR", borrower.dscr],
            [
              "Revenue decline",
              borrower.revenue_decline == null
                ? "—"
                : borrower.revenue_decline + "%",
            ],
            ["Cash flow", borrower.cash_flow],
            [
              "Restructured",
              borrower.restructured == null
                ? "—"
                : borrower.restructured === true || borrower.restructured === 1
                  ? "Yes"
                  : "No",
            ],
            ["Static risk score", borrower.score],
          ].map(([name, value]) => (
            <div key={name}>
              <span>{name}</span>
              <strong>{value ?? "—"}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
