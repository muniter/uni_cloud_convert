from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "Records"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
