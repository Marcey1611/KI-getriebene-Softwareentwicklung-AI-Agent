import os
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import (
    get_gmail_credentials,
    build_resource_service,
)

BASE = "app/mailing"

credentials = get_gmail_credentials(
    token_file=os.getenv("GOOGLE_MAIL_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://mail.google.com/"]
)

api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)
tools = toolkit.get_tools()

print("🔍 Tools geladen:")
for t in tools:
    print(f"- {t.name} ({type(t).__name__})")
    print("  ↳ Beschreibung:", getattr(t, "__doc__", "")[:100])
