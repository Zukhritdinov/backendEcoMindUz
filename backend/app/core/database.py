from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Uses local database for dev outside docker or docker db container depending on env
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost:5432/ecominduz"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
