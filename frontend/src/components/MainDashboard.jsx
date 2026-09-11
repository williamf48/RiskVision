import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import RiskChart from "./RiskChart";
import TopRiskAccounts from "./TopRiskAccounts";
import AlertsPanel from "./AlertsPanel";


function MainDashboard() {
  const [portfolioSummary, setPortfolioSummary] = useState(null);
  const [interventionSummary, setInterventionSummary] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {

    Promise.all([
      fetch("http://127.0.0.1:8000/portfolio_summary"),
      fetch("http://127.0.0.1:8000/intervention_summary"),
    ])

      .then(async (
        [
          portfolioResponse,
          interventionResponse,
        ]
      ) => {

        if (
          !portfolioResponse.ok ||
          !interventionResponse.ok
        ) {
          throw new Error(
            "Unable to load dashboard intelligence"
          );
        }


        return {
          portfolio:
            await portfolioResponse.json(),

          intervention:
            await interventionResponse.json(),
        };
      })

      .then((data) => {

        setPortfolioSummary(
          data.portfolio
        );

        setInterventionSummary(
          data.intervention
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Dashboard loading error:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  if (loading) {

    return (
      <div className="dashboard-state">
        Loading portfolio intelligence...
      </div>
    );
  }


  if (error) {

    return (
      <div className="dashboard-state error">
        {error}
      </div>
    );
  }


  const assessable =
    interventionSummary
      ?.historically_assessable_borrowers
    || 0;


  const totalBorrowers =
    interventionSummary
      ?.total_borrowers
    || 0;


  const coveragePercentage =
    totalBorrowers > 0
      ? Math.round(
          (
            assessable /
            totalBorrowers
          )
          * 100
        )
      : 0;


  return (
    <div className="executive-dashboard">

      {/* =================================================
          KPI CARDS
          ================================================= */}

      <div className="executive-kpi-grid">

        <Link
          to="/portfolio"
          className="executive-kpi-card"
        >

          <span>
            Total Exposure
          </span>

          <strong>
            ₹
            {
              Number(
                portfolioSummary
                  .total_exposure
              )
              .toLocaleString(
                "en-IN"
              )
            }
            {" Cr"}
          </strong>

          <small>
            View portfolio →
          </small>

        </Link>


        <Link
          to="/borrowers"
          className="executive-kpi-card"
        >

          <span>
            Borrowers
          </span>

          <strong>
            {totalBorrowers}
          </strong>

          <small>
            Open directory →
          </small>

        </Link>


        <Link
          to="/interventions"
          className="executive-kpi-card attention"
        >

          <span>
            Actionable Borrowers
          </span>

          <strong>
            {
              interventionSummary
                .actionable_borrowers
            }
          </strong>

          <small>
            Review interventions →
          </small>

        </Link>


        <Link
          to="/interventions"
          className="executive-kpi-card urgent"
        >

          <span>
            Urgent
          </span>

          <strong>
            {
              interventionSummary
                .urgent
            }
          </strong>

          <small>
            Highest priority →
          </small>

        </Link>


        <Link
          to="/portfolio"
          className="executive-kpi-card"
        >

          <span>
            Historical Coverage
          </span>

          <strong>
            {coveragePercentage}%
          </strong>

          <small>
            {assessable}
            {" / "}
            {totalBorrowers}
            {" assessable"}
          </small>

        </Link>

      </div>


      {/* =================================================
          PRIMARY DASHBOARD CONTENT
          ================================================= */}

      <div className="executive-dashboard-grid">

        <div className="executive-chart-section">

          <div className="dashboard-section-header">

            <div>

              <h2>
                Portfolio Intervention Profile
              </h2>

              <p>
                Distribution across historically assessable borrowers.
              </p>

            </div>


            <Link
              to="/portfolio"
              className="dashboard-text-link"
            >
              Open Portfolio →
            </Link>

          </div>


          <RiskChart />

        </div>


        <div className="dashboard-quick-actions">

          <div className="dashboard-section-header">

            <div>

              <h2>
                Quick Actions
              </h2>

              <p>
                Move directly into analyst workflows.
              </p>

            </div>

          </div>


          <div className="quick-action-grid">

            <Link
              to="/interventions"
              className="quick-action-card"
            >
              <strong>
                Intervention Centre
              </strong>

              <span>
                Review prioritized deterioration cases.
              </span>
            </Link>


            <Link
              to="/borrowers"
              className="quick-action-card"
            >
              <strong>
                Borrower Directory
              </strong>

              <span>
                Search and inspect borrower intelligence.
              </span>
            </Link>


            <Link
              to="/alerts"
              className="quick-action-card"
            >
              <strong>
                Alert Feed
              </strong>

              <span>
                Review monitoring alerts and events.
              </span>
            </Link>


            <Link
              to="/reports"
              className="quick-action-card"
            >
              <strong>
                Reports
              </strong>

              <span>
                Open portfolio reporting workspace.
              </span>
            </Link>

          </div>

        </div>

      </div>


      {/* =================================================
          TOP ACCOUNTS
          ================================================= */}

      <div className="dashboard-section">

        <div className="dashboard-section-header">

          <div>

            <h2>
              Highest Intervention Priorities
            </h2>

            <p>
              Borrowers ranked by deterioration intelligence.
            </p>

          </div>


          <Link
            to="/interventions"
            className="dashboard-text-link"
          >
            View all →
          </Link>

        </div>


        <TopRiskAccounts />

      </div>


      {/* =================================================
          PRIORITY DRIVERS
          ================================================= */}

      <div className="dashboard-section">

        <div className="dashboard-section-header">

          <div>

            <h2>
              Emerging Risk Drivers
            </h2>

            <p>
              Explainable reasons behind current intervention priorities.
            </p>

          </div>

        </div>


        <AlertsPanel />

      </div>

    </div>
  );
}


export default MainDashboard;