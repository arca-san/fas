#!/usr/bin/env python3
"""
E-posta bildirimleri modülü.
Flask-Mail ile SMTP üzerinden e-posta gönderimi.

Kullanım için .env dosyasında şu değişkenler tanımlı olmalı:
    FAS_SMTP_HOST=smtp.gmail.com
    FAS_SMTP_PORT=587
    FAS_SMTP_USER=ornek@gmail.com
    FAS_SMTP_PASS=uygulama_sifresi
    FAS_ALERT_EMAIL=ornek@gmail.com

Örnek:
    from components.notifications import send_alert
    send_alert("Portföy Uyarısı", "MAC fonu %5 düştü", ["ornek@email.com"])
"""

import os
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# SMTP config from .env
SMTP_HOST = os.environ.get("FAS_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("FAS_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("FAS_SMTP_USER", "")
SMTP_PASS = os.environ.get("FAS_SMTP_PASS", "")
ALERT_EMAIL = os.environ.get("FAS_ALERT_EMAIL", "")

ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def send_alert(subject: str, body: str, recipients: list = None):
    """E-posta uyarısı gönder. SMTP yapılandırılmamışsa sessizce geç."""
    if not ENABLED:
        logger.debug("E-posta uyarısı atlandı (SMTP yapılandırılmamış): %s", subject)
        return False

    if not recipients:
        recipients = [ALERT_EMAIL] if ALERT_EMAIL else []

    if not recipients:
        logger.debug("E-posta uyarısı atlandı (alıcı yok): %s", subject)
        return False

    try:
        import smtplib
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = f"[FAS] {subject}"
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        logger.info("E-posta uyarısı gönderildi: %s → %s", subject, recipients)
        return True

    except Exception as exc:
        logger.warning("E-posta gönderilemedi: %s", exc)
        return False


def send_daily_report(html_content: str, recipients: list = None):
    """HTML içerikli günlük rapor e-postası."""
    if not ENABLED:
        return False

    if not recipients:
        recipients = [ALERT_EMAIL] if ALERT_EMAIL else []

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "[FAS] Günlük Rapor"
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(recipients or [])
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        return True
    except Exception as exc:
        logger.warning("Günlük rapor e-postası gönderilemedi: %s", exc)
        return False
