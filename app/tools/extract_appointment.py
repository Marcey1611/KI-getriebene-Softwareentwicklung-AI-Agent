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

prompt = PromptTemplate.from_template("""
You are an assistant that extracts calendar event data from emails.

Your task is to extract and return the following fields in JSON format:
- summary: The title or subject of the appointment or meeting
- start_datetime: Start time in ISO 8601 format (e.g. 2025-06-25T10:00:00+02:00)
- end_datetime: End time in ISO 8601 format; estimate if not explicitly given
- timezone: Timezone of the event (default to 'Europe/Berlin' if unclear)
- location: Location or address (if available. If not put an empty String)
- description: What the event is about

Even if the email is an invitation or informal scheduling message, do your best to infer these fields.

Input email:
\"\"\"{email}\"\"\"
""".strip())

chain = prompt | llm | StrOutputParser()


def extract_appointment_from_text(email_text: str) -> dict:
    if not email_text.strip():
        raise ValueError("Email text cannot be empty.")
    result_str = chain.invoke({"email": email_text})

    # Versuch, JSON-String zu extrahieren falls umgeben von Text
    try:
        # Falls result_str nur JSON ist:
        return json.loads(result_str)
    except json.JSONDecodeError:
        # Versuch, JSON-Teil aus Text zu extrahieren (z.B. mit Regex)
        import re
        match = re.search(r'\{.*\}', result_str, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse LLM output as JSON. Output was: {result_str}")
