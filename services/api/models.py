import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False, default="uploaded")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    original_file = Column(String, nullable=False)
    original_format = Column(String, nullable=False)
    original_size = Column(Integer, nullable=False)

    processed_file = Column(String, nullable=False)
    processed_format = Column(String, nullable=False)
    processed_size = Column(Integer, nullable=False)

    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
