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
api_key = os.getenv("GROQ_API_KEY")#
openai_key ="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"

# 🧠 LLM initialisieren
#llm = ChatGroq(api_key=api_key, model="llama3-8b-8192")
llm =  ChatOpenAI(api_key=openai_key,)


# 🛠️ Gmail Toolkit vorbereiten
credentials = get_gmail_credentials(
    token_file=os.path.join(os.path.dirname(__file__), "../mailing/token.json"),
    client_secrets_file=os.path.join(os.path.dirname(__file__), "../mailing/credentials.json"),
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
from app.calendar.calendar_tool import create_event_from_json

extract_tool = Tool(
    name="extract_appointment",
    func=extract_appointment_from_text,
    description="Analysiert eine E-Mail und extrahiert Termin-Infos wie Datum, Uhrzeit, Ort."
)

create_event_via_llm_function = Tool(
    name="create_event_via_llm",
    description="Erstellt einen Kalendereintrag aus einem JSON",
    func=create_event_from_json,
)
# 🤖 Agent bauen
agent = initialize_agent(
    tools=[search_gmail_tool, get_gmail_message_tool, extract_tool,create_event_via_llm_function],
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
