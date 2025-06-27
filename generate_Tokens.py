import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
load_dotenv()  # Lädt Variablen aus .env

def get_google_credentials(token_file: str, scopes: list, client_secrets_file: str) -> Credentials:
    creds = None

    # Lade Token aus JSON (wenn vorhanden)
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, scopes)

    # Erzeuge neue Token falls nötig
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)

        # Speichere Credentials als JSON
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        print(f"✅ Neues Token gespeichert: {token_file}")
    else:
        print(f"☑️ Token gültig: {token_file}")

    return creds


get_google_credentials(
    token_file=os.getenv("GOOGLE_CALENDAR_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://www.googleapis.com/auth/calendar"]
)
get_google_credentials(
    token_file=os.getenv("GOOGLE_MAIL_TOKEN"),
    client_secrets_file=os.getenv("GOOGLE_CREDENTIALS"),
    scopes=["https://mail.google.com/"]
)