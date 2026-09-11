import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import Header from "../components/Header";
import CovenantPressurePanel from "../components/CovenantPressurePanel";
import PortfolioAnalyticsPanel from "../components/PortfolioAnalyticsPanel";


function PortfolioPage() {
  const [summary, setSummary] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [borrowers, setBorrowers] = useState([]);

  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [sectorFilter, setSectorFilter] = useState("ALL");
  const [coverageFilter, setCoverageFilter] = useState("ALL");

  const [expandedId, setExpandedId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  // =====================================================
  // LOAD PORTFOLIO DATA
  // =====================================================

  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      fetch("http://127.0.0.1:8000/intervention_summary"),
      fetch("http://127.0.0.1:8000/intervention_watchlist"),
      fetch("http://127.0.0.1:8000/borrowers"),
    ])

      .then(async (
        [
          summaryResponse,
          portfolioResponse,
          borrowersResponse,
        ]
      ) => {

        if (
          !summaryResponse.ok ||
          !portfolioResponse.ok ||
          !borrowersResponse.ok
        ) {
          throw new Error(
            "Unable to load portfolio intelligence"
          );
        }


        return {
          summary:
            await summaryResponse.json(),

          portfolio:
            await portfolioResponse.json(),

          borrowers:
            await borrowersResponse.json(),
        };
      })

      .then((data) => {
        setSummary(data.summary);
        setPortfolio(data.portfolio);
        setBorrowers(data.borrowers);

        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Portfolio loading error:",
          error
        );

        setError(error.message);
        setLoading(false);
      });

  }, []);


  // =====================================================
  // BORROWER LOOKUP
  // =====================================================

  const borrowerMap = useMemo(() => {
    const map = {};

    borrowers.forEach((borrower) => {
      map[borrower.id] = borrower;
    });

    return map;

  }, [borrowers]);


  // =====================================================
  // ENRICH INTERVENTION DATA
  // =====================================================

  const enrichedPortfolio = useMemo(() => {

    return portfolio.map((account) => {

      const borrower =
        borrowerMap[
          account.borrower_id
        ];


      return {
        ...account,

        sector:
          borrower?.sector || "Unknown",

        loan_amount:
          borrower?.loan_amount ?? null,
      };

    });

  }, [
    portfolio,
    borrowerMap,
  ]);


  // =====================================================
  // SECTOR OPTIONS
  // =====================================================

  const sectors = useMemo(() => {

    return [
      ...new Set(
        enrichedPortfolio
          .map(
            (account) =>
              account.sector
          )
          .filter(Boolean)
      ),
    ].sort();

  }, [enrichedPortfolio]);


  // =====================================================
  // FILTER PORTFOLIO
  // =====================================================

  const filteredPortfolio = useMemo(() => {

    return enrichedPortfolio.filter(
      (account) => {

        const matchesSearch =
          account.borrower_name
            .toLowerCase()
            .includes(
              search
                .trim()
                .toLowerCase()
            );


        const matchesPriority =
          priorityFilter === "ALL"
          ||
          account.intervention_priority
          === priorityFilter;


        const matchesSector =
          sectorFilter === "ALL"
          ||
          account.sector
          === sectorFilter;


        const sufficientHistory =
          account.metrics_analyzed > 0;


        const matchesCoverage =
          coverageFilter === "ALL"

          ||

          (
            coverageFilter
            === "SUFFICIENT"

            &&

            sufficientHistory
          )

          ||

          (
            coverageFilter
            === "INSUFFICIENT"

            &&

            !sufficientHistory
          );


        return (
          matchesSearch
          &&
          matchesPriority
          &&
          matchesSector
          &&
          matchesCoverage
        );
      }
    );

  }, [
    enrichedPortfolio,
    search,
    priorityFilter,
    sectorFilter,
    coverageFilter,
  ]);


  // =====================================================
  // RESET FILTERS
  // =====================================================

  function resetFilters() {
    setSearch("");
    setPriorityFilter("ALL");
    setSectorFilter("ALL");
    setCoverageFilter("ALL");
  }


  return (
    <div className="page">

      <Header
        title="Portfolio Intelligence"
        subtitle="Portfolio-wide deterioration, intervention priority, covenant pressure, concentration and historical coverage."
      />


      {/* =================================================
          SUMMARY
          ================================================= */}

      {summary && (

        <div className="summary-grid">

          <div className="summary-card">

            <span>
              Total Borrowers
            </span>

            <strong>
              {summary.total_borrowers}
            </strong>

          </div>


          <div className="summary-card">

            <span>
              Historically Assessable
            </span>

            <strong>
              {
                summary
                  .historically_assessable_borrowers
              }
            </strong>

          </div>


          <div className="summary-card urgent-card">

            <span>
              Urgent
            </span>

            <strong>
              {summary.urgent}
            </strong>

          </div>


          <div className="summary-card">

            <span>
              Actionable
            </span>

            <strong>
              {
                summary
                  .actionable_borrowers
              }
            </strong>

          </div>


          <div className="summary-card">

            <span>
              Insufficient History
            </span>

            <strong>
              {
                summary
                  .insufficient_data
              }
            </strong>

          </div>

        </div>

      )}


      {/* =================================================
          PORTFOLIO RANKING
          ================================================= */}

      <section className="section-card">

        <div className="section-heading">

          <h2>
            Portfolio Ranking
          </h2>

          <p>
            Ranked using current condition, deterioration trajectory,
            persistence and cross-signal convergence.
          </p>

        </div>


        {/* ===============================================
            FILTERS
            =============================================== */}

        <div className="portfolio-filter-bar">

          <input
            type="text"
            placeholder="Search borrower..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            className="search-control"
          />


          <select
            value={priorityFilter}
            onChange={(event) =>
              setPriorityFilter(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All priorities
            </option>

            <option value="URGENT">
              Urgent
            </option>

            <option value="HIGH">
              High
            </option>

            <option value="MEDIUM">
              Medium
            </option>

            <option value="LOW">
              Low
            </option>

            <option value="INSUFFICIENT_DATA">
              Insufficient Data
            </option>

          </select>


          <select
            value={sectorFilter}
            onChange={(event) =>
              setSectorFilter(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All sectors
            </option>

            {sectors.map(
              (sector) => (

                <option
                  key={sector}
                  value={sector}
                >
                  {sector}
                </option>

              )
            )}

          </select>


          <select
            value={coverageFilter}
            onChange={(event) =>
              setCoverageFilter(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All history coverage
            </option>

            <option value="SUFFICIENT">
              Sufficient history
            </option>

            <option value="INSUFFICIENT">
              Insufficient history
            </option>

          </select>


          <button
            onClick={resetFilters}
            className="secondary-button"
          >
            Reset
          </button>

        </div>


        <div className="portfolio-result-count">

          Showing{" "}

          <strong>
            {filteredPortfolio.length}
          </strong>

          {" of "}

          <strong>
            {enrichedPortfolio.length}
          </strong>

          {" borrowers"}

        </div>


        {/* ===============================================
            LOADING / ERROR / EMPTY
            =============================================== */}

        {loading ? (

          <div className="portfolio-state">
            Loading portfolio intelligence...
          </div>

        ) : error ? (

          <div className="portfolio-state error">

            <h3>
              Unable to load portfolio
            </h3>

            <p>
              {error}
            </p>

          </div>

        ) : filteredPortfolio.length === 0 ? (

          <div className="portfolio-state">

            <h3>
              No borrowers match the filters
            </h3>

            <button
              onClick={resetFilters}
              className="secondary-button"
            >
              Clear Filters
            </button>

          </div>

        ) : (

          <div className="table-scroll">

            <table className="data-table portfolio-table">

              <thead>

                <tr>
                  <th>Rank</th>
                  <th>Borrower</th>
                  <th>Sector</th>
                  <th>Exposure</th>
                  <th>Priority</th>
                  <th>Critical</th>
                  <th>Deteriorating</th>
                  <th>Persistent</th>
                  <th>Convergence</th>
                  <th></th>
                </tr>

              </thead>


              <tbody>

                {filteredPortfolio.map(
                  (account) => {

                    const expanded =
                      expandedId
                      === account.borrower_id;


                    const hasHistory =
                      account.metrics_analyzed
                      > 0;


                    return (

                      <PortfolioRow
                        key={
                          account.borrower_id
                        }
                        account={account}
                        expanded={expanded}
                        hasHistory={hasHistory}
                        onToggle={() =>
                          setExpandedId(
                            expanded
                              ? null
                              : account.borrower_id
                          )
                        }
                      />

                    );

                  }
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* =================================================
          COVENANT PRESSURE
          ================================================= */}

      <CovenantPressurePanel />


      {/* =================================================
          PORTFOLIO CONCENTRATION ANALYTICS
          ================================================= */}

      <PortfolioAnalyticsPanel />

    </div>
  );
}


function PortfolioRow({
  account,
  expanded,
  hasHistory,
  onToggle,
}) {

  return (
    <>

      <tr
        className={
          expanded
            ? "portfolio-row expanded"
            : "portfolio-row"
        }
      >

        <td>
          {
            account
              .portfolio_rank
          }
        </td>


        <td>

          <Link
            to={
              `/borrower/${account.borrower_id}`
            }
            className="borrower-link"
          >
            {
              account
                .borrower_name
            }
          </Link>

        </td>


        <td>
          {account.sector}
        </td>


        <td>
          {
            account.loan_amount
            !== null

              ? `₹${account.loan_amount} Cr`

              : "—"
          }
        </td>


        <td>

          <span
            className={
              `priority-badge ${
                account
                  .intervention_priority
                  .toLowerCase()
              }`
            }
          >
            {
              account
                .intervention_priority
            }
          </span>

        </td>


        <td>
          {
            account
              .critical_condition_signals
          }
        </td>


        <td>

          {
            account
              .deteriorating_signals
          }

          /

          {
            account
              .metrics_analyzed
          }

        </td>


        <td>
          {
            account
              .persistent_deterioration_signals
          }
        </td>


        <td>
          {
            account
              .convergence_percentage
          }
          %
        </td>


        <td>

          <button
            className="row-expand-button"
            onClick={onToggle}
          >
            {
              expanded
                ? "Hide"
                : "Details"
            }
          </button>

        </td>

      </tr>


      {expanded && (

        <tr className="portfolio-expanded-row">

          <td colSpan="10">

            <div className="portfolio-expanded-content">

              <div className="portfolio-expanded-top">

                <div>

                  <h3>
                    {
                      account
                        .borrower_name
                    }
                  </h3>

                  <p>
                    {
                      account.sector
                    }

                    {" · "}

                    {
                      hasHistory
                        ? "Historical trajectory available"
                        : "Insufficient historical trajectory"
                    }
                  </p>

                </div>


                <Link
                  to={
                    `/borrower/${account.borrower_id}`
                  }
                  className="primary-button"
                >
                  Open Borrower
                </Link>

              </div>


              {/* =========================================
                  DETAIL METRICS
                  ========================================= */}

              <div className="expanded-metric-grid">

                <div>

                  <span>
                    Critical Signals
                  </span>

                  <strong>
                    {
                      account
                        .critical_condition_signals
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Weak Signals
                  </span>

                  <strong>
                    {
                      account
                        .weak_condition_signals
                    }
                  </strong>

                </div>


                <div>

                  <span>
                    Persistent
                  </span>

                  <strong>
                    {
                      account
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
                      account
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
                      account
                        .convergence_percentage
                    }
                    %
                  </strong>

                </div>

              </div>


              {/* =========================================
                  EXPLAINABILITY
                  ========================================= */}

              {
                account
                  .explanations
                  ?.length > 0
                && (

                  <div className="expanded-intelligence-grid">

                    <div>

                      <h4>
                        Why Flagged
                      </h4>

                      <ul>

                        {
                          account
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

                    </div>


                    <div>

                      <h4>
                        Recommended Investigation
                      </h4>


                      {
                        account
                          .recommended_investigations
                          ?.length > 0
                        ? (

                          <ul>

                            {
                              account
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

                        ) : (

                          <p className="muted-text">
                            No investigation recommendations generated.
                          </p>

                        )
                      }

                    </div>

                  </div>

                )
              }

            </div>

          </td>

        </tr>

      )}

    </>
  );
}


export default PortfolioPage;