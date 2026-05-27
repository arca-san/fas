#!/usr/bin/env python3
"""
Flask-Login auth yapılandırması. Login/logout yardımcıları.
"""

from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db
from models import User

login_manager = LoginManager()
login_manager.login_view = "/giris"


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    try:
        return db.query(User).filter(User.id == int(user_id)).first()
    finally:
        db.close()


def init_auth(server):
    """Flask-Login'i başlat ve varsayılan admin kullanıcısını oluştur."""
    login_manager.init_app(server)

    # Varsayılan admin kullanıcısı (ilk çalıştırmada)
    db = get_db()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            import logging
            logging.getLogger(__name__).info("Varsayılan admin kullanıcısı oluşturuldu (admin/admin)")
    finally:
        db.close()


def try_login(username: str, password: str):
    """Kullanıcı adı/şifre doğrula. Başarılıysa login_user() çağır."""
    db = get_db()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return True, "Giriş başarılı"
        return False, "Kullanıcı adı veya şifre hatalı"
    finally:
        db.close()


def require_role(role: str):
    """Decorator: belirli role sahip kullanıcı gerektirir."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return {"error": "login required"}, 401
            if role == "admin" and current_user.role != "admin":
                return {"error": "admin required"}, 403
            return f(*args, **kwargs)
        return wrapped
    return decorator
