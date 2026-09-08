import pandas as pd

from connection import engine


# =========================================================
# METRIC CONFIGURATION
# =========================================================
#
# IMPORTANT:
# These condition thresholds are DEVELOPMENT / MVP DEFAULTS.
# They are NOT institutionally validated credit-policy limits.
#
# Later they can vary by:
# - lender
# - industry
# - geography
# - borrower type
# - underwriting policy
# =========================================================

METRIC_CONFIG = {

    "DSCR": {
        "bad_direction": "DOWN",

        # Healthy:  >= 1.50
        # Watch:    1.20 - 1.49
        # Weak:     1.00 - 1.19
        # Critical: < 1.00

        "condition_thresholds": {
            "critical": 1.00,
            "weak": 1.20,
            "watch": 1.50,
        },
    },


    "BOUNCE_RATE": {
        "bad_direction": "UP",

        # Healthy:  <= 2.0
        # Watch:    > 2.0 to 5.0
        # Weak:     > 5.0 to 8.0
        # Critical: > 8.0

        "condition_thresholds": {
            "watch": 2.0,
            "weak": 5.0,
            "critical": 8.0,
        },
    },


    "RECEIVABLE_DAYS": {
        "bad_direction": "UP",

        # Healthy:  <= 45
        # Watch:    > 45 to 60
        # Weak:     > 60 to 90
        # Critical: > 90

        "condition_thresholds": {
            "watch": 45,
            "weak": 60,
            "critical": 90,
        },
    },


    "DEBT_EBITDA": {
        "bad_direction": "UP",

        # Healthy:  <= 2.0
        # Watch:    > 2.0 to 3.0
        # Weak:     > 3.0 to 4.0
        # Critical: > 4.0

        "condition_thresholds": {
            "watch": 2.0,
            "weak": 3.0,
            "critical": 4.0,
        },
    },
}


# =========================================================
# LOAD METRIC HISTORY
# =========================================================

def get_metric_history(
    borrower_id,
    metric_code,
):

    query = """
    SELECT
        metric_value,
        observation_date
    FROM borrower_metric_observations
    WHERE borrower_id = %(borrower_id)s
      AND metric_code = %(metric_code)s
    ORDER BY observation_date
    """

    return pd.read_sql(
        query,
        engine,
        params={
            "borrower_id": borrower_id,
            "metric_code": metric_code,
        },
    )


# =========================================================
# CURRENT-CONDITION CLASSIFICATION
# =========================================================

def classify_condition(
    current_value,
    bad_direction,
    thresholds,
):
    """
    Classify the CURRENT condition of one metric.

    Severity:
        HEALTHY  = 0
        WATCH    = 1
        WEAK     = 2
        CRITICAL = 3
    """

    if current_value is None:

        return {
            "condition":
                "INSUFFICIENT_DATA",

            "condition_severity":
                None,
        }


    value = float(current_value)


    # -----------------------------------------------------
    # LOWER VALUES ARE WORSE
    # Example: DSCR
    # -----------------------------------------------------

    if bad_direction == "DOWN":

        if value < thresholds["critical"]:

            condition = "CRITICAL"
            severity = 3

        elif value < thresholds["weak"]:

            condition = "WEAK"
            severity = 2

        elif value < thresholds["watch"]:

            condition = "WATCH"
            severity = 1

        else:

            condition = "HEALTHY"
            severity = 0


    # -----------------------------------------------------
    # HIGHER VALUES ARE WORSE
    # Examples:
    # Bounce Rate
    # Receivable Days
    # Debt / EBITDA
    # -----------------------------------------------------

    else:

        if value > thresholds["critical"]:

            condition = "CRITICAL"
            severity = 3

        elif value > thresholds["weak"]:

            condition = "WEAK"
            severity = 2

        elif value > thresholds["watch"]:

            condition = "WATCH"
            severity = 1

        else:

            condition = "HEALTHY"
            severity = 0


    return {
        "condition":
            condition,

        "condition_severity":
            severity,
    }


# =========================================================
# TIME-NORMALIZED RISK VELOCITY
# =========================================================

def calculate_risk_velocity(
    old_value,
    new_value,
    old_date,
    new_date,
    bad_direction,
):
    """
    Calculate percentage deterioration normalized
    to a 30-day period.

    Positive velocity = deterioration
    Negative velocity = improvement
    """

    old_value = float(old_value)
    new_value = float(new_value)

    old_date = pd.Timestamp(
        old_date
    )

    new_date = pd.Timestamp(
        new_date
    )


    days = (
        new_date
        - old_date
    ).days


    if days <= 0:

        return (
            None,
            None,
        )


    if old_value == 0:

        return (
            days,
            None,
        )


    raw_percentage_change = (

        (
            new_value
            - old_value
        )

        / abs(old_value)

    ) * 100


    # -----------------------------------------------------
    # NORMALIZE INTO A COMMON RISK DIRECTION
    # -----------------------------------------------------

    if bad_direction == "UP":

        risk_percentage_change = (
            raw_percentage_change
        )

    else:

        risk_percentage_change = (
            -raw_percentage_change
        )


    risk_velocity_30d = (

        risk_percentage_change

        * (
            30
            / days
        )
    )


    return (
        days,
        risk_velocity_30d,
    )


# =========================================================
# ANALYZE ONE TRAJECTORY
# =========================================================

def analyze_trajectory(
    values,
    dates,
    bad_direction,
):

    # -----------------------------------------------------
    # NO HISTORY
    # -----------------------------------------------------

    if len(values) == 0:

        return {

            "current_value":
                None,

            "previous_value":
                None,

            "absolute_change":
                None,

            "percentage_change":
                None,

            "direction":
                "INSUFFICIENT_HISTORY",

            "persistence":
                0,

            "days_since_previous":
                None,

            "risk_velocity_30d":
                None,

            "previous_risk_velocity_30d":
                None,

            "velocity_change_30d":
                None,

            "acceleration_direction":
                "INSUFFICIENT_HISTORY",
        }


    # -----------------------------------------------------
    # ONE OBSERVATION
    #
    # Current condition CAN be assessed later,
    # but trajectory cannot yet be calculated.
    # -----------------------------------------------------

    if len(values) == 1:

        return {

            "current_value":
                round(
                    float(values[-1]),
                    4,
                ),

            "previous_value":
                None,

            "absolute_change":
                None,

            "percentage_change":
                None,

            "direction":
                "INSUFFICIENT_HISTORY",

            "persistence":
                0,

            "days_since_previous":
                None,

            "risk_velocity_30d":
                None,

            "previous_risk_velocity_30d":
                None,

            "velocity_change_30d":
                None,

            "acceleration_direction":
                "INSUFFICIENT_HISTORY",
        }


    # =====================================================
    # CURRENT AND PREVIOUS VALUE
    # =====================================================

    current_value = float(
        values[-1]
    )

    previous_value = float(
        values[-2]
    )


    absolute_change = (

        current_value
        - previous_value

    )


    # =====================================================
    # LATEST PERCENTAGE CHANGE
    # =====================================================

    if previous_value != 0:

        percentage_change = (

            absolute_change

            / abs(
                previous_value
            )

        ) * 100

    else:

        percentage_change = None


    # =====================================================
    # CURRENT DIRECTION
    # =====================================================

    if (
        current_value
        > previous_value
    ):

        movement = "UP"


    elif (
        current_value
        < previous_value
    ):

        movement = "DOWN"


    else:

        movement = "FLAT"


    if movement == "FLAT":

        direction = "STABLE"


    elif (
        movement
        == bad_direction
    ):

        direction = (
            "DETERIORATING"
        )


    else:

        direction = (
            "IMPROVING"
        )


    # =====================================================
    # PERSISTENCE
    # =====================================================

    persistence = 0


    for i in range(
        len(values) - 1,
        0,
        -1,
    ):

        change = (

            float(
                values[i]
            )

            -

            float(
                values[i - 1]
            )
        )


        if (
            bad_direction == "UP"
            and change > 0
        ):

            persistence += 1


        elif (
            bad_direction == "DOWN"
            and change < 0
        ):

            persistence += 1


        else:

            break


    # =====================================================
    # CURRENT RISK VELOCITY
    # =====================================================

    (
        days_since_previous,
        risk_velocity_30d,
    ) = calculate_risk_velocity(

        old_value=
            values[-2],

        new_value=
            values[-1],

        old_date=
            dates[-2],

        new_date=
            dates[-1],

        bad_direction=
            bad_direction,
    )


    # =====================================================
    # PREVIOUS RISK VELOCITY
    # =====================================================

    previous_risk_velocity_30d = (
        None
    )


    if len(values) >= 3:

        (
            _,
            previous_risk_velocity_30d,

        ) = calculate_risk_velocity(

            old_value=
                values[-3],

            new_value=
                values[-2],

            old_date=
                dates[-3],

            new_date=
                dates[-2],

            bad_direction=
                bad_direction,
        )


    # =====================================================
    # CHANGE IN VELOCITY
    # =====================================================

    velocity_change_30d = None

    acceleration_direction = (
        "INSUFFICIENT_HISTORY"
    )


    if (
        risk_velocity_30d
        is not None

        and

        previous_risk_velocity_30d
        is not None
    ):

        velocity_change_30d = (

            risk_velocity_30d

            -

            previous_risk_velocity_30d
        )


        tolerance = 0.01


        if (
            velocity_change_30d
            > tolerance
        ):

            acceleration_direction = (
                "ACCELERATING"
            )


        elif (
            velocity_change_30d
            < -tolerance
        ):

            acceleration_direction = (
                "DECELERATING"
            )


        else:

            acceleration_direction = (
                "STEADY"
            )


    # =====================================================
    # RETURN TRAJECTORY
    # =====================================================

    return {

        "current_value":
            round(
                current_value,
                4,
            ),

        "previous_value":
            round(
                previous_value,
                4,
            ),

        "absolute_change":
            round(
                absolute_change,
                4,
            ),

        "percentage_change": (
            round(
                percentage_change,
                2,
            )

            if percentage_change
            is not None

            else None
        ),

        "direction":
            direction,

        "persistence":
            persistence,

        "days_since_previous":
            days_since_previous,

        "risk_velocity_30d": (
            round(
                risk_velocity_30d,
                2,
            )

            if risk_velocity_30d
            is not None

            else None
        ),

        "previous_risk_velocity_30d": (
            round(
                previous_risk_velocity_30d,
                2,
            )

            if previous_risk_velocity_30d
            is not None

            else None
        ),

        "velocity_change_30d": (
            round(
                velocity_change_30d,
                2,
            )

            if velocity_change_30d
            is not None

            else None
        ),

        "acceleration_direction":
            acceleration_direction,
    }


# =========================================================
# ANALYZE ONE METRIC
# =========================================================

def analyze_metric(
    borrower_id,
    metric_code,
):

    metric_code = (
        metric_code.upper()
    )


    if (
        metric_code
        not in METRIC_CONFIG
    ):

        raise ValueError(
            f"Unknown metric_code: "
            f"{metric_code}"
        )


    config = (
        METRIC_CONFIG[
            metric_code
        ]
    )


    bad_direction = (
        config[
            "bad_direction"
        ]
    )


    thresholds = (
        config[
            "condition_thresholds"
        ]
    )


    df = get_metric_history(
        borrower_id,
        metric_code,
    )


    values = (
        df[
            "metric_value"
        ]
        .tolist()
    )


    dates = (
        df[
            "observation_date"
        ]
        .tolist()
    )


    result = analyze_trajectory(
        values,
        dates,
        bad_direction,
    )


    # =====================================================
    # CURRENT CONDITION
    # =====================================================

    condition_result = (
        classify_condition(

            current_value=
                result[
                    "current_value"
                ],

            bad_direction=
                bad_direction,

            thresholds=
                thresholds,
        )
    )


    result.update(
        condition_result
    )


    # =====================================================
    # METADATA
    # =====================================================

    result["borrower_id"] = (
        borrower_id
    )

    result["metric_code"] = (
        metric_code
    )

    result["bad_direction"] = (
        bad_direction
    )

    result["observations"] = (
        len(values)
    )


    return result


# =========================================================
# ANALYZE ENTIRE BORROWER
# =========================================================

def analyze_borrower(
    borrower_id,
):

    metric_results = []


    deteriorating_signals = 0

    improving_signals = 0

    stable_signals = 0

    insufficient_history_signals = 0


    accelerating_deterioration_signals = 0

    decelerating_deterioration_signals = 0


    critical_condition_signals = 0

    weak_condition_signals = 0

    watch_condition_signals = 0

    healthy_condition_signals = 0


    # =====================================================
    # RUN ALL CONFIGURED METRICS
    # =====================================================

    for metric_code in METRIC_CONFIG:

        result = analyze_metric(
            borrower_id,
            metric_code,
        )


        metric_results.append(
            result
        )


        direction = (
            result[
                "direction"
            ]
        )


        condition = (
            result[
                "condition"
            ]
        )


        # -------------------------------------------------
        # TRAJECTORY COUNTS
        # -------------------------------------------------

        if (
            direction
            == "DETERIORATING"
        ):

            deteriorating_signals += 1


            if (
                result[
                    "acceleration_direction"
                ]
                == "ACCELERATING"
            ):

                accelerating_deterioration_signals += 1


            elif (
                result[
                    "acceleration_direction"
                ]
                == "DECELERATING"
            ):

                decelerating_deterioration_signals += 1


        elif (
            direction
            == "IMPROVING"
        ):

            improving_signals += 1


        elif (
            direction
            == "STABLE"
        ):

            stable_signals += 1


        elif (
            direction
            == "INSUFFICIENT_HISTORY"
        ):

            insufficient_history_signals += 1


        # -------------------------------------------------
        # CURRENT-CONDITION COUNTS
        # -------------------------------------------------

        if condition == "CRITICAL":

            critical_condition_signals += 1


        elif condition == "WEAK":

            weak_condition_signals += 1


        elif condition == "WATCH":

            watch_condition_signals += 1


        elif condition == "HEALTHY":

            healthy_condition_signals += 1


    # =====================================================
    # METRICS WITH TRAJECTORY HISTORY
    # =====================================================

    metrics_analyzed = (

        deteriorating_signals

        + improving_signals

        + stable_signals
    )


    # =====================================================
    # CROSS-SIGNAL CONVERGENCE
    # =====================================================

    if metrics_analyzed > 0:

        convergence_ratio = (

            deteriorating_signals

            / metrics_analyzed
        )

    else:

        convergence_ratio = 0.0


    convergence_percentage = (

        convergence_ratio
        * 100

    )


    # =====================================================
    # PERSISTENT DETERIORATION
    # =====================================================

    persistent_deterioration_signals = sum(

        1

        for result
        in metric_results

        if (
            result[
                "direction"
            ]
            == "DETERIORATING"

            and

            result[
                "persistence"
            ]
            >= 2
        )
    )


    # =====================================================
    # RETURN BORROWER ANALYSIS
    # =====================================================

    return {

        "borrower_id":
            borrower_id,

        "configured_metrics":
            len(
                METRIC_CONFIG
            ),

        "metrics_analyzed":
            metrics_analyzed,


        "deteriorating_signals":
            deteriorating_signals,

        "improving_signals":
            improving_signals,

        "stable_signals":
            stable_signals,

        "insufficient_history_signals":
            insufficient_history_signals,


        "persistent_deterioration_signals":
            persistent_deterioration_signals,

        "accelerating_deterioration_signals":
            accelerating_deterioration_signals,

        "decelerating_deterioration_signals":
            decelerating_deterioration_signals,


        "critical_condition_signals":
            critical_condition_signals,

        "weak_condition_signals":
            weak_condition_signals,

        "watch_condition_signals":
            watch_condition_signals,

        "healthy_condition_signals":
            healthy_condition_signals,


        "convergence_ratio":
            round(
                convergence_ratio,
                4,
            ),

        "convergence_percentage":
            round(
                convergence_percentage,
                2,
            ),


        "metric_results":
            metric_results,
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    result = analyze_borrower(
        borrower_id=65
    )


    print(
        "=========================================="
    )

    print(
        "FALCON REALTY - DETERIORATION ANALYSIS"
    )

    print(
        "=========================================="
    )


    print()

    print(
        "CURRENT CONDITION"
    )


    print(
        "Critical:",
        result[
            "critical_condition_signals"
        ]
    )


    print(
        "Weak:",
        result[
            "weak_condition_signals"
        ]
    )


    print(
        "Watch:",
        result[
            "watch_condition_signals"
        ]
    )


    print(
        "Healthy:",
        result[
            "healthy_condition_signals"
        ]
    )


    print()

    print(
        "TRAJECTORY"
    )


    print(
        "Deteriorating:",
        result[
            "deteriorating_signals"
        ]
    )


    print(
        "Persistent:",
        result[
            "persistent_deterioration_signals"
        ]
    )


    print(
        "Accelerating:",
        result[
            "accelerating_deterioration_signals"
        ]
    )


    print(
        "Decelerating:",
        result[
            "decelerating_deterioration_signals"
        ]
    )


    print(
        "Convergence:",
        f'{result["convergence_percentage"]}%'
    )


    print()

    print(
        "SIGNAL DETAILS"
    )


    for metric in result[
        "metric_results"
    ]:

        print(

            metric[
                "metric_code"
            ],

            "| Current:",
            metric[
                "current_value"
            ],

            "| Condition:",
            metric[
                "condition"
            ],

            "| Severity:",
            metric[
                "condition_severity"
            ],

            "| Direction:",
            metric[
                "direction"
            ],

            "| Velocity:",
            metric[
                "risk_velocity_30d"
            ],

            "| Acceleration:",
            metric[
                "acceleration_direction"
            ],

            "| Persistence:",
            metric[
                "persistence"
            ],
        )