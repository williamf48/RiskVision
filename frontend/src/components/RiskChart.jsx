import { apiFetch } from "../utils/api";
import { useEffect, useState } from "react";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


function RiskChart() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);


  useEffect(() => {

    apiFetch(
      "/intervention_summary"
    )
      .then((response) => {

        if (!response.ok) {
          throw new Error(
            "Unable to load intervention summary"
          );
        }

        return response.json();
      })

      .then((data) => {

        setSummary(data);

      })

      .catch((error) => {

        console.error(
          "Error loading intervention summary:",
          error
        );

        setError(error.message);

      });

  }, []);


  if (error) {
    return (
      <div className="chart-card">

        <h2>
          Intervention Priority Distribution
        </h2>

        <p>
          Unable to load intervention summary.
        </p>

      </div>
    );
  }


  if (!summary) {
    return (
      <div className="chart-card">

        <h2>
          Intervention Priority Distribution
        </h2>

        <p>
          Loading...
        </p>

      </div>
    );
  }


  const data = [

    {
      priority: "Urgent",
      borrowers: summary.urgent,
    },

    {
      priority: "High",
      borrowers: summary.high,
    },

    {
      priority: "Medium",
      borrowers: summary.medium,
    },

    {
      priority: "Low",
      borrowers: summary.low,
    },

  ];


  return (
    <div className="chart-card">

      <h2>
        Intervention Priority Distribution
      </h2>


      <ResponsiveContainer
        width="100%"
        height={300}
      >

        <BarChart data={data}>

          <XAxis
            dataKey="priority"
          />

          <YAxis
            allowDecimals={false}
          />

          <Tooltip />

          <Bar
            dataKey="borrowers"
            fill="#3b82f6"
          />

        </BarChart>

      </ResponsiveContainer>


      <div
        style={{
          marginTop: "12px",
          textAlign: "center",
        }}
      >

        <p>
          <strong>
            Historically Assessable:
          </strong>{" "}
          {
            summary
              .historically_assessable_borrowers
          }
          {" / "}
          {summary.total_borrowers}
        </p>


        <p>
          <strong>
            Insufficient Historical Data:
          </strong>{" "}
          {summary.insufficient_data}
        </p>


        <p>
          <strong>
            Actionable Borrowers:
          </strong>{" "}
          {summary.actionable_borrowers}
        </p>

      </div>

    </div>
  );
}


export default RiskChart;