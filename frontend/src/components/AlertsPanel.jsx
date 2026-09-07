import { useEffect, useState } from "react";

function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/alerts")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load alerts");
        }

        return response.json();
      })
      .then((data) => setAlerts(data))
      .catch((error) =>
        console.error("Error loading alerts:", error)
      );
  }, []);

  return (
    <div className="alerts-panel">
      <h2>Risk Alerts</h2>

      {alerts.slice(0, 10).map((alert) => (
        <div
          key={alert.alert_id}
          className="alert-item"
        >
          <strong>{alert.borrower_name}</strong>

          <p>{alert.alert_type}</p>

          <span>
            {alert.severity}
          </span>
        </div>
      ))}
    </div>
  );
}

export default AlertsPanel;