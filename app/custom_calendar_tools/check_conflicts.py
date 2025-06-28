#app/custom_calendar_tools/check_conflicts.py
from langchain.tools import tool
from app.rag.rag_calendar import get_similar_events
from dateutil import parser
from app.utils.logger import logger

@tool
def check_conflicts(start_datetime: str) -> str:
    """Checks whether an appointment already exists in the calendar at the specified time."""
    try:
        logger.debug(" - Checking conflict for start datetime: %s", start_datetime)
        target_time = parser.parse(start_datetime).strftime("%Y-%m-%d %H:%M:%S")
        matches = get_similar_events(start_datetime, k=100)

        for doc in matches:
            first_line = doc.page_content.split("\n")[0].strip()
            if first_line == target_time:
                return "Found a conflict with an existing event for the start datetime."
        return "No conflicts were found for the specified start datetime."

    except Exception as exception:
        logger.error(" - Error checking conflicts: %s", exception)
        return "Error checking conflicts!"
