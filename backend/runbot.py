import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from telegram_bot import start_service

if __name__ == "__main__":
    start_service()