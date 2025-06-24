import os
import sys
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool, tool
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)


# 🔐 .env laden
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

# 🧠 LLM initialisieren
#llm = ChatGroq(api_key=api_key, model="llama3-8b-8192")
llm =  ChatOpenAI(api_key=openai_key,)


# 🛠️ Gmail Toolkit vorbereiten
credentials = get_gmail_credentials(
    token_file=os.getenv("GOOGLE_MAIL_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://mail.google.com/"],
)
resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=resource)
gmail_tools = toolkit.get_tools()

# ✅ Tools extrahieren
search_tool = next(t for t in gmail_tools if t.name == "search_gmail")
get_tool = next(t for t in gmail_tools if t.name == "get_gmail_message")

# 🔁 Single-Input Wrapper
@tool
def search_gmail_tool(query: str) -> str:
    """Suche in Gmail-E-Mails nach einem bestimmten Betreff (z. B. 'Termin') und gibt die Message-ID der ersten E-Mail zurück."""
    results = search_tool.run({"query": query, "maxResults": 1})
    if not results:
        return "Keine E-Mail gefunden."
    return results[0]["id"]

@tool
def get_gmail_message_tool(message_id: str) -> str:
    """Lädt den Inhalt einer Gmail-Nachricht per ID und gibt ihn als Klartext zurück (Betreff + Snippet)."""
    message = get_tool.run({"message_id": message_id})
    subject = ""
    for header in message.get("payload", {}).get("headers", []):
        if header["name"].lower() == "subject":
            subject = header["value"]
    return f"{subject}\n{message.get('snippet', '')}"

# 🧩 Eigenes Analyse-Tool
from app.tools.extract_appointment import extract_appointment_from_text
from app.custom_calendar_tools.calendar_tool import create_event_from_json

extract_tool = Tool(
    name="extract_appointment",
    func=extract_appointment_from_text,
    description="Analysiert eine E-Mail und extrahiert Termin-Infos wie Datum, Uhrzeit, Ort."
)

create_event_tool = Tool(
    name="create_event_via_llm",
    func=create_event_from_json,
    description=(
        "Erstellt einen Google-Kalendertermin. "
        "Eingabe ist ein gültiges JSON mit folgenden Feldern:\n"
        "- summary (z. B. 'Meeting mit Anna' hier soll also der Titel des Kalendereintrages rein.)\n"
        "- start_datetime (z. B. '2025-06-24T10:00:00+02:00' hier soll also der Beginn des Kalendereintrages rein.)\n"
        "- end_datetime (z. B. '2025-06-24T11:00:00+02:00' hier soll also das Ende des Kalendereintrages rein.)\n"
        "- timezone (z. B. 'Europe/Berlin' hier soll also die Zeitzone des Kalendereintrages rein.)\n"
        "- location (z. B. 'Berlin' hier soll also der Ort des Kalendereintrages rein.)\n"
        "- description (z. B. 'Dies ist eine Erinnerung an das Meeting mit Anna.' hier soll also die Beschreibung des Kalendereintrages rein.)\n"
        "Bitte gebe als Parameter nur ein valides JSON, beginnen und endend mit einer geschweiften Klammer, mit keine sonstigen EIngaben von dir!"

    )
)
# 🤖 Agent bauen
agent = initialize_agent(
    tools=[search_gmail_tool, get_gmail_message_tool, extract_tool,create_event_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

def run_agent(msg_id):
    print(f"🤖 Agent ruft Nachricht mit ID: {msg_id}")
    query = (
        f"Lade die Gmail-Nachricht mit der ID {msg_id}. "
        "Analysiere, ob es um einen Termin/Einladung geht. "
        "Mache danach eine Erinnerung im Kalender mit den Daten Titel, Datum, Uhrzeit und Ort"
        #"Wenn ja, extrahiere Titel, Datum, Uhrzeit und Ort."
        "Wenn nein, tu nichts und sag mir Bescheid."
    )
    response = agent.invoke(query)
    print("\n📅 Antwort:")
    print(response)
