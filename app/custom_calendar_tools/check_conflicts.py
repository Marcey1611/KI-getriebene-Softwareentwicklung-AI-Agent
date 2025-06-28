from langchain.tools import tool, Tool
from app.rag.rag_calendar import get_similar_events

from dateutil import parser

@tool
def check_conflicts(start_datetime: str) -> str:
    """Prüft, ob zu dem angegebenen Zeitpunkt bereits ein Termin im Kalender existiert."""
    try:
        print(f"Prüfe Konflikte für: {start_datetime}")

        # Startzeit parsen und im richtigen Format (ohne 'T') speichern
        target_time = parser.parse(start_datetime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Vergleichszeitpunkt (formatiert): {target_time}")

        matches = get_similar_events(start_datetime, k=100)

        for doc in matches:
            first_line = doc.page_content.split("\n")[0].strip()
            print("Gespeicherte Event-Zeit:", first_line)
            if first_line == target_time:
                return "⚠️ Konflikt: Bereits ein Termin zum gleichen Zeitpunkt vorhanden."

        return "✅ Kein Konflikt gefunden."

    except Exception as e:
        return f"Fehler bei der Konfliktprüfung: {e}"
