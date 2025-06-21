import os
import sys

# 🔧 Pfade setzen, damit Imports immer funktionieren
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# 🔄 Tools importieren
from extract_appointment import extract_appointment_from_json

from mailing.gmail_read_and_extract import run_gmail_extraction

# 📩 Test-E-Mail (optional)
STATIC_EMAIL = """Hallo Max,
wir bestätigen deinen Vorstellungstermin am 21. Juni 2025 um 14:30 Uhr
in unserem Büro in Ravensburg. Bitte sei pünktlich. Viele Grüße"""

def run_static_test():
    print("📥 Test-E-Mail analysieren...")
    result = extract_appointment_from_json(STATIC_EMAIL)
    print("📅 Analyse-Ergebnis:")
    print(result)

def run_gmail():
    print("📥 Gmail-E-Mail abrufen & analysieren...")
    run_gmail_extraction()

if __name__ == "__main__":
    # 🔁 Hier wählst du, was gestartet wird:
    MODE = "gmail"  # "static" oder "gmail"

    if MODE == "static":
        run_static_test()
    elif MODE == "gmail":
        run_gmail()
    else:
        print("❌ Unbekannter Modus:", MODE)
