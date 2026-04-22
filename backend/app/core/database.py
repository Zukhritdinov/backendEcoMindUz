from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Uses local database for dev outside docker or docker db container depending on env
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:dUUGWvFJgxWmhVIamicsgQSvgiduUFQc@postgres.railway.internal:5432/railway"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
