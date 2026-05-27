#!/usr/bin/env python3
"""
WebSocket altyapısı — gerçek zamanlı veri güncellemeleri için iskelet.

flask-socketio ile Dash'in yanında çalışır.
Not: TEFAS rate-limit'i (10s) nedeniyle gerçek zamanlı TEFAS verisi mümkün değil.
Bu modül ileride harici veri kaynağı (Yahoo Finance, BIST feed) ile
doldurulmak üzere altyapı sağlar.
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*")

# Bağlı kullanıcılar (room bazında)
connected_users = {}


def init_socketio(app):
    """SocketIO'yu Flask uygulamasına bağla."""
    socketio.init_app(app, async_mode=None)
    logger.info("WebSocket başlatıldı")


@socketio.on("connect")
def handle_connect():
    """Yeni bağlantı — client ID logla."""
    sid = request.sid
    logger.debug("WebSocket bağlandı: %s", sid)


@socketio.on("disconnect")
def handle_disconnect():
    """Bağlantı koptu — temizlik."""
    sid = request.sid
    logger.debug("WebSocket koptu: %s", sid)


@socketio.on("subscribe")
def handle_subscribe(data):
    """Belirli bir sembole abone ol."""
    symbol = data.get("symbol", "").upper()
    if symbol:
        join_room(symbol)
        logger.debug("Abone olundu: %s", symbol)


@socketio.on("unsubscribe")
def handle_unsubscribe(data):
    """Abonelikten çık."""
    symbol = data.get("symbol", "").upper()
    if symbol:
        leave_room(symbol)


def emit_price_update(symbol: str, price: float, change: float = None):
    """Fiyat güncellemesi yayınla (abonelere)."""
    data = {
        "symbol": symbol,
        "price": price,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    if change is not None:
        data["change"] = change
    socketio.emit("price_update", data, room=symbol)
