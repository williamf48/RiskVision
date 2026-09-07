import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

function BorrowerPage() {
  const { id } = useParams();

  const [borrower, setBorrower] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(`http://127.0.0.1:8000/borrowers/${id}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Borrower not found");
        }

        return response.json();
      })
      .then((data) => {
        setBorrower(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error loading borrower:", error);
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

        <Link to="/">Return to Dashboard</Link>
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

      {/* Borrower Information */}

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
          <strong>Borrower ID:</strong> {borrower.borrower_id}
        </p>

        <p>
          <strong>Name:</strong> {borrower.borrower_name}
        </p>

        <p>
          <strong>Sector:</strong> {borrower.sector}
        </p>

        <p>
          <strong>Loan Amount:</strong> {borrower.loan_amount}
        </p>
      </div>

      {/* Financial Metrics */}

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
          <strong>DPD:</strong> {borrower.dpd}
        </p>

        <p>
          <strong>DSCR:</strong> {borrower.dscr}
        </p>

        <p>
          <strong>Revenue Decline:</strong>{" "}
          {borrower.revenue_decline}%
        </p>

        <p>
          <strong>Cash Flow:</strong> {borrower.cash_flow}
        </p>

        <p>
          <strong>Restructured:</strong>{" "}
          {borrower.restructured ? "Yes" : "No"}
        </p>
      </div>

      {/* Risk Assessment */}

      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >
        <h2>Risk Assessment</h2>

        <br />

        <p>
          <strong>Risk Score:</strong> {borrower.score}
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

      {/* Active Alerts */}

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
          <p>No active alerts.</p>
        ) : (
          <ul>
            {borrower.alerts.map((alert) => (
              <li
                key={alert.alert_id}
                style={{
                  marginBottom: "15px",
                }}
              >
                <strong>{alert.alert_type}</strong>

                {" — "}

                {alert.severity}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default BorrowerPage;