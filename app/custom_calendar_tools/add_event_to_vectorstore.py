#app/custom_calendar_tools/add_event_to_vectorstore.py
from langchain.tools import tool
from app.rag.rag_calendar import load_vectorstore, print_all_vectorstore_texts
import json
from app.utils.logger import logger

@tool
def add_event_to_vectorstore(json_str: str) -> str:
    """Saves a calendar event to the vector store. Expects a JSON with: summary, start_datetime, description, location."""
    data = extract_clean_json(json_str)
    logger.debug(" - Extracted JSON: %s", data)
    if isinstance(data, str):
        data = json.loads(data)
    logger.debug(" - Parsed JSON:", data)
    try:
        summary = data.get("summary", "")
        start_datetime = data.get("start_datetime", "")
        description = data.get("description", "")
        location = data.get("location", "")
        text = f"{start_datetime}\n{summary}\n{description}\n{location}"
        vectorstore = load_vectorstore()
        vectorstore.add_texts([text])
        vectorstore.save_local("calendar_faiss_index")
        return "Event stored successfully in the vectorstore."
    except Exception as exception:
        logger.error(" - Error storing event in vectorstore: %s", exception)
        return "Error storing event in vectorstore."
    finally:
        print_all_vectorstore_texts()

def extract_clean_json(s: str) -> str | None:
    start = s.find('{')
    if start == -1:
        return None

    s = s[start:]

    brace_count = 0
    for i, c in enumerate(s):
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                return s[:i+1]
  
    return None