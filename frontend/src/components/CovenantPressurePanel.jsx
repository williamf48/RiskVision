import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";


function CovenantPressurePanel() {
  const [summary, setSummary] = useState(null);
  const [watchlist, setWatchlist] = useState([]);

  const [statusFilter, setStatusFilter] =
    useState("ALL");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState(null);


  useEffect(() => {
    Promise.all([
      fetch(
        "http://127.0.0.1:8000/covenant_summary"
      ),
      fetch(
        "http://127.0.0.1:8000/covenant_watchlist"
      ),
    ])

      .then(async (
        [
          summaryResponse,
          watchlistResponse,
        ]
      ) => {

        if (
          !summaryResponse.ok
          ||
          !watchlistResponse.ok
        ) {
          throw new Error(
            "Unable to load covenant intelligence"
          );
        }


        return {
          summary:
            await summaryResponse.json(),

          watchlist:
            await watchlistResponse.json(),
        };
      })

      .then((data) => {
        setSummary(
          data.summary
        );

        setWatchlist(
          data.watchlist
        );

        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Covenant loading error:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  const filteredWatchlist =
    useMemo(() => {

      if (
        statusFilter
        === "ALL"
      ) {
        return watchlist;
      }


      return watchlist.filter(
        (borrower) =>
          borrower
            .covenant_pressure_status
          === statusFilter
      );

    }, [
      watchlist,
      statusFilter,
    ]);


  if (loading) {
    return (
      <section className="section-card">

        <div className="portfolio-state">
          Loading covenant pressure...
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


  return (
    <section className="section-card">

      <div className="covenant-portfolio-header">

        <div className="section-heading">

          <h2>
            Covenant Pressure
          </h2>

          <p>
            Portfolio-level covenant headroom,
            breaches and near-breach monitoring.
          </p>

        </div>


        <select
          value={statusFilter}
          onChange={(event) =>
            setStatusFilter(
              event.target.value
            )
          }
          className="filter-control"
        >

          <option value="ALL">
            All covenant states
          </option>

          <option value="BREACHED">
            Breached
          </option>

          <option value="NEAR_BREACH">
            Near Breach
          </option>

          <option value="TIGHT">
            Tight
          </option>

          <option value="HEALTHY">
            Healthy
          </option>

          <option value="INSUFFICIENT_DATA">
            Insufficient Data
          </option>

        </select>

      </div>


      <div className="covenant-portfolio-summary">

        <div>
          <span>
            Borrowers with Covenants
          </span>

          <strong>
            {
              summary
                .borrowers_with_covenants
            }
          </strong>
        </div>


        <div>
          <span>
            Under Pressure
          </span>

          <strong>
            {
              summary
                .borrowers_under_covenant_pressure
            }
          </strong>
        </div>


        <div>
          <span>
            Breached
          </span>

          <strong>
            {
              summary
                .borrowers_breached
            }
          </strong>
        </div>


        <div>
          <span>
            Near Breach
          </span>

          <strong>
            {
              summary
                .borrowers_near_breach
            }
          </strong>
        </div>


        <div>
          <span>
            Tight
          </span>

          <strong>
            {
              summary
                .borrowers_tight
            }
          </strong>
        </div>


        <div>
          <span>
            Healthy
          </span>

          <strong>
            {
              summary
                .borrowers_healthy
            }
          </strong>
        </div>

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
              filteredWatchlist.map(
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

                      <span
                        className={
                          `covenant-status-badge ${
                            borrower
                              .covenant_pressure_status
                              .toLowerCase()
                          }`
                        }
                      >
                        {
                          borrower
                            .covenant_pressure_status
                        }
                      </span>

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
  );
}


export default CovenantPressurePanel;