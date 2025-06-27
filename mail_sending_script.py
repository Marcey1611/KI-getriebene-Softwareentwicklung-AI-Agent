import smtplib
from email.message import EmailMessage
import os

EMAIL_ADDRESS = "REPLACE_WITH_YOUR_OWN_EMAIL_ADDRESS"
EMAIL_PASSWORD = "REPLACE_WITH_YOUR_OWN_APP_PASSWORD"

def send_email(to, subject, body, attachment_path=None):
    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = os.path.basename(attachment_path)
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print(f"✅ E-Mail erfolgreich gesendet an: {to}")

if __name__ == "__main__":
    send_email(
        to="sysad.project.ws2425@gmail.com",
        subject="Termin am Samstag 9 Uhr in Wangen im Allgäu",
        body="Bitte vergesse unseren Geschäfts Termin am Samstag (28.06.2025) von 9 Uhr in Wangen im Allgäu (Deutschland) nicht.",
        attachment_path=None
    )