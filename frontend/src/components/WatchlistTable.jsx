import { useEffect, useState } from "react";
import { Link } from "react-router-dom";


function WatchlistTable() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {

    fetch(
      "http://127.0.0.1:8000/intervention_watchlist"
    )
      .then((response) => {

        if (!response.ok) {
          throw new Error(
            "Unable to load intervention watchlist"
          );
        }

        return response.json();
      })

      .then((data) => {

        const actionableBorrowers = data.filter(
          (borrower) =>
            borrower.intervention_priority
            !== "INSUFFICIENT_DATA"
        );

        setWatchlist(
          actionableBorrowers
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Error loading intervention watchlist:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  return (
    <div className="watchlist-card">

      <h2>
        Intervention Watchlist
      </h2>


      {loading ? (

        <p>
          Loading intervention priorities...
        </p>

      ) : error ? (

        <p>
          Unable to load intervention watchlist.
        </p>

      ) : watchlist.length === 0 ? (

        <p>
          No borrowers currently have sufficient
          historical data for prioritization.
        </p>

      ) : (

        <table className="watchlist-table">

          <thead>

            <tr>

              <th>
                Rank
              </th>

              <th>
                Borrower
              </th>

              <th>
                Priority
              </th>

              <th>
                Deteriorating
              </th>

              <th>
                Convergence
              </th>

            </tr>

          </thead>


          <tbody>

            {watchlist.map(
              (borrower) => (

                <tr
                  key={
                    borrower.borrower_id
                  }
                >

                  <td>
                    {
                      borrower.portfolio_rank
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
                        borrower.borrower_name
                      }

                    </Link>

                  </td>


                  <td>

                    <strong>
                      {
                        borrower
                          .intervention_priority
                      }
                    </strong>

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
                        .convergence_percentage
                    }
                    %

                  </td>

                </tr>

              )
            )}

          </tbody>

        </table>

      )}

    </div>
  );
}


export default WatchlistTable;