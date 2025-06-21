from tools.extract_appointment import extract_appointment

text = """Hallo Max,
wir bestätigen deinen Vorstellungstermin am 21. Juni 2025 um 14:30 Uhr
in unserem Büro in Ravensburg."""

result = extract_appointment(text)
print("📅 Ergebnis:")
print(result)
