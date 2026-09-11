from collections import defaultdict

from sqlalchemy import text

from connection import engine

from trajectory_engine import analyze_portfolio
from covenant_engine import analyze_portfolio_covenants


# =========================================================
# PORTFOLIO ANALYTICS
# =========================================================

def analyze_portfolio_concentration():

    # -----------------------------------------------------
    # BASE BORROWER DATA
    # -----------------------------------------------------

    borrower_query = text("""
        SELECT
            id AS borrower_id,
            borrower_name,
            sector,
            loan_amount

        FROM borrowers

        ORDER BY id
    """)


    with engine.connect() as conn:

        borrowers = conn.execute(
            borrower_query
        ).mappings().all()


    borrower_records = [
        dict(row)
        for row in borrowers
    ]


    # -----------------------------------------------------
    # INTERVENTION INTELLIGENCE
    # -----------------------------------------------------

    intervention_results = (
        analyze_portfolio()
    )


    intervention_map = {
        item["borrower_id"]: item
        for item in intervention_results
    }


    # -----------------------------------------------------
    # COVENANT INTELLIGENCE
    # -----------------------------------------------------

    covenant_results = (
        analyze_portfolio_covenants()
    )


    covenant_map = {
        item["borrower_id"]: item
        for item in covenant_results
    }


    # -----------------------------------------------------
    # TOTAL EXPOSURE
    # -----------------------------------------------------

    total_exposure = sum(
        float(
            borrower[
                "loan_amount"
            ]
            or 0
        )
        for borrower
        in borrower_records
    )


    total_borrowers = len(
        borrower_records
    )


    # -----------------------------------------------------
    # SECTOR AGGREGATION
    # -----------------------------------------------------

    sector_data = defaultdict(
        lambda: {
            "borrower_count": 0,
            "total_exposure": 0.0,
            "urgent": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "insufficient_data": 0,
            "actionable_borrowers": 0,
            "historically_assessable": 0,
            "covenant_pressure_borrowers": 0,
            "breached_covenant_borrowers": 0,
        }
    )


    for borrower in borrower_records:

        borrower_id = (
            borrower[
                "borrower_id"
            ]
        )


        sector = (
            borrower[
                "sector"
            ]
            or "Unknown"
        )


        exposure = float(
            borrower[
                "loan_amount"
            ]
            or 0
        )


        sector_record = (
            sector_data[
                sector
            ]
        )


        sector_record[
            "borrower_count"
        ] += 1


        sector_record[
            "total_exposure"
        ] += exposure


        # -----------------------------------------------
        # INTERVENTION
        # -----------------------------------------------

        intervention = (
            intervention_map.get(
                borrower_id
            )
        )


        if intervention:

            priority = (
                intervention[
                    "intervention_priority"
                ]
            )


            if priority == "URGENT":

                sector_record[
                    "urgent"
                ] += 1


            elif priority == "HIGH":

                sector_record[
                    "high"
                ] += 1


            elif priority == "MEDIUM":

                sector_record[
                    "medium"
                ] += 1


            elif priority == "LOW":

                sector_record[
                    "low"
                ] += 1


            elif (
                priority
                == "INSUFFICIENT_DATA"
            ):

                sector_record[
                    "insufficient_data"
                ] += 1


            if priority in {
                "URGENT",
                "HIGH",
                "MEDIUM",
            }:

                sector_record[
                    "actionable_borrowers"
                ] += 1


            if (
                intervention[
                    "metrics_analyzed"
                ]
                > 0
            ):

                sector_record[
                    "historically_assessable"
                ] += 1


        # -----------------------------------------------
        # COVENANT PRESSURE
        # -----------------------------------------------

        covenant = (
            covenant_map.get(
                borrower_id
            )
        )


        if covenant:

            covenant_status = (
                covenant[
                    "covenant_pressure_status"
                ]
            )


            if covenant_status in {
                "BREACHED",
                "NEAR_BREACH",
                "TIGHT",
            }:

                sector_record[
                    "covenant_pressure_borrowers"
                ] += 1


            if (
                covenant_status
                == "BREACHED"
            ):

                sector_record[
                    "breached_covenant_borrowers"
                ] += 1


    # -----------------------------------------------------
    # FINAL SECTOR RESULTS
    # -----------------------------------------------------

    sectors = []


    for (
        sector,
        values,
    ) in sector_data.items():

        exposure = (
            values[
                "total_exposure"
            ]
        )


        borrower_count = (
            values[
                "borrower_count"
            ]
        )


        if total_exposure > 0:

            exposure_share = (
                exposure
                /
                total_exposure
                *
                100
            )

        else:

            exposure_share = 0


        if borrower_count > 0:

            history_coverage = (
                values[
                    "historically_assessable"
                ]
                /
                borrower_count
                *
                100
            )

            actionable_ratio = (
                values[
                    "actionable_borrowers"
                ]
                /
                borrower_count
                *
                100
            )

        else:

            history_coverage = 0
            actionable_ratio = 0


        sectors.append({

            "sector":
                sector,

            "borrower_count":
                borrower_count,

            "total_exposure":
                round(
                    exposure,
                    2,
                ),

            "exposure_share_percentage":
                round(
                    exposure_share,
                    2,
                ),

            "urgent":
                values[
                    "urgent"
                ],

            "high":
                values[
                    "high"
                ],

            "medium":
                values[
                    "medium"
                ],

            "low":
                values[
                    "low"
                ],

            "insufficient_data":
                values[
                    "insufficient_data"
                ],

            "actionable_borrowers":
                values[
                    "actionable_borrowers"
                ],

            "actionable_ratio_percentage":
                round(
                    actionable_ratio,
                    2,
                ),

            "historically_assessable":
                values[
                    "historically_assessable"
                ],

            "history_coverage_percentage":
                round(
                    history_coverage,
                    2,
                ),

            "covenant_pressure_borrowers":
                values[
                    "covenant_pressure_borrowers"
                ],

            "breached_covenant_borrowers":
                values[
                    "breached_covenant_borrowers"
                ],
        })


    sectors.sort(
        key=lambda item:
            item[
                "total_exposure"
            ],
        reverse=True,
    )


    # -----------------------------------------------------
    # BORROWER CONCENTRATION
    # -----------------------------------------------------

    borrower_exposures = []


    for borrower in borrower_records:

        exposure = float(
            borrower[
                "loan_amount"
            ]
            or 0
        )


        exposure_share = (
            exposure
            /
            total_exposure
            *
            100
            if total_exposure > 0
            else 0
        )


        borrower_exposures.append({

            "borrower_id":
                borrower[
                    "borrower_id"
                ],

            "borrower_name":
                borrower[
                    "borrower_name"
                ],

            "sector":
                borrower[
                    "sector"
                ]
                or "Unknown",

            "exposure":
                round(
                    exposure,
                    2,
                ),

            "portfolio_share_percentage":
                round(
                    exposure_share,
                    2,
                ),
        })


    borrower_exposures.sort(
        key=lambda item:
            item[
                "exposure"
            ],
        reverse=True,
    )


    top_5_exposure = sum(
        borrower[
            "exposure"
        ]
        for borrower
        in borrower_exposures[:5]
    )


    top_5_share = (
        top_5_exposure
        /
        total_exposure
        *
        100
        if total_exposure > 0
        else 0
    )


    largest_borrower_share = (
        borrower_exposures[0][
            "portfolio_share_percentage"
        ]
        if borrower_exposures
        else 0
    )


    # -----------------------------------------------------
    # HHI - BORROWER EXPOSURE CONCENTRATION
    # -----------------------------------------------------

    borrower_hhi = sum(
        (
            borrower[
                "portfolio_share_percentage"
            ]
        ) ** 2
        for borrower
        in borrower_exposures
    )


    # -----------------------------------------------------
    # HHI - SECTOR EXPOSURE CONCENTRATION
    # -----------------------------------------------------

    sector_hhi = sum(
        (
            sector[
                "exposure_share_percentage"
            ]
        ) ** 2
        for sector
        in sectors
    )


    # -----------------------------------------------------
    # PORTFOLIO HISTORY COVERAGE
    # -----------------------------------------------------

    historically_assessable = sum(
        1
        for item
        in intervention_results
        if item[
            "metrics_analyzed"
        ] > 0
    )


    history_coverage_percentage = (
        historically_assessable
        /
        total_borrowers
        *
        100
        if total_borrowers > 0
        else 0
    )


    # -----------------------------------------------------
    # ACTIONABLE EXPOSURE
    # -----------------------------------------------------

    actionable_ids = {
        item[
            "borrower_id"
        ]
        for item
        in intervention_results
        if item[
            "intervention_priority"
        ] in {
            "URGENT",
            "HIGH",
            "MEDIUM",
        }
    }


    actionable_exposure = sum(
        float(
            borrower[
                "loan_amount"
            ]
            or 0
        )
        for borrower
        in borrower_records
        if borrower[
            "borrower_id"
        ] in actionable_ids
    )


    actionable_exposure_share = (
        actionable_exposure
        /
        total_exposure
        *
        100
        if total_exposure > 0
        else 0
    )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "portfolio_summary": {

            "total_borrowers":
                total_borrowers,

            "total_exposure":
                round(
                    total_exposure,
                    2,
                ),

            "sector_count":
                len(
                    sectors
                ),

            "historically_assessable_borrowers":
                historically_assessable,

            "history_coverage_percentage":
                round(
                    history_coverage_percentage,
                    2,
                ),

            "actionable_exposure":
                round(
                    actionable_exposure,
                    2,
                ),

            "actionable_exposure_share_percentage":
                round(
                    actionable_exposure_share,
                    2,
                ),

            "largest_borrower_share_percentage":
                round(
                    largest_borrower_share,
                    2,
                ),

            "top_5_borrower_exposure_share_percentage":
                round(
                    top_5_share,
                    2,
                ),

            "borrower_exposure_hhi":
                round(
                    borrower_hhi,
                    2,
                ),

            "sector_exposure_hhi":
                round(
                    sector_hhi,
                    2,
                ),
        },

        "sectors":
            sectors,

        "top_exposures":
            borrower_exposures[:10],
    }


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    analytics = (
        analyze_portfolio_concentration()
    )


    print(
        "=" * 85
    )

    print(
        "RISKVISION - PORTFOLIO CONCENTRATION ANALYTICS"
    )

    print(
        "=" * 85
    )


    summary = (
        analytics[
            "portfolio_summary"
        ]
    )


    print(
        f"\nTotal exposure: "
        f"{summary['total_exposure']}"
    )

    print(
        f"History coverage: "
        f"{summary['history_coverage_percentage']}%"
    )

    print(
        f"Actionable exposure: "
        f"{summary['actionable_exposure']} "
        f"({summary['actionable_exposure_share_percentage']}%)"
    )

    print(
        f"Largest borrower share: "
        f"{summary['largest_borrower_share_percentage']}%"
    )

    print(
        f"Top 5 borrower share: "
        f"{summary['top_5_borrower_exposure_share_percentage']}%"
    )

    print(
        f"Borrower HHI: "
        f"{summary['borrower_exposure_hhi']}"
    )

    print(
        f"Sector HHI: "
        f"{summary['sector_exposure_hhi']}"
    )


    print(
        "\nSECTOR ANALYTICS"
    )


    for sector in analytics[
        "sectors"
    ]:

        print(
            f"{sector['sector']:<24}"
            f" | Exposure {sector['total_exposure']:<8}"
            f" | Share {sector['exposure_share_percentage']:>6}%"
            f" | Borrowers {sector['borrower_count']:<2}"
            f" | Actionable {sector['actionable_borrowers']:<2}"
            f" | Coverage {sector['history_coverage_percentage']:>6}%"
            f" | Covenant Pressure "
            f"{sector['covenant_pressure_borrowers']}"
        )