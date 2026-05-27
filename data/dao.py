#!/usr/bin/env python3
"""
Kullanıcı verileri için DAO (Data Access Object).
Favoriler, kayıtlı portföyler için CRUD işlemleri.
"""

from database import get_db
from models import User, Favorite, SavedPortfolio


# ── Favoriler ──────────────────────────────────────────────────────────

def get_favorites(user_id: int):
    db = get_db()
    try:
        return [f.fon_kodu for f in db.query(Favorite).filter(Favorite.user_id == user_id).all()]
    finally:
        db.close()


def add_favorite(user_id: int, fon_kodu: str):
    db = get_db()
    try:
        existing = db.query(Favorite).filter(
            Favorite.user_id == user_id, Favorite.fon_kodu == fon_kodu
        ).first()
        if not existing:
            fav = Favorite(user_id=user_id, fon_kodu=fon_kodu)
            db.add(fav)
            db.commit()
        return True
    finally:
        db.close()


def remove_favorite(user_id: int, fon_kodu: str):
    db = get_db()
    try:
        fav = db.query(Favorite).filter(
            Favorite.user_id == user_id, Favorite.fon_kodu == fon_kodu
        ).first()
        if fav:
            db.delete(fav)
            db.commit()
        return True
    finally:
        db.close()


def sync_favorites(user_id: int, fon_kodlari: list):
    """Favori listesini tamamen senkronize et (mevcutları sil, yenilerini ekle)."""
    db = get_db()
    try:
        db.query(Favorite).filter(Favorite.user_id == user_id).delete()
        for kod in fon_kodlari:
            db.add(Favorite(user_id=user_id, fon_kodu=kod))
        db.commit()
        return True
    finally:
        db.close()


# ── Portföyler ─────────────────────────────────────────────────────────

def list_portfolios(user_id: int):
    db = get_db()
    try:
        return [p.to_dict() for p in
                db.query(SavedPortfolio).filter(SavedPortfolio.user_id == user_id)
                .order_by(SavedPortfolio.updated_at.desc()).all()]
    finally:
        db.close()


def save_portfolio(user_id: int, name: str, fund_codes: list, weights: dict = None, fon_tipi: str = "YAT"):
    db = get_db()
    try:
        existing = db.query(SavedPortfolio).filter(
            SavedPortfolio.user_id == user_id, SavedPortfolio.name == name
        ).first()
        if existing:
            existing.fund_codes = fund_codes
            existing.weights = weights
            existing.fon_tipi = fon_tipi
        else:
            pf = SavedPortfolio(
                user_id=user_id, name=name,
                fund_codes=fund_codes, weights=weights, fon_tipi=fon_tipi,
            )
            db.add(pf)
        db.commit()
        return True
    finally:
        db.close()


def delete_portfolio(portfolio_id: int, user_id: int):
    db = get_db()
    try:
        pf = db.query(SavedPortfolio).filter(
            SavedPortfolio.id == portfolio_id, SavedPortfolio.user_id == user_id
        ).first()
        if pf:
            db.delete(pf)
            db.commit()
        return True
    finally:
        db.close()
