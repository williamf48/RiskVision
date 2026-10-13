from sqlalchemy import text

from connection import engine


# =========================================================
# STATUS ORDER
# =========================================================

COVENANT_STATUS_RANK = {
    "NO_TEST": 0,
    "HEALTHY": 1,
    "TIGHT": 2,
    "NEAR_BREACH": 3,
    "BREACHED": 4,
}


# =========================================================
# HEADROOM CALCULATION
# =========================================================

def calculate_headroom(
    actual_value,
    threshold_value,
    threshold_direction,
):
    """
    Positive headroom = compliant.
    Zero headroom     = exactly at threshold.
    Negative headroom = breached.

    MINIMUM:
        actual >= threshold

        Example:
        DSCR actual = 1.30
        threshold = 1.10
        headroom = +0.20

    MAXIMUM:
        actual <= threshold

        Example:
        Debt/EBITDA actual = 3.10
        threshold = 3.50
        headroom = +0.40
    """

    actual_value = float(
        actual_value
    )

    threshold_value = float(
        threshold_value
    )


    if threshold_direction == "MINIMUM":

        headroom_absolute = (
            actual_value
            -
            threshold_value
        )


    elif threshold_direction == "MAXIMUM":

        headroom_absolute = (
            threshold_value
            -
            actual_value
        )


    else:

        raise ValueError(
            "threshold_direction must be "
            "'MINIMUM' or 'MAXIMUM'"
        )


    if threshold_value == 0:

        headroom_percentage = None

    else:

        headroom_percentage = (
            headroom_absolute
            /
            abs(
                threshold_value
            )
        ) * 100


    return (
        round(
            headroom_absolute,
            6,
        ),
        (
            round(
                headroom_percentage,
                4,
            )
            if headroom_percentage
            is not None
            else None
        ),
    )


# =========================================================
# HEADROOM STATUS
# =========================================================

def classify_headroom(
    headroom_percentage,
    warning_buffer_pct=15,
):
    """
    MVP development thresholds.

    BREACHED:
        headroom < 0%

    NEAR_BREACH:
        0% <= headroom < 5%

    TIGHT:
        5% <= headroom < warning buffer

    HEALTHY:
        headroom >= warning buffer

    These are development thresholds,
    not institutional policy thresholds.
    """

    if headroom_percentage is None:

        return "NO_TEST"


    headroom_percentage = float(
        headroom_percentage
    )


    warning_buffer_pct = float(
        warning_buffer_pct
    )


    if headroom_percentage < 0:

        return "BREACHED"


    if headroom_percentage < 5:

        return "NEAR_BREACH"


    if (
        headroom_percentage
        < warning_buffer_pct
    ):

        return "TIGHT"


    return "HEALTHY"


# =========================================================
# ANALYZE ONE COVENANT
# =========================================================

def analyze_covenant(
    covenant_id,
):

    query = text("""
        SELECT
            c.id AS covenant_id,
            c.covenant_code,
            c.covenant_name,
            c.metric_code,
            c.threshold_direction,
            c.threshold_value,
            c.warning_buffer_pct,
            c.testing_frequency,
            c.next_test_date,
            c.status AS covenant_status,

            f.id AS facility_id,
            f.facility_code,
            f.facility_name,
            f.facility_type,
            f.sanctioned_amount,
            f.outstanding_amount,

            b.id AS borrower_id,
            b.borrower_name,

            ct.id AS covenant_test_id,
            ct.test_date,
            ct.actual_value,
            ct.headroom_absolute,
            ct.headroom_percentage,
            ct.test_status,
            ct.source,
            ct.data_quality

        FROM covenants c

        JOIN facilities f
            ON f.id = c.facility_id

        JOIN borrowers b
            ON b.id = f.borrower_id

        LEFT JOIN covenant_tests ct ON ct.id = (
            SELECT ct_inner.id
            FROM covenant_tests ct_inner
            WHERE ct_inner.covenant_id = c.id
            ORDER BY ct_inner.test_date DESC, ct_inner.id DESC
            LIMIT 1
        )

        WHERE c.id = :covenant_id
    """)


    with engine.connect() as conn:

        row = conn.execute(
            query,
            {
                "covenant_id":
                    covenant_id
            },
        ).mappings().one_or_none()


    if row is None:

        return None


    result = dict(
        row
    )


    if (
        result[
            "covenant_test_id"
        ]
        is None
    ):

        result[
            "test_status"
        ] = "NO_TEST"


    result[
        "status_rank"
    ] = (
        COVENANT_STATUS_RANK.get(
            result[
                "test_status"
            ],
            0,
        )
    )


    return result


# =========================================================
# BORROWER COVENANT ANALYSIS
# =========================================================

def analyze_borrower_covenants(
    borrower_id,
):

    query = text("""
        SELECT
            c.id AS covenant_id,
            c.covenant_code,
            c.covenant_name,
            c.metric_code,
            c.threshold_direction,
            c.threshold_value,
            c.warning_buffer_pct,
            c.testing_frequency,
            c.next_test_date,

            f.id AS facility_id,
            f.facility_code,
            f.facility_name,
            f.facility_type,
            f.sanctioned_amount,
            f.outstanding_amount,

            b.id AS borrower_id,
            b.borrower_name,

            ct.id AS covenant_test_id,
            ct.test_date,
            ct.actual_value,
            ct.headroom_absolute,
            ct.headroom_percentage,
            ct.test_status,
            ct.source,
            ct.data_quality

        FROM borrowers b

        JOIN facilities f
            ON f.borrower_id = b.id

        JOIN covenants c
            ON c.facility_id = f.id

        LEFT JOIN covenant_tests ct ON ct.id = (
            SELECT ct_inner.id FROM covenant_tests ct_inner
            WHERE ct_inner.covenant_id = c.id
            ORDER BY ct_inner.test_date DESC, ct_inner.id DESC LIMIT 1
        )

        WHERE
            b.id = :borrower_id

            AND f.status = 'ACTIVE'

            AND c.status = 'ACTIVE'

        ORDER BY
            f.id,
            c.id
    """)


    with engine.connect() as conn:

        rows = conn.execute(
            query,
            {
                "borrower_id":
                    borrower_id
            },
        ).mappings().all()


    covenant_results = []


    for row in rows:

        result = dict(
            row
        )


        if (
            result[
                "covenant_test_id"
            ]
            is None
        ):

            result[
                "test_status"
            ] = "NO_TEST"


        result[
            "status_rank"
        ] = (
            COVENANT_STATUS_RANK.get(
                result[
                    "test_status"
                ],
                0,
            )
        )


        covenant_results.append(
            result
        )


    breached = sum(
        1
        for item
        in covenant_results
        if item[
            "test_status"
        ] == "BREACHED"
    )


    near_breach = sum(
        1
        for item
        in covenant_results
        if item[
            "test_status"
        ] == "NEAR_BREACH"
    )


    tight = sum(
        1
        for item
        in covenant_results
        if item[
            "test_status"
        ] == "TIGHT"
    )


    healthy = sum(
        1
        for item
        in covenant_results
        if item[
            "test_status"
        ] == "HEALTHY"
    )


    no_test = sum(
        1
        for item
        in covenant_results
        if item[
            "test_status"
        ] == "NO_TEST"
    )


    if breached > 0:

        pressure_status = (
            "BREACHED"
        )


    elif near_breach > 0:

        pressure_status = (
            "NEAR_BREACH"
        )


    elif tight > 0:

        pressure_status = (
            "TIGHT"
        )


    elif (
        healthy > 0
        and
        no_test == 0
    ):

        pressure_status = (
            "HEALTHY"
        )


    elif no_test > 0:

        pressure_status = (
            "INSUFFICIENT_DATA"
        )


    else:

        pressure_status = (
            "NO_COVENANTS"
        )


    borrower_name = None


    if covenant_results:

        borrower_name = (
            covenant_results[0][
                "borrower_name"
            ]
        )


    return {

        "borrower_id":
            borrower_id,

        "borrower_name":
            borrower_name,

        "covenants_analyzed":
            len(
                covenant_results
            ),

        "breached_covenants":
            breached,

        "near_breach_covenants":
            near_breach,

        "tight_covenants":
            tight,

        "healthy_covenants":
            healthy,

        "untested_covenants":
            no_test,

        "covenant_pressure_status":
            pressure_status,

        "covenants":
            covenant_results,
    }


# =========================================================
# PORTFOLIO COVENANT ANALYSIS
# =========================================================

def analyze_portfolio_covenants():

    borrower_query = text("""
        SELECT DISTINCT
            b.id,
            b.borrower_name

        FROM borrowers b

        JOIN facilities f
            ON f.borrower_id = b.id

        JOIN covenants c
            ON c.facility_id = f.id

        WHERE
            f.status = 'ACTIVE'
            AND c.status = 'ACTIVE'

        ORDER BY b.id
    """)


    with engine.connect() as conn:

        borrowers = conn.execute(
            borrower_query
        ).mappings().all()


    results = []


    for borrower in borrowers:

        result = (
            analyze_borrower_covenants(
                borrower[
                    "id"
                ]
            )
        )


        result[
            "borrower_name"
        ] = (
            borrower[
                "borrower_name"
            ]
        )


        results.append(
            result
        )


    pressure_rank = {
        "BREACHED": 5,
        "NEAR_BREACH": 4,
        "TIGHT": 3,
        "HEALTHY": 2,
        "INSUFFICIENT_DATA": 1,
        "NO_COVENANTS": 0,
    }


    results.sort(
        key=lambda item: (
            pressure_rank.get(
                item[
                    "covenant_pressure_status"
                ],
                0,
            ),
            item[
                "breached_covenants"
            ],
            item[
                "near_breach_covenants"
            ],
            item[
                "tight_covenants"
            ],
        ),
        reverse=True,
    )


    for index, item in enumerate(
        results,
        start=1,
    ):

        item[
            "covenant_pressure_rank"
        ] = index


    return results


# =========================================================
# PORTFOLIO COVENANT SUMMARY
# =========================================================

def summarize_portfolio_covenants():

    portfolio = (
        analyze_portfolio_covenants()
    )


    summary = {

        "borrowers_with_covenants":
            len(
                portfolio
            ),

        "borrowers_breached":
            0,

        "borrowers_near_breach":
            0,

        "borrowers_tight":
            0,

        "borrowers_healthy":
            0,

        "borrowers_insufficient_data":
            0,

        "total_covenants":
            0,

        "breached_covenants":
            0,

        "near_breach_covenants":
            0,

        "tight_covenants":
            0,

        "healthy_covenants":
            0,

        "untested_covenants":
            0,
    }


    for borrower in portfolio:

        summary[
            "total_covenants"
        ] += (
            borrower[
                "covenants_analyzed"
            ]
        )


        summary[
            "breached_covenants"
        ] += (
            borrower[
                "breached_covenants"
            ]
        )


        summary[
            "near_breach_covenants"
        ] += (
            borrower[
                "near_breach_covenants"
            ]
        )


        summary[
            "tight_covenants"
        ] += (
            borrower[
                "tight_covenants"
            ]
        )


        summary[
            "healthy_covenants"
        ] += (
            borrower[
                "healthy_covenants"
            ]
        )


        summary[
            "untested_covenants"
        ] += (
            borrower[
                "untested_covenants"
            ]
        )


        status = (
            borrower[
                "covenant_pressure_status"
            ]
        )


        if status == "BREACHED":

            summary[
                "borrowers_breached"
            ] += 1


        elif status == "NEAR_BREACH":

            summary[
                "borrowers_near_breach"
            ] += 1


        elif status == "TIGHT":

            summary[
                "borrowers_tight"
            ] += 1


        elif status == "HEALTHY":

            summary[
                "borrowers_healthy"
            ] += 1


        elif (
            status
            == "INSUFFICIENT_DATA"
        ):

            summary[
                "borrowers_insufficient_data"
            ] += 1


    summary[
        "borrowers_under_covenant_pressure"
    ] = (

        summary[
            "borrowers_breached"
        ]

        +

        summary[
            "borrowers_near_breach"
        ]

        +

        summary[
            "borrowers_tight"
        ]
    )


    return summary


# =========================================================
# COMMAND LINE TEST
# =========================================================

if __name__ == "__main__":

    portfolio = (
        analyze_portfolio_covenants()
    )


    print(
        "=" * 80
    )

    print(
        "RISKVISION - COVENANT PRESSURE"
    )

    print(
        "=" * 80
    )


    for borrower in portfolio:

        print(
            f"{borrower['borrower_name']:<30}"
            f" | "
            f"{borrower['covenant_pressure_status']:<18}"
            f" | Breached: "
            f"{borrower['breached_covenants']}"
            f" | Near: "
            f"{borrower['near_breach_covenants']}"
            f" | Tight: "
            f"{borrower['tight_covenants']}"
            f" | Healthy: "
            f"{borrower['healthy_covenants']}"
            f" | Untested: "
            f"{borrower['untested_covenants']}"
        )


    print(
        "\nSUMMARY"
    )

    print(
        summarize_portfolio_covenants()
    )