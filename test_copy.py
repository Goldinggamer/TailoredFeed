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
        'reisen': 'Lifestyle'
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
        'reisen': "Reisen und Lifestyle"
    }
    
    if category not in categories_map:
        return None, None, None
        
    search_term = categories_map[category]
    display_name = display_map[category]
    
    # DEBUG: Überprüfe Suchbegriff
    print(f"DEBUG: Suche für Kategorie '{category}' mit Term: '{search_term}'", flush=True)
    
    # Vector Store und Suche
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    results = db.similarity_search(search_term, k=1)
    
    # DEBUG: Überprüfe Suchergebnisse
    print(f"DEBUG: Gefundene Ergebnisse: {len(results)}", flush=True)
    print(f"DEBUG: Chroma DB hat {db._collection.count()} Dokumente", flush=True)
    for i, doc in enumerate(results):
        print(f"DEBUG: Ergebnis {i+1}: Titel='{doc.metadata.get('title', 'N/A')}'", flush=True)
    
    category_context = ""
    image_urls = []
    
    for doc in results:
        title = doc.metadata['title']
        print(f"DEBUG: Verarbeite Dokument mit Titel: '{title}'", flush=True)
        
        image_url = doc.metadata.get('image', '')
        if image_url and image_url.strip():
            image_urls.append(image_url.strip())
        
        # Verwende direkt den Text aus dem Vector Store
        article_text = doc.page_content
        if article_text and article_text.strip():
            print(f"DEBUG: Verwende Text aus Vector Store (erste 200 Zeichen): {article_text[:200]}...", flush=True)
            category_context += f"Titel: {title}\nInhalt: {article_text}\n\n"
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
                category_context += f"Titel: {title}\nInhalt: {article_text}\n\n"
            else:
                print(f"DEBUG: Auch in JSON nicht gefunden", flush=True)
    
    # Stelle sicher, dass mindestens eine leere Liste zurückgegeben wird
    if not image_urls:
        image_urls = []
    
    if not category_context.strip():
        print(f"DEBUG: Kein Content für Kategorie '{category}' gefunden", flush=True)
        return display_name, "Keine aktuellen Nachrichten verfügbar.", []
    
    # Format-Anweisung
    format_instruction = "Erstelle einen ausführlichen Artikel mit 5-15 Sätzen." if news_format == 'ausfuehrlich' else "Fasse die Information in 1-3 prägnanten Sätzen zusammen."
        
    category_prompt = f"""
    Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert.
    Deine Aufgabe ist es, eine relevante Nachricht zur Kategorie "{display_name}" zu erstellen.

    Verwende NUR die bereitgestellten Informationen aus folgenden Quellen:
    {category_context}

    Persönliche Anpassungen:
    - Nutzer ist {age} Jahre alt und {gender}
    - {age_instruction}     
    - {format_instruction}
    - Wähle die relevantesten und aktuellsten Informationen aus
    - Achte auf eine klare, verständliche, neutrale Sprache
    - Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
    - Die Nachrichtenausgabe MUSS in {user_language}{dialect_instruction} verfasst werden!
    
    Deine Ausgabe sollte rein faktisch und ohne Einleitung oder Schlussformulierung sein.
    """
    
    print(f"DEBUG: LLM-Prompt:\n{category_prompt}", flush=True)
    print(f"DEBUG: Rufe LLM auf...", flush=True)
    
    # LLM aufrufen
    model = Ollama(model="deepseek-r1:32b", base_url="http://127.0.0.1:11434")
    category_content = model.invoke(category_prompt)
    
    if "</think>" in category_content:
        _, category_content = category_content.split("</think>")
        print(f"DEBUG: LLM-Antwort (nach </think> Split): {category_content}", flush=True)
    
    final_content = category_content.strip()
    print(f"DEBUG: Finale Nachricht: {final_content}", flush=True)
    
    return display_name, final_content, image_urls

def main(user_info=None):
    """Hauptfunktion zur Generierung des personalisierten Nachrichtenfeed"""
    if user_info is None:
        user_info = {
            'age_group': '30',
            'gender': 'keine_angabe', 
            'language': 'Deutsch',
            'categories': ['muenchen', 'politik', 'wirtschaft', 'sport'],
            'format': 'kurz'
        }
    
    selected_categories = user_info.get('categories', ['politik', 'wirtschaft', 'sport'])
    
    embedding_function = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://127.0.0.1:11434"
    )
    
    category_results = []
    
    for category in selected_categories:
        display_name, content, image_urls = query_and_process_category(
            category, embedding_function, user_info
        )
        
        if display_name and content:
            category_results.append({
                'category': display_name,
                'content': content,
                'images': image_urls
            })
    
    return category_results