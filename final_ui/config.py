# config.py
from pathlib import Path

KNOX_URL = "http://localhost:8080"
PORT = 5050

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "genocad" / "genocad.db"

SKIP_LETTERS = {"S", "[", "]", "(", ")", "{", "}", "CAS", "TP"}