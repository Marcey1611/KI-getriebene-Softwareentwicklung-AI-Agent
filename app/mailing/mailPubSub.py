from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.cloud import pubsub_v1
import json
from langchain_google_community.gmail.get_message import GmailGetMessage


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
                    full_msg = gmail_service.users().messages().get(userId='me', id=message_id, format='metadata').execute()
                    if 'INBOX' in full_msg.get('labelIds', []):  # Nur echte eingehende Mails
                        messages.append(message_id)

    return messages

class MailPubSub:

    def __init__(self):
        gmail_creds = Credentials.from_authorized_user_file('token.json', ['https://mail.google.com/'])
        self.gmail_service = build('gmail', 'v1', credentials=gmail_creds)

        watch_request = {
            'labelIds': ['INBOX'],
            'topicName': 'projects/noah-ai-agent/topics/gmail-notify'
        }
        response = self.gmail_service.users().watch(userId='me', body=watch_request).execute()
        print("✅ Watch activated:", response)
        self.last_processed_history_id = int(response['historyId'])
        self.gmail_get_message = GmailGetMessage()

        pubsub_creds = service_account.Credentials.from_service_account_file("service-account.json")
        self.subscriber = pubsub_v1.SubscriberClient(credentials=pubsub_creds)
        self.subscription_path = self.subscriber.subscription_path('noah-ai-agent', 'gmail-notify-sub')

    def callback(self,message):
        try:
            decoded_text = message.data.decode("utf-8")
            json_data = json.loads(decoded_text)

            history_id = json_data.get("historyId")
            email_address = json_data.get("emailAddress")
            print(f"📬 Gmail-Update: {email_address}, History ID: {history_id}")

            new_message_ids = get_new_messages_since_history(self.gmail_service, 'me', self.last_processed_history_id)
            print(new_message_ids)
            for ids in new_message_ids:
                print("E-Mail ID:", ids)

            self.last_processed_history_id = history_id

        except Exception as e:
            print("Error:", e)
        finally:
            message.ack()

    def spinup_subscription(self):

        streaming_pull_future = self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        print("Listening for messages...")

        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()

def main():
    pub_sub=MailPubSub()
    pub_sub.spinup_subscription()

if __name__ == '__main__':
    main()