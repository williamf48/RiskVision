import { useEffect, useState } from "react";

function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/alerts")
      .then((response) => response.json())
      .then((data) => setAlerts(data))
      .catch((error) => console.error("Error loading alerts:", error));
  }, []);

  return (
    <div className="alerts-card">
      <h2>Risk Alerts</h2>

      {alerts.length === 0 ? (
        <p>No alerts available</p>
      ) : (
        alerts.slice(0, 10).map((alert, index) => (
          <div key={index} className="alert-item">
            <span
              className={`severity ${
                alert.severity
                  ? alert.severity.toLowerCase()
                  : "medium"
              }`}
            >
              {alert.severity}
            </span>

            <p>
              <strong>{alert.borrower_name}</strong>
            </p>

            <p>{alert.alert_type}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default AlertsPanel;