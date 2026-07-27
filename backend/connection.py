from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:william4256@localhost:5432/risk_platform"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

db = SessionLocal()

query = text("""
INSERT INTO borrowers (borrower_name, sector, loan_amount)
VALUES (:name, :sector, :loan_amount)
""")

db.execute(query, {
    "name": "ABC Ltd",
    "sector": "Manufacturing",
    "loan_amount": 5000000
})

db.commit()

print("Borrower inserted successfully")