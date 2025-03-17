# TailoredFeed - individuelle Nachrichten-App

TailoredFeed ist eine Flask-basierte Web-Anwendung, die einen Einstiegspunkt zu ausgewogenen Nachrichten mit hoher lokaler und persöhnlicher Relevanz anbietet. Dabei werden soziale Strukturen und geografische Gegebenheiten beachtet.

## Funktionen

- Erfassung demographischer Daten (Alter, Geschlecht)
- Spracheinstellungen inkl. optionaler Dialekt-Auswahl
- Auswahl aus verschiedenen Nachrichtenkategorien
- Wahl zwischen Kurzmeldungen und ausführlichen Artikeln
- Speicherung von Benutzereinstellungen für Personalisierung

## Installation

1. Stellen Sie sicher, dass Python 3.7+ und flask (über die Konsole mit dem Befehl pip install flask) installiert ist
2. Klonen Sie das Repository

## Projektstruktur

```
TailoredFeed/
├── static/
│   ├── styles.css     # Zentrales Stylesheet
│   └── scripts.js     # JavaScript-Funktionen
├── templates/
│   ├── index.html     # Startseite
│   ├── user_input.html # Benutzerinformationen 
│   ├── categories.html # Kategorien- und Format-Auswahl
│   └── feed_placeholder.html # (wird automatisch generiert)
├── user_data/         # Gespeicherte Benutzerdaten
├── app.py             # Flask-Anwendung
└── README.md          # Dokumentation
```

## Verwendung

1. Starten Sie die Anwendung:

```bash
python app.py
```

2. Öffnen Sie einen Browser und navigieren Sie zu `http://localhost:5000`
3. Folgen Sie dem Benutzerfluss:
   - Persönliche Informationen eingeben (Alter, Geschlecht, Sprache)
   - Nachrichtenkategorien auswählen
   - Bevorzugtes Nachrichtenformat wählen

## Erweiterungsmöglichkeiten

- Integration einer tatsächlichen News-API
- Benutzerprofile und Authentifizierung
- KI-gestützte Artikelempfehlungen
- Lokale Nachrichtenanpassung basierend auf Standort
- Mobile App-Version

## Lizenz

Dieses Projekt ist für Bildungszwecke gedacht.
