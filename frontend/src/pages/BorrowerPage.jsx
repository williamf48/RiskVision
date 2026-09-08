import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";


const metricLabels = {
  DSCR: "DSCR",
  BOUNCE_RATE: "Bounce Rate",
  RECEIVABLE_DAYS: "Receivable Days",
  DEBT_EBITDA: "Debt / EBITDA",
};


function BorrowerPage() {
  const { id } = useParams();

  const [borrower, setBorrower] = useState(null);
  const [deterioration, setDeterioration] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      fetch(`http://127.0.0.1:8000/borrowers/${id}`),
      fetch(`http://127.0.0.1:8000/borrowers/${id}/deterioration`),
    ])
      .then(async ([borrowerResponse, deteriorationResponse]) => {

        if (!borrowerResponse.ok) {
          throw new Error("Borrower not found");
        }

        if (!deteriorationResponse.ok) {
          throw new Error(
            "Unable to load deterioration analysis"
          );
        }

        const borrowerData = await borrowerResponse.json();

        const deteriorationData =
          await deteriorationResponse.json();

        return {
          borrowerData,
          deteriorationData,
        };
      })

      .then(({ borrowerData, deteriorationData }) => {

        setBorrower(borrowerData);

        setDeterioration(
          deteriorationData
        );

        setLoading(false);
      })

      .catch((error) => {

        console.error(
          "Error loading borrower:",
          error
        );

        setError(error.message);

        setLoading(false);
      });

  }, [id]);


  if (loading) {
    return (
      <div
        style={{
          padding: "30px",
          color: "white",
          backgroundColor: "#0f172a",
          minHeight: "100vh",
        }}
      >
        <h2>Loading borrower...</h2>
      </div>
    );
  }


  if (error || !borrower) {
    return (
      <div
        style={{
          padding: "30px",
          color: "white",
          backgroundColor: "#0f172a",
          minHeight: "100vh",
        }}
      >
        <h2>Unable to load borrower</h2>

        <p>{error}</p>

        <br />

        <Link to="/">
          Return to Dashboard
        </Link>
      </div>
    );
  }


  return (
    <div
      style={{
        padding: "30px",
        color: "white",
        backgroundColor: "#0f172a",
        minHeight: "100vh",
      }}
    >

      <Link
        to="/"
        style={{
          color: "#60a5fa",
          textDecoration: "none",
        }}
      >
        ← Back to Dashboard
      </Link>


      <h1
        style={{
          marginTop: "20px",
          marginBottom: "25px",
        }}
      >
        Borrower Risk Profile
      </h1>


      {/* ================================================= */}
      {/* BORROWER INFORMATION */}
      {/* ================================================= */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >

        <h2>Borrower Information</h2>

        <br />

        <p>
          <strong>Borrower ID:</strong>{" "}
          {borrower.borrower_id}
        </p>

        <p>
          <strong>Name:</strong>{" "}
          {borrower.borrower_name}
        </p>

        <p>
          <strong>Sector:</strong>{" "}
          {borrower.sector}
        </p>

        <p>
          <strong>Loan Amount:</strong>{" "}
          {borrower.loan_amount}
        </p>

      </div>


      {/* ================================================= */}
      {/* FINANCIAL METRICS */}
      {/* ================================================= */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >

        <h2>Financial Metrics</h2>

        <br />

        <p>
          <strong>DPD:</strong>{" "}
          {borrower.dpd}
        </p>

        <p>
          <strong>DSCR:</strong>{" "}
          {borrower.dscr}
        </p>

        <p>
          <strong>Revenue Decline:</strong>{" "}
          {borrower.revenue_decline}%
        </p>

        <p>
          <strong>Cash Flow:</strong>{" "}
          {borrower.cash_flow}
        </p>

        <p>
          <strong>Restructured:</strong>{" "}
          {borrower.restructured
            ? "Yes"
            : "No"}
        </p>

      </div>


      {/* ================================================= */}
      {/* CURRENT RISK ASSESSMENT */}
      {/* ================================================= */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >

        <h2>Current Risk Assessment</h2>

        <br />

        <p>
          <strong>Risk Score:</strong>{" "}
          {borrower.score}
        </p>

        <p>
          <strong>Classification:</strong>{" "}

          <span
            style={{
              fontWeight: "bold",
            }}
          >
            {borrower.classification}
          </span>

        </p>

      </div>


      {/* ================================================= */}
      {/* DETERIORATION INTELLIGENCE */}
      {/* ================================================= */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >

        <h2>Deterioration Intelligence</h2>

        <br />

        {!deterioration ? (

          <p>
            Deterioration analysis unavailable.
          </p>

        ) : deterioration.metrics_analyzed === 0 ? (

          <div>

            <p>
              <strong>Status:</strong>{" "}
              Insufficient historical data
            </p>

            <p>
              Historical signals available: 0 /{" "}
              {deterioration.configured_metrics}
            </p>

            <p>
              RiskVision requires multiple historical
              observations before trajectory deterioration
              can be assessed.
            </p>

          </div>

        ) : (

          <div>

            <p>
              <strong>Signals Analyzed:</strong>{" "}
              {deterioration.metrics_analyzed}
            </p>

            <p>
              <strong>Deteriorating Signals:</strong>{" "}
              {deterioration.deteriorating_signals}
            </p>

            <p>
              <strong>
                Persistent Deterioration Signals:
              </strong>{" "}
              {
                deterioration
                  .persistent_deterioration_signals
              }
            </p>

            <p>
              <strong>
                Cross-Signal Convergence:
              </strong>{" "}
              {
                deterioration
                  .convergence_percentage
              }
              %
            </p>


            <br />

            <h3>Signal Analysis</h3>

            <br />


            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
              }}
            >

              <thead>

                <tr>

                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px",
                    }}
                  >
                    Signal
                  </th>

                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px",
                    }}
                  >
                    Current
                  </th>

                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px",
                    }}
                  >
                    Latest Change
                  </th>

                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px",
                    }}
                  >
                    Direction
                  </th>

                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px",
                    }}
                  >
                    Persistence
                  </th>

                </tr>

              </thead>


              <tbody>

                {deterioration.metric_results.map(
                  (metric) => (

                    <tr
                      key={metric.metric_code}
                    >

                      <td
                        style={{
                          padding: "10px",
                        }}
                      >
                        {
                          metricLabels[
                            metric.metric_code
                          ] || metric.metric_code
                        }
                      </td>


                      <td
                        style={{
                          padding: "10px",
                        }}
                      >
                        {metric.current_value}
                      </td>


                      <td
                        style={{
                          padding: "10px",
                        }}
                      >
                        {
                          metric.percentage_change
                        }
                        %
                      </td>


                      <td
                        style={{
                          padding: "10px",
                          fontWeight: "bold",
                        }}
                      >
                        {metric.direction}
                      </td>


                      <td
                        style={{
                          padding: "10px",
                        }}
                      >
                        {metric.persistence}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </div>


      {/* ================================================= */}
      {/* ACTIVE ALERTS */}
      {/* ================================================= */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
        }}
      >

        <h2>Active Alerts</h2>

        <br />

        {borrower.alerts.length === 0 ? (

          <p>
            No active alerts.
          </p>

        ) : (

          <ul>

            {borrower.alerts.map(
              (alert) => (

                <li
                  key={alert.alert_id}
                  style={{
                    marginBottom: "15px",
                  }}
                >

                  <strong>
                    {alert.alert_type}
                  </strong>

                  {" — "}

                  {alert.severity}

                </li>

              )
            )}

          </ul>

        )}

      </div>

    </div>
  );
}


export default BorrowerPage;