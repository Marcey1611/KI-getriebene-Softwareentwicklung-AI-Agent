from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

# .env laden, aber nur einmal (bei direktem Skriptstart oder Initialisierung)
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# LLM + Chain vorbereiten (nur einmal erzeugen)
llm = ChatGroq(api_key=api_key, model="llama3-8b-8192")

prompt = PromptTemplate.from_template("""
Du bekommst eine E-Mail und sollst daraus folgende Felder im Klartext extrahieren:
- Titel des Termins
- Datum (z. B. 21. Juni 2025)
- Uhrzeit (z. B. 14:30 Uhr)
- Ort (wenn vorhanden)

E-Mail:
"{email}"
""")

parser = StrOutputParser()
chain = prompt | llm | parser

# Die eigentliche Tool-Funktion
def extract_appointment(email_text: str) -> str:
    return chain.invoke({"email": email_text})
