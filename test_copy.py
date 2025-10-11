import json
import sys
import io
import asyncio
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter  
# from langchain.schema import Document  
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document


from title_translation import translate_with_ollama
from database import db, metadata_func#, complete_documents

model = Ollama(model="gpt-oss:120b", base_url="http://127.0.0.1:11434") 

# Terminal-Kodierung auf UTF-8 setzen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Keine persistente DB mehr - In-Memory nur
CHROMA_PATH = None
json_file = open("./data/alle_news_json.json", "r", encoding="utf-8")
news_json_arr = json.load(json_file)['news']


def query_and_process_category(category, user_info):
    """
    … (Dokustring ggf. gekürzt) …
    """
    # Nutzerpräferenzen
    complexity_level = user_info.get('complexity_level', 'standard')
    user_language = user_info.get('language', 'Deutsch')
    format_pref = user_info.get('format', 'kurz')
    language = 'Deutsch' if user_language == 'Deutsch' else user_language

    # Format-Anweisungen
    format_instructions = {
        'kurz': "Fasse die Information in 1-3 prägnanten Sätzen zusammen.",
        'ausfuehrlich': "Erstelle einen ausführlichen Artikel mit 5-8 Sätzen."
    }
    format_instruction = format_instructions.get(format_pref, format_instructions['kurz'])

    # Mehrsprachige "Keine (weiteren) Nachrichten verfügbar"
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
        'einfach': "Verwende ausschließlich einfache, kinderfreundliche Wörter ohne Fachbegriffe, sodass jedes Kind die Nachrichten verstehen kann",
        'standard': "Verwende jugendgerechte Sprache und erkläre komplexe Themen verständlich.",
        'detailliert': "Verwende angemessen komplexe Sprache mit notwendigen Fachbegriffen, bleibe präzise und objektiv ohne verzerrende oder manipulative Formulierungen."
    }
    
    complexity_instruction = complexity_instructions.get(complexity_level, complexity_instructions['standard'])
    
    # Kategorien → Suchterme
    categories_map = {
        'politik': "politik deutschland bundesregierung bundestag",
        'wissenschaft': "wissenschaft forschung studie innovation",
        'wissenswertes': "interessant fakten wissen entdeckung",
        'wirtschaft': "wirtschaft konjunktur unternehmen märkte",
        'gesundheit': "gesundheit medizin krankenhaus therapie",
        'muenchen': "münchen bayern bavaria",
        'technologie': "technologie digital ki innovation",
        'sport': "sport deutschland liga turnier",
        'custom': ""
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
    
    # Vektor-DB aufbauen (in-memory) & abfragen
    # db = create_in_memory_chroma_db(embedding_function)
    if db is None:
        return display_name, [{'content': no_news_text, 'images': [], 'title': f"{display_name} - {no_news_text}"}]
    
    # Ähnliche Dokumente holen
    results = db.similarity_search(search_term, k=15)
    print(f"DEBUG: {len(results)} Roh-Treffer für '{search_term}'", flush=True)

     # DEBUG: Überprüfe Suchergebnisse
    print(f"DEBUG: Gefundene Ergebnisse: {len(results)}", flush=True)
    print(f"DEBUG: Chroma DB hat {db._collection.count()} Dokumente", flush=True)

    distinct_results = {}

    doc_loader = JSONLoader(
            file_path="./data/alle_news_json.json",
            jq_schema='.news[]',  
            content_key="text",
            metadata_func=metadata_func
        )
    print("JSON LOADER")
    complete_documents = doc_loader.load()

    for i, chunk in enumerate(results):
        _title = chunk.metadata.get("title")
        if _title not in distinct_results:
            # distinct_results[_title] = doc

            _doc = next((x for x in complete_documents if x.metadata.get("title") == chunk.metadata.get("title")), chunk)
            print(f"Chunk länge {len(chunk.page_content)} - beitrag länge {len(_doc.page_content)}")

            distinct_results[_title] = _doc


    print(f"Distinct ergebnisse: {len(distinct_results.values())}")

    distinct_documents = list(distinct_results.values())


    print(f"DEBUG: Nach Duplikatsentfernung: {len(distinct_documents)} eindeutige Artikel", flush=True)
    results = distinct_documents
    

    # Begrenzen auf maximal 3 Artikel für die parallele Verarbeitung
    results = results[:3]
        
    # Falls immer noch keine Artikel vorhanden, früh zurückkehren
    if not results:
        print(f"DEBUG: Kein Content für Kategorie '{category}' gefunden", flush=True)
        return display_name, [{'content': category_no_news_text, 'images': [], 'title': f"{display_name} - {no_news_text}"}]
    
    print(f"DEBUG: Verarbeite {len(results)} eindeutige Artikel parallel", flush=True)

    # --- Parallel statt sequenziell: Ollama-Requests concurrently ausführen ---
    category_articles = []  # wird unten aus den Ergebnissen gefüllt

    async def _process_doc_async(doc):
        title = doc.metadata['title']
        print(f"DEBUG: Verarbeite Dokument mit Titel: '{title}'", flush=True)

        image_url = doc.metadata.get('image', '')
        article_images = []
        if image_url and image_url.strip():
            article_images.append(image_url.strip())

        # Verwende direkt den Text aus dem Vector Store
        article_text = doc.page_content
        if article_text and article_text.strip():
            print(f"DEBUG: Verwende Text aus Vector Store (erste 50 Zeichen): {article_text[:50]}...", flush=True)
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
                return None

        # Prompt für diesen Artikel
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

        try:
            # Verwende ainvoke, wenn vorhanden; sonst Thread-Executor
            if hasattr(model, "ainvoke"):
                article_content = await model.ainvoke(article_prompt)
            else:
                loop = asyncio.get_running_loop()
                article_content = await loop.run_in_executor(None, model.invoke, article_prompt)
        except Exception as e:
            print(f"DEBUG: Fehler beim LLM-Aufruf für '{title}': {e}", flush=True)
            return None

        if "</think>" in article_content:
            _, article_content = article_content.split("</think>", 1)

        final_article_content = article_content.strip()

        # "Keine Nachrichten" -> signalisiere Sofort-Abbruch
        if category_no_news_text in final_article_content:
            return {
                "type": "no_news",
                "entry": {
                    'content': final_article_content,
                    'images': [],
                    'title': f"{display_name} - {no_news_text}"
                },
                "title": title
            }

        # Titel-Übersetzung (synchrone Funktion asynchron ausführen)
        loop = asyncio.get_running_loop()
        def _translate_call():
            return translate_with_ollama(title, target_language=language)
        translated_title = await loop.run_in_executor(None, _translate_call)

        return {
            "type": "article",
            "entry": {
                'content': final_article_content,
                'images': article_images,
                'title': translated_title
            },
            "title": title
        }

    async def _collect_articles_parallel(docs):
        # Nur so viele parallele Tasks wie tatsächlich benötigte Artikel (maximal 3)
        max_conc = min(len(docs), 3)  # Begrenzt auf 3, da wir nur 3 Artikel brauchen
        sem = asyncio.Semaphore(max_conc)

        async def _guarded(doc):
            async with sem:
                return await _process_doc_async(doc)

        # Nur Tasks für die tatsächlich benötigten Artikel erstellen
        tasks = [asyncio.create_task(_guarded(doc)) for doc in docs[:3]]
        results_accum = []
        no_news_entries = []
        try:
            for fut in asyncio.as_completed(tasks):
                res = await fut
                if not res:
                    continue
                if res["type"] == "no_news":
                    print(f"DEBUG: LLM hat 'keine Nachrichten' für Artikel '{res['title']}' zurückgegeben - überspringe diesen", flush=True)
                    # Sammle "keine Nachrichten" Einträge, aber brich nicht ab
                    no_news_entries.append(res["entry"])
                else:
                    results_accum.append(res["entry"])
            
            # Wenn wir normale Artikel haben, gib diese zurück
            if results_accum:
                return results_accum
            # Andernfalls, wenn nur "keine Nachrichten" Ergebnisse vorhanden sind, gib diese zurück
            elif no_news_entries:
                return no_news_entries[:1]  # Nur einen "keine Nachrichten" Eintrag
            # Falls gar nichts da ist, leere Liste
            return []
        finally:
            for t in tasks:
                if not t.done():
                    t.cancel()

    category_articles = asyncio.run(_collect_articles_parallel(results))

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
    
    
    
    category_results = []
    
    for category in selected_categories:
        display_name, articles = query_and_process_category(
            category, user_info
        )
        
        if display_name and articles:
            category_results.append({
                'category': display_name,
                'articles': articles,
                'current_index': 0  # Aktueller Artikel-Index für Carousel
            })
    
    return category_results
