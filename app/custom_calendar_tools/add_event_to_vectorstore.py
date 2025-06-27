from langchain.tools import tool
from app.rag.rag_calendar import load_vectorstore
import json

@tool
def add_event_to_vectorstore(json_str: str) -> str:
    """
    Speichert einen Kalender-Termin im Vektorstore.
    Erwartet ein JSON mit: summary, start_datetime, description, location.
    """
    data = extract_clean_json(json_str)
    print("Extracted JSON:", data)
    if isinstance(data, str):
        data = json.loads(data)
    print("Parsed JSON:", data)
    try:
        summary = data.get("summary", "")
        start_datetime = data.get("start_datetime", "")
        description = data.get("description", "")
        location = data.get("location", "")
        text = f"{start_datetime}\n{summary}\n{description}\n{location}"
        vectorstore = load_vectorstore()
        vectorstore.add_texts([text])
        return "✅ Termin im Vektorstore gespeichert."
    except Exception as e:
        return f"Fehler beim Speichern im Vektorstore: {e}"
    finally:
        print_all_vectorstore_texts()

def extract_clean_json(s: str) -> str | None:
    # Schritt 1: Alles vor dem ersten { entfernen
    start = s.find('{')
    if start == -1:
        return None

    s = s[start:]  # Schneide vorne ab

    # Schritt 2: Jetzt nach balancierten {} suchen
    brace_count = 0
    for i, c in enumerate(s):
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                return s[:i+1]  # inkl. letzter geschlossener Klammer

    return None  # Falls nie geschlossen

def print_all_vectorstore_texts():
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search("", k=100)  # oder ein anderer allgemeiner Begriff
    for i, doc in enumerate(results, 1):
        print(f"\n📄 Event {i}:\n{doc.page_content}")