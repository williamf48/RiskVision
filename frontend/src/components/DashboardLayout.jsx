import Sidebar from './Sidebar'
import Header from './Header'
import MainDashboard from './MainDashboard'

function DashboardLayout() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <div className="main-section">
        <Header />
        <MainDashboard />
      </div>
    </div>
  )
}

export default DashboardLayout