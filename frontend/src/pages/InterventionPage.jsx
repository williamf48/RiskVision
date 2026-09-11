import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import Header from "../components/Header";


function InterventionPage() {
  const [accounts, setAccounts] = useState([]);
  const [borrowers, setBorrowers] = useState([]);

  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [sectorFilter, setSectorFilter] = useState("ALL");

  const [expandedId, setExpandedId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {

    Promise.all([
      fetch(
        "http://127.0.0.1:8000/intervention_watchlist"
      ),
      fetch(
        "http://127.0.0.1:8000/borrowers"
      ),
    ])

      .then(async (
        [
          interventionResponse,
          borrowersResponse,
        ]
      ) => {

        if (
          !interventionResponse.ok
          ||
          !borrowersResponse.ok
        ) {
          throw new Error(
            "Unable to load intervention centre"
          );
        }


        return {
          accounts:
            await interventionResponse.json(),

          borrowers:
            await borrowersResponse.json(),
        };

      })

      .then((data) => {

        setAccounts(
          data.accounts
        );

        setBorrowers(
          data.borrowers
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Intervention loading error:",
          error
        );

        setError(error.message);
        setLoading(false);
      });

  }, []);


  const borrowerMap = useMemo(() => {
    const map = {};

    borrowers.forEach(
      (borrower) => {
        map[borrower.id] = borrower;
      }
    );

    return map;

  }, [borrowers]);


  const enrichedAccounts = useMemo(() => {

    return accounts.map(
      (account) => {

        const borrower =
          borrowerMap[
            account.borrower_id
          ];


        return {
          ...account,

          sector:
            borrower?.sector
            || "Unknown",

          loan_amount:
            borrower?.loan_amount
            ?? null,
        };

      }
    );

  }, [
    accounts,
    borrowerMap,
  ]);


  const sectors = useMemo(() => {

    return [
      ...new Set(
        enrichedAccounts
          .map(
            (account) =>
              account.sector
          )
          .filter(Boolean)
      ),
    ].sort();

  }, [enrichedAccounts]);


  const filteredAccounts = useMemo(() => {

    return enrichedAccounts.filter(
      (account) => {

        const actionable =
          account.intervention_priority
          !== "INSUFFICIENT_DATA";


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


        return (
          actionable
          &&
          matchesSearch
          &&
          matchesPriority
          &&
          matchesSector
        );

      }
    );

  }, [
    enrichedAccounts,
    search,
    priorityFilter,
    sectorFilter,
  ]);


  function resetFilters() {
    setSearch("");
    setPriorityFilter("ALL");
    setSectorFilter("ALL");
  }


  return (
    <div className="page">

      <Header
        title="Intervention Centre"
        subtitle="Prioritized borrower review queue with explainable deterioration drivers."
      />


      <section className="section-card">

        <div className="intervention-filter-bar">

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


          <button
            className="secondary-button"
            onClick={resetFilters}
          >
            Reset
          </button>

        </div>


        <div className="portfolio-result-count">

          Showing{" "}
          <strong>
            {filteredAccounts.length}
          </strong>
          {" intervention cases"}

        </div>

      </section>


      {loading ? (

        <div className="portfolio-state">
          Loading intervention queue...
        </div>

      ) : error ? (

        <div className="portfolio-state error">
          {error}
        </div>

      ) : filteredAccounts.length === 0 ? (

        <div className="section-card portfolio-state">

          <h3>
            No intervention cases match the filters.
          </h3>

        </div>

      ) : (

        <div className="intervention-list">

          {filteredAccounts.map(
            (account) => {

              const expanded =
                expandedId
                === account.borrower_id;


              return (
                <div
                  key={
                    account.borrower_id
                  }
                  className="intervention-card"
                >

                  <div className="intervention-card-header">

                    <div>

                      <span className="rank-label">
                        Portfolio Rank #
                        {
                          account
                            .portfolio_rank
                        }
                      </span>


                      <h3>
                        {
                          account
                            .borrower_name
                        }
                      </h3>


                      <p className="intervention-subtitle">
                        {
                          account.sector
                        }

                        {" · "}

                        {
                          account.loan_amount
                          !== null
                            ? `₹${account.loan_amount} Cr`
                            : "Exposure unavailable"
                        }
                      </p>

                    </div>


                    <span
                      className={
                        `priority-badge large ${
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

                  </div>


                  <div className="intervention-metrics">

                    <span>
                      <strong>
                        {
                          account
                            .critical_condition_signals
                        }
                      </strong>
                      Critical
                    </span>


                    <span>
                      <strong>
                        {
                          account
                            .deteriorating_signals
                        }
                        /
                        {
                          account
                            .metrics_analyzed
                        }
                      </strong>
                      Deteriorating
                    </span>


                    <span>
                      <strong>
                        {
                          account
                            .persistent_deterioration_signals
                        }
                      </strong>
                      Persistent
                    </span>


                    <span>
                      <strong>
                        {
                          account
                            .accelerating_deterioration_signals
                        }
                      </strong>
                      Accelerating
                    </span>


                    <span>
                      <strong>
                        {
                          account
                            .convergence_percentage
                        }
                        %
                      </strong>
                      Convergence
                    </span>

                  </div>


                  <div className="card-actions">

                    <button
                      onClick={() =>
                        setExpandedId(
                          expanded
                            ? null
                            : account.borrower_id
                        )
                      }
                      className="secondary-button"
                    >
                      {
                        expanded
                          ? "Hide rationale"
                          : "Why flagged?"
                      }
                    </button>


                    <Link
                      to={
                        `/borrower/${account.borrower_id}`
                      }
                      className="primary-button"
                    >
                      Open Borrower
                    </Link>

                  </div>


                  {expanded && (

                    <div className="intervention-expanded-grid">

                      <div>

                        <h4>
                          Why Flagged
                        </h4>

                        <ul>

                          {
                            account
                              .explanations
                              ?.map(
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

                  )}

                </div>
              );

            }
          )}

        </div>

      )}

    </div>
  );
}


export default InterventionPage;