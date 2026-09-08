import pandas as pd

from connection import engine


# =========================================================
# METRIC CONFIGURATION
# =========================================================

METRIC_CONFIG = {
    "DSCR": {
        "bad_direction": "DOWN",
    },

    "BOUNCE_RATE": {
        "bad_direction": "UP",
    },

    "RECEIVABLE_DAYS": {
        "bad_direction": "UP",
    },

    "DEBT_EBITDA": {
        "bad_direction": "UP",
    },
}


# =========================================================
# LOAD METRIC HISTORY
# =========================================================

def get_metric_history(borrower_id, metric_code):
    """
    Load one borrower's historical observations
    for one metric from PostgreSQL.
    """

    query = """
    SELECT
        metric_value,
        observation_date
    FROM borrower_metric_observations
    WHERE borrower_id = %(borrower_id)s
      AND metric_code = %(metric_code)s
    ORDER BY observation_date
    """

    df = pd.read_sql(
        query,
        engine,
        params={
            "borrower_id": borrower_id,
            "metric_code": metric_code,
        },
    )

    return df


# =========================================================
# ANALYZE ONE TRAJECTORY
# =========================================================

def analyze_trajectory(values, bad_direction):
    """
    Analyze one metric trajectory.

    bad_direction:
        "UP"   -> increasing values mean deterioration
        "DOWN" -> decreasing values mean deterioration
    """

    if len(values) < 2:
        return {
            "current_value": None,
            "previous_value": None,
            "absolute_change": None,
            "percentage_change": None,
            "direction": "INSUFFICIENT_HISTORY",
            "persistence": 0,
        }

    current_value = float(values[-1])
    previous_value = float(values[-2])

    # -----------------------------------------------------
    # LATEST CHANGE
    # -----------------------------------------------------

    absolute_change = current_value - previous_value

    if previous_value != 0:
        percentage_change = (
            absolute_change / abs(previous_value)
        ) * 100
    else:
        percentage_change = None

    # -----------------------------------------------------
    # LATEST MOVEMENT
    # -----------------------------------------------------

    if current_value > previous_value:
        movement = "UP"

    elif current_value < previous_value:
        movement = "DOWN"

    else:
        movement = "FLAT"

    # -----------------------------------------------------
    # CREDIT-RISK INTERPRETATION
    # -----------------------------------------------------

    if movement == "FLAT":
        direction = "STABLE"

    elif movement == bad_direction:
        direction = "DETERIORATING"

    else:
        direction = "IMPROVING"

    # -----------------------------------------------------
    # PERSISTENCE
    # -----------------------------------------------------
    # Count consecutive deteriorating movements backwards
    # from the most recent observation.
    #
    # Example:
    #
    # DSCR:
    # 1.45 -> 1.31 -> 1.12 -> 0.90
    #
    # Three consecutive deteriorating movements
    # persistence = 3
    # -----------------------------------------------------

    persistence = 0

    for i in range(len(values) - 1, 0, -1):

        change = float(values[i]) - float(values[i - 1])

        if bad_direction == "UP" and change > 0:
            persistence += 1

        elif bad_direction == "DOWN" and change < 0:
            persistence += 1

        else:
            break

    return {
        "current_value": round(current_value, 4),
        "previous_value": round(previous_value, 4),
        "absolute_change": round(absolute_change, 4),

        "percentage_change": (
            round(percentage_change, 2)
            if percentage_change is not None
            else None
        ),

        "direction": direction,
        "persistence": persistence,
    }


# =========================================================
# ANALYZE ONE METRIC FOR ONE BORROWER
# =========================================================

def analyze_metric(borrower_id, metric_code):
    """
    Analyze one configured metric for one borrower.

    RiskVision automatically determines whether
    UP or DOWN represents deterioration.
    """

    metric_code = metric_code.upper()

    if metric_code not in METRIC_CONFIG:
        raise ValueError(
            f"Unknown metric_code: {metric_code}"
        )

    bad_direction = (
        METRIC_CONFIG[metric_code]["bad_direction"]
    )

    df = get_metric_history(
        borrower_id,
        metric_code,
    )

    values = df["metric_value"].tolist()

    result = analyze_trajectory(
        values,
        bad_direction,
    )

    result["borrower_id"] = borrower_id
    result["metric_code"] = metric_code
    result["bad_direction"] = bad_direction
    result["observations"] = len(values)

    return result


# =========================================================
# ANALYZE ENTIRE BORROWER
# =========================================================

def analyze_borrower(borrower_id):
    """
    Analyze every configured historical signal
    for one borrower.

    This is the first cross-signal convergence layer.
    """

    metric_results = []

    deteriorating_signals = 0
    improving_signals = 0
    stable_signals = 0
    insufficient_history_signals = 0

    # -----------------------------------------------------
    # RUN EVERY CONFIGURED METRIC
    # -----------------------------------------------------

    for metric_code in METRIC_CONFIG:

        result = analyze_metric(
            borrower_id=borrower_id,
            metric_code=metric_code,
        )

        metric_results.append(result)

        direction = result["direction"]

        if direction == "DETERIORATING":
            deteriorating_signals += 1

        elif direction == "IMPROVING":
            improving_signals += 1

        elif direction == "STABLE":
            stable_signals += 1

        elif direction == "INSUFFICIENT_HISTORY":
            insufficient_history_signals += 1

    # -----------------------------------------------------
    # NUMBER OF METRICS WITH ENOUGH HISTORY
    # -----------------------------------------------------

    metrics_analyzed = (
        deteriorating_signals
        + improving_signals
        + stable_signals
    )

    # -----------------------------------------------------
    # CROSS-SIGNAL CONVERGENCE
    # -----------------------------------------------------
    #
    # Example:
    #
    # 4 deteriorating signals / 4 analyzed signals
    # convergence_ratio = 1.0
    # convergence_percentage = 100%
    # -----------------------------------------------------

    if metrics_analyzed > 0:

        convergence_ratio = (
            deteriorating_signals
            / metrics_analyzed
        )

    else:

        convergence_ratio = 0.0

    convergence_percentage = (
        convergence_ratio * 100
    )

    # -----------------------------------------------------
    # PERSISTENT DETERIORATION
    # -----------------------------------------------------
    #
    # Count metrics where deterioration has persisted
    # for at least two consecutive movements.
    # -----------------------------------------------------

    persistent_deterioration_signals = sum(
        1
        for result in metric_results
        if result["direction"] == "DETERIORATING"
        and result["persistence"] >= 2
    )

    return {
        "borrower_id": borrower_id,

        "configured_metrics": len(METRIC_CONFIG),

        "metrics_analyzed": metrics_analyzed,

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

        "convergence_ratio":
            round(convergence_ratio, 4),

        "convergence_percentage":
            round(convergence_percentage, 2),

        "metric_results":
            metric_results,
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=========================================")
    print("FALCON REALTY - BORROWER ANALYSIS")
    print("=========================================")

    result = analyze_borrower(
        borrower_id=65
    )

    print(
        "Borrower ID:",
        result["borrower_id"]
    )

    print(
        "Metrics analyzed:",
        result["metrics_analyzed"]
    )

    print(
        "Deteriorating signals:",
        result["deteriorating_signals"]
    )

    print(
        "Improving signals:",
        result["improving_signals"]
    )

    print(
        "Stable signals:",
        result["stable_signals"]
    )

    print(
        "Persistent deterioration signals:",
        result["persistent_deterioration_signals"]
    )

    print(
        "Convergence:",
        f'{result["convergence_percentage"]}%'
    )

    print()

    print("METRIC DETAILS")

    for metric in result["metric_results"]:

        print(
            metric["metric_code"],
            "->",
            metric["direction"],
            "| Current:",
            metric["current_value"],
            "| Change:",
            metric["percentage_change"],
            "%",
            "| Persistence:",
            metric["persistence"],
        )