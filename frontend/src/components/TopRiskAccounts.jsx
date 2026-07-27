import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function TopRiskAccounts() {
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/top_risk_accounts")
      .then((response) => response.json())
      .then((data) => setAccounts(data))
      .catch((error) =>
        console.error("Error loading top risk accounts:", error)
      );
  }, []);

  return (
    <div className="risk-table-card">
      <h2>Top Risk Accounts</h2>

      <table className="risk-table">
        <thead>
          <tr>
            <th>Borrower</th>
            <th>Risk Score</th>
            <th>Classification</th>
          </tr>
        </thead>

        <tbody>
          {accounts.map((account, index) => (
            <tr key={index}>
              <td>
                <Link
                  to={`/borrower/${index + 1}`}
                  className="borrower-link"
                >
                  {account.borrower_name}
                </Link>
              </td>

              <td>{account.score}</td>

              <td>{account.classification}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TopRiskAccounts;