import { BrowserRouter, Routes, Route } from "react-router-dom";

import DashboardLayout from "./components/DashboardLayout";

import Dashboard from "./pages/Dashboard";
import PortfolioPage from "./pages/PortfolioPage";
import BorrowersPage from "./pages/BorrowersPage";
import InterventionPage from "./pages/InterventionPage";
import AlertsPage from "./pages/AlertsPage";
import ReportsPage from "./pages/ReportsPage";
import BorrowerPage from "./pages/BorrowerPage";

import "./App.css";


function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route element={<DashboardLayout />}>

          <Route
            path="/"
            element={<Dashboard />}
          />

          <Route
            path="/portfolio"
            element={<PortfolioPage />}
          />

          <Route
            path="/borrowers"
            element={<BorrowersPage />}
          />

          <Route
            path="/borrower/:id"
            element={<BorrowerPage />}
          />

          <Route
            path="/interventions"
            element={<InterventionPage />}
          />

          <Route
            path="/alerts"
            element={<AlertsPage />}
          />

          <Route
            path="/reports"
            element={<ReportsPage />}
          />

        </Route>

      </Routes>

    </BrowserRouter>
  );
}


export default App;