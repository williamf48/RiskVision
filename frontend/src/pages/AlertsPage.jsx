import { apiFetch } from "../utils/api";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import Header from "../components/Header";


function AlertsPage() {
  const [alerts, setAlerts] = useState([]);

  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const [expandedId, setExpandedId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  useEffect(() => {
    apiFetch("/alerts")

      .then((response) => {
        if (!response.ok) {
          throw new Error(
            "Unable to load alerts"
          );
        }

        return response.json();
      })

      .then((data) => {
        setAlerts(data);
        setLoading(false);
      })

      .catch((error) => {
        console.error(
          "Alert loading error:",
          error
        );

        setError(error.message);
        setLoading(false);
      });

  }, []);


  const alertTypes = useMemo(() => {
    return [
      ...new Set(
        alerts.map(
          (alert) =>
            alert.alert_type
        )
      ),
    ].sort();

  }, [alerts]);


  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {

      const matchesSearch =
        alert.borrower_name
          .toLowerCase()
          .includes(
            search
              .trim()
              .toLowerCase()
          );


      const matchesSeverity =
        severityFilter === "ALL"
        ||
        alert.severity === severityFilter;


      const matchesType =
        typeFilter === "ALL"
        ||
        alert.alert_type === typeFilter;


      return (
        matchesSearch
        &&
        matchesSeverity
        &&
        matchesType
      );

    });

  }, [
    alerts,
    search,
    severityFilter,
    typeFilter,
  ]);


  function resetFilters() {
    setSearch("");
    setSeverityFilter("ALL");
    setTypeFilter("ALL");
  }


  return (
    <div className="page">

      <Header
        title="Alerts"
        subtitle="Borrower monitoring alerts and events requiring analyst review."
      />


      <section className="section-card">

        <div className="section-heading">

          <h2>
            Alert Feed
          </h2>

          <p>
            Search, filter and investigate borrower monitoring events.
          </p>

        </div>


        <div className="alert-filter-bar">

          <input
            type="text"
            placeholder="Search borrower..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            className="search-control"
          />


          <select
            value={severityFilter}
            onChange={(event) =>
              setSeverityFilter(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All severities
            </option>

            <option value="HIGH">
              High
            </option>

            <option value="MEDIUM">
              Medium
            </option>

            <option value="LOW">
              Low
            </option>

          </select>


          <select
            value={typeFilter}
            onChange={(event) =>
              setTypeFilter(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All alert types
            </option>

            {alertTypes.map(
              (type) => (

                <option
                  key={type}
                  value={type}
                >
                  {type}
                </option>

              )
            )}

          </select>


          <button
            className="secondary-button"
            onClick={resetFilters}
          >
            Reset
          </button>

        </div>


        <div className="portfolio-result-count">
          Showing{" "}
          <strong>
            {filteredAlerts.length}
          </strong>
          {" of "}
          <strong>
            {alerts.length}
          </strong>
          {" alerts"}
        </div>


        {loading ? (

          <div className="portfolio-state">
            Loading alerts...
          </div>

        ) : error ? (

          <div className="portfolio-state error">
            {error}
          </div>

        ) : filteredAlerts.length === 0 ? (

          <div className="portfolio-state">
            No alerts match the selected filters.
          </div>

        ) : (

          <div className="interactive-alert-list">

            {filteredAlerts.map(
              (alert) => {

                const expanded =
                  expandedId
                  === alert.alert_id;


                return (
                  <div
                    key={alert.alert_id}
                    className={
                      expanded
                        ? "interactive-alert-card expanded"
                        : "interactive-alert-card"
                    }
                  >

                    <div className="interactive-alert-header">

                      <div>

                        <Link
                          to={
                            `/borrower/${alert.borrower_id}`
                          }
                          className="borrower-link"
                        >
                          {alert.borrower_name}
                        </Link>

                        <h3>
                          {alert.alert_type}
                        </h3>

                      </div>


                      <span
                        className={
                          `severity-badge ${
                            alert
                              .severity
                              .toLowerCase()
                          }`
                        }
                      >
                        {alert.severity}
                      </span>

                    </div>


                    <div className="interactive-alert-meta">

                      <span>
                        Alert #{alert.alert_id}
                      </span>

                      <span>
                        Borrower ID {alert.borrower_id}
                      </span>

                      <span>
                        {
                          new Date(
                            alert.created_at
                          )
                          .toLocaleString()
                        }
                      </span>

                    </div>


                    <div className="card-actions">

                      <button
                        className="secondary-button"
                        onClick={() =>
                          setExpandedId(
                            expanded
                              ? null
                              : alert.alert_id
                          )
                        }
                      >
                        {
                          expanded
                            ? "Hide details"
                            : "View details"
                        }
                      </button>


                      <Link
                        to={
                          `/borrower/${alert.borrower_id}`
                        }
                        className="primary-button"
                      >
                        Open Borrower
                      </Link>

                    </div>


                    {expanded && (

                      <div className="alert-expanded-content">

                        <div>

                          <span>
                            Alert Type
                          </span>

                          <strong>
                            {alert.alert_type}
                          </strong>

                        </div>


                        <div>

                          <span>
                            Severity
                          </span>

                          <strong>
                            {alert.severity}
                          </strong>

                        </div>


                        <div>

                          <span>
                            Borrower
                          </span>

                          <strong>
                            {alert.borrower_name}
                          </strong>

                        </div>


                        <div>

                          <span>
                            Created
                          </span>

                          <strong>
                            {
                              new Date(
                                alert.created_at
                              )
                              .toLocaleString()
                            }
                          </strong>

                        </div>

                      </div>

                    )}

                  </div>
                );

              }
            )}

          </div>

        )}

      </section>

    </div>
  );
}


export default AlertsPage;