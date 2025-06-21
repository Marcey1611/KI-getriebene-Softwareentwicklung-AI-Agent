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
- Titel des Termins
- Datum (z. B. 21. Juni 2025)
- Uhrzeit (z. B. 14:30 Uhr)
- Ort (wenn vorhanden)

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
