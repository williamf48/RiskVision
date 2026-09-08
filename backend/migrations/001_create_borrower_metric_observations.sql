CREATE TABLE IF NOT EXISTS borrower_metric_observations (

    id SERIAL PRIMARY KEY,

    borrower_id INTEGER NOT NULL
        REFERENCES borrowers(id),

    metric_code TEXT NOT NULL,

    metric_value NUMERIC NOT NULL,

    observation_date DATE NOT NULL,

    period_start DATE,
    period_end DATE,

    reporting_frequency TEXT NOT NULL,

    source TEXT NOT NULL DEFAULT 'SYNTHETIC',

    data_quality TEXT NOT NULL DEFAULT 'VALID',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_reporting_frequency
        CHECK (
            reporting_frequency IN (
                'DAILY',
                'WEEKLY',
                'MONTHLY',
                'QUARTERLY',
                'ANNUAL',
                'EVENT'
            )
        ),

    CONSTRAINT valid_data_quality
        CHECK (
            data_quality IN (
                'VALID',
                'ESTIMATED',
                'STALE'
            )
        ),

    CONSTRAINT uq_borrower_metric_date_source
        UNIQUE (
            borrower_id,
            metric_code,
            observation_date,
            source
        ),

    CONSTRAINT valid_period_range
        CHECK (
            period_start IS NULL
            OR period_end IS NULL
            OR period_end >= period_start
        )
);