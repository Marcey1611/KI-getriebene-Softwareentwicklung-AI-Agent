import os
import sys
from dotenv import load_dotenv
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)

# 🔧 Pfad für tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.extract_appointment import extract_appointment_from_text

load_dotenv()

# 🔐 Authentifiziere mit Google einmalig beim Laden
credentials = get_gmail_credentials(
    token_file=os.path.join(os.path.dirname(__file__), "token.json"),
    client_secrets_file=os.path.join(os.path.dirname(__file__), "credentials.json"),
    scopes=["https://mail.google.com/"],  # WICHTIG: voller Zugriff
)

api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)
tools = toolkit.get_tools()

# Tool-Referenzen (global für alle Funktionen)
gmail_search = next((t for t in tools if t.name == "search_gmail"), None)
gmail_get = next((t for t in tools if t.name == "get_gmail_message"), None)

def run_gmail_extraction():
    print("🛠️ Verfügbare Tools:")
    for t in tools:
        print("-", t.name)

    if gmail_search is None or gmail_get is None:
        print("❌ Fehler: Tools `search_gmail` oder `get_gmail_message` wurden nicht geladen.")
        print("💡 Lösung: Stelle sicher, dass du die richtigen OAuth-Scopes erlaubt hast.")
        return

    print("🔍 Suche nach E-Mail mit Betreff 'Termin' ...")
    search_result = gmail_search.run({
        "query": "subject:Termin",
        "maxResults": 1
    })

    if not search_result or not isinstance(search_result, list):
        print("❌ Keine passende E-Mail gefunden.")
        return

    message_id = search_result[0]["id"]
    result = analyze_message_by_id(message_id)

    print("📅 Analyse-Ergebnis:")
    print(result)

def analyze_message_by_id(message_id: str) -> str:
    if gmail_get is None:
        raise RuntimeError("❌ Tool `get_gmail_message` ist nicht verfügbar!")

    print(f"📩 Lade Nachricht mit ID: {message_id}")
    message_data = gmail_get.run({"message_id": message_id})

    subject = ""
    for header in message_data.get("payload", {}).get("headers", []):
        if header["name"].lower() == "subject":
            subject = header["value"]

    email_text = f"{subject}\n{message_data.get('snippet', '')}"
    print("📥 E-Mail-Inhalt übergeben an Analyse-Modell ...")
    return extract_appointment_from_text(email_text)
