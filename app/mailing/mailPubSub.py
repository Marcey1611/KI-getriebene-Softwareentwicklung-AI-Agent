from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.cloud import pubsub_v1
import json



# Gmail API – über OAuth2 Token (token-2.json)
gmail_creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.readonly'])
gmail_service = build('gmail', 'v1', credentials=gmail_creds)

# Nur beim ersten Start nötig – ansonsten auskommentieren!
watch_request = {
    'labelIds': ['INBOX'],
    'topicName': 'projects/noah-ai-agent/topics/gmail-notify'
}
response = gmail_service.users().watch(userId='me', body=watch_request).execute()
print("✅ Watch aktiviert:", response)
last_processed_history_id = int(response['historyId'])

# Pub/Sub API – mit Service Account (z. B. service-account.json)
pubsub_creds = service_account.Credentials.from_service_account_file("service-account.json")
subscriber = pubsub_v1.SubscriberClient(credentials=pubsub_creds)
subscription_path = subscriber.subscription_path('noah-ai-agent', 'gmail-notify-sub')

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
                    messages.append(msg['message']['id'])

    return messages


def callback(message):
    global last_processed_history_id

    try:
        decoded_text = message.data.decode("utf-8")
        json_data = json.loads(decoded_text)

        history_id = json_data.get("historyId")
        email_address = json_data.get("emailAddress")

        print(f"📬 Gmail-Aktivität erkannt: {email_address}, History ID: {history_id}")

        new_message_ids = get_new_messages_since_history(gmail_service, 'me', last_processed_history_id)
        print(new_message_ids)

        last_processed_history_id = history_id

    except Exception as e:
        print("Fehler:", e)
    finally:
        message.ack()

def spinup_subscription():

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    print("Listening for messages...")

    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
    except BaseException as e:
        spinup_subscription()

spinup_subscription()