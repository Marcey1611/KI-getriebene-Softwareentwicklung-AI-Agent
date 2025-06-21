# calendar_tool.py
from langchain_google_community.calendar.utils import get_google_credentials, build_resource_service
from langchain_google_community import CalendarToolkit
from langchain_core.tools import tool
from datetime import datetime
from pathlib import Path
import json


cal_credentials = get_google_credentials(
    token_file=str( "cal-token.json"),
    scopes=["https://www.googleapis.com/auth/calendar.events"],
    client_secrets_file=str("credentials.json")
)

service = build_resource_service(cal_credentials)
toolkit = CalendarToolkit(api_resource=service)
calendar_tool = [t for t in toolkit.get_tools() if t.name == "create_calendar_event"][0]

@tool
def create_event_via_llm(title: str, start_datetime: str, end_datetime: str, timezone: str) -> str:
    """Creates a google calendar event."""
    try:
        start = datetime.fromisoformat(start_datetime).strftime("%Y-%m-%d %H:%M:%S")
        end = datetime.fromisoformat(end_datetime).strftime("%Y-%m-%d %H:%M:%S")

        return calendar_tool.run({
            "title": title,
            "start_datetime": start,
            "end_datetime": end,
            "timezone": timezone,
            "conference_data": False
        })
    except Exception as exception:
        return "Error creating calendar event."
@tool
def create_event_from_json(json_payload: str) -> str:
    """Erstellt ein Kalender-Event aus einem JSON-String mit title, start_datetime, end_datetime, timezone."""
    try:
        data = json.loads(json_payload)
        return create_event_via_llm(
            title=data["title"],
            start_datetime=data["start_datetime"],
            end_datetime=data["end_datetime"],
            timezone=data["timezone"],
        )
    except Exception as e:
        return f"Fehler beim Erstellen des Events: {str(e)}"