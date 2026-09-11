import {
  NavLink,
} from "react-router-dom";


function Sidebar() {

  const navItems = [

    {
      label: "Dashboard",
      path: "/",
      end: true,
    },

    {
      label: "Portfolio",
      path: "/portfolio",
    },

    {
      label: "Borrowers",
      path: "/borrowers",
    },

    {
      label: "Interventions",
      path: "/interventions",
    },

    {
      label: "Alerts",
      path: "/alerts",
    },

    {
      label: "Reports",
      path: "/reports",
    },

    {
      label: "Validation",
      path: "/validation",
    },

  ];


  return (
    <aside className="sidebar">

      <div className="sidebar-brand">

        <div className="brand-mark">
          RV
        </div>

        <div>

          <h2>
            RiskVision
          </h2>

          <span>
            Credit Intelligence
          </span>

        </div>

      </div>


      <nav className="sidebar-nav">

        {
          navItems.map(
            (item) => (

              <NavLink

                key={
                  item.path
                }

                to={
                  item.path
                }

                end={
                  item.end
                }

                className={({
                  isActive,
                }) =>

                  isActive
                    ? "sidebar-link active"
                    : "sidebar-link"

                }

              >
                {
                  item.label
                }
              </NavLink>

            )
          )
        }

      </nav>


      <div className="sidebar-footer">

        <span>
          Historical Intelligence Engine
        </span>

      </div>

    </aside>
  );
}


export default Sidebar;