import os
import requests
from dotenv import load_dotenv

# Lade .env-Datei
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Prompt Template
PROMPT_TEMPLATE = """
Du bist ein hilfsbereiter und sachlicher KI-Assistent.
Beantworte bitte folgende Benutzerfrage möglichst verständlich und präzise:

Frage: {question}
"""

# Funktion zur Anfrage an Groq
def run_chat(question):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
            {"role": "user", "content": PROMPT_TEMPLATE.format(question=question)}
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Fehler: {response.status_code} - {response.text}"

# Einstiegspunkt
if __name__ == "__main__":
    print("🧠 Groq-basierter Chatbot mit LLaMA 3 – ohne OpenAI!")
    while True:
        frage = input("\n❓ Deine Frage (oder 'exit'): ")
        if frage.lower() in ["exit", "quit"]:
            print("👋 Auf Wiedersehen!")
            break
        antwort = run_chat(frage)
        print(f"\n💬 Antwort:\n{antwort}")
