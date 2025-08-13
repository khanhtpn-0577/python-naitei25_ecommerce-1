import os
import requests
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string


def verify_email(email):
    
    API_KEY = os.environ.get("ABSTRACT_API_KEY")
    url = "https://emailvalidation.abstractapi.com/v1/"
    params = {
        "api_key": API_KEY,
        "email": email
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    # Kiểm tra hợp lệ
    if data.get("deliverability") == "DELIVERABLE":
        return True
    return False


def send_welcome_email(user_email, username):
    subject = "Chào mừng bạn đến với Website!"
    context = {
        "username": username,
    }
    html_content = render_to_string("emails/welcome_email.html", context)

    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=None,  # None => DEFAULT_FROM_EMAIL
        to=[user_email],
    )
    email.content_subtype = "html"  # gửi HTML
    email.send()
    

def send_activation_email(email, username, uidb64, token):
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
    SITE_URL = os.environ.get("SITE_URL")
    activation_link = f"{SITE_URL}/user/activate/{uidb64}/{token}/"
    subject = "Kích hoạt tài khoản của bạn"
    message = f"Xin chào {username},\n\nVui lòng nhấn vào liên kết sau để kích hoạt tài khoản:\n{activation_link}\n\nCảm ơn!"
    send_mail(subject, message, DEFAULT_FROM_EMAIL, [email])
