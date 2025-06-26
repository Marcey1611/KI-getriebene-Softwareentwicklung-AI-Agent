# calendar_tool.py
from langchain_google_community.calendar.utils import get_google_credentials, build_resource_service
from langchain_google_community import CalendarToolkit
from langchain_core.tools import tool
from datetime import datetime
import json
import os

cal_credentials = get_google_credentials(
    token_file=os.getenv("GOOGLE_CALENDAR_TOKEN"),
    scopes=["https://www.googleapis.com/auth/calendar"],
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS")
)

service = build_resource_service(cal_credentials)
cal_toolkit = CalendarToolkit(api_resource=service)
calendar_tool = [t for t in cal_toolkit.get_tools() if t.name == "create_calendar_event"][0]


def create_event_via_llm(summary: str, start_datetime: str, end_datetime: str, timezone: str, location: str,description:str=None) -> str:
    """Creates a google calendar event."""
    try:
        start = datetime.fromisoformat(start_datetime).strftime("%Y-%m-%d %H:%M:%S")
        end = datetime.fromisoformat(end_datetime).strftime("%Y-%m-%d %H:%M:%S")
        return calendar_tool.invoke({
            "summary": summary,
            "start_datetime": start,
            "end_datetime": end,
            "timezone": timezone,
            "location": location,
            "conference_data": False,
            "description":description
        })
    except Exception:
        return "Error creating calendar event."
    
@tool
def create_event_from_json(json_payload) -> str:
    """Erstellt ein Kalender-Event aus einem JSON-Objekt oder JSON-String mit summary, start_datetime, end_datetime, timezone, description."""
    try:
        json_payload = extract_clean_json(json_payload)
        print("Extracted JSON:", json_payload)
        if isinstance(json_payload, str):
            data = json.loads(json_payload)
        else:
            data = json_payload
        print("Parsed JSON:", data)
        return create_event_via_llm(
            summary=data["summary"],
            start_datetime=data["start_datetime"],
            end_datetime=data["end_datetime"],
            timezone=data["timezone"],
            location=data["location"],
            description= data["description"]
        )
    except Exception as e:
        return f"Fehler beim Erstellen des Events.{e}"

import re

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
