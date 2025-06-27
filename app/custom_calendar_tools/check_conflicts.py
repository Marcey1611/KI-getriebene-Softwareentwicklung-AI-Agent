from langchain.tools import tool, Tool
from app.rag.rag_calendar import get_similar_events

@tool
def check_conflicts(start_datetime: str) -> str:
    """Prüft, ob zu dem angegebenen Zeitpunkt bereits ein Termin im Kalender existiert."""
    try:
        print(f"Prüfe Konflikte für: {start_datetime}")
        matches = get_similar_events(start_datetime, k=100)
        if any(start_datetime[:16] in doc.page_content for doc in matches):
            return "⚠️ Konflikt: Bereits ein Termin zum gleichen Zeitpunkt vorhanden."
        return "✅ Kein Konflikt gefunden."
    except Exception as e:
        return f"Fehler bei der Konfliktprüfung: {e}"