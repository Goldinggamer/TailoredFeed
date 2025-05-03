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

PROMPT_TEMPLATE = """

Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert. Deine Aufgabe ist es, einen ausgewogenen, faktisch korrekten und relevanten Nachrichtenüberblick zu erstellen.

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
9. Die Sprache in der die Nachrichten erfolgen müssen ist ausschließlich Deutsch
10. Du darfst keine Aussagen treffen, die nicht direkt durch den Kontext belegbar sind.

Erstelle einen strukturierten Nachrichtenüberblick mit folgenden Kategorien:
1. München aktuell (höchste Priorität)
2. Wirtschaft
3. Inlandsnachrichten Deutschland
4. Internationale Nachrichten 
5. Sport Deutschland
6. Wissen und Forschung

Für jede Kategorie:
- Wähle die relevantesten und aktuellsten Informationen aus
- Fasse sie in 1-3 prägnanten Sätzen zusammen
- Achte auf eine klare, verständliche, neutrale und deutsche Sprache

Deine Ausgabe MUSS exakt diesem Format folgen:

München aktuell: [prägnante Nachricht zur aktuellen Situation in München]

Wirtschaft: [wichtige Wirtschaftsnachricht mit Relevanz]

Inlandsnachrichten Deutschland: [bedeutende Nachricht aus Deutschland]

Internationale Nachrichten: [relevante internationale Nachricht]

Sport Deutschland: [aktuelle Sportnachricht mit Fokus auf lokale Teams wenn möglich]

Wissen und Forschung: [interessante wissenschaftliche oder bildungsrelevante Nachricht]
"""

def query_rag_aggregated():
    # Update embedding function to use remote server
    embedding_function = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://10.40.15.6:80"  # Your server URL
    )
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Variable zum Sammeln des Kontexts
    aggregated_context = ""
    
    # Schleife durch alle Kategorien
    for category in CATEGORIES:
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
        
       # print(f"Verarbeite Kategorie: {category}")
       # print(f"Gefundene Dokumente: {len(results)}")
    
    return aggregated_context

def generate_news_summary(full_context):
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=full_context)

    # Print the complete prompt including context
    print("\n=== VOLLSTÄNDIGER PROMPT MIT KONTEXT ===")
    print(prompt)
    print("=====================================\n")
    
    # Update model to use remote server
    model = Ollama(
        model="deepseek-r1:70b",
        base_url="http://10.40.15.6:80"  # Your server URL
    )
    news_summary = model.invoke(prompt)
    
    # Löscht den Think Teil der llm raus
    if "</think>" in news_summary:
        _, final_text = news_summary.split("</think>")
        return final_text.strip()
    
    return news_summary.strip()

def main():
    full_context = query_rag_aggregated()
  #  print("Folgender Kontext wurde benutzt: \n")
  #  print(full_context)
    news_summary = generate_news_summary(full_context)

    print("Folgendes wurde abhängig vom Kontext von der KI generiert: \n ")
    print(news_summary)

if __name__ == "__main__":
    main()