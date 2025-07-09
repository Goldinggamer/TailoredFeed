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



def query_and_process_category(category, embedding_function, user_info):
    """
    Verarbeitet eine einzelne Kategorie: Sucht relevante Artikel und generiert eine Zusammenfassung
    
    Args:
        category (str): Die zu verarbeitende Kategorie-ID
        embedding_function: Die Embedding-Funktion für die Vektorsuche
        user_info (dict): Benutzerinformationen für Personalisierung
    
    Returns:
        tuple: (category_display_name, generated_content)
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
    
    # Dialektanweisung
    dialect_instruction = f" im {dialect}-Dialekt" if dialect else ""
    
    # Altersgerechte Anpassungen
    if age < 12:
        age_instruction = "Verwende einfache, kinderfreundliche Sprache und vermeide komplexe Themen."
    elif age < 18:
        age_instruction = "Verwende jugendgerechte Sprache und erkläre komplexe Themen verständlich."
    elif age > 60:
        age_instruction = "Berücksichtige Themen, die für ältere Menschen relevant sein könnten."
    else:
        age_instruction = ""
    
    # Kategorie-Mapping für die Suche
    categories_map = {
        'politik': 'Politik Deutschland',
        'wissenschaft': 'Wissenschaft und Forschung',
        'unterhaltung': 'Unterhaltung Freizeit',
        'wirtschaft': 'Wirtschaft Geld Deutschland',
        'gesundheit': 'Gesundheit Medizin',
        'gaming': 'Gaming',
        'technologie': 'Technologie',
        'sport': 'Sport Deutschland',
        'reisen': 'Reisen Lifestyle'
    }

    # Mapping für die Anzeigeform
    display_map = {
        'politik': "Politik Deutschland",
        'wissenschaft': "Wissen und Forschung",
        'unterhaltung': "Unterhaltung und Kultur",
        'wirtschaft': "Wirtschaft",
        'gesundheit': "Gesundheit und Medizin",
        'gaming': "Gaming",
        'technologie': "Technologie und Innovation",
        'sport': "Sport Deutschland",
        'reisen': "Reisen und Lifestyle"
    }
    
    # Wenn die Kategorie nicht im Mapping ist, überspringen
    if category not in categories_map:
        return None, None
        
    search_term = categories_map[category]
    display_name = display_map[category]
    
    # Vector Store initialisieren
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Suche nach ähnlichen Dokumenten für diese Kategorie
    results = db.similarity_search(search_term, k=3)  # Erhöht auf 3 für mehr Kontext
    
    # Context für diese Kategorie sammeln
    category_context = ""
    for doc in results:
        title = doc.metadata['title']
        # Finde den vollständigen Artikel im JSON
        matching_article = next((x for x in news_json_arr if x["title"] == title), None)
        
        if matching_article:
            # Füge den Artikel-Text zum Kategoriekontext hinzu
            category_context += f"Titel: {title}\nInhalt: {matching_article.get('text', '')}\n\n"
    
    # Wenn kein Kontext gefunden wurde, überspringen
    if not category_context.strip():
        return display_name, "Keine aktuellen Nachrichten verfügbar."
    
    # Mini-Prompt nur für diese Kategorie erstellen
    format_instruction = ""
    if news_format == 'ausfuehrlich':
        format_instruction = "Erstelle einen ausführlichen Artikel mit 5-15 Sätzen."
    else:  # 'kurz' ist der Standardwert
        format_instruction = "Fasse die Information in 1-3 prägnanten Sätzen zusammen."
        
    category_prompt = f"""
    Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert.
    Deine Aufgabe ist es, eine relevante Nachricht zur Kategorie "{display_name}" zu erstellen.

    Persönliche Anpassungen:
    - Die Nachricht soll auf {user_language}{dialect_instruction} verfasst werden
    - Nutzer ist {age} Jahre alt und {gender}
    - {age_instruction}  

    Verwende NUR die bereitgestellten Informationen aus folgenden Quellen:
    
    {category_context}
    
    - Wähle die relevantesten und aktuellsten Informationen aus
    - {format_instruction}
    - Achte auf eine klare, verständliche, neutrale Sprache
    - Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
    - Verzichte auf reißerische oder polarisierende Formulierungen
    
    Deine Ausgabe sollte rein faktisch und ohne Einleitung oder Schlussformulierung sein.
    """
    
    # Prompt zur Überprüfung in der Konsole ausgeben
    print("\n" + "="*80)
    print(f"PROMPT FÜR KATEGORIE: {display_name}")
    print("="*80)
    print(category_prompt)
    print("="*80 + "\n")
    
    # LLM für diese Kategorie aufrufen
    model = Ollama(
        model="qwen3:32b",
        base_url="http://localhost:11435"
    )
    
    category_content = model.invoke(category_prompt)
    
    # Entferne mögliche Think-Teile oder andere Formatierungen
    if "</think>" in category_content:
        _, category_content = category_content.split("</think>")
    
    # Auch die Antwort des LLM ausgeben
    print("\n" + "-"*80)
    print(f"ANTWORT FÜR KATEGORIE: {display_name}")
    print("-"*80)
    print(category_content.strip())
    print("-"*80 + "\n")
    
    return display_name, category_content.strip()

def main(user_info=None):
    """
    Hauptfunktion zur Generierung des personalisierten Nachrichtenfeed
    """
    # Standard-User-Info, falls keine übergeben wurde
    if user_info is None:
        user_info = {
            'age_group': '30',
            'gender': 'keine_angabe',
            'language': 'Deutsch',
            'dialect': '',
            'categories': ['muenchen', 'politik', 'wirtschaft', 'sport'],
            'format': 'kurz'
        }
    
    # Extrahiere die benötigten Informationen
    selected_categories = user_info.get('categories', [])
    
    # Wenn keine Kategorien ausgewählt wurden, verwende Standardkategorien
    if not selected_categories:
        selected_categories = ['politik', 'wirtschaft', 'sport']
    
    # Embedding-Funktion initialisieren (nur einmal für alle Kategorien)
    embedding_function = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11435"
    )
    
    # Ergebnisse für jede Kategorie sammeln
    category_results = []
    
    print(f"Verarbeite {len(selected_categories)} Kategorien...")
    
    # Jede Kategorie einzeln verarbeiten
    for category in selected_categories:
        print(f"Verarbeite Kategorie: {category}")
        display_name, content = query_and_process_category(
            category, 
            embedding_function,
            user_info  # Übergebe das gesamte user_info-Dictionary
        )
        
        if display_name and content:
            category_results.append((display_name, content))
            print(f"✓ {display_name} verarbeitet")
        else:
            print(f"✗ Kategorie '{category}' konnte nicht verarbeitet werden")
    
    # Gesamtergebnis zusammensetzen
    final_output = ""
    for display_name, content in category_results:
        final_output += f"{display_name}: {content}\n\n"
    
    print("\nFertig! Gesamtergebnis:")
    print(final_output)
    
    return final_output

# Direkter Aufruf ohne Benutzerinformationen
if __name__ == "__main__":
    # Einfacher Aufruf ohne Benutzerinformationen
    main()