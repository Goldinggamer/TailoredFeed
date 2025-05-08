import json
import sys
import io
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.llms import Ollama

# Terminal-Kodierung auf UTF-8 setzen, um Unicode-Zeichen zu unterstützen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CHROMA_PATH = "chroma_db/"
json_file = open("./data/alle_news_json.json", "r", encoding="utf-8")
news_json_arr = json.load(json_file)['news']

CATEGORIES = [
    "München",
    "Wirtschaft Geld Deutschland",
    "Inlandsnachrichten Deutschland",
    "Internationale Nachrichten", 
    "Sport Deutschland",
    "Wissenschaft und Forschung"
]

# Basis-Template für den Prompt
BASE_PROMPT_TEMPLATE = """
Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert. Deine Aufgabe ist es, einen ausgewogenen, faktisch korrekten und relevanten Nachrichtenüberblick zu erstellen.

{personalization}

1. Verwende NUR die bereitgestellten Informationen aus den folgenden vertrauenswürdigen Quellen:

Kontext Anfang:

{context}

Kontext Ende.

2. Lies dir den kompletten von "Kontext Anfang:" bis "Kontext Ende." durch und merke dir alle relevanten Informationen.
3. Stelle Nachrichten abhängig von den obigen Quellen in einem ausgewogenen Kontext dar, ohne politische Verzerrung
4. Berücksichtige unterschiedliche Perspektiven zu kontroversen Themen
5. Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
6. Verzichte auf reißerische oder polarisierende Formulierungen
7. Stelle die lokale Relevanz für München und Bayern in den Vordergrund
8. Bei unsicheren Informationen kennzeichne diese entsprechend
9. Die Sprache in der die Nachrichten erfolgen müssen ist {user_language}{dialect_instruction}
10. Du darfst keine Aussagen treffen, die nicht direkt durch den Kontext belegbar sind.

Erstelle einen strukturierten Nachrichtenüberblick mit folgenden Kategorien:
{categories_list}

Für jede Kategorie:
- Wähle die relevantesten und aktuellsten Informationen aus
- Fasse sie in 1-3 prägnanten Sätzen zusammen
- Achte auf eine klare, verständliche, neutrale Sprache{age_appropriate_instruction}

Deine Ausgabe MUSS exakt diesem Format folgen:
{categories_output_format}
"""
def get_display_categories(selected_categories=None):
    """
    Erzeugt eine Liste von anzuzeigenden Kategorien basierend auf den ausgewählten Kategorien.
    """
    # Definiere die Standard-Anzeigeformen
    default_display_categories = [
        "München aktuell",
        "Wirtschaft",
        "Inlandsnachrichten Deutschland",
        "Internationale Nachrichten", 
        "Sport Deutschland",
        "Wissen und Forschung"
    ]
    
    # Mapping von Kategorie-IDs zu Anzeigeformen
    category_display_map = {
        'politik': "Politik Deutschland",
        'wissenschaft': "Wissen und Forschung",
        'unterhaltung': "Unterhaltung und Kultur",
        'wirtschaft': "Wirtschaft",
        'gesundheit': "Gesundheit und Medizin",
        'gaming': "Gaming und Digital",
        'technologie': "Technologie und Innovation",
        'sport': "Sport Deutschland",
        'reisen': "Reisen und Lifestyle",
        'muenchen': "München aktuell"  # Falls explizit München ausgewählt wurde
    }
    
    # Wenn keine spezifischen Kategorien ausgewählt wurden, verwende Standardkategorien
    if not selected_categories or len(selected_categories) == 0:
        return default_display_categories
    
    # Sonst verwende ausgewählte Kategorien - ohne erzwungenes München
    display_categories = []
    
    for category in selected_categories:
        if category in category_display_map:
            display_cat = category_display_map[category]
            if display_cat not in display_categories:  # Vermeidet Duplikate
                display_categories.append(display_cat)
     
    return display_categories

def query_rag_aggregated(selected_categories=None):
    # Update embedding function to use remote server
    embedding_function = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://10.40.15.6:80"  # Your server URL
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Mapping für die Kategorien
    categories_map = {
        'politik': 'Politik Deutschland',
        'wissenschaft': 'Wissenschaft und Forschung',
        'unterhaltung': 'Unterhaltung Freizeit',
        'wirtschaft': 'Wirtschaft Geld Deutschland',
        'gesundheit': 'Gesundheit Medizin',
        'gaming': 'Gaming Spiele',
        'technologie': 'Technologie IT Digital',
        'sport': 'Sport Deutschland',
        'reisen': 'Reisen Lifestyle'
    }
    
    # Variable zum Sammeln des Kontexts
    aggregated_context = ""
    
    # Wenn spezifische Kategorien ausgewählt wurden, verwenden wir diese
    search_categories = []
    if selected_categories and len(selected_categories) > 0:
        for category in selected_categories:
            if category in categories_map:
                search_categories.append(categories_map[category])
    # Ansonsten Standardkategorien verwenden
    else:
        search_categories = CATEGORIES
    
    # Entferne den Code, der immer München hinzufügt
    # Benutzer entscheidet selbst, ob München-Nachrichten gewünscht sind
    
    # Schleife durch alle Kategorien
    for category in search_categories:
        # Suche nach ähnlichen Dokumenten für die aktuelle Kategorie
        results = db.similarity_search(category, k=2)
        
        # Sammle Kontexte für diese Kategorie
        category_context = ""
        for doc in results:
            title = doc.metadata['title']
            # Finde den vollständigen Artikel im JSON
            matching_article = next((x for x in news_json_arr if x["title"] == title), None)
            
            if matching_article:
                # Füge den Artikel-Text zum Kategoriekontext hinzu
                category_context += f"Titel: {title}\nInhalt: {matching_article.get('text', '')}\n\n"
        
        # Füge Kategoriekontext zum Gesamtkontext hinzu
        aggregated_context += f"{category_context}\n"
    
    return aggregated_context

def create_personalized_prompt(user_info):
    """
    Erstellt einen personalisierten Prompt basierend auf den Benutzerdaten.
    """
    age = int(user_info.get('age_group', '30'))
    gender = user_info.get('gender', 'keine_angabe')
    language = user_info.get('language', 'Deutsch')
    dialect = user_info.get('dialect', '')
    selected_categories = user_info.get('categories', [])
    news_format = user_info.get('format', 'kurz')  # Hole das Format
    
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
    
    # Dialektanweisung (falls angegeben)
    dialect_instruction = f" mit {dialect}-Dialekt" if dialect else ""
    
    # Altersgerechte Anpassungen
    if age < 12:
        age_appropriate_instruction = "\n- Verwende einfache, kinderfreundliche Sprache und vermeide komplexe Themen"
    elif age < 18:
        age_appropriate_instruction = "\n- Verwende jugendgerechte Sprache und erkläre komplexe Themen verständlich"
    elif age > 60:
        age_appropriate_instruction = "\n- Berücksichtige Themen, die für ältere Menschen relevant sein könnten"
    else:
        age_appropriate_instruction = ""
    
    # Format-Anweisung basierend auf der Benutzerauswahl
    if news_format == 'ausfuehrlich':
        format_instruction = "\n- Erstelle ausführliche Artikel mit 5-15 Sätzen pro Kategorie"
    else:  # 'kurz' ist der Standardwert
        format_instruction = "\n- Fasse jede Kategorie in 1-3 prägnanten Sätzen zusammen"
    
    # Personalisierungstext
    personalization_text = f"""
Du sprichst mit einer Person mit folgenden Merkmalen:
- Alter: {age} Jahre
- Geschlecht: {gender}
- Bevorzugte Sprache: {user_language}
"""
    if dialect:
        personalization_text += f"- Bevorzugter Dialekt: {dialect}\n"
    
    personalization_text += """
Berücksichtige diese Informationen bei der Auswahl und Formulierung der Nachrichten, ohne die Objektivität und Ausgewogenheit zu beeinträchtigen.
"""
    
    # Dynamische Kategorienliste basierend auf den Benutzerauswahlen
    display_categories = get_display_categories(selected_categories)
    
    # Erstelle die nummerierte Kategorienliste für den Prompt
    categories_list = ""
    for i, category in enumerate(display_categories, 1):
        categories_list += f"{i}. {category}\n"
    
    # Erstelle das Ausgabeformat für die Kategorien
    categories_output_format = "\n\n".join([f"{category}: [Nachricht zu {category}]" for category in display_categories])
    
    # Vollständiger personalisierter Prompt
    return BASE_PROMPT_TEMPLATE.format(
        personalization=personalization_text,
        context="{context}",  # Platzhalter für den späteren Kontext
        user_language=user_language,
        dialect_instruction=dialect_instruction,
        age_appropriate_instruction=age_appropriate_instruction + format_instruction,  # Format-Anweisung hinzufügen
        categories_list=categories_list,
        categories_output_format=categories_output_format
    )

def generate_news_summary(full_context, user_info=None):
    """
    Generiert eine personalisierte Nachrichtenübersicht basierend auf dem Kontext und den Benutzerinformationen.
    
    Args:
        full_context (str): Der vollständige Kontext aus der RAG-Abfrage
        user_info (dict, optional): Ein Dictionary mit Benutzerinformationen
    
    Returns:
        str: Die generierte Nachrichtenübersicht
    """
    if user_info:
        # Personalisierter Prompt
        personalized_template = create_personalized_prompt(user_info)
        prompt_template = ChatPromptTemplate.from_template(personalized_template)
    else:
        # Standard-Prompt wenn keine Benutzerinformationen vorliegen
        prompt_template = ChatPromptTemplate.from_template(BASE_PROMPT_TEMPLATE.format(
            personalization="",
            context="{context}",
            user_language="Deutsch",
            dialect_instruction="",
            age_appropriate_instruction="\n- Fasse jede Kategorie in 1-3 prägnanten Sätzen zusammen"  # Standardformat
        ))
    
    prompt = prompt_template.format(context=full_context)

    # Print the complete prompt including context
    print("\n=== VOLLSTÄNDIGER PROMPT MIT KONTEXT ===")
    print(prompt)
    print("=====================================\n")
    
    # Update model to use remote server
    model = Ollama(
        model="deepseek-r1:32b",
        base_url="http://10.40.15.6:80"  # Your server URL
    )
    news_summary = model.invoke(prompt)
    
    # Löscht den Think Teil der llm raus
    if "</think>" in news_summary:
        _, final_text = news_summary.split("</think>")
        return final_text.strip()
    
    return news_summary.strip()

def main(user_info=None):
    # Extrahiere die Kategorien aus user_info, falls vorhanden
    selected_categories = None
    if user_info and 'categories' in user_info:
        selected_categories = user_info['categories']
    
    # Übergebe die ausgewählten Kategorien an die RAG-Funktion
    full_context = query_rag_aggregated(selected_categories)
    news_summary = generate_news_summary(full_context, user_info)

    print("Folgendes wurde abhängig vom Kontext und Benutzereinstellungen von der KI generiert: \n ")
    print(news_summary)
    
    return news_summary

# Direkter Aufruf ohne Benutzerinformationen
if __name__ == "__main__":
    # Einfacher Aufruf ohne Benutzerinformationen
    main()