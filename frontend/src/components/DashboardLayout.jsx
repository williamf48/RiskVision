import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";


function DashboardLayout() {
  return (
    <div className="app-shell">

      <Sidebar />

      <main className="app-content">
        <Outlet />
      </main>

    </div>
  );
}


export default DashboardLayout;