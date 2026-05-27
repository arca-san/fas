#!/usr/bin/env python3
"""
SQLAlchemy ORM modelleri.
User, Favorite, SavedPortfolio.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from flask_login import UserMixin

from database import Base


class User(Base, UserMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # admin, analyst, viewer
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("SavedPortfolio", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fon_kodu = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")


class SavedPortfolio(Base):
    __tablename__ = "saved_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    fund_codes = Column(JSON, nullable=False)        # ["MAC", "TI2", ...]
    weights = Column(JSON, nullable=True)             # {"MAC": 40, "TI2": 30, ...}
    fon_tipi = Column(String(10), default="YAT")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="portfolios")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "fund_codes": self.fund_codes,
            "weights": self.weights,
            "fon_tipi": self.fon_tipi,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
