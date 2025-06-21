import json
import os

TOKEN_PATH = "app/mailing/token.json"

if not os.path.exists(TOKEN_PATH):
    print("❌ Keine token.json gefunden.")
    exit()

with open(TOKEN_PATH, "r") as f:
    token_data = json.load(f)

scope = token_data.get("scope", "Keine Scope gefunden.")
print("🔍 Aktive Scope(s):")
print(scope)
