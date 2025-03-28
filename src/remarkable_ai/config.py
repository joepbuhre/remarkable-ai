# src/remarkable_ai/config.py
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_FOLDER = os.getenv("EMAIL_FOLDER")

OPENAPI_APIKEY = os.getenv("OPENAPI_APIKEY")

EMAIL_SMTP = os.getenv("EMAIL_SMTP")
SMTP_PORT = os.getenv("SMTP_PORT")


WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8000))
