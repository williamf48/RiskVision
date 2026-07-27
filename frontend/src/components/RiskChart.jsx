import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'

const data = [
  {
    borrower: 'ABC Infra',
    risk: 92
  },
  {
    borrower: 'Zenith',
    risk: 84
  },
  {
    borrower: 'Nova',
    risk: 77
  },
  {
    borrower: 'Delta',
    risk: 69
  }
]

function RiskChart() {
  return (
    <div className="chart-card">
      <h2>Borrower Risk Distribution</h2>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey="borrower" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="risk" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default RiskChart