import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


const METRIC_LABELS = {
  DSCR: "DSCR",
  BOUNCE_RATE: "Bounce Rate",
  RECEIVABLE_DAYS: "Receivable Days",
  DEBT_EBITDA: "Debt / EBITDA",
};


const METRIC_ORDER = [
  "DSCR",
  "BOUNCE_RATE",
  "RECEIVABLE_DAYS",
  "DEBT_EBITDA",
];


function formatBoolean(value) {

  if (value === true) {
    return "Yes";
  }

  if (value === false) {
    return "No";
  }

  return value ?? "—";
}


function HistoryTooltip({
  active,
  payload,
  label,
}) {

  if (
    !active ||
    !payload ||
    payload.length === 0
  ) {
    return null;
  }


  const observation =
    payload[0].payload;


  return (
    <div className="history-tooltip">

      <strong>
        {label}
      </strong>

      <p>
        Value: {observation.value}
      </p>

      <p>
        Frequency:{" "}
        {
          observation.reporting_frequency
          || "—"
        }
      </p>

      <p>
        Source:{" "}
        {
          observation.source
          || "—"
        }
      </p>

      <p>
        Data quality:{" "}
        {
          observation.data_quality
          || "—"
        }
      </p>

    </div>
  );
}


function BorrowerPage() {

  const { id } = useParams();


  const [borrower, setBorrower] =
    useState(null);

  const [deterioration, setDeterioration] =
    useState(null);

  const [history, setHistory] =
    useState(null);

  const [activeTab, setActiveTab] =
    useState("overview");

  const [selectedMetric, setSelectedMetric] =
    useState("DSCR");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  // =====================================================
  // LOAD BORROWER DATA
  // =====================================================

  useEffect(() => {

    setLoading(true);
    setError(null);


    Promise.all([
      fetch(
        `http://127.0.0.1:8000/borrowers/${id}`
      ),
      fetch(
        `http://127.0.0.1:8000/borrowers/${id}/deterioration`
      ),
      fetch(
        `http://127.0.0.1:8000/borrowers/${id}/history`
      ),
    ])

      .then(async (
        [
          borrowerResponse,
          deteriorationResponse,
          historyResponse,
        ]
      ) => {

        if (!borrowerResponse.ok) {
          throw new Error(
            "Borrower could not be loaded"
          );
        }

        if (!deteriorationResponse.ok) {
          throw new Error(
            "Deterioration intelligence could not be loaded"
          );
        }

        if (!historyResponse.ok) {
          throw new Error(
            "Historical observations could not be loaded"
          );
        }


        return {
          borrower:
            await borrowerResponse.json(),

          deterioration:
            await deteriorationResponse.json(),

          history:
            await historyResponse.json(),
        };
      })

      .then((data) => {

        setBorrower(
          data.borrower
        );

        setDeterioration(
          data.deterioration
        );

        setHistory(
          data.history
        );


        const availableMetrics =
          METRIC_ORDER.filter(
            (metric) =>
              data.history.metrics?.[metric]
                ?.length > 0
          );


        if (availableMetrics.length > 0) {

          setSelectedMetric(
            availableMetrics[0]
          );

        }


        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Borrower page error:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, [id]);


  // =====================================================
  // HISTORY
  // =====================================================

  const availableMetrics = useMemo(() => {

    if (!history) {
      return [];
    }


    return METRIC_ORDER.filter(
      (metric) =>
        history.metrics?.[metric]
          ?.length > 0
    );

  }, [history]);


  const selectedHistory = useMemo(() => {

    if (
      !history ||
      !selectedMetric
    ) {
      return [];
    }


    return (
      history.metrics?.[
        selectedMetric
      ] || []
    );

  }, [
    history,
    selectedMetric,
  ]);


  // =====================================================
  // LOADING / ERROR
  // =====================================================

  if (loading) {

    return (
      <div className="page">

        <div className="borrower-loading">
          Loading borrower intelligence...
        </div>

      </div>
    );
  }


  if (
    error ||
    !borrower ||
    !deterioration
  ) {

    return (
      <div className="page">

        <div className="borrower-error">

          <h2>
            Unable to load borrower
          </h2>

          <p>
            {error}
          </p>

          <Link
            to="/borrowers"
            className="primary-button"
          >
            Back to Borrowers
          </Link>

        </div>

      </div>
    );
  }


  const priority =
    deterioration
      .intervention_priority;


  const hasTrajectory =
    deterioration
      .metrics_analyzed > 0;


  return (
    <div className="page">

      {/* =================================================
          PAGE HEADER
          ================================================= */}

      <div className="borrower-page-header">

        <div>

          <Link
            to="/borrowers"
            className="back-link"
          >
            ← Borrower Directory
          </Link>


          <div className="borrower-title-row">

            <div>

              <h1>
                {
                  borrower
                    .borrower_name
                }
              </h1>

              <p>
                {
                  borrower.sector
                  || "Sector unavailable"
                }
                {" · Borrower ID "}
                {
                  borrower
                    .borrower_id
                }
              </p>

            </div>


            <span
              className={
                `priority-badge large ${
                  priority
                    .toLowerCase()
                }`
              }
            >
              {priority}
            </span>

          </div>

        </div>

      </div>


      {/* =================================================
          QUICK SUMMARY
          ================================================= */}

      <div className="borrower-summary-grid">

        <div className="borrower-summary-card">

          <span>
            Exposure
          </span>

          <strong>
            ₹
            {
              borrower
                .loan_amount
            }
            {" Cr"}
          </strong>

        </div>


        <div className="borrower-summary-card">

          <span>
            Current Risk
          </span>

          <strong>
            {
              borrower
                .classification
            }
          </strong>

        </div>


        <div className="borrower-summary-card">

          <span>
            Intervention Priority
          </span>

          <strong>
            {priority}
          </strong>

        </div>


        <div className="borrower-summary-card">

          <span>
            Historical Coverage
          </span>

          <strong>
            {
              history
                ?.observation_count
              || 0
            }
            {" observations"}
          </strong>

        </div>

      </div>


      {/* =================================================
          TABS
          ================================================= */}

      <div className="borrower-tabs">

        <button
          className={
            activeTab === "overview"
              ? "borrower-tab active"
              : "borrower-tab"
          }
          onClick={() =>
            setActiveTab(
              "overview"
            )
          }
        >
          Overview
        </button>


        <button
          className={
            activeTab === "deterioration"
              ? "borrower-tab active"
              : "borrower-tab"
          }
          onClick={() =>
            setActiveTab(
              "deterioration"
            )
          }
        >
          Deterioration
        </button>


        <button
          className={
            activeTab === "history"
              ? "borrower-tab active"
              : "borrower-tab"
          }
          onClick={() =>
            setActiveTab(
              "history"
            )
          }
        >
          History
        </button>


        <button
          className={
            activeTab === "alerts"
              ? "borrower-tab active"
              : "borrower-tab"
          }
          onClick={() =>
            setActiveTab(
              "alerts"
            )
          }
        >
          Alerts
          {" ("}
          {
            borrower
              .alerts
              ?.length || 0
          }
          {")"}
        </button>

      </div>


      {/* =================================================
          OVERVIEW TAB
          ================================================= */}

      {activeTab === "overview" && (

        <div className="borrower-tab-content">

          <div className="borrower-content-grid">

            <section className="section-card">

              <div className="section-heading">

                <h2>
                  Borrower Information
                </h2>

                <p>
                  Current facility and borrower profile.
                </p>

              </div>


              <div className="detail-grid">

                <div>
                  <span>Borrower ID</span>
                  <strong>
                    {
                      borrower
                        .borrower_id
                    }
                  </strong>
                </div>

                <div>
                  <span>Sector</span>
                  <strong>
                    {
                      borrower.sector
                      || "—"
                    }
                  </strong>
                </div>

                <div>
                  <span>Exposure</span>
                  <strong>
                    ₹
                    {
                      borrower
                        .loan_amount
                    }
                    {" Cr"}
                  </strong>
                </div>

                <div>
                  <span>Risk Score</span>
                  <strong>
                    {
                      borrower.score
                      ?? "—"
                    }
                  </strong>
                </div>

              </div>

            </section>


            <section className="section-card">

              <div className="section-heading">

                <h2>
                  Financial Snapshot
                </h2>

                <p>
                  Latest borrower-level financial indicators.
                </p>

              </div>


              <div className="detail-grid">

                <div>
                  <span>DPD</span>
                  <strong>
                    {
                      borrower.dpd
                      ?? "—"
                    }
                  </strong>
                </div>

                <div>
                  <span>DSCR</span>
                  <strong>
                    {
                      borrower.dscr
                      ?? "—"
                    }
                  </strong>
                </div>

                <div>
                  <span>Revenue Decline</span>
                  <strong>
                    {
                      borrower
                        .revenue_decline
                      ?? "—"
                    }
                    %
                  </strong>
                </div>

                <div>
                  <span>Cash Flow</span>
                  <strong>
                    {
                      borrower
                        .cash_flow
                      ?? "—"
                    }
                  </strong>
                </div>

                <div>
                  <span>Restructured</span>
                  <strong>
                    {
                      formatBoolean(
                        borrower
                          .restructured
                      )
                    }
                  </strong>
                </div>

              </div>

            </section>

          </div>


          <section className="section-card borrower-intervention-summary">

            <div className="section-heading">

              <h2>
                Intervention Summary
              </h2>

              <p>
                Explainable output from the borrower deterioration engine.
              </p>

            </div>


            {priority ===
            "INSUFFICIENT_DATA" ? (

              <div className="insufficient-state">

                <h3>
                  Insufficient historical data
                </h3>

                <p>
                  RiskVision currently has{" "}
                  {
                    deterioration
                      .metrics_analyzed
                  }
                  {" of "}
                  {
                    deterioration
                      .configured_metrics
                  }
                  {" historical signals available for trajectory analysis."}
                </p>

              </div>

            ) : (

              <div className="intervention-overview-grid">

                <div>

                  <span>
                    Priority Rank
                  </span>

                  <strong>
                    {
                      deterioration
                        .priority_rank
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Deteriorating
                  </span>

                  <strong>
                    {
                      deterioration
                        .deteriorating_signals
                    }
                    /
                    {
                      deterioration
                        .metrics_analyzed
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Persistent
                  </span>

                  <strong>
                    {
                      deterioration
                        .persistent_deterioration_signals
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Accelerating
                  </span>

                  <strong>
                    {
                      deterioration
                        .accelerating_deterioration_signals
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Convergence
                  </span>

                  <strong>
                    {
                      deterioration
                        .convergence_percentage
                    }
                    %
                  </strong>

                </div>

              </div>

            )}

          </section>

        </div>

      )}


      {/* =================================================
          DETERIORATION TAB
          ================================================= */}

      {activeTab === "deterioration" && (

        <div className="borrower-tab-content">

          {!hasTrajectory ? (

            <section className="section-card">

              <div className="insufficient-state">

                <h2>
                  Insufficient historical data
                </h2>

                <p>
                  Multiple historical observations are required before trajectory deterioration can be assessed.
                </p>

              </div>

            </section>

          ) : (

            <>

              <div className="borrower-content-grid">

                <section className="section-card">

                  <div className="section-heading">

                    <h2>
                      Why Flagged?
                    </h2>

                    <p>
                      Primary drivers behind the intervention priority.
                    </p>

                  </div>


                  <ul className="intelligence-list">

                    {
                      deterioration
                        .explanations
                        .map(
                          (
                            explanation,
                            index
                          ) => (

                            <li
                              key={index}
                            >
                              {
                                explanation
                              }
                            </li>

                          )
                        )
                    }

                  </ul>

                </section>


                <section className="section-card">

                  <div className="section-heading">

                    <h2>
                      Recommended Investigation
                    </h2>

                    <p>
                      Analyst review actions suggested by the current signals.
                    </p>

                  </div>


                  <ul className="intelligence-list">

                    {
                      deterioration
                        .recommended_investigations
                        .map(
                          (
                            recommendation,
                            index
                          ) => (

                            <li
                              key={index}
                            >
                              {
                                recommendation
                              }
                            </li>

                          )
                        )
                    }

                  </ul>

                </section>

              </div>


              <section className="section-card">

                <div className="section-heading">

                  <h2>
                    Signal Analysis
                  </h2>

                  <p>
                    Current condition and trajectory characteristics by signal.
                  </p>

                </div>


                <div className="table-scroll">

                  <table className="data-table">

                    <thead>

                      <tr>
                        <th>Signal</th>
                        <th>Current</th>
                        <th>Condition</th>
                        <th>Latest Change</th>
                        <th>Velocity / 30d</th>
                        <th>Direction</th>
                        <th>Acceleration</th>
                        <th>Persistence</th>
                      </tr>

                    </thead>


                    <tbody>

                      {
                        deterioration
                          .metric_results
                          .map(
                            (metric) => (

                              <tr
                                key={
                                  metric
                                    .metric_code
                                }
                              >

                                <td>
                                  {
                                    METRIC_LABELS[
                                      metric
                                        .metric_code
                                    ]
                                    ||
                                    metric
                                      .metric_code
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .current_value
                                    ?? "—"
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .condition
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .percentage_change
                                    !== null
                                      ? `${metric.percentage_change}%`
                                      : "—"
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .risk_velocity_30d
                                    !== null
                                      ? `${metric.risk_velocity_30d}%`
                                      : "—"
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .direction
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .acceleration_direction
                                  }
                                </td>

                                <td>
                                  {
                                    metric
                                      .persistence
                                  }
                                </td>

                              </tr>

                            )
                          )
                      }

                    </tbody>

                  </table>

                </div>

              </section>

            </>

          )}

        </div>

      )}


      {/* =================================================
          HISTORY TAB
          ================================================= */}

      {activeTab === "history" && (

        <div className="borrower-tab-content">

          {
            history
              ?.observation_count === 0
            ? (

              <section className="section-card">

                <div className="insufficient-state">

                  <h2>
                    No historical observations
                  </h2>

                  <p>
                    Historical signal data has not yet been loaded for this borrower.
                  </p>

                </div>

              </section>

            ) : (

              <>

                <section className="section-card">

                  <div className="history-header">

                    <div className="section-heading">

                      <h2>
                        Historical Signal Analysis
                      </h2>

                      <p>
                        Select a signal to inspect its observed trajectory.
                      </p>

                    </div>


                    <div className="history-coverage">

                      {
                        history
                          .observation_count
                      }
                      {" observations · "}
                      {
                        history
                          .metric_count
                      }
                      {" metrics"}

                    </div>

                  </div>


                  <div className="metric-selector">

                    {
                      availableMetrics.map(
                        (metric) => (

                          <button
                            key={metric}
                            className={
                              selectedMetric === metric
                                ? "metric-button active"
                                : "metric-button"
                            }
                            onClick={() =>
                              setSelectedMetric(
                                metric
                              )
                            }
                          >
                            {
                              METRIC_LABELS[
                                metric
                              ]
                            }
                          </button>

                        )
                      )
                    }

                  </div>


                  <div className="history-chart">

                    <ResponsiveContainer
                      width="100%"
                      height={380}
                    >

                      <LineChart
                        data={
                          selectedHistory
                        }
                      >

                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="#24344a"
                        />

                        <XAxis
                          dataKey="date"
                          stroke="#64748b"
                        />

                        <YAxis
                          stroke="#64748b"
                          domain={[
                            "auto",
                            "auto",
                          ]}
                        />

                        <Tooltip
                          content={
                            <HistoryTooltip />
                          }
                        />

                        <Line
                          type="monotone"
                          dataKey="value"
                          stroke="#3b82f6"
                          strokeWidth={3}
                          dot={{
                            r: 5,
                          }}
                          activeDot={{
                            r: 7,
                          }}
                        />

                      </LineChart>

                    </ResponsiveContainer>

                  </div>

                </section>


                <section className="section-card">

                  <div className="section-heading">

                    <h2>
                      Observation History
                    </h2>

                    <p>
                      Underlying historical observations for the selected signal.
                    </p>

                  </div>


                  <div className="table-scroll">

                    <table className="data-table">

                      <thead>

                        <tr>
                          <th>Date</th>
                          <th>Value</th>
                          <th>Frequency</th>
                          <th>Period</th>
                          <th>Source</th>
                          <th>Data Quality</th>
                        </tr>

                      </thead>


                      <tbody>

                        {
                          selectedHistory
                            .map(
                              (
                                observation,
                                index
                              ) => (

                                <tr
                                  key={index}
                                >

                                  <td>
                                    {
                                      observation
                                        .date
                                    }
                                  </td>

                                  <td>
                                    {
                                      observation
                                        .value
                                    }
                                  </td>

                                  <td>
                                    {
                                      observation
                                        .reporting_frequency
                                    }
                                  </td>

                                  <td>
                                    {
                                      observation
                                        .period_start
                                    }
                                    {" → "}
                                    {
                                      observation
                                        .period_end
                                    }
                                  </td>

                                  <td>
                                    {
                                      observation
                                        .source
                                    }
                                  </td>

                                  <td>
                                    {
                                      observation
                                        .data_quality
                                    }
                                  </td>

                                </tr>

                              )
                            )
                        }

                      </tbody>

                    </table>

                  </div>

                </section>

              </>

            )
          }

        </div>

      )}


      {/* =================================================
          ALERTS TAB
          ================================================= */}

      {activeTab === "alerts" && (

        <div className="borrower-tab-content">

          <section className="section-card">

            <div className="section-heading">

              <h2>
                Borrower Alerts
              </h2>

              <p>
                Active borrower-specific monitoring alerts.
              </p>

            </div>


            {
              borrower
                .alerts
                ?.length > 0
              ? (

                <div className="borrower-alert-grid">

                  {
                    borrower
                      .alerts
                      .map(
                        (alert) => (

                          <div
                            key={
                              alert
                                .alert_id
                            }
                            className="borrower-alert-card"
                          >

                            <div>

                              <h3>
                                {
                                  alert
                                    .alert_type
                                }
                              </h3>

                              <span>
                                {
                                  alert
                                    .created_at
                                }
                              </span>

                            </div>


                            <span
                              className={
                                `severity-badge ${
                                  alert
                                    .severity
                                    .toLowerCase()
                                }`
                              }
                            >
                              {
                                alert
                                  .severity
                              }
                            </span>

                          </div>

                        )
                      )
                  }

                </div>

              ) : (

                <div className="insufficient-state">

                  <h3>
                    No active alerts
                  </h3>

                  <p>
                    No borrower-specific alerts are currently available.
                  </p>

                </div>

              )
            }

          </section>

        </div>

      )}

    </div>
  );
}


export default BorrowerPage;