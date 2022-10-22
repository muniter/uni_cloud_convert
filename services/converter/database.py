import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

USER = os.environ.get("POSTGRES_USER")
PASSWORD = os.environ.get("POSTGRES_PASSWORD")
HOST = os.environ.get("POSTGRES_HOST")
DATABASE = os.environ.get("POSTGRES_DB")

if not all([USER, PASSWORD, HOST, DATABASE]):
    raise ValueError(
        f"Missing database configuration values: \
        USER={USER},\
        PASSWORD={PASSWORD},\
        HOST={HOST},\
        DATABASE={DATABASE},\
        "
    )

SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()