import { useEffect, useState } from "react";
import { Link } from "react-router-dom";


function TopRiskAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {

    fetch(
      "http://127.0.0.1:8000/intervention_watchlist"
    )
      .then((response) => {

        if (!response.ok) {
          throw new Error(
            "Failed to load intervention accounts"
          );
        }

        return response.json();
      })

      .then((data) => {

        const assessableAccounts = data
          .filter(
            (account) =>
              account.intervention_priority
              !== "INSUFFICIENT_DATA"
          )
          .slice(0, 10);

        setAccounts(
          assessableAccounts
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Error loading intervention accounts:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  return (
    <div className="risk-table-card">

      <h2>
        Top Intervention Accounts
      </h2>


      {loading ? (

        <p>
          Loading intervention accounts...
        </p>

      ) : error ? (

        <p>
          Unable to load intervention accounts.
        </p>

      ) : accounts.length === 0 ? (

        <p>
          No borrowers currently have sufficient
          historical data for intervention ranking.
        </p>

      ) : (

        <table className="risk-table">

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
                Critical
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

            {accounts.map(
              (account) => (

                <tr
                  key={
                    account.borrower_id
                  }
                >

                  <td>
                    {
                      account.portfolio_rank
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
                        account.borrower_name
                      }

                    </Link>

                  </td>


                  <td>

                    <strong>
                      {
                        account
                          .intervention_priority
                      }
                    </strong>

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


export default TopRiskAccounts;