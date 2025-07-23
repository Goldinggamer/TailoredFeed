import json
import sys
import io
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama

# Terminal-Kodierung auf UTF-8 setzen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CHROMA_PATH = "chroma_db/"
json_file = open("./data/alle_news_json.json", "r", encoding="utf-8")
news_json_arr = json.load(json_file)['news']

def query_and_process_category(category, embedding_function, user_info):
    """
    Verarbeitet eine einzelne Kategorie: Sucht relevante Artikel und generiert eine Zusammenfassung
    """
    # Extrahiere Benutzerinformationen
    age = int(user_info.get('age_group', '30'))
    gender = user_info.get('gender', 'keine_angabe')
    language = user_info.get('language', 'Deutsch')
    dialect = user_info.get('dialect', '')
    news_format = user_info.get('format', 'kurz')
    
    # Sprachanpassung
    language_map = {
        'Deutsch': 'Deutsch',
        'English': 'Englisch',
        'Français': 'Französisch',
        'Español': 'Spanisch',
        'Русский': 'Russisch',
        'Română': 'Rumänisch'
    }
    
    user_language = language_map.get(language, 'Deutsch')
    dialect_instruction = f" im {dialect}-Dialekt" if dialect else ""
    
    # Altersgerechte Anpassungen
    if age < 12:
        age_instruction = "Verwende ausschließlich einfache, kinderfreundliche Sprache und verwende keine Fachbegriffe, sodass jedes Kind die Nachrichten verstehen kann"
    elif age < 25:
        age_instruction = "Verwende jugendgerechte Sprache und erkläre komplexe Themen verständlich."
    elif age >= 25:
        age_instruction = "Verwende angemessen komplexe Sprache mit Fachbegriffen, wo erforderlich. Bleibe sachlich und objektiv ohne verzerrende oder manipulative Formulierungen."
    else:
        age_instruction = ""
    
    # Kategorie-Mappings
    categories_map = {
        'politik': 'Politik Deutschland',
        'wissenschaft': 'Wissenschaft und Forschung',
        'wissenswertes': 'wissenswertes interessant',
        'wirtschaft': 'Wirtschaft Geld Deutschland',
        'gesundheit': 'Gesundheit Medizin',
        'muenchen': 'München',
        'technologie': 'Technologie',
        'sport': 'Sport Deutschland',
        'custom': None  # Wird dynamisch gesetzt
    }

    display_map = {
        'politik': "Politik Deutschland",
        'wissenschaft': "Wissen und Forschung",
        'wissenswertes': "Wissenswertes",
        'wirtschaft': "Wirtschaft",
        'gesundheit': "Gesundheit und Medizin",
        'muenchen': "München aktuell",
        'technologie': "Technologie und Innovation",
        'sport': "Sport Deutschland",
        'custom': "Custom Suche"
    }
    
    if category not in categories_map:
        return None, None, None
    
    # Handle Custom category
    if category == 'custom':
        custom_search_term = user_info.get('custom_search_term', '')
        if not custom_search_term.strip():
            return display_map[category], "Kein Suchbegriff für Custom Suche angegeben.", []
        search_term = custom_search_term.strip()
        display_name = f"Custom Suche: {search_term}"
    else:
        search_term = categories_map[category]
        display_name = display_map[category]
    
    # DEBUG: Überprüfe Suchbegriff
    print(f"DEBUG: Suche für Kategorie '{category}' mit Term: '{search_term}'", flush=True)
    
    # Vector Store und Suche
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    # Hole mehr Ergebnisse um Duplikate herausfiltern zu können
    results = db.similarity_search(search_term, k=10)
    
    # DEBUG: Überprüfe Suchergebnisse
    print(f"DEBUG: Gefundene Ergebnisse: {len(results)}", flush=True)
    print(f"DEBUG: Chroma DB hat {db._collection.count()} Dokumente", flush=True)
    for i, doc in enumerate(results):
        print(f"DEBUG: Ergebnis {i+1}: Titel='{doc.metadata.get('title', 'N/A')}'", flush=True)
    
    # Entferne Duplikate basierend auf Titel und Content
    unique_results = []
    seen_titles = set()
    seen_content_hashes = set()
    
    for doc in results:
        title = doc.metadata.get('title', '').strip().lower()
        content = doc.page_content.strip()
        
        # Erstelle einen Hash für den Content um ähnliche Inhalte zu erkennen
        import hashlib
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Prüfe auf Duplikate anhand von Titel
        title_similarity = False
        for seen_title in seen_titles:
            # Prüfe auf sehr ähnliche Titel (gleiche Worte, andere Reihenfolge)
            title_words = set(title.split())
            seen_words = set(seen_title.split())
            if len(title_words & seen_words) / max(len(title_words), len(seen_words), 1) > 0.8:
                title_similarity = True
                break
        
        # Prüfe auf Duplikate
        if not title_similarity and title not in seen_titles and content_hash not in seen_content_hashes:
            seen_titles.add(title)
            seen_content_hashes.add(content_hash)
            unique_results.append(doc)
            
            # Stoppe bei 3 eindeutigen Artikeln
            if len(unique_results) >= 3:
                break
    
    print(f"DEBUG: Nach Duplikatsentfernung: {len(unique_results)} eindeutige Artikel", flush=True)
    results = unique_results
    
    # Falls weniger als 3 eindeutige Artikel gefunden wurden, versuche andere Suchbegriffe
    if len(results) < 3:
        print(f"DEBUG: Nur {len(results)} eindeutige Artikel gefunden, versuche erweiterte Suche", flush=True)
        
        # Erweiterte Suchbegriffe für verschiedene Kategorien
        fallback_terms = {
            'politik': ['politik deutschland', 'bundestag', 'regierung', 'wahlen'],
            'wirtschaft': ['wirtschaft', 'unternehmen', 'börse', 'inflation'],
            'sport': ['sport', 'fußball', 'bundesliga', 'olympia'],
            'muenchen': ['münchen', 'bayern', 'bavaria'],
            'wissenschaft': ['wissenschaft', 'forschung', 'studie', 'innovation'],
            'technologie': ['technologie', 'tech', 'digital', 'ki'],
            'gesundheit': ['gesundheit', 'medizin', 'krankenhaus', 'therapie'],
            'wissenswertes': ['interessant', 'fakten', 'wissen', 'entdeckung']
        }
        
        category_key = category.lower()
        if category_key in fallback_terms:
            for fallback_term in fallback_terms[category_key]:
                if len(results) >= 3:
                    break
                
                fallback_results = db.similarity_search(fallback_term, k=5)
                for doc in fallback_results:
                    title = doc.metadata.get('title', '').strip().lower()
                    content = doc.page_content.strip()
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    # Prüfe ob dieser Artikel schon vorhanden ist
                    title_exists = False
                    for seen_title in seen_titles:
                        title_words = set(title.split())
                        seen_words = set(seen_title.split())
                        if len(title_words & seen_words) / max(len(title_words), len(seen_words), 1) > 0.8:
                            title_exists = True
                            break
                    
                    if not title_exists and content_hash not in seen_content_hashes:
                        seen_titles.add(title)
                        seen_content_hashes.add(content_hash)
                        results.append(doc)
                        
                        if len(results) >= 3:
                            break
        
        print(f"DEBUG: Nach erweiterter Suche: {len(results)} Artikel gefunden", flush=True)
    
    # Format-Anweisung
    format_instruction = "Erstelle einen ausführlichen Artikel mit 5-15 Sätzen." if news_format == 'ausfuehrlich' else "Fasse die Information in 1-3 prägnanten Sätzen zusammen."
    
    category_articles = []
    
    for doc in results:
        title = doc.metadata['title']
        print(f"DEBUG: Verarbeite Dokument mit Titel: '{title}'", flush=True)
        
        image_url = doc.metadata.get('image', '')
        article_images = []
        if image_url and image_url.strip():
            article_images.append(image_url.strip())
        
        # Verwende direkt den Text aus dem Vector Store
        article_text = doc.page_content
        if article_text and article_text.strip():
            print(f"DEBUG: Verwende Text aus Vector Store (erste 200 Zeichen): {article_text[:200]}...", flush=True)
            current_article_content = f"Titel: {title}\nInhalt: {article_text}"
        else:
            print(f"DEBUG: Kein Text im Vector Store, suche in JSON", flush=True)
            # Fallback zur JSON-Suche mit flexibler Suche
            matching_article = None
            for article in news_json_arr:
                if title.strip().lower() == article['title'].strip().lower():
                    matching_article = article
                    break
            
            if matching_article:
                article_text = matching_article.get('text', '')
                current_article_content = f"Titel: {title}\nInhalt: {article_text}"
            else:
                print(f"DEBUG: Auch in JSON nicht gefunden", flush=True)
                continue
        
        # Generiere Inhalt für diesen einzelnen Artikel
        article_prompt = f"""
        Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert.
        Deine Aufgabe ist es, eine relevante Nachricht zur Kategorie "{display_name}" zu erstellen.

        Verwende NUR die bereitgestellten Informationen aus folgender Quelle:
        {current_article_content}

        WICHTIGE ANWEISUNG: Falls die bereitgestellten Informationen nicht ausreichend oder nicht relevant für die Kategorie "{display_name}" sind, antworte EXAKT mit folgendem Text:
        "Zu dieser Kategorie gibt es aktuell keine Nachrichten"

        Persönliche Anpassungen:
        - Nutzer ist {age} Jahre alt und {gender}
        - {age_instruction}     
        - {format_instruction}
        - Achte auf eine klare, verständliche, neutrale Sprache
        - Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
        - Die Nachrichtenausgabe MUSS in {user_language}{dialect_instruction} verfasst werden! 
        - Verwende KEINE chinesischen, japanischen oder anderen asiatischen Schriftzeichen!
        - Verwende KEINE Sternchen (*) oder andere Formatierungszeichen in deiner Antwort!
        
        Deine Ausgabe sollte rein faktisch und ohne Einleitung oder Schlussformulierung sein.
        """
        
        # LLM aufrufen für einzelnen Artikel
        model = Ollama(model="deepseek-r1:32b", base_url="http://127.0.0.1:11434")
        article_content = model.invoke(article_prompt)
        
        if "</think>" in article_content:
            _, article_content = article_content.split("</think>")
        
        final_article_content = article_content.strip()
        
        # Prüfe ob das LLM die "Keine Nachrichten" Nachricht zurückgegeben hat
        if "Zu dieser Kategorie gibt es aktuell keine Nachrichten" in final_article_content:
            print(f"DEBUG: LLM hat 'keine Nachrichten' für Artikel '{title}' zurückgegeben", flush=True)
            category_articles.append({
                'content': final_article_content,
                'images': [],  # Kein Bild bei "keine Nachrichten"
                'title': f"{display_name} - Keine Nachrichten verfügbar"
            })
            # Breche die Schleife ab, da wir nur einen "Keine Nachrichten" Kasten anzeigen möchten
            break
        else:
            category_articles.append({
                'content': final_article_content,
                'images': article_images,
                'title': title
            })
    
    # Stelle sicher, dass mindestens ein Artikel vorhanden ist
    if not category_articles:
        print(f"DEBUG: Kein Content für Kategorie '{category}' gefunden", flush=True)
        return display_name, [{'content': "Zu dieser Kategorie gibt es aktuell keine Nachrichten", 'images': [], 'title': f"{display_name} - Keine Nachrichten verfügbar"}]
    
    
    print(f"DEBUG: Generierte {len(category_articles)} Artikel für Kategorie '{category}'", flush=True)
    
    return display_name, category_articles

def main(user_info=None):
    """Hauptfunktion zur Generierung des personalisierten Nachrichtenfeed"""
    if user_info is None:
        user_info = {
            'age_group': '30',
            'gender': 'keine_angabe', 
            'language': 'Deutsch',
            'categories': ['muenchen', 'politik', 'wirtschaft', 'sport'],
            'format': 'kurz',
            'custom_search_term': ''
        }
    
    selected_categories = user_info.get('categories', ['politik', 'wirtschaft', 'sport'])
    
    embedding_function = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://127.0.0.1:11434"
    )
    
    category_results = []
    
    for category in selected_categories:
        display_name, articles = query_and_process_category(
            category, embedding_function, user_info
        )
        
        if display_name and articles:
            category_results.append({
                'category': display_name,
                'articles': articles,
                'current_index': 0  # Aktueller Artikel-Index für Carousel
            })
    
    return category_results