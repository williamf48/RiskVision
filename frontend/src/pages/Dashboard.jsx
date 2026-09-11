import Header from "../components/Header";
import MainDashboard from "../components/MainDashboard";


function Dashboard() {
  return (
    <div className="page">

      <Header
        title="Risk Intelligence Dashboard"
        subtitle="Portfolio deterioration, intervention priorities and emerging borrower risk."
      />

      <MainDashboard />

    </div>
  );
}


export default Dashboard;