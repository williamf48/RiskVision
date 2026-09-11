import sys
import unittest
from pathlib import Path


BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

sys.path.insert(
    0,
    str(BACKEND_DIR),
)


from fastapi.testclient import TestClient

from api_schemas import (
    BacktestSummaryResponse,
    BorrowerBacktestResponse,
    BorrowerDeteriorationResponse,
    CovenantSummaryResponse,
    InterventionSummaryResponse,
    PortfolioAnalyticsResponse,
    PortfolioSummaryResponse,
    ReplayResponse,
    RootResponse,
)

from main import app


client = TestClient(app)


class APIContractTests(
    unittest.TestCase
):

    def validate(
        self,
        path,
        model,
    ):

        response = client.get(
            path
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        validated = (
            model.model_validate(
                response.json()
            )
        )

        self.assertIsInstance(
            validated,
            model,
        )


    def test_root_contract(self):
        self.validate(
            "/",
            RootResponse,
        )


    def test_deterioration_contract(self):
        self.validate(
            "/borrowers/65/deterioration",
            BorrowerDeteriorationResponse,
        )


    def test_replay_contract(self):
        self.validate(
            "/borrowers/65/replay",
            ReplayResponse,
        )


    def test_borrower_backtest_contract(self):
        self.validate(
            "/borrowers/65/backtest",
            BorrowerBacktestResponse,
        )


    def test_backtest_summary_contract(self):
        self.validate(
            "/backtest_summary",
            BacktestSummaryResponse,
        )


    def test_intervention_summary_contract(self):
        self.validate(
            "/intervention_summary",
            InterventionSummaryResponse,
        )


    def test_covenant_summary_contract(self):
        self.validate(
            "/covenant_summary",
            CovenantSummaryResponse,
        )


    def test_portfolio_analytics_contract(self):
        self.validate(
            "/portfolio_analytics",
            PortfolioAnalyticsResponse,
        )


    def test_portfolio_summary_contract(self):
        self.validate(
            "/portfolio_summary",
            PortfolioSummaryResponse,
        )


    def test_fastapi_routes_bind_response_models(self):

        expected = {
            "/": RootResponse,

            "/borrowers/{borrower_id}/deterioration":
                BorrowerDeteriorationResponse,

            "/borrowers/{borrower_id}/replay":
                ReplayResponse,

            "/borrowers/{borrower_id}/backtest":
                BorrowerBacktestResponse,

            "/backtest_summary":
                BacktestSummaryResponse,

            "/intervention_summary":
                InterventionSummaryResponse,

            "/covenant_summary":
                CovenantSummaryResponse,

            "/portfolio_analytics":
                PortfolioAnalyticsResponse,

            "/portfolio_summary":
                PortfolioSummaryResponse,
        }


        routes = {
            route.path: route
            for route in app.routes
            if hasattr(
                route,
                "response_model",
            )
        }


        for path, model in expected.items():

            self.assertIn(
                path,
                routes,
            )

            self.assertIs(
                routes[path].response_model,
                model,
                msg=(
                    f"Incorrect response model "
                    f"for {path}"
                ),
            )



if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
