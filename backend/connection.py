import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_FILE)

DEMO_MODE = os.getenv("RISK_DEMO_MODE") == "1"

required_variables = [
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

missing_variables = [
    variable for variable in required_variables
    if not os.getenv(variable)
]

if missing_variables and not DEMO_MODE:
    raise RuntimeError(
        f"Missing environment variables: {', '.join(missing_variables)}"
    )


DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")) if not DEMO_MODE else 5432,
    database=os.getenv("DB_NAME"),
)

if DEMO_MODE:
    demo_path = Path(__file__).resolve().parent / ".demo" / "riskvision.sqlite3"
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        URL.create("sqlite", database=str(demo_path)),
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
