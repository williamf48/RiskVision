import TopRiskAccounts from './TopRiskAccounts'
import AlertsPanel from './AlertsPanel'
import WatchlistTable from './WatchlistTable'
import RiskChart from './RiskChart'

function MainDashboard() {
  return (
    <div className="main-dashboard">
      <div className="card">Total Exposure</div>

      <RiskChart />

      <TopRiskAccounts />

      <AlertsPanel />

      <WatchlistTable />
    </div>
  )
}

export default MainDashboard