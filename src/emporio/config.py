import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "emporio.db"
POLICY_PDF = DATA_DIR / "politicas_da_loja.pdf"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

MAX_TOOL_ROUNDS = 6
HISTORY_TURNS = 12

STORE_NAME = "Empório da Música"
STORE_ADDRESS = "Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, 79202-333"
STORE_WHATSAPP = "(67) 3321-4500"
STORE_PHONE = "(67) 3341-4444"
STORE_EMAIL = "contato@emporiodamusica.com.br"


def today() -> date:
    """Reference date for every deadline calculation.

    The dataset is a snapshot whose last order is from March 2026. EMPORIO_TODAY
    pins the clock so the examples and the tests stay reproducible; without it
    the real system date is used.
    """
    override = os.getenv("EMPORIO_TODAY")
    return date.fromisoformat(override) if override else date.today()


def now() -> datetime:
    """Wall clock, on the reference date.

    "Está aberto agora?" needs the hour, which no dataset carries, so the time
    of day is always the real one. Only the date is pinned, otherwise a run with
    EMPORIO_TODAY set to a Sunday would still report the store open.
    """
    clock = datetime.now()
    return clock.replace(year=today().year, month=today().month, day=today().day)
