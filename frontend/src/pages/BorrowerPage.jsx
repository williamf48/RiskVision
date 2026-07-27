import React from "react";

function BorrowerPage() {
  const borrower = {
    borrower_name: "ABC Infra Ltd",
    sector: "Infrastructure",
    exposure: "₹48 Cr",
    dpd: 45,
    dscr: 0.8,
    revenue_decline: "25%",
    cash_flow: "Negative",
    restructured: "Yes",
    risk_score: 92,
    classification: "High Risk",
    alerts: [
      "DPD > 30",
      "DSCR < 1",
      "Revenue Decline > 20%",
      "Negative Cash Flow",
      "Loan Restructured",
    ],
  };

  return (
    <div
      style={{
        padding: "30px",
        color: "white",
        backgroundColor: "#0f172a",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ marginBottom: "25px" }}>Borrower Risk Profile</h1>

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
          <strong>Name:</strong> {borrower.borrower_name}
        </p>
        <p>
          <strong>Sector:</strong> {borrower.sector}
        </p>
        <p>
          <strong>Total Exposure:</strong> {borrower.exposure}
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
          <strong>Revenue Decline:</strong> {borrower.revenue_decline}
        </p>
        <p>
          <strong>Cash Flow:</strong> {borrower.cash_flow}
        </p>
        <p>
          <strong>Restructured:</strong> {borrower.restructured}
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
          <strong>Risk Score:</strong> {borrower.risk_score}
        </p>

        <p>
          <strong>Classification:</strong>{" "}
          <span
            style={{
              color: "#ef4444",
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
        <h2>Triggered Alerts</h2>
        <br />

        <ul>
          {borrower.alerts.map((alert, index) => (
            <li key={index} style={{ marginBottom: "10px" }}>
              {alert}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default BorrowerPage;