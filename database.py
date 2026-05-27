#!/usr/bin/env python3
"""
Veritabanı başlatma ve session yönetimi.
SQLite (geliştirme) → PostgreSQL (üretim) geçişine hazır.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config.settings import PROJECT_ROOT, DATABASE_URL as CFG_DATABASE_URL

DATABASE_URL = CFG_DATABASE_URL or os.environ.get("FAS_DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data' / 'fas.db'}")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db(app=None):
    """Tüm tabloları oluştur. Flask init_app olarak da kullanılabilir."""
    from models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
    if app:
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            SessionLocal.remove()


def get_db():
    """Yeni bir DB session döndürür."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def get_session():
    """Context manager olarak kullanılabilir session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
