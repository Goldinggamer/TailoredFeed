import requests
import json
from bs4 import BeautifulSoup

def clean_html(html):
    """Entfernt HTML-Tags und gibt den reinen Text zurück."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def extract_article(news_item):
    """
    Extrahiert den Titel und den Artikelinhalt aus einem News-Item,
    das bereits alle Content-Informationen enthält.
    """
    title = news_item.get("title", "")
    article_parts = []
    for part in news_item.get("content", []):
        if part.get("type") in ["text", "headline"]:
            article_parts.append(clean_html(part.get("value", "")))
    article = "\n".join(article_parts)
    return {"title": title, "article": article}

def process_news_with_details(item):
    """
    Nutzt den 'details'-Link, um das detaillierte JSON abzurufen und
    daraus den Titel und Artikelinhalt zu extrahieren.
    """
    detail_url = item.get("details")
    if not detail_url:
        return None
    resp = requests.get(detail_url)
    if resp.status_code != 200:
        return None
    detail_json = resp.json()
    return extract_article(detail_json)

def process_category(url):
    """
    Ruft die Kategorie-URL ab, iteriert über die News-Items und
    nutzt für jedes Item den 'details'-Link, um den vollständigen Artikel abzurufen.
    Gibt eine Liste von Artikeln (als Dictionary mit "title" und "article") zurück.
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    items = data.get("news", [])
    articles = []
    for item in items:
        if "details" in item:
            article = process_news_with_details(item)
        else:
            article = extract_article(item)
        if article:
            articles.append(article)
    return articles

def process_direct_news(data):
    """
    Verarbeitet ein JSON, das direkt alle News-Items enthält (ohne extra 'details'-Aufruf)
    und extrahiert Titel und Artikel.
    """
    news_list = data.get("news", [])
    articles = []
    for item in news_list:
        articles.append(extract_article(item))
    return articles

def process_homepage(url="https://www.tagesschau.de/api2u/homepage"):
    """
    Ruft die Homepage-JSON ab und verarbeitet alle News-Items direkt.
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    articles = []
    for item in data.get("news", []):
        articles.append(extract_article(item))
    return articles

def process_search_news(data):
    """
    Verarbeitet ein Such-JSON (wie von der München-URL),
    bei dem die Ergebnisse in "searchResults" stehen.
    """
    results = data.get("searchResults", [])
    articles = []
    for item in results:
        articles.append(extract_article(item))
    return articles

# URLs für die fünf Kategorien:
categories = {
    "sport": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=sport",
    "inland": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=inland",
    "ausland": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=ausland",
    "wirtschaft": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=wirtschaft",
    "wissen": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=wissen"
}

# URL für die München-Such-JSON (anstelle einer lokalen Datei)
muenchen_url = "https://www.tagesschau.de/api2u/search/?searchText=M%C3%BCnchen&pageSize=1&resultPage=30"

# Dictionary, in dem die Ausgaben gespeichert werden
outputs = {}

# Verarbeitung der Homepage (direkt, ohne extra details)
homepage_articles = process_homepage()
home_str = ""
for art in homepage_articles:
    home_str += "Titel: " + art["title"] + "\n"
    home_str += "Artikel:\n" + art["article"] + "\n"
    home_str += "\n" + "="*50 + "\n"
outputs["homepage"] = home_str

# Verarbeitung der fünf Kategorien (über details-Links)
for cat, url in categories.items():
    articles = process_category(url)
    out_str = ""
    for art in articles:
        out_str += "Titel: " + art["title"] + "\n"
        out_str += "Artikel:\n" + art["article"] + "\n"
        out_str += "\n" + "="*50 + "\n"
    outputs[cat] = out_str

# Verarbeitung der München-Such-JSON (direkt aus dem Link, Ergebnisse in "searchResults")
resp = requests.get(muenchen_url)
if resp.status_code == 200:
    muenchen_data = resp.json()
    muenchen_articles = process_search_news(muenchen_data)
    muenchen_str = ""
    for art in muenchen_articles:
        muenchen_str += "Titel: " + art["title"] + "\n"
        muenchen_str += "Artikel:\n" + art["article"] + "\n"
        muenchen_str += "\n" + "="*50 + "\n"
    outputs["münchen"] = muenchen_str
else:
    outputs["münchen"] = "Fehler beim Abrufen der München-Daten."

# Beispielhafte Ausgabe für die Homepage:
print("Output für 'homepage':\n")
print(outputs["homepage"])

for key in outputs:
    print(f"Output für '{key}':\n")
    print(outputs[key])
    print("\n" + "#"*80 + "\n")
