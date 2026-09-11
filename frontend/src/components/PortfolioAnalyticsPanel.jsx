import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


function PortfolioAnalyticsPanel() {
  const [analytics, setAnalytics] = useState(null);

  const [activeView, setActiveView] =
    useState("sectors");

  const [sectorSort, setSectorSort] =
    useState("exposure");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  useEffect(() => {
    fetch(
      "http://127.0.0.1:8000/portfolio_analytics"
    )

      .then((response) => {
        if (!response.ok) {
          throw new Error(
            "Unable to load portfolio analytics"
          );
        }

        return response.json();
      })

      .then((data) => {
        setAnalytics(data);
        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Portfolio analytics error:",
          error
        );

        setError(error.message);
        setLoading(false);
      });

  }, []);


  const sortedSectors = useMemo(() => {
    if (!analytics) {
      return [];
    }


    const data = [
      ...analytics.sectors
    ];


    if (sectorSort === "exposure") {
      data.sort(
        (a, b) =>
          b.total_exposure
          -
          a.total_exposure
      );
    }


    if (sectorSort === "actionable") {
      data.sort(
        (a, b) =>
          b.actionable_borrowers
          -
          a.actionable_borrowers
      );
    }


    if (sectorSort === "coverage") {
      data.sort(
        (a, b) =>
          b.history_coverage_percentage
          -
          a.history_coverage_percentage
      );
    }


    if (sectorSort === "covenant") {
      data.sort(
        (a, b) =>
          b.covenant_pressure_borrowers
          -
          a.covenant_pressure_borrowers
      );
    }


    return data;

  }, [
    analytics,
    sectorSort,
  ]);


  if (loading) {
    return (
      <section className="section-card">
        <div className="portfolio-state">
          Loading portfolio analytics...
        </div>
      </section>
    );
  }


  if (error) {
    return (
      <section className="section-card">
        <div className="portfolio-state error">
          {error}
        </div>
      </section>
    );
  }


  const summary =
    analytics.portfolio_summary;


  const chartData =
    analytics.sectors
      .slice(0, 8)
      .map((sector) => ({
        sector:
          sector.sector,

        exposure:
          sector.total_exposure,

        share:
          sector.exposure_share_percentage,
      }));


  return (
    <section className="section-card">

      <div className="analytics-header">

        <div className="section-heading">

          <h2>
            Portfolio Analytics
          </h2>

          <p>
            Exposure concentration, sector risk,
            data coverage and intervention concentration.
          </p>

        </div>

      </div>


      {/* ===============================================
          ANALYTICS KPIs
          =============================================== */}

      <div className="analytics-kpi-grid">

        <div>
          <span>
            Actionable Exposure
          </span>

          <strong>
            ₹
            {
              summary
                .actionable_exposure
            }
            {" Cr"}
          </strong>

          <small>
            {
              summary
                .actionable_exposure_share_percentage
            }
            % of portfolio
          </small>
        </div>


        <div>
          <span>
            History Coverage
          </span>

          <strong>
            {
              summary
                .history_coverage_percentage
            }
            %
          </strong>

          <small>
            {
              summary
                .historically_assessable_borrowers
            }
            {" borrowers"}
          </small>
        </div>


        <div>
          <span>
            Largest Borrower
          </span>

          <strong>
            {
              summary
                .largest_borrower_share_percentage
            }
            %
          </strong>

          <small>
            portfolio share
          </small>
        </div>


        <div>
          <span>
            Top 5 Exposure
          </span>

          <strong>
            {
              summary
                .top_5_borrower_exposure_share_percentage
            }
            %
          </strong>

          <small>
            portfolio share
          </small>
        </div>


        <div>
          <span>
            Borrower HHI
          </span>

          <strong>
            {
              summary
                .borrower_exposure_hhi
            }
          </strong>

          <small>
            exposure concentration
          </small>
        </div>


        <div>
          <span>
            Sector HHI
          </span>

          <strong>
            {
              summary
                .sector_exposure_hhi
            }
          </strong>

          <small>
            sector concentration
          </small>
        </div>

      </div>


      {/* ===============================================
          EXPOSURE CHART
          =============================================== */}

      <div className="analytics-chart-card">

        <div className="section-heading">

          <h3>
            Largest Sector Exposures
          </h3>

          <p>
            Top sectors ranked by total lending exposure.
          </p>

        </div>


        <ResponsiveContainer
          width="100%"
          height={320}
        >

          <BarChart
            data={chartData}
          >

            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#24344a"
            />

            <XAxis
              dataKey="sector"
              stroke="#64748b"
            />

            <YAxis
              stroke="#64748b"
              allowDecimals={false}
            />

            <Tooltip />

            <Bar
              dataKey="exposure"
              fill="#3b82f6"
            />

          </BarChart>

        </ResponsiveContainer>

      </div>


      {/* ===============================================
          VIEW SWITCH
          =============================================== */}

      <div className="analytics-tabs">

        <button
          className={
            activeView === "sectors"
              ? "analytics-tab active"
              : "analytics-tab"
          }
          onClick={() =>
            setActiveView("sectors")
          }
        >
          Sector Analysis
        </button>


        <button
          className={
            activeView === "borrowers"
              ? "analytics-tab active"
              : "analytics-tab"
          }
          onClick={() =>
            setActiveView("borrowers")
          }
        >
          Largest Exposures
        </button>

      </div>


      {/* ===============================================
          SECTOR VIEW
          =============================================== */}

      {activeView === "sectors" && (

        <>

          <div className="analytics-toolbar">

            <span>
              Sort sectors by
            </span>


            <select
              value={sectorSort}
              onChange={(event) =>
                setSectorSort(
                  event.target.value
                )
              }
              className="filter-control"
            >

              <option value="exposure">
                Exposure
              </option>

              <option value="actionable">
                Actionable Borrowers
              </option>

              <option value="coverage">
                History Coverage
              </option>

              <option value="covenant">
                Covenant Pressure
              </option>

            </select>

          </div>


          <div className="table-scroll">

            <table className="data-table">

              <thead>

                <tr>
                  <th>Sector</th>
                  <th>Borrowers</th>
                  <th>Exposure</th>
                  <th>Portfolio Share</th>
                  <th>Actionable</th>
                  <th>History Coverage</th>
                  <th>Covenant Pressure</th>
                  <th>Breached</th>
                </tr>

              </thead>


              <tbody>

                {sortedSectors.map(
                  (sector) => (

                    <tr
                      key={sector.sector}
                    >

                      <td>
                        {sector.sector}
                      </td>


                      <td>
                        {
                          sector
                            .borrower_count
                        }
                      </td>


                      <td>
                        ₹
                        {
                          sector
                            .total_exposure
                        }
                        {" Cr"}
                      </td>


                      <td>
                        {
                          sector
                            .exposure_share_percentage
                        }
                        %
                      </td>


                      <td>
                        {
                          sector
                            .actionable_borrowers
                        }
                      </td>


                      <td>
                        {
                          sector
                            .history_coverage_percentage
                        }
                        %
                      </td>


                      <td>
                        {
                          sector
                            .covenant_pressure_borrowers
                        }
                      </td>


                      <td>
                        {
                          sector
                            .breached_covenant_borrowers
                        }
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        </>

      )}


      {/* ===============================================
          BORROWER EXPOSURE VIEW
          =============================================== */}

      {activeView === "borrowers" && (

        <div className="table-scroll">

          <table className="data-table">

            <thead>

              <tr>
                <th>Rank</th>
                <th>Borrower</th>
                <th>Sector</th>
                <th>Exposure</th>
                <th>Portfolio Share</th>
              </tr>

            </thead>


            <tbody>

              {
                analytics
                  .top_exposures
                  .map(
                    (
                      borrower,
                      index
                    ) => (

                      <tr
                        key={
                          borrower
                            .borrower_id
                        }
                      >

                        <td>
                          {index + 1}
                        </td>


                        <td>

                          <Link
                            to={
                              `/borrower/${borrower.borrower_id}`
                            }
                            className="borrower-link"
                          >
                            {
                              borrower
                                .borrower_name
                            }
                          </Link>

                        </td>


                        <td>
                          {
                            borrower
                              .sector
                          }
                        </td>


                        <td>
                          ₹
                          {
                            borrower
                              .exposure
                          }
                          {" Cr"}
                        </td>


                        <td>
                          {
                            borrower
                              .portfolio_share_percentage
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

      )}

    </section>
  );
}


export default PortfolioAnalyticsPanel;