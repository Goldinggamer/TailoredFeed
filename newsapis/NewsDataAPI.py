import os
import sys
import io
import json
from newsdataapi import NewsDataApiClient

# Terminal-Kodierung auf UTF-8 setzen, um Unicode-Zeichen zu unterstützen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Sicherstellen, dass das data-Verzeichnis existiert
os.makedirs('data', exist_ok=True)

# API key authorization, Initialize the client with your API key
api = NewsDataApiClient(apikey="pub_76858c02a16677eb5f34bfc2e3a12283f4657")

# API-Anfrage
response = api.latest_api(
    domainurl="www.sueddeutsche.de", 
    country="de",
    size= 10
)

# Speichern der Antwort in einer JSON-Datei
output_file = 'data/news_response.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(response, f, ensure_ascii=False, indent=4)

print(f"Antwort wurde in {output_file} gespeichert.")