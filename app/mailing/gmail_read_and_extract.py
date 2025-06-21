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

def run_gmail_extraction():
    print("🔐 Authentifiziere mit Google ...")
    credentials = get_gmail_credentials(
        token_file=os.path.join(os.path.dirname(__file__), "token.json"),
        client_secrets_file=os.path.join(os.path.dirname(__file__), "credentials.json"),
        scopes=["https://mail.google.com/"],  # WICHTIG: voller Zugriff
    )

    print("🔌 Gmail-API verbinden ...")
    api_resource = build_resource_service(credentials=credentials)
    toolkit = GmailToolkit(api_resource=api_resource)
    tools = toolkit.get_tools()

    print("🛠️ Verfügbare Tools:")
    for t in tools:
        print("-", t.name)

    gmail_search = next((t for t in tools if t.name == "search_gmail"), None)
    gmail_get = next((t for t in tools if t.name == "get_gmail_message"), None)

    if gmail_search is None or gmail_get is None:
        print("❌ Fehler: Tools `gmail_search` oder `gmail_get_message` wurden nicht geladen.")
        print("💡 Lösung: Stelle sicher, dass du die richtigen OAuth-Scopes erlaubt hast.")
        print("🔁 Versuche evtl. erneut mit einem neuen Token.")
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
    message_data = gmail_get.run({"message_id": message_id})

    subject = ""
    for header in message_data.get("payload", {}).get("headers", []):
        if header["name"].lower() == "subject":
            subject = header["value"]

    email_text = f"{subject}\n{message_data.get('snippet', '')}"
    print("📥 E-Mail-Inhalt übergeben an Analyse-Modell ...")
    result = extract_appointment_from_text(email_text)

    print("📅 Analyse-Ergebnis:")
    print(result)
