import json
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from app.tools.agent_runner import AgentRunner
import os

def get_gmail_credentials(token_file, client_secrets_file, scopes):
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    return creds

processed_message_ids = set()

def get_new_messages_since_history(gmail_service, user_id, start_history_id):
    history = gmail_service.users().history().list(
        userId=user_id,
        startHistoryId=start_history_id,
        historyTypes=['messageAdded']
    ).execute()

    messages = []
    if 'history' in history:
        for record in history['history']:
            if 'messagesAdded' in record:
                for msg in record['messagesAdded']:
                    message_id = msg['message']['id']
                    if message_id in processed_message_ids:
                        continue  # Schon verarbeitet -> überspringen
                    full_msg = gmail_service.users().messages().get(userId='me', id=message_id, format='metadata').execute()
                    if 'INBOX' in full_msg.get('labelIds', []):  # Nur echte eingehende Mails
                        messages.append(message_id)
                        processed_message_ids.add(message_id)

    return messages

class GmailPubSub:
    def __init__(self,agent:AgentRunner):
        self.last_processed_history_id=None
        self.agent = agent
        creds = get_gmail_credentials(os.getenv("GOOGLE_MAIL_TOKEN"),os.getenv("GOOGLE_CREDENTIALS"),["https://mail.google.com/"])
        #creds = get_gmail_credentials("../../ai_agent_config/google-mail-token.json","../../ai_agent_config/google-credentials.json",["https://mail.google.com/"])
        self.gmail_service = build("gmail", "v1", credentials=creds)
        watch_request = {
            'labelIds': ['INBOX'],
            'topicName': 'projects/noah-ai-agent/topics/gmail-notify'
        }
        response = self.gmail_service.users().watch(userId='me', body=watch_request).execute()
        print("✅ Watch activated:", response)
        self.last_processed_history_id = int(response['historyId'])
        pubsub_creds = service_account.Credentials.from_service_account_file(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
        #pubsub_creds = service_account.Credentials.from_service_account_file("../../ai_agent_config/google-service-account.json")
        client_options = ClientOptions(api_endpoint="pubsub.googleapis.com")
        self.subscriber = pubsub_v1.SubscriberClient(credentials=pubsub_creds,client_options=client_options)
        self.subscription_path = self.subscriber.subscription_path('noah-ai-agent', 'gmail-notify-sub')
        print("Done Init")


    def callback(self,message):
        try:
            decoded_text = message.data.decode("utf-8")
            json_data = json.loads(decoded_text)

            history_id = json_data.get("historyId")
            email_address = json_data.get("emailAddress")
            print(f"📬 Gmail-Update: {email_address}, History ID: {history_id}")
#
            new_message_ids = get_new_messages_since_history(self.gmail_service, 'me', self.last_processed_history_id)
            for ids in new_message_ids:
                print("E-Mail ID:", ids)
                self.agent.run_agent_executor(ids)
            self.last_processed_history_id = history_id

        except Exception as e:
            print(str(message.data))
            print("Error:", e)
        finally:
            message.ack()

    def run(self):
        streaming_pull_future = self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        print("Listening for messages...")
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()