import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

# .env laden
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# LLM initialisieren
llm = ChatGroq(api_key=api_key, model="llama3-8b-8192")

# Prompt definieren
prompt = PromptTemplate.from_template("""
Du bekommst eine E-Mail und sollst daraus folgende Felder im Klartext extrahieren:
- summary (Titel des Termins)
- start_datetime (z.B. 2025-06-25T10:00:00+02:00)
- end_datetime (z.B. 2025-06-25T10:00:00+02:00)
- timezone(default Berlin)
- location (wenn vorhanden)
- description (Von wem kommt die Mail und was wird passieren)
und das bitte als Json.
Mach das bitte auch wenn das nicht direkt ein Termin sondern eine Einladung ist.
Wenn nichts von einem ende drin steht dann überlege dir wie lange so ein Termin in der regel dauert.

E-Mail:
"{email}"
""")

# Chain aufbauen
parser = StrOutputParser()
chain = prompt | llm | parser

# Hauptfunktion: liest automatisch aus Datei, analysiert, gibt Ergebnis zurück
# ... (oben bleibt gleich)

def extract_appointment_from_json(path: str = "email.json") -> str:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    subject = data.get("subject", "")
    body = data.get("body", "")
    email_text = f"{subject}\n{body}".strip()
    return chain.invoke({"email": email_text})

# ✅ NEU: für direkten Text
def extract_appointment_from_text(email_text: str) -> str:
    return chain.invoke({"email": email_text})
