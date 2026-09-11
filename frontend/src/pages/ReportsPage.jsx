import { useEffect, useState } from "react";

import Header from "../components/Header";


function ReportsPage() {
  const [portfolio, setPortfolio] =
    useState(null);

  const [intervention, setIntervention] =
    useState(null);

  const [covenants, setCovenants] =
    useState(null);

  const [interventionWatchlist, setInterventionWatchlist] =
    useState([]);

  const [covenantWatchlist, setCovenantWatchlist] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  useEffect(() => {

    Promise.all([
      fetch("http://127.0.0.1:8000/portfolio_summary"),
      fetch("http://127.0.0.1:8000/intervention_summary"),
      fetch("http://127.0.0.1:8000/covenant_summary"),
      fetch("http://127.0.0.1:8000/intervention_watchlist"),
      fetch("http://127.0.0.1:8000/covenant_watchlist"),
    ])

      .then(async (
        [
          portfolioResponse,
          interventionResponse,
          covenantResponse,
          interventionWatchlistResponse,
          covenantWatchlistResponse,
        ]
      ) => {

        const responses = [
          portfolioResponse,
          interventionResponse,
          covenantResponse,
          interventionWatchlistResponse,
          covenantWatchlistResponse,
        ];


        if (
          responses.some(
            (response) =>
              !response.ok
          )
        ) {
          throw new Error(
            "Unable to generate live portfolio report"
          );
        }


        return {
          portfolio:
            await portfolioResponse.json(),

          intervention:
            await interventionResponse.json(),

          covenants:
            await covenantResponse.json(),

          interventionWatchlist:
            await interventionWatchlistResponse.json(),

          covenantWatchlist:
            await covenantWatchlistResponse.json(),
        };
      })

      .then((data) => {
        setPortfolio(data.portfolio);
        setIntervention(data.intervention);
        setCovenants(data.covenants);

        setInterventionWatchlist(
          data.interventionWatchlist
        );

        setCovenantWatchlist(
          data.covenantWatchlist
        );

        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Report loading error:",
          error
        );

        setError(error.message);
        setLoading(false);
      });

  }, []);


  function downloadJsonReport() {

    const report = {
      generated_at:
        new Date().toISOString(),

      portfolio_summary:
        portfolio,

      intervention_summary:
        intervention,

      covenant_summary:
        covenants,

      intervention_watchlist:
        interventionWatchlist,

      covenant_watchlist:
        covenantWatchlist,
    };


    const blob = new Blob(
      [
        JSON.stringify(
          report,
          null,
          2
        )
      ],
      {
        type:
          "application/json",
      }
    );


    const url =
      URL.createObjectURL(
        blob
      );


    const link =
      document.createElement(
        "a"
      );


    link.href = url;

    link.download =
      `riskvision-report-${
        new Date()
          .toISOString()
          .slice(0, 10)
      }.json`;


    link.click();


    URL.revokeObjectURL(
      url
    );
  }


  function downloadCsvReport() {

    const rows = [

      [
        "Portfolio Rank",
        "Borrower",
        "Priority",
        "Critical Signals",
        "Deteriorating Signals",
        "Persistent Signals",
        "Accelerating Signals",
        "Convergence %",
      ],

      ...interventionWatchlist.map(
        (borrower) => [

          borrower
            .portfolio_rank,

          borrower
            .borrower_name,

          borrower
            .intervention_priority,

          borrower
            .critical_condition_signals,

          `${borrower.deteriorating_signals}/${borrower.metrics_analyzed}`,

          borrower
            .persistent_deterioration_signals,

          borrower
            .accelerating_deterioration_signals,

          borrower
            .convergence_percentage,

        ]
      ),

    ];


    const csv = rows
      .map(
        (row) =>
          row
            .map(
              (value) =>
                `"${String(value ?? "").replaceAll('"', '""')}"`
            )
            .join(",")
      )
      .join("\n");


    const blob = new Blob(
      [csv],
      {
        type:
          "text/csv;charset=utf-8;",
      }
    );


    const url =
      URL.createObjectURL(
        blob
      );


    const link =
      document.createElement(
        "a"
      );


    link.href = url;

    link.download =
      `riskvision-intervention-report-${
        new Date()
          .toISOString()
          .slice(0, 10)
      }.csv`;


    link.click();


    URL.revokeObjectURL(
      url
    );
  }


  if (loading) {

    return (
      <div className="page">

        <Header
          title="Reports"
          subtitle="Portfolio and borrower intelligence reporting workspace."
        />

        <div className="portfolio-state">
          Generating live report...
        </div>

      </div>
    );
  }


  if (error) {

    return (
      <div className="page">

        <Header
          title="Reports"
          subtitle="Portfolio and borrower intelligence reporting workspace."
        />

        <div className="portfolio-state error">
          {error}
        </div>

      </div>
    );
  }


  return (
    <div className="page">

      <Header
        title="Reports"
        subtitle="Live portfolio deterioration, intervention and covenant intelligence."
      />


      <div className="report-actions">

        <button
          className="primary-button"
          onClick={
            downloadCsvReport
          }
        >
          Export Intervention CSV
        </button>


        <button
          className="secondary-button"
          onClick={
            downloadJsonReport
          }
        >
          Export Full JSON
        </button>

      </div>


      <div className="report-kpi-grid">

        <div className="report-kpi-card">

          <span>
            Total Exposure
          </span>

          <strong>
            ₹
            {
              Number(
                portfolio
                  .total_exposure
              )
              .toLocaleString(
                "en-IN"
              )
            }
            {" Cr"}
          </strong>

        </div>


        <div className="report-kpi-card">

          <span>
            Total Borrowers
          </span>

          <strong>
            {
              portfolio
                .total_borrowers
            }
          </strong>

        </div>


        <div className="report-kpi-card">

          <span>
            Actionable Borrowers
          </span>

          <strong>
            {
              intervention
                .actionable_borrowers
            }
          </strong>

        </div>


        <div className="report-kpi-card">

          <span>
            Historically Assessable
          </span>

          <strong>
            {
              intervention
                .historically_assessable_borrowers
            }
          </strong>

        </div>


        <div className="report-kpi-card">

          <span>
            Covenant Pressure
          </span>

          <strong>
            {
              covenants
                .borrowers_under_covenant_pressure
            }
          </strong>

        </div>

      </div>


      <div className="report-section-grid">

        <section className="section-card">

          <div className="section-heading">

            <h2>
              Intervention Summary
            </h2>

            <p>
              Borrower deterioration priority distribution.
            </p>

          </div>


          <div className="report-stat-list">

            <div>
              <span>Urgent</span>
              <strong>
                {
                  intervention
                    .urgent
                }
              </strong>
            </div>

            <div>
              <span>High</span>
              <strong>
                {
                  intervention
                    .high
                }
              </strong>
            </div>

            <div>
              <span>Medium</span>
              <strong>
                {
                  intervention
                    .medium
                }
              </strong>
            </div>

            <div>
              <span>Low</span>
              <strong>
                {
                  intervention
                    .low
                }
              </strong>
            </div>

            <div>
              <span>Insufficient Data</span>
              <strong>
                {
                  intervention
                    .insufficient_data
                }
              </strong>
            </div>

          </div>

        </section>


        <section className="section-card">

          <div className="section-heading">

            <h2>
              Covenant Summary
            </h2>

            <p>
              Portfolio covenant pressure and compliance.
            </p>

          </div>


          <div className="report-stat-list">

            <div>
              <span>Breached Borrowers</span>
              <strong>
                {
                  covenants
                    .borrowers_breached
                }
              </strong>
            </div>

            <div>
              <span>Near Breach</span>
              <strong>
                {
                  covenants
                    .borrowers_near_breach
                }
              </strong>
            </div>

            <div>
              <span>Tight</span>
              <strong>
                {
                  covenants
                    .borrowers_tight
                }
              </strong>
            </div>

            <div>
              <span>Healthy</span>
              <strong>
                {
                  covenants
                    .borrowers_healthy
                }
              </strong>
            </div>

            <div>
              <span>Untested Covenants</span>
              <strong>
                {
                  covenants
                    .untested_covenants
                }
              </strong>
            </div>

          </div>

        </section>

      </div>


      <section className="section-card">

        <div className="section-heading">

          <h2>
            Top Intervention Accounts
          </h2>

          <p>
            Highest-priority borrowers requiring analyst attention.
          </p>

        </div>


        <div className="table-scroll">

          <table className="data-table">

            <thead>

              <tr>
                <th>Rank</th>
                <th>Borrower</th>
                <th>Priority</th>
                <th>Critical</th>
                <th>Deteriorating</th>
                <th>Persistent</th>
                <th>Accelerating</th>
                <th>Convergence</th>
              </tr>

            </thead>


            <tbody>

              {
                interventionWatchlist
                  .slice(0, 10)
                  .map(
                    (borrower) => (

                      <tr
                        key={
                          borrower
                            .borrower_id
                        }
                      >

                        <td>
                          {
                            borrower
                              .portfolio_rank
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .borrower_name
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .intervention_priority
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .critical_condition_signals
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .deteriorating_signals
                          }
                          /
                          {
                            borrower
                              .metrics_analyzed
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .persistent_deterioration_signals
                          }
                        </td>

                        <td>
                          {
                            borrower
                              .accelerating_deterioration_signals
                          }
                        </td>

                        <td>
                          {
                            borrower
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

      </section>


      <section className="section-card">

        <div className="section-heading">

          <h2>
            Covenant Pressure Watchlist
          </h2>

          <p>
            Borrowers ranked by current covenant pressure.
          </p>

        </div>


        <div className="table-scroll">

          <table className="data-table">

            <thead>

              <tr>
                <th>Rank</th>
                <th>Borrower</th>
                <th>Status</th>
                <th>Breached</th>
                <th>Near Breach</th>
                <th>Tight</th>
                <th>Healthy</th>
                <th>Untested</th>
              </tr>

            </thead>


            <tbody>

              {
                covenantWatchlist.map(
                  (borrower) => (

                    <tr
                      key={
                        borrower
                          .borrower_id
                      }
                    >

                      <td>
                        {
                          borrower
                            .covenant_pressure_rank
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .borrower_name
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .covenant_pressure_status
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .breached_covenants
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .near_breach_covenants
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .tight_covenants
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .healthy_covenants
                        }
                      </td>

                      <td>
                        {
                          borrower
                            .untested_covenants
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

    </div>
  );
}


export default ReportsPage;