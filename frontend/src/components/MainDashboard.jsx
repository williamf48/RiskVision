import { useEffect, useState } from "react";

import TopRiskAccounts from "./TopRiskAccounts";
import AlertsPanel from "./AlertsPanel";
import WatchlistTable from "./WatchlistTable";
import RiskChart from "./RiskChart";

function MainDashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/portfolio_summary")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load portfolio summary");
        }

        return response.json();
      })
      .then((data) => {
        setSummary(data);
      })
      .catch((error) => {
        console.error("Error loading portfolio summary:", error);
        setError(error.message);
      });
  }, []);

  return (
    <div className="main-dashboard">

      <div className="card">
        <h2>Total Exposure</h2>

        {error ? (
          <p>Unable to load exposure</p>
        ) : summary ? (
          <h1>
            ₹
            {Number(summary.total_exposure).toLocaleString("en-IN")} Cr
          </h1>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      <RiskChart summary={summary} />

      <TopRiskAccounts />

      <AlertsPanel />

      <WatchlistTable />

    </div>
  );
}

export default MainDashboard;