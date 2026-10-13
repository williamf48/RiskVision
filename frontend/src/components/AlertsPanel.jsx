import { apiFetch } from "../utils/api";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";


function AlertsPanel() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {

    apiFetch(
      "/intervention_watchlist"
    )
      .then((response) => {

        if (!response.ok) {
          throw new Error(
            "Failed to load intervention priorities"
          );
        }

        return response.json();
      })

      .then((data) => {

        /*
        Only show borrowers requiring intervention.

        LOW and INSUFFICIENT_DATA are excluded because
        this panel is intended to explain the accounts
        currently requiring analyst attention.
        */

        const actionableAccounts = data.filter(
          (account) =>
            account.intervention_priority === "URGENT" ||
            account.intervention_priority === "HIGH" ||
            account.intervention_priority === "MEDIUM"
        );

        setAccounts(
          actionableAccounts
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Error loading priority drivers:",
          error
        );

        setError(
          error.message
        );

        setLoading(false);
      });

  }, []);


  return (
    <div className="alerts-panel">

      <h2>
        Priority Drivers
      </h2>


      {loading ? (

        <p>
          Loading priority drivers...
        </p>

      ) : error ? (

        <p>
          Unable to load priority drivers.
        </p>

      ) : accounts.length === 0 ? (

        <p>
          No borrowers currently require intervention.
        </p>

      ) : (

        accounts.map(
          (account) => (

            <div
              key={
                account.borrower_id
              }
              className="alert-item"
            >

              <Link
                to={
                  `/borrower/${account.borrower_id}`
                }
                className="borrower-link"
              >

                <strong>
                  {
                    account.borrower_name
                  }
                </strong>

              </Link>


              <p>
                Priority:{" "}
                <strong>
                  {
                    account.intervention_priority
                  }
                </strong>
              </p>


              {
                account.explanations
                  .slice(0, 2)
                  .map(
                    (explanation, index) => (

                      <p
                        key={
                          `${account.borrower_id}-reason-${index}`
                        }
                      >
                        • {explanation}
                      </p>

                    )
                  )
              }


              <span>
                {
                  account.deteriorating_signals
                }
                /
                {
                  account.metrics_analyzed
                }
                {" deteriorating | "}
                {
                  account.convergence_percentage
                }
                % convergence
              </span>

            </div>

          )
        )

      )}

    </div>
  );
}


export default AlertsPanel;