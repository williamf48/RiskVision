import { lazy } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import DashboardLayout from "./components/DashboardLayout";

import MonitoringPage from "./pages/MonitoringPage";
import PolicyPage from "./pages/PolicyPage";
const PortfolioPage = lazy(() => import("./pages/PortfolioPage"));
const BorrowersPage = lazy(() => import("./pages/BorrowersPage"));
const InterventionPage = lazy(() => import("./pages/InterventionPage"));
const AlertsPage = lazy(() => import("./pages/AlertsPage"));
const ReportsPage = lazy(() => import("./pages/ReportsPage"));
const BorrowerPage = lazy(() => import("./pages/BorrowerPage"));
const ValidationPage = lazy(() => import("./pages/ValidationPage"));

import "./App.css";
import "./professional.css";
import "./monitoring.css";


function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route element={<DashboardLayout />}>

          <Route
            path="/"
            element={<MonitoringPage key="monitoring" />}
          />
          <Route path="/cases" element={<MonitoringPage key="cases" view="cases" />} />
          <Route path="/covenants" element={<MonitoringPage key="covenants" view="covenants" />} />
          <Route path="/data-quality" element={<MonitoringPage key="quality" view="quality" />} />
          <Route path="/policy" element={<PolicyPage />} />

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

          <Route
            path="/validation"
            element={<ValidationPage />}
          />

        </Route>

      </Routes>

    </BrowserRouter>
  );
}


export default App;
