# TailoredFeed

Eine personalisierte Nachrichten-App, die Ollama LLMs verwendet, um News basierend auf Benutzerpräferenzen zu kuratieren und zusammenzufassen.

## Voraussetzungen

- Python 3.10+
- [Ollama](https://ollama.ai/) - lokal installiert oder als Remote-Server verfügbar
- Die folgenden Ollama-Modelle müssen heruntergeladen sein:
  - `gpt-oss:120b` (Haupt-LLM für News-Generierung)
  - `nomic-embed-text` (Embedding-Modell für Vektordatenbank)
  - `phi4` (für Titel-Übersetzungen)

## Ollama Konfiguration

### Ollama-Server starten

**Lokal:**
```bash
ollama serve
```

**Remote-Server:**
Stelle sicher, dass der Ollama-Server auf dem Remote-Host läuft und erreichbar ist.

### Konfigurationsstellen

Die Ollama-Server-Adresse und die verwendeten Modelle müssen in **drei Dateien** angepasst werden:

---

#### 1. `test_copy.py` (Zeile 17)
**Haupt-LLM für die News-Generierung**

```python
model = Ollama(model="gpt-oss:120b", base_url="http://127.0.0.1:11434")
```

| Parameter | Beschreibung |
|-----------|-------------|
| `model` | Name des Ollama-Modells für die News-Zusammenfassung |
| `base_url` | URL des Ollama-Servers |

---

#### 2. `database.py` (Zeilen 10-12)
**Embedding-Modell für die Vektordatenbank (ChromaDB)**

```python
embedding_function = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://127.0.0.1:11434"
)
```

| Parameter | Beschreibung |
|-----------|-------------|
| `model` | Name des Embedding-Modells (empfohlen: `nomic-embed-text`) |
| `base_url` | URL des Ollama-Servers |

---

#### 3. `title_translation.py` (Zeilen 4 und 7)
**Modell für Titel-Übersetzungen**

```python
ollama_host = 'http://127.0.0.1:11434' 
# ...
def translate_with_ollama(text, target_language='German', model='phi4'):
```

| Parameter | Beschreibung |
|-----------|-------------|
| `ollama_host` | URL des Ollama-Servers |
| `model` | Name des Modells für Übersetzungen (Standard: `phi4`) |

---

## Schnellkonfiguration

### Für lokale Ollama-Installation (Standard)
Keine Änderungen nötig - die Standardkonfiguration verwendet `http://127.0.0.1:11434`.

### Für Remote-Ollama-Server
Ersetze überall `http://127.0.0.1:11434` durch die IP-Adresse/URL deines Servers, z.B. `http://192.168.1.100:11434`.

**Dateien die angepasst werden müssen:**
1. `test_copy.py` → Zeile 17: `base_url="http://DEINE-IP:11434"`
2. `database.py` → Zeile 12: `base_url="http://DEINE-IP:11434"`
3. `title_translation.py` → Zeile 4: `ollama_host = 'http://DEINE-IP:11434'`

---

## Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/TailoredFeed.git
   cd TailoredFeed
   ```

2. **Virtuelle Umgebung erstellen (empfohlen):**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ollama-Modelle herunterladen:**
   ```bash
   ollama pull gpt-oss:120b
   ollama pull nomic-embed-text
   ollama pull phi4
   ```
   
   > ⚠️ **Hinweis:** Je nach verwendetem Modell können die Namen abweichen. Passe die Modellnamen in den Konfigurationsdateien entsprechend an.

---

## App starten

1. **Sicherstellen, dass Ollama läuft:**
   ```bash
   ollama serve
   ```
   (In einem separaten Terminal-Fenster ausführen)

2. **Flask-App starten:**
   ```bash
   python app.py
   ```

3. **App im Browser öffnen:**
   ```
   http://127.0.0.1:5000
   ```

---

## Projektstruktur

```
TailoredFeed/
├── app.py                 # Flask-Hauptanwendung
├── test_copy.py           # News-Generierungslogik mit Ollama LLM
├── database.py            # ChromaDB Vektordatenbank mit Ollama Embeddings
├── title_translation.py   # Titel-Übersetzungen mit Ollama
├── ApiNews.py             # Tagesschau API Abruf
├── translations.py        # UI-Übersetzungen (DE/EN)
├── requirements.txt       # Python-Abhängigkeiten
├── data/                  # Gespeicherte News-Daten
├── static/                # CSS & JavaScript
├── templates/             # HTML-Templates
└── user_data/             # Benutzer-Session-Daten
```

---

## Fehlerbehebung

### "Connection refused" Fehler
- Überprüfe, ob Ollama läuft: `ollama list`
- Überprüfe die Server-URL in allen drei Konfigurationsdateien
- Bei Remote-Server: Firewall-Einstellungen prüfen (Port 11434)

### Modell nicht gefunden
- Überprüfe verfügbare Modelle: `ollama list`
- Lade das fehlende Modell herunter: `ollama pull MODELLNAME`
- Passe den Modellnamen in der entsprechenden Datei an

### Langsame Generierung
- Die News-Generierung kann je nach Modellgröße und Hardware 15-30 Sekunden dauern
- Bei Remote-Servern kann die Netzwerklatenz die Geschwindigkeit beeinflussen
