import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import Header from "../components/Header";


function BorrowersPage() {

  const [borrowers, setBorrowers] = useState([]);
  const [interventions, setInterventions] = useState([]);

  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("ALL");


  useEffect(() => {

    Promise.all([
      fetch("http://127.0.0.1:8000/borrowers"),
      fetch("http://127.0.0.1:8000/intervention_watchlist"),
    ])

      .then(async ([borrowersResponse, interventionsResponse]) => {

        return {
          borrowers:
            await borrowersResponse.json(),

          interventions:
            await interventionsResponse.json(),
        };
      })

      .then((data) => {

        setBorrowers(
          data.borrowers
        );

        setInterventions(
          data.interventions
        );
      });

  }, []);


  const interventionMap = useMemo(() => {

    const map = {};

    interventions.forEach(
      (item) => {

        map[item.borrower_id] = item;

      }
    );

    return map;

  }, [interventions]);


  const sectors = useMemo(() => {

    return [
      ...new Set(
        borrowers
          .map(
            (borrower) =>
              borrower.sector
          )
          .filter(Boolean)
      ),
    ].sort();

  }, [borrowers]);


  const filteredBorrowers = useMemo(() => {

    return borrowers.filter(
      (borrower) => {

        const matchesSearch =
          borrower.borrower_name
            ?.toLowerCase()
            .includes(
              search.toLowerCase()
            );


        const matchesSector =
          sector === "ALL"
          ||
          borrower.sector === sector;


        return (
          matchesSearch &&
          matchesSector
        );

      }
    );

  }, [
    borrowers,
    search,
    sector,
  ]);


  return (
    <div className="page">

      <Header
        title="Borrower Directory"
        subtitle="Search the lending portfolio and open borrower-level risk intelligence."
      />


      <section className="section-card">

        <div className="section-toolbar">

          <input
            type="text"
            placeholder="Search borrower..."
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            className="search-control"
          />


          <select
            value={sector}
            onChange={(event) =>
              setSector(
                event.target.value
              )
            }
            className="filter-control"
          >

            <option value="ALL">
              All sectors
            </option>

            {sectors.map(
              (sectorName) => (

                <option
                  key={sectorName}
                  value={sectorName}
                >
                  {sectorName}
                </option>

              )
            )}

          </select>

        </div>


        <div className="table-scroll">

          <table className="data-table">

            <thead>
              <tr>
                <th>Borrower</th>
                <th>Sector</th>
                <th>Exposure</th>
                <th>Intervention Priority</th>
                <th>Coverage</th>
              </tr>
            </thead>


            <tbody>

              {filteredBorrowers.map(
                (borrower) => {

                  const intelligence =
                    interventionMap[
                      borrower.id
                    ];


                  return (
                    <tr
                      key={
                        borrower.id
                      }
                    >

                      <td>

                        <Link
                          to={
                            `/borrower/${borrower.id}`
                          }
                          className="borrower-link"
                        >
                          {
                            borrower
                              .borrower_name
                          }
                        </Link>

                      </td>


                      <td>
                        {
                          borrower.sector
                          || "—"
                        }
                      </td>


                      <td>
                        {
                          borrower.loan_amount
                          ?? "—"
                        }
                      </td>


                      <td>

                        {intelligence ? (

                          <span
                            className={
                              `priority-badge ${
                                intelligence
                                  .intervention_priority
                                  .toLowerCase()
                              }`
                            }
                          >
                            {
                              intelligence
                                .intervention_priority
                            }
                          </span>

                        ) : "—"}

                      </td>


                      <td>

                        {
                          intelligence
                            ?.metrics_analyzed
                          > 0
                            ? "Sufficient History"
                            : "Insufficient History"
                        }

                      </td>

                    </tr>
                  );

                }
              )}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}


export default BorrowersPage;