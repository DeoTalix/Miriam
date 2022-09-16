import os
from loguru import logger
from dotenv import load_dotenv



cwd = os.getcwd()
assert os.path.exists(os.path.join(cwd, ".env")), "Для работы приложения необходим файл .env"

load_dotenv()


# TELEGRAM
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

# QIWI
QIWI_SECRET_KEY = os.getenv("QIWI_SECRET_KEY")
BILL_LIFETIME = 5

assert TELEGRAM_API_TOKEN is not None, "Для работы приложения необходим TELEGRAM_API_TOKEN"
assert QIWI_SECRET_KEY is not None, "Для работы приложения необходим QIWI_SECRET_KEY"

# LOGGING
LOGGER_PATH = os.path.join(cwd, "logs")
LOGGER_DEFAULT_LEVEL = "INFO"

logger.add(
    os.path.join(LOGGER_PATH, "debug.log"), 
    level="DEBUG", 
    rotation="1 week", 
    compression="zip",
    enqueue=True,
)
logger.add(
    os.path.join(LOGGER_PATH, "warning.log"), 
    level="WARNING",
    rotation="1 week", 
    compression="zip",
    enqueue=True,
)

# BACKEND
# настройки бэкенда находятся в файле backend/backend/settings.py

BACKEND_URL = "http://127.0.0.1:8000"
ADMIN_URL = os.path.join(BACKEND_URL, "admin")