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
    results = db.similarity_search(search_term, k=3)
    
    # DEBUG: Überprüfe Suchergebnisse
    print(f"DEBUG: Gefundene Ergebnisse: {len(results)}", flush=True)
    print(f"DEBUG: Chroma DB hat {db._collection.count()} Dokumente", flush=True)
    for i, doc in enumerate(results):
        print(f"DEBUG: Ergebnis {i+1}: Titel='{doc.metadata.get('title', 'N/A')}'", flush=True)
    
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
        
        category_articles.append({
            'content': final_article_content,
            'images': article_images,
            'title': title
        })
    
    # Stelle sicher, dass mindestens ein Artikel vorhanden ist
    if not category_articles:
        print(f"DEBUG: Kein Content für Kategorie '{category}' gefunden", flush=True)
        return display_name, [{'content': "Keine aktuellen Nachrichten verfügbar.", 'images': [], 'title': 'Keine Nachrichten'}], []
    
    
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