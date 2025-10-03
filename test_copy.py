import json
import sys
import io
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain.schema import Document  
from langchain_community.document_loaders import JSONLoader

from title_translation import translate_with_ollama

# Terminal-Kodierung auf UTF-8 setzen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Keine persistente DB mehr - In-Memory nur
CHROMA_PATH = None
json_file = open("./data/alle_news_json.json", "r", encoding="utf-8")
news_json_arr = json.load(json_file)['news']

def create_in_memory_chroma_db(embedding_function):
    """
    Erstellt eine In-Memory ChromaDB aus den News-Daten
    """
    try:
        # Metadaten der json file extrahieren - gleiche Funktion wie in database.py
        def metadata_func(record: dict, metadata: dict) -> dict:
            metadata["kategorie"] = record.get("kategorie")
            metadata["title"] = record.get("title")
            metadata["image"] = record.get("image") 
            return metadata

        # Json file laden - gleich wie database.py
        doc_loader = JSONLoader(
            file_path="./data/alle_news_json.json",
            jq_schema='.news[]',  
            content_key="text",   # text ist das was später dann gechunkt werden soll
            metadata_func=metadata_func  # metadaten laden
        )
        documents = doc_loader.load()
        
        # Text chunking - gleich wie database.py
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=250,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        
        # In-Memory ChromaDB erstellen (ohne persist_directory)
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            # Kein persist_directory = In-Memory
        )
        
        print(f"Created in-memory ChromaDB with {len(chunks)} chunks.")
        return db
        
    except Exception as e:
        print(f"Error creating in-memory ChromaDB: {str(e)}")
        return None

def query_and_process_category(category, embedding_function, user_info):
    """
    Verarbeitet eine einzelne Kategorie: Sucht relevante Artikel und generiert eine Zusammenfassung
    """
    # Extrahiere Benutzerinformationen
    complexity_level = user_info.get('complexity_level', 'standard')
    language = user_info.get('language', 'Deutsch')
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
    
    # Mehrsprachige "Keine Nachrichten" Texte
    no_news_messages = {
        'Deutsch': 'Keine (weiteren) Nachrichten verfügbar',
        'Englisch': 'No (further) news available',
        'Französisch': 'Aucune (autre) actualité disponible',
        'Spanisch': 'No hay (más) noticias disponibles',
        'Russisch': 'Нет (дополнительных) новостей',
        'Rumänisch': 'Nu sunt (alte) știri disponibile'
    }
    no_news_text = no_news_messages.get(user_language, 'Keine (weiteren) Nachrichten verfügbar')
    
    # Mehrsprachige "Zu dieser Kategorie gibt es keine Nachrichten" Texte für LLM
    category_no_news_messages = {
        'Deutsch': 'Zu dieser Kategorie gibt es aktuell keine Nachrichten',
        'Englisch': 'There are currently no news available for this category',
        'Französisch': 'Il n\'y a actuellement aucune actualité disponible pour cette catégorie',
        'Spanisch': 'Actualmente no hay noticias disponibles para esta categoría',
        'Russisch': 'В настоящее время для этой категории нет доступных новостей',
        'Rumänisch': 'În prezent nu sunt disponibile știri pentru această categorie'
    }
    category_no_news_text = category_no_news_messages.get(user_language, 'Zu dieser Kategorie gibt es aktuell keine Nachrichten')
    
    # Komplexitätsanweisungen basierend auf der Auswahl
    complexity_instructions = {
        'einfach': "Verwende ausschließlich einfache, kinderfreundliche Sprache und verwende keine Fachbegriffe, sodass jedes Kind die Nachrichten verstehen kann",
        'standard': "Verwende jugendgerechte Sprache und erkläre komplexe Themen verständlich.",
        'detailliert': "Verwende angemessen komplexe Sprache mit Fachbegriffen, wo erforderlich. Bleibe sachlich und objektiv ohne verzerrende oder manipulative Formulierungen."
    }
    
    complexity_instruction = complexity_instructions.get(complexity_level, complexity_instructions['standard'])
    
    # Kategorie-Mappings
    categories_map = {
        'politik': 'Politik',
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
        'politik': "Politik",
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
    
    # Vector Store und Suche - erstelle In-Memory DB
    db = create_in_memory_chroma_db(embedding_function)
    if db is None:
        return display_name, "Fehler beim Erstellen der Datenbank.", []
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

        WICHTIGE ANWEISUNG: Falls die bereitgestellten Informationen nicht ausreichend oder nicht relevant für die Kategorie "{display_name}" sind, antworte in EXAKT mit folgendem Text:
        "{category_no_news_text}"

        Persönliche Anpassungen:
        - Sprachkomplexität: {complexity_level} 
        - {complexity_instruction}     
        - {format_instruction}
        - Achte auf eine klare, verständliche, neutrale Sprache
        - Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
        - Die Nachrichtenausgabe MUSS in {user_language} verfasst werden! 
        - Verwende KEINE chinesischen, japanischen oder anderen asiatischen Schriftzeichen!
        - Verwende KEINE Sternchen (*) oder andere Formatierungszeichen in deiner Antwort!
        
        Deine Ausgabe sollte rein faktisch und ohne Einleitung oder Schlussformulierung sein.
        """
        
        # LLM aufrufen für einzelnen Artikel
        model = Ollama(model="deepseek-r1:70b", base_url="http://127.0.0.1:11434")
        article_content = model.invoke(article_prompt)
        
        if "</think>" in article_content:
            _, article_content = article_content.split("</think>")
        
        final_article_content = article_content.strip()
        
        # Prüfe ob das LLM die "Keine Nachrichten" Nachricht zurückgegeben hat
        if category_no_news_text in final_article_content:
            print(f"DEBUG: LLM hat 'keine Nachrichten' für Artikel '{title}' zurückgegeben", flush=True)
            category_articles.append({
                'content': final_article_content,
                'images': [],  # Kein Bild bei "keine Nachrichten"
                'title': f"{display_name} - {no_news_text}"
            })
            # Breche die Schleife ab, da wir nur einen "Keine Nachrichten" Kasten anzeigen möchten
            break
        else:
            translated_title = translate_with_ollama(title, target_language=language)
            category_articles.append({
                'content': final_article_content,
                'images': article_images,
                'title': translated_title
            })
    
    # Stelle sicher, dass mindestens ein Artikel vorhanden ist
    if not category_articles:
        print(f"DEBUG: Kein Content für Kategorie '{category}' gefunden", flush=True)
        return display_name, [{'content': category_no_news_text, 'images': [], 'title': f"{display_name} - {no_news_text}"}]
    
    
    print(f"DEBUG: Generierte {len(category_articles)} Artikel für Kategorie '{category}'", flush=True)
    
    return display_name, category_articles

def main(user_info=None):
    """Hauptfunktion zur Generierung des personalisierten Nachrichtenfeed"""
    if user_info is None:
        user_info = {
            'complexity_level': 'standard',
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