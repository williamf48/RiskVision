from sqlalchemy import text
import pandas as pd

from connection import engine

from trajectory_engine import (
    analyze_borrower,
    PRIORITY_RANK,
)


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_ALERT_THRESHOLD = "HIGH"

DEFAULT_MAX_LOOKBACK_DAYS = 180


# =========================================================
# LOAD BORROWER
# =========================================================

def get_borrower(
    borrower_id,
):

    query = """
    SELECT
        id,
        borrower_name

    FROM borrowers

    WHERE id = :borrower_id
    """


    df = pd.read_sql(
        text(query),
        engine,
        params={
            "borrower_id":
                borrower_id
        },
    )


    if df.empty:

        raise ValueError(
            f"Borrower not found: "
            f"{borrower_id}"
        )


    return (
        df
        .iloc[0]
        .to_dict()
    )


# =========================================================
# LOAD REPLAY DATES
# =========================================================

def get_replay_dates(
    borrower_id,
):

    query = """
    SELECT DISTINCT
        observation_date

    FROM borrower_metric_observations

    WHERE borrower_id = :borrower_id

    ORDER BY observation_date
    """


    df = pd.read_sql(
        text(query),
        engine,
        params={
            "borrower_id":
                borrower_id
        },
    )


    if df.empty:
        return []


    return [

        pd.Timestamp(
            value
        ).date()

        for value
        in df[
            "observation_date"
        ].tolist()
    ]


# =========================================================
# LOAD STRESS EVENTS
# =========================================================

def get_stress_events(
    borrower_id,
):

    query = """
    SELECT
        id,
        event_type,
        event_date,
        severity,
        source,
        notes

    FROM borrower_stress_events

    WHERE borrower_id = :borrower_id

    ORDER BY event_date
    """


    df = pd.read_sql(
        text(query),
        engine,
        params={
            "borrower_id":
                borrower_id
        },
    )


    if df.empty:
        return []


    results = []


    for row in (
        df.to_dict(
            orient="records"
        )
    ):

        row[
            "event_date"
        ] = str(
            pd.Timestamp(
                row[
                    "event_date"
                ]
            ).date()
        )


        results.append(
            row
        )


    return results


# =========================================================
# HISTORICAL BORROWER REPLAY
# =========================================================

def replay_borrower(
    borrower_id,
):

    borrower = (
        get_borrower(
            borrower_id
        )
    )


    replay_dates = (
        get_replay_dates(
            borrower_id
        )
    )


    timeline = []


    for replay_date in replay_dates:

        result = (
            analyze_borrower(

                borrower_id,

                as_of_date=
                    replay_date,
            )
        )


        timeline.append({

            "as_of_date":
                str(
                    replay_date
                ),

            "intervention_priority":
                result[
                    "intervention_priority"
                ],

            "priority_rank":
                result[
                    "priority_rank"
                ],

            "metrics_analyzed":
                result[
                    "metrics_analyzed"
                ],

            "deteriorating_signals":
                result[
                    "deteriorating_signals"
                ],

            "critical_condition_signals":
                result[
                    "critical_condition_signals"
                ],

            "weak_condition_signals":
                result[
                    "weak_condition_signals"
                ],

            "persistent_deterioration_signals":
                result[
                    "persistent_deterioration_signals"
                ],

            "accelerating_deterioration_signals":
                result[
                    "accelerating_deterioration_signals"
                ],

            "convergence_percentage":
                result[
                    "convergence_percentage"
                ],

            "reason_codes":
                result[
                    "reason_codes"
                ],
        })


    return {

        "borrower_id":
            borrower_id,

        "borrower_name":
            borrower[
                "borrower_name"
            ],

        "replay_points":
            len(
                timeline
            ),

        "timeline":
            timeline,
    }


# =========================================================
# FIRST PRIORITY DATE
# =========================================================

def first_priority_date(
    timeline,
    minimum_priority,
):

    minimum_rank = (
        PRIORITY_RANK[
            minimum_priority
        ]
    )


    for point in timeline:

        if (
            point[
                "priority_rank"
            ]
            >= minimum_rank
        ):

            return (
                point[
                    "as_of_date"
                ]
            )


    return None


# =========================================================
# MAXIMUM PRIORITY
# =========================================================

def get_max_priority(
    timeline,
):

    if not timeline:

        return {
            "priority":
                "INSUFFICIENT_DATA",

            "priority_rank":
                0,

            "date":
                None,
        }


    maximum = max(

        timeline,

        key=lambda point:
            point[
                "priority_rank"
            ],
    )


    return {

        "priority":
            maximum[
                "intervention_priority"
            ],

        "priority_rank":
            maximum[
                "priority_rank"
            ],

        "date":
            maximum[
                "as_of_date"
            ],
    }


# =========================================================
# BORROWER BACKTEST
# =========================================================

def backtest_borrower(
    borrower_id,
    alert_threshold=
        DEFAULT_ALERT_THRESHOLD,
):

    replay = (
        replay_borrower(
            borrower_id
        )
    )


    timeline = (
        replay[
            "timeline"
        ]
    )


    events = (
        get_stress_events(
            borrower_id
        )
    )


    first_medium = (
        first_priority_date(
            timeline,
            "MEDIUM",
        )
    )


    first_high = (
        first_priority_date(
            timeline,
            "HIGH",
        )
    )


    first_urgent = (
        first_priority_date(
            timeline,
            "URGENT",
        )
    )


    first_alert = (
        first_priority_date(
            timeline,
            alert_threshold,
        )
    )


    max_priority = (
        get_max_priority(
            timeline
        )
    )


    max_convergence = (

        max(

            (
                point[
                    "convergence_percentage"
                ]

                for point
                in timeline
            ),

            default=0.0,
        )
    )


    first_event = (

        events[0]

        if events

        else None
    )


    lead_time_days = None


    if (
        first_alert is not None

        and

        first_event is not None
    ):

        alert_date = (
            pd.Timestamp(
                first_alert
            )
        )


        event_date = (
            pd.Timestamp(
                first_event[
                    "event_date"
                ]
            )
        )


        lead_time_days = (
            event_date
            - alert_date
        ).days


    return {

        "borrower_id":
            borrower_id,

        "borrower_name":
            replay[
                "borrower_name"
            ],

        "alert_threshold":
            alert_threshold,

        "replay_points":
            replay[
                "replay_points"
            ],

        "stress_event_present":
            bool(
                events
            ),

        "stress_events":
            events,

        "first_medium_date":
            first_medium,

        "first_high_date":
            first_high,

        "first_urgent_date":
            first_urgent,

        "first_alert_date":
            first_alert,

        "lead_time_days":
            lead_time_days,

        "maximum_priority":
            max_priority[
                "priority"
            ],

        "maximum_priority_date":
            max_priority[
                "date"
            ],

        "maximum_convergence_percentage":
            round(
                max_convergence,
                2,
            ),

        "timeline":
            timeline,
    }


# =========================================================
# HISTORICALLY ASSESSABLE BORROWERS
# =========================================================

def get_historically_assessable_borrowers():

    query = """
    SELECT DISTINCT
        b.id,
        b.borrower_name

    FROM borrowers b

    JOIN borrower_metric_observations o
        ON o.borrower_id = b.id

    ORDER BY b.id
    """


    df = pd.read_sql(
        text(query),
        engine,
    )


    return (
        df.to_dict(
            orient="records"
        )
    )


# =========================================================
# PORTFOLIO BACKTEST
# =========================================================

def backtest_portfolio(
    alert_threshold=
        DEFAULT_ALERT_THRESHOLD,
):

    borrowers = (
        get_historically_assessable_borrowers()
    )


    results = []


    threshold_rank = (
        PRIORITY_RANK[
            alert_threshold
        ]
    )


    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0


    lead_times = []


    for borrower in borrowers:

        result = (
            backtest_borrower(

                int(
                    borrower[
                        "id"
                    ]
                ),

                alert_threshold=
                    alert_threshold,
            )
        )


        results.append(
            result
        )


        event_present = (
            result[
                "stress_event_present"
            ]
        )


        alert_generated = (

            PRIORITY_RANK[
                result[
                    "maximum_priority"
                ]
            ]

            >= threshold_rank
        )


        # -------------------------------------------------
        # CONFUSION MATRIX
        # -------------------------------------------------

        if (
            event_present
            and
            alert_generated
        ):

            true_positive += 1


            if (
                result[
                    "lead_time_days"
                ]
                is not None

                and

                result[
                    "lead_time_days"
                ]
                >= 0
            ):

                lead_times.append(
                    result[
                        "lead_time_days"
                    ]
                )


        elif (
            event_present
            and
            not alert_generated
        ):

            false_negative += 1


        elif (
            not event_present
            and
            alert_generated
        ):

            false_positive += 1


        else:

            true_negative += 1


    # =====================================================
    # METRICS
    # =====================================================

    precision_denominator = (

        true_positive
        + false_positive
    )


    recall_denominator = (

        true_positive
        + false_negative
    )


    specificity_denominator = (

        true_negative
        + false_positive
    )


    precision = (

        true_positive
        / precision_denominator

        if precision_denominator > 0

        else None
    )


    recall = (

        true_positive
        / recall_denominator

        if recall_denominator > 0

        else None
    )


    specificity = (

        true_negative
        / specificity_denominator

        if specificity_denominator > 0

        else None
    )


    average_lead_time = (

        sum(
            lead_times
        )

        / len(
            lead_times
        )

        if lead_times

        else None
    )


    return {

        "alert_threshold":
            alert_threshold,

        "historically_assessable_borrowers":
            len(
                borrowers
            ),

        "labelled_stress_events":
            sum(

                1

                for result
                in results

                if result[
                    "stress_event_present"
                ]
            ),

        "confusion_matrix": {

            "true_positive":
                true_positive,

            "false_positive":
                false_positive,

            "true_negative":
                true_negative,

            "false_negative":
                false_negative,
        },

        "precision": (

            round(
                precision,
                4,
            )

            if precision
            is not None

            else None
        ),

        "recall": (

            round(
                recall,
                4,
            )

            if recall
            is not None

            else None
        ),

        "specificity": (

            round(
                specificity,
                4,
            )

            if specificity
            is not None

            else None
        ),

        "average_lead_time_days": (

            round(
                average_lead_time,
                2,
            )

            if average_lead_time
            is not None

            else None
        ),

        "borrowers":
            results,
    }


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    portfolio = (
        backtest_portfolio()
    )


    print(
        "=" * 100
    )

    print(
        "RISKVISION - HISTORICAL REPLAY BACKTEST"
    )

    print(
        "=" * 100
    )


    print()

    print(
        "Alert threshold:",
        portfolio[
            "alert_threshold"
        ]
    )


    print(
        "Assessable borrowers:",
        portfolio[
            "historically_assessable_borrowers"
        ]
    )


    print(
        "Synthetic stress events:",
        portfolio[
            "labelled_stress_events"
        ]
    )


    print()

    print(
        "Confusion matrix:",
        portfolio[
            "confusion_matrix"
        ]
    )


    print(
        "Precision:",
        portfolio[
            "precision"
        ]
    )


    print(
        "Recall:",
        portfolio[
            "recall"
        ]
    )


    print(
        "Specificity:",
        portfolio[
            "specificity"
        ]
    )


    print(
        "Average lead time:",
        portfolio[
            "average_lead_time_days"
        ],
        "days",
    )


    print()

    print(
        "-" * 100
    )


    for borrower in (
        portfolio[
            "borrowers"
        ]
    ):

        print(
            borrower[
                "borrower_name"
            ],
            "| max:",
            borrower[
                "maximum_priority"
            ],
            "| first alert:",
            borrower[
                "first_alert_date"
            ],
            "| event:",
            borrower[
                "stress_event_present"
            ],
            "| lead:",
            borrower[
                "lead_time_days"
            ],
        )