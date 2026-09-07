import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function RiskChart({ summary }) {

  if (!summary) {
    return (
      <div className="chart-card">
        <h2>Borrower Risk Distribution</h2>
        <p>Loading...</p>
      </div>
    );
  }

  const data = [
    {
      classification: "Low Risk",
      borrowers: summary.low_risk,
    },
    {
      classification: "Watchlist",
      borrowers: summary.watchlist,
    },
    {
      classification: "High Risk",
      borrowers: summary.high_risk,
    },
  ];

  return (
    <div className="chart-card">
      <h2>Borrower Risk Distribution</h2>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey="classification" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar
            dataKey="borrowers"
            fill="#3b82f6"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default RiskChart;