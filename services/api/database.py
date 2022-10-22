import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Important: https://towardsdatascience.com/use-flask-and-sqlalchemy-not-flask-sqlalchemy-5a64fafe22a4

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
Base.query = db_session.query_property()


def init_db():
    import models

    Base.metadata.create_all(bind=engine)
    # Look for user with id=1
    user = models.User.query.filter_by(id=1).one_or_none()
    if not user:
        email = os.environ.get("EMAIL_USER", "admin@admin.com")
        user = models.User(username="admin", email=email, password="admin")
        db_session.add(user)
        db_session.commit()
