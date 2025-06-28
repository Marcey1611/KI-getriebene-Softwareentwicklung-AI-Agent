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