import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import Icon from "../components/Icon";
import { getJson, money, label } from "../utils/api";
export default function BorrowersPage() {
  const [params, setParams] = useSearchParams();
  const search = params.get("q") || "";
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [sector, setSector] = useState("ALL");
  const [priority, setPriority] = useState("ALL");
  useEffect(() => {
    let active = true;
    Promise.all([getJson("/borrowers"), getJson("/intervention_watchlist")])
      .then(([borrowers, interventions]) => {
        if (active)
          setData({
            borrowers,
            map: Object.fromEntries(
              interventions.map((a) => [a.borrower_id, a]),
            ),
          });
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  const sectors = useMemo(
    () =>
      [...new Set(data?.borrowers.map((b) => b.sector).filter(Boolean))].sort(),
    [data],
  );
  const rows =
    data?.borrowers.filter(
      (b) =>
        b.borrower_name.toLowerCase().includes(search.trim().toLowerCase()) &&
        (sector === "ALL" || sector === b.sector) &&
        (priority === "ALL" ||
          priority === data.map[b.id]?.intervention_priority),
    ) || [];
  return (
    <div className="page">
      <Header
        title="Borrower directory"
        subtitle="Every borrower, their financial exposure and the evidence available for review."
      />
      <section className="section-card">
        <div className="section-toolbar">
          <input
            aria-label="Search borrower directory"
            className="search-control"
            placeholder="Search borrower…"
            value={search}
            onChange={(e) =>
              setParams(e.target.value ? { q: e.target.value } : {}, {
                replace: true,
              })
            }
          />
          <select
            aria-label="Filter by sector"
            className="filter-control"
            value={sector}
            onChange={(e) => setSector(e.target.value)}
          >
            <option value="ALL">All sectors</option>
            {sectors.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            aria-label="Filter by priority"
            className="filter-control"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="ALL">All priorities</option>
            {["URGENT", "HIGH", "MEDIUM", "LOW", "INSUFFICIENT_DATA"].map(
              (p) => (
                <option value={p} key={p}>
                  {label(p)}
                </option>
              ),
            )}
          </select>
          <span className="muted-text">
            {data ? `${rows.length} borrowers` : "Loading…"}
          </span>
        </div>
        {error ? (
          <div className="empty-state" role="alert">
            <p>{error}</p>
            <button
              className="secondary-button"
              onClick={() => {
                setError("");
                setAttempt((a) => a + 1);
              }}
            >
              Try again
            </button>
          </div>
        ) : !data ? (
          <div className="empty-state" role="status">
            Loading borrower intelligence…
          </div>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Borrower</th>
                  <th>Sector</th>
                  <th>Exposure</th>
                  <th>Intervention priority</th>
                  <th>History coverage</th>
                  <th>
                    <span className="sr-only">Review</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((b) => {
                  const a = data.map[b.id];
                  return (
                    <tr key={b.id}>
                      <td>
                        <Link
                          className="borrower-link"
                          to={`/borrower/${b.id}`}
                        >
                          {b.borrower_name}
                        </Link>
                      </td>
                      <td>{b.sector || "—"}</td>
                      <td>{money(b.loan_amount)} Cr</td>
                      <td>
                        <span
                          className={`priority-badge ${a?.intervention_priority?.toLowerCase() || "insufficient_data"}`}
                        >
                          {label(a?.intervention_priority)}
                        </span>
                      </td>
                      <td>{a?.metrics_analyzed || 0} / 4 metrics</td>
                      <td>
                        <Link
                          className="row-arrow"
                          to={`/borrower/${b.id}`}
                          aria-label={`Open ${b.borrower_name}`}
                        >
                          <Icon name="arrow" size={16} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {!rows.length && (
              <div className="empty-state">
                <h3>No matching borrowers</h3>
                <p>Try a different name or clear your filters.</p>
                <button
                  className="secondary-button"
                  onClick={() => {
                    setParams({});
                    setSector("ALL");
                    setPriority("ALL");
                  }}
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
