import requests
import json
from bs4 import BeautifulSoup
import concurrent.futures
import json

def clean_html(html):
    """Entfernt HTML-Tags und gibt den reinen Text zurück."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def extract_article(news_item):
    """
    Extrahiert den Titel, Artikelinhalt und das 1x1-256 Bild aus einem News-Item.
    """
    title = news_item.get("title", "")
    article_parts = []
    for part in news_item.get("content", []):
        if part.get("type") in ["text", "headline"]:
            article_parts.append(clean_html(part.get("value", "")))
    article = "\n".join(article_parts)
    
    # Nur das 1x1-256 Bild extrahieren
    image_url = ""
    teaser_image = news_item.get("teaserImage", {})
    if teaser_image and teaser_image.get("imageVariants", {}):
        image_url = teaser_image["imageVariants"].get("1x1-256", "")
    
    return {
        "title": title, 
        "article": article,
        "image": image_url
    }

def process_news_with_details(item, session):
    """
    Nutzt den 'details'-Link, um das detaillierte JSON abzurufen und
    daraus den Titel und Artikelinhalt zu extrahieren.
    """
    detail_url = item.get("details")
    if not detail_url:
        return None
    resp = session.get(detail_url)
    if resp.status_code != 200:
        return None
    detail_json = resp.json()
    return extract_article(detail_json)

def process_category(url, session):
    """
    Ruft die Kategorie-URL ab, iteriert über die News-Items und
    nutzt für jedes Item den 'details'-Link, um den vollständigen Artikel abzurufen.
    """
    resp = session.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    items = data.get("news", [])
    
    articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Erstelle eine Liste von Futures für jeden Artikel, der Details benötigt
        future_to_item = {
            executor.submit(process_news_with_details, item, session): item
            for item in items if "details" in item
        }
        
        # Verarbeite die Ergebnisse, sobald sie verfügbar sind
        for future in concurrent.futures.as_completed(future_to_item):
            article = future.result()
            if article:
                articles.append(article)
                
        # Füge die Artikel hinzu, die keine Details erfordern
        for item in items:
            if "details" not in item:
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

def process_homepage(url="https://www.tagesschau.de/api2u/homepage", session=None):
    """
    Ruft die Homepage-JSON ab und verarbeitet alle News-Items direkt.
    """
    if session is None:
        session = requests.Session()
    
    resp = session.get(url)
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

def format_output(articles):
    """Formatiert die Artikel für die Ausgabe."""
    arr = []
    for art in articles:
        arr.append({
            'title': art["title"],
            'text': art["article"],
            'image': art.get("image", "")
        })
    return arr

def main():
    # URLs für die fünf Kategorien:
    categories = {
        "sport": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=sport",
        "inland": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=inland",
        "ausland": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=ausland",
        "wirtschaft": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=wirtschaft",
        "wissen": "https://www.tagesschau.de/api2u/news/?regions=2&ressort=wissen"
    }

    # URL für die München-Such-JSON
    muenchen_url = "https://www.tagesschau.de/api2u/search/?searchText=M%C3%BCnchen&pageSize=1&resultPage=30"

    # Dictionary, in dem die Ausgaben gespeichert werden
    outputs = {}
    
    # Wiederverwendbare Session für alle Anfragen
    session = requests.Session()
    
    # Parallel-Verarbeitung für alle Kategorien und die Homepage
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        # Starte die Verarbeitung für jede Kategorie
        future_to_category = {
            executor.submit(process_category, url, session): cat
            for cat, url in categories.items()
        }
        
        # Homepage auch parallel verarbeiten
        homepage_future = executor.submit(process_homepage, "https://www.tagesschau.de/api2u/homepage", session)
        
        # München-Such-JSON parallel abrufen
        muenchen_future = executor.submit(session.get, muenchen_url)
        
        # Sammle die Ergebnisse für die Kategorien
        for future in concurrent.futures.as_completed(future_to_category):
            cat = future_to_category[future]
            try:
                articles = future.result()
                outputs[cat] = format_output(articles)
            except Exception as exc:
                print(f"Fehler bei Kategorie {cat}: {exc}")
                outputs[cat] = f"Fehler bei Kategorie {cat}: {exc}"
        
        # Homepage-Ergebnisse abrufen
        try:
            homepage_articles = homepage_future.result()
            outputs["homepage"] = format_output(homepage_articles)
        except Exception as exc:
            print(f"Fehler bei Homepage: {exc}")
            outputs["homepage"] = f"Fehler bei Homepage: {exc}"
        
        # München-Ergebnisse verarbeiten
        try:
            muenchen_resp = muenchen_future.result()
            if muenchen_resp.status_code == 200:
                muenchen_data = muenchen_resp.json()
                muenchen_articles = process_search_news(muenchen_data)
                outputs["münchen"] = format_output(muenchen_articles)
            else:
                outputs["münchen"] = "Fehler beim Abrufen der München-Daten."
        except Exception as exc:
            print(f"Fehler bei München-Daten: {exc}")
            outputs["münchen"] = f"Fehler bei München-Daten: {exc}"

    news_arr = []

    for key in outputs:

        try: 
            for n in outputs[key]:
                print(str(n))
                news_arr.append({
                    'kategorie': key, 
                    'title': n["title"],
                    'text': n["text"],
                    'image': n["image"] 
                })
        except: 
            print("fehler")


    

    # alle_news.txt wird erstellt, der Inhalt gelöscht und der neue Inhalt der AlleNews Variable reingeschrieben.
    with open("data/alle_news_json.json", "w", encoding="utf-8") as f:
        # f.write(AlleNews)
        data = {
            'news': news_arr
        }
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    
    # Ausgabe aller News direkt aus der AlleNews-Variable
    print("Alle News wurden erfolgreich gespeichert!")


if __name__ == "__main__":
    main()