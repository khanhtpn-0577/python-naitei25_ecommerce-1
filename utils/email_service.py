import os
from django.core.mail import send_mail
import requests
import logging
logger = logging.getLogger(__name__)

def send_activation_email(email, username, uidb64, token):
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@example.com")
    SITE_URL = os.environ.get("SITE_URL", "http://localhost:8000")
    activation_link = f"{SITE_URL}/user/activate/{uidb64}/{token}/"
    subject = "Kích hoạt tài khoản của bạn"
    message = f"Xin chào {username},\n\nVui lòng nhấn vào liên kết sau để kích hoạt tài khoản:\n{activation_link}\n\nCảm ơn!"
    send_mail(subject, message, DEFAULT_FROM_EMAIL, [email])


def is_valid_email(email):
    API_KEY = os.environ.get("ABSTRACT_API_KEY")
    if not API_KEY:
        logger.error("ABSTRACT_API_KEY is not configured in environment.")
        return False
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={API_KEY}&email={email}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        # Kiểm tra email hợp lệ, tồn tại mailbox
        if data.get("is_valid_format", {}).get("value") and data.get("is_smtp_valid", {}).get("value"):
            return True
        return False
    except requests.RequestException:
        return False
