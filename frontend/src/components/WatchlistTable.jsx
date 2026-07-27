import { useEffect, useState } from "react";

function WatchlistTable() {
  const [watchlist, setWatchlist] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/watchlist")
      .then((response) => response.json())
      .then((data) => setWatchlist(data))
      .catch((error) =>
        console.error("Error loading watchlist:", error)
      );
  }, []);

  return (
    <div className="watchlist-card">
      <h2>Watchlist Monitoring</h2>

      <table className="watchlist-table">
        <thead>
          <tr>
            <th>Borrower</th>
            <th>Risk Score</th>
            <th>Classification</th>
          </tr>
        </thead>

        <tbody>
          {watchlist.map((item, index) => (
            <tr key={index}>
              <td>{item.borrower_name}</td>
              <td>{item.score}</td>
              <td>{item.classification}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default WatchlistTable;