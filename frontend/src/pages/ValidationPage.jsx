import { apiFetch } from "../utils/api";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Header from "../components/Header";





const PRIORITY_SCORE = {
  INSUFFICIENT_DATA: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  URGENT: 4,
};


const PRIORITY_LABEL = {
  0: "Insufficient",
  1: "Low",
  2: "Medium",
  3: "High",
  4: "Urgent",
};


function ValidationPage() {
  const [borrowers, setBorrowers] = useState([]);
  const [selectedBorrowerId, setSelectedBorrowerId] =
    useState("65");

  const [portfolioBacktest, setPortfolioBacktest] =
    useState(null);

  const [replay, setReplay] =
    useState(null);

  const [backtest, setBacktest] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const [borrowerLoading, setBorrowerLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  // =====================================================
  // LOAD PORTFOLIO VALIDATION + BORROWERS
  // =====================================================

  useEffect(() => {
    Promise.all([
      apiFetch(`/borrowers`),
      apiFetch(`/backtest_summary`),
    ])

      .then(async (responses) => {
        const [
          borrowersResponse,
          backtestResponse,
        ] = responses;

        if (
          !borrowersResponse.ok ||
          !backtestResponse.ok
        ) {
          throw new Error(
            "Unable to load validation workspace"
          );
        }

        return {
          borrowers:
            await borrowersResponse.json(),

          portfolioBacktest:
            await backtestResponse.json(),
        };
      })

      .then((data) => {
        setBorrowers(
          data.borrowers
        );

        setPortfolioBacktest(
          data.portfolioBacktest
        );

        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Validation workspace error:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  // =====================================================
  // LOAD SELECTED BORROWER REPLAY
  // =====================================================

  useEffect(() => {
    let active = true;
    if (!selectedBorrowerId) {
      return;
    }


    Promise.all([
      apiFetch(
        `/borrowers/${selectedBorrowerId}/replay`
      ),

      apiFetch(
        `/borrowers/${selectedBorrowerId}/backtest`
      ),
    ])

      .then(async (responses) => {
        const [
          replayResponse,
          backtestResponse,
        ] = responses;

        if (
          !replayResponse.ok ||
          !backtestResponse.ok
        ) {
          throw new Error(
            "Unable to load borrower replay"
          );
        }

        return {
          replay:
            await replayResponse.json(),

          backtest:
            await backtestResponse.json(),
        };
      })

      .then((data) => {
        if (!active) return;
        setReplay(
          data.replay
        );

        setBacktest(
          data.backtest
        );

        setBorrowerLoading(false);
      })

      .catch((error) => {
        if (!active) return;
        console.error(
          "Borrower replay error:",
          error
        );

        setReplay(null);
        setBacktest(null);

        setBorrowerLoading(false);
      });

    return () => { active = false; };
  }, [selectedBorrowerId]);


  // =====================================================
  // HISTORICALLY ASSESSABLE BORROWERS
  // =====================================================

  const validationBorrowers = useMemo(() => {
    if (!portfolioBacktest) {
      return [];
    }

    const validIds = new Set(
      portfolioBacktest.borrowers.map(
        (borrower) =>
          borrower.borrower_id
      )
    );

    return borrowers.filter(
      (borrower) =>
        validIds.has(
          borrower.id
        )
    );

  }, [
    borrowers,
    portfolioBacktest,
  ]);


  // =====================================================
  // CHART DATA
  // =====================================================

  const replayChartData = useMemo(() => {
    if (!replay) {
      return [];
    }

    return replay.timeline.map(
      (point) => ({
        date:
          point.as_of_date,

        priority:
          PRIORITY_SCORE[
            point.intervention_priority
          ] ?? 0,

        priorityLabel:
          point.intervention_priority,

        convergence:
          point.convergence_percentage,

        deteriorating:
          point.deteriorating_signals,

        critical:
          point.critical_condition_signals,
      })
    );

  }, [replay]);


  if (loading) {
    return (
      <div className="page">
        <Header
          title="Validation & Replay"
          subtitle="Loading historical validation workspace..."
        />

        <div className="section-card">
          Loading validation data...
        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div className="page">
        <Header
          title="Validation & Replay"
          subtitle="Historical replay and backtesting."
        />

        <div className="section-card">
          <div className="portfolio-state error">
            {error}
          </div>
        </div>
      </div>
    );
  }


  const matrix =
    portfolioBacktest
      ?.confusion_matrix;


  return (
    <div className="page">

      <Header
        title="Validation & Replay"
        subtitle="Point-in-time historical replay, priority migration and synthetic stress-event backtesting."
      />


      {/* =================================================
          IMPORTANT VALIDATION NOTICE
          ================================================= */}

      <div className="validation-notice">

        <div>

          <strong>
            SYNTHETIC VALIDATION
          </strong>

          <p>
            Historical observations and stress-event labels
            in this development environment are synthetic.
            Results validate system behaviour and replay
            mechanics, not institutional predictive accuracy.
          </p>

        </div>

      </div>


      {/* =================================================
          PORTFOLIO VALIDATION SUMMARY
          ================================================= */}

      <section className="section-card">

        <div className="section-heading">

          <h2>
            Historical Validation Summary
          </h2>

          <p>
            Point-in-time replay using a HIGH intervention
            threshold.
          </p>

        </div>


        <div className="validation-kpi-grid">

          <ValidationMetric
            label="Replay Borrowers"
            value={
              portfolioBacktest
                .historically_assessable_borrowers
            }
          />

          <ValidationMetric
            label="Labelled Events"
            value={
              portfolioBacktest
                .labelled_stress_events
            }
          />

          <ValidationMetric
            label="True Positive"
            value={
              matrix
                .true_positive
            }
          />

          <ValidationMetric
            label="False Positive"
            value={
              matrix
                .false_positive
            }
          />

          <ValidationMetric
            label="True Negative"
            value={
              matrix
                .true_negative
            }
          />

          <ValidationMetric
            label="False Negative"
            value={
              matrix
                .false_negative
            }
          />

        </div>


        <div className="validation-disclaimer">

          Current precision, recall and lead-time values
          are deliberately not presented as production
          performance metrics because the labelled
          validation sample is synthetic and small.

        </div>

      </section>


      {/* =================================================
          BORROWER SELECTOR
          ================================================= */}

      <section className="section-card">

        <div className="validation-selector-row">

          <div className="section-heading">

            <h2>
              Borrower Historical Replay
            </h2>

            <p>
              Reconstruct what RiskVision knew at each
              historical observation date.
            </p>

          </div>


          <select
            value={
              selectedBorrowerId
            }
            onChange={(event) => {
              setBorrowerLoading(true);
              setSelectedBorrowerId(event.target.value);
            }}
            className="filter-control validation-select"
          >

            {
              validationBorrowers.map(
                (borrower) => (

                  <option
                    key={
                      borrower.id
                    }
                    value={
                      borrower.id
                    }
                  >
                    {
                      borrower
                        .borrower_name
                    }
                  </option>

                )
              )
            }

          </select>

        </div>


        {
          borrowerLoading
          ? (

            <div className="portfolio-state">
              Running historical replay...
            </div>

          )
          : (
            replay
            &&
            backtest
          )
          ? (

            <>

              {/* =========================================
                  BORROWER SUMMARY
                  ========================================= */}

              <div className="validation-borrower-heading">

                <div>

                  <h3>
                    {
                      replay
                        .borrower_name
                    }
                  </h3>

                  <span>
                    {
                      replay
                        .replay_points
                    }
                    {" historical replay points"}
                  </span>

                </div>


                <Link
                  to={
                    `/borrower/${replay.borrower_id}`
                  }
                  className="primary-button"
                >
                  Open Borrower
                </Link>

              </div>


              {/* =========================================
                  ESCALATION DATES
                  ========================================= */}

              <div className="validation-event-grid">

                <ValidationMetric
                  label="First Medium"
                  value={
                    backtest
                      .first_medium_date
                    || "—"
                  }
                />

                <ValidationMetric
                  label="First High"
                  value={
                    backtest
                      .first_high_date
                    || "—"
                  }
                />

                <ValidationMetric
                  label="First Urgent"
                  value={
                    backtest
                      .first_urgent_date
                    || "—"
                  }
                />

                <ValidationMetric
                  label="Maximum Priority"
                  value={
                    backtest
                      .maximum_priority
                  }
                />

                <ValidationMetric
                  label="Stress Event"
                  value={
                    backtest
                      .stress_event_present
                    ? "LABELLED"
                    : "NONE"
                  }
                />

                <ValidationMetric
                  label="Lead Time"
                  value={
                    backtest
                      .lead_time_days
                    !== null
                    ? `${backtest.lead_time_days} days`
                    : "—"
                  }
                />

              </div>


              {/* =========================================
                  PRIORITY MIGRATION CHART
                  ========================================= */}

              <div className="validation-chart-card">

                <div className="section-heading">

                  <h3>
                    Intervention Priority Migration
                  </h3>

                  <p>
                    Point-in-time priority generated without
                    using observations from future dates.
                  </p>

                </div>


                <ResponsiveContainer
                  width="100%"
                  height={300}
                >

                  <LineChart
                    data={
                      replayChartData
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
                      domain={[0, 4]}
                      ticks={[
                        0,
                        1,
                        2,
                        3,
                        4,
                      ]}
                      tickFormatter={
                        (value) =>
                          PRIORITY_LABEL[
                            value
                          ]
                      }
                      stroke="#64748b"
                      width={90}
                    />

                    <Tooltip
                      formatter={(
                        value,
                        name,
                        props
                      ) => {

                        if (
                          name
                          === "priority"
                        ) {
                          return [
                            props
                              .payload
                              .priorityLabel,
                            "Priority",
                          ];
                        }

                        return [
                          value,
                          name,
                        ];
                      }}
                    />

                    <Line
                      type="monotone"
                      dataKey="priority"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      dot
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>


              {/* =========================================
                  REPLAY TABLE
                  ========================================= */}

              <div className="table-scroll">

                <table className="data-table">

                  <thead>

                    <tr>
                      <th>Date</th>
                      <th>Priority</th>
                      <th>Metrics</th>
                      <th>Deteriorating</th>
                      <th>Critical</th>
                      <th>Persistent</th>
                      <th>Accelerating</th>
                      <th>Convergence</th>
                    </tr>

                  </thead>


                  <tbody>

                    {
                      replay
                        .timeline
                        .map(
                          (
                            point,
                            index
                          ) => (

                            <tr
                              key={
                                `${point.as_of_date}-${index}`
                              }
                            >

                              <td>
                                {
                                  point
                                    .as_of_date
                                }
                              </td>


                              <td>

                                <span
                                  className={
                                    `priority-badge ${
                                      point
                                        .intervention_priority
                                        .toLowerCase()
                                    }`
                                  }
                                >
                                  {
                                    point
                                      .intervention_priority
                                  }
                                </span>

                              </td>


                              <td>
                                {
                                  point
                                    .metrics_analyzed
                                }
                              </td>


                              <td>
                                {
                                  point
                                    .deteriorating_signals
                                }
                              </td>


                              <td>
                                {
                                  point
                                    .critical_condition_signals
                                }
                              </td>


                              <td>
                                {
                                  point
                                    .persistent_deterioration_signals
                                }
                              </td>


                              <td>
                                {
                                  point
                                    .accelerating_deterioration_signals
                                }
                              </td>


                              <td>
                                {
                                  point
                                    .convergence_percentage
                                }
                                %
                              </td>

                            </tr>

                          )
                        )
                    }

                  </tbody>

                </table>

              </div>


              {/* =========================================
                  LABELLED EVENTS
                  ========================================= */}

              {
                backtest
                  .stress_events
                  ?.length > 0
                && (

                  <div className="validation-events">

                    <h3>
                      Synthetic Stress Events
                    </h3>


                    {
                      backtest
                        .stress_events
                        .map(
                          (event) => (

                            <div
                              key={
                                event.id
                              }
                              className="validation-event-row"
                            >

                              <div>

                                <strong>
                                  {
                                    event
                                      .event_type
                                  }
                                </strong>

                                <span>
                                  {
                                    event
                                      .event_date
                                  }
                                </span>

                              </div>


                              <span className="synthetic-badge">
                                {
                                  event
                                    .severity
                                }
                              </span>

                            </div>

                          )
                        )
                    }

                  </div>

                )
              }

            </>

          )
          : (

            <div className="portfolio-state">
              No replay data available.
            </div>

          )
        }

      </section>

    </div>
  );
}


function ValidationMetric({
  label,
  value,
}) {

  return (
    <div className="validation-metric">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


export default ValidationPage;