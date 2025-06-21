# calendar_tool.py
from langchain_google_community.calendar.utils import get_google_credentials, build_resource_service
from langchain_google_community import CalendarToolkit
from langchain_core.tools import tool
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

credentials = get_google_credentials(
    token_file=str(BASE_DIR / "token.json"),
    scopes=["https://www.googleapis.com/auth/calendar.events"],
    client_secrets_file=str(BASE_DIR / "credentials.json")
)

service = build_resource_service(credentials)
toolkit = CalendarToolkit(api_resource=service)
calendar_tool = [t for t in toolkit.get_tools() if t.name == "create_calendar_event"][0]

@tool
def create_event_via_llm(summary: str, start_datetime: str, end_datetime: str, timezone: str, reminders: list = None) -> str:
    """Creates a google calendar event."""
    try:
        start = datetime.fromisoformat(start_datetime).strftime("%Y-%m-%d %H:%M:%S")
        end = datetime.fromisoformat(end_datetime).strftime("%Y-%m-%d %H:%M:%S")

        return calendar_tool.run({
            "summary": summary,
            "start_datetime": start,
            "end_datetime": end,
            "timezone": timezone,
            "reminders": reminders,
            "conference_data": False
        })
    except Exception as exception:
        return "Error creating calendar event."
