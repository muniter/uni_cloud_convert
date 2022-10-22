import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, UniqueConstraint
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
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(
        Enum("uploaded", "processed", name="status_enum", create_type=False),
        nullable=False,
        default="uploaded",
    )
    # Unique field to ask for a specific file
    file_id = Column(String, nullable=False, index=True, unique=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    new_format = Column(String, nullable=False)
    uploaded_filename = Column(String, nullable=False)
    original_file = Column(String, nullable=False)
    original_format = Column(String, nullable=False)
    original_size = Column(Integer, nullable=False)
    processed_file = Column(String, nullable=True)
    processed_format = Column(String, nullable=True)
    processed_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
