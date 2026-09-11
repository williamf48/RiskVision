import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


from read_models import (
    get_borrower_detail,
    get_borrower_history_payload,
    get_borrower_identity,
    get_portfolio_summary,
    list_alerts,
    list_borrowers,
    list_legacy_watchlist,
    list_risk_scores,
    list_top_risk_accounts,
)


class ReadModelTests(unittest.TestCase):

    def test_borrower_directory(self):
        borrowers = list_borrowers()
        self.assertEqual(len(borrowers), 25)
        self.assertEqual(borrowers[0]["id"], 47)

    def test_identity_and_detail(self):
        identity = get_borrower_identity(65)
        detail = get_borrower_detail(65)

        self.assertIsNotNone(identity)
        self.assertIsNotNone(detail)
        self.assertEqual(identity["borrower_name"], "Falcon Realty Ltd")
        self.assertEqual(detail["borrower_name"], "Falcon Realty Ltd")
        self.assertIsInstance(detail["alerts"], list)

    def test_unknown_borrower_returns_none(self):
        self.assertIsNone(get_borrower_identity(999999))
        self.assertIsNone(get_borrower_detail(999999))
        self.assertIsNone(get_borrower_history_payload(999999))

    def test_history_payload(self):
        payload = get_borrower_history_payload(65)
        self.assertIsNotNone(payload)
        self.assertGreater(payload["metric_count"], 0)
        self.assertGreater(payload["observation_count"], 0)
        self.assertIn("DSCR", payload["metrics"])

    def test_portfolio_summary_and_lists(self):
        summary = get_portfolio_summary()
        self.assertEqual(summary["total_borrowers"], 25)
        self.assertAlmostEqual(summary["total_exposure"], 1056.0, places=2)
        self.assertEqual(len(list_risk_scores()), 25)
        self.assertEqual(len(list_alerts()), 46)
        self.assertTrue(all(row["severity"] == "HIGH" for row in list_alerts("HIGH")))

    def test_ranked_read_models(self):
        watchlist = list_legacy_watchlist()
        top = list_top_risk_accounts()

        self.assertGreater(len(watchlist), 0)
        self.assertLessEqual(len(top), 10)
        scores = [float(row["score"]) for row in top]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
