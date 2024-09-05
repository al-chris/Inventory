# backend/database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL = "sqlite:///./inventory.db"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)  # New creation date field
    items = relationship("Item", back_populates="category")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    quantity = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime, default=datetime.utcnow)  # New creation date field
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated at field

    category = relationship("Category", back_populates="items")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    quantity_change = Column(Integer, nullable=True)
    description = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item")
    category = relationship("Category")


# Create tables
Base.metadata.create_all(bind=engine)
