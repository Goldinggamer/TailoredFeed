from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
import sys
import io
from datetime import datetime

# Terminal-Kodierung auf UTF-8 setzen, um Unicode-Zeichen zu unterstützen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CHROMA_PATH = "chroma_db/"

PROMPT_TEMPLATE = """

Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm in der Schellingstraße in München kuratiert. Dieser Ort wird hauptsächlich von Studenten der LMU und intellektuell aufgeschlossenen Menschen besucht. Deine Aufgabe ist es, einen ausgewogenen, faktisch korrekten und relevanten Nachrichtenüberblick zu erstellen.

1. Verwende NUR die bereitgestellten Informationen aus den folgenden vertrauenswürdigen Quellen:
{context}

2. Stelle Nachrichten in einem ausgewogenen Kontext dar, ohne politische Verzerrung
3. Berücksichtige unterschiedliche Perspektiven zu kontroversen Themen
4. Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
5. Verzichte auf reißerische oder polarisierende Formulierungen
6. Stelle die lokale Relevanz für München und Bayern in den Vordergrund
7. Bei unsicheren Informationen kennzeichne diese entsprechend

Erstelle einen strukturierten Nachrichtenüberblick mit folgenden Kategorien:
1. München aktuell (höchste Priorität)
2. Politik
3. Wirtschaft
4. Inland 
5. Ausland
6. Sport
7. Wissen

Für jede Kategorie:
- Wähle die relevantesten und aktuellsten Informationen aus
- Fasse sie in 1-3 prägnanten Sätzen zusammen
- Achte auf eine klare, verständliche und neutrale Sprache
- Berücksichtige die Zielgruppe: Studierende und Bewohner im Umfeld der Schellingstraße

Deine Ausgabe MUSS exakt diesem Format folgen:

München aktuell: [prägnante Nachricht zur aktuellen Situation in München]
Politik: [relevante und ausgewogene politische Nachricht]
Wirtschaft: [wichtige Wirtschaftsnachricht mit Relevanz]
Inland: [bedeutende Nachricht aus Deutschland]
Ausland: [relevante internationale Nachricht]
Sport: [aktuelle Sportnachricht mit Fokus auf lokale Teams wenn möglich]
Wissen: [interessante wissenschaftliche oder bildungsrelevante Nachricht]

Aktuelles Datum: {date}

Beantworte AUSSCHLIESSLICH die folgende Anfrage basierend auf den bereitgestellten Informationen: {question}
"""

def main():
    try:
        # Aktuelle Kategorien definieren
        CATEGORIES = [
            "München aktuell",
            "Politik",
            "Wirtschaft", 
            "Inland",
            "Ausland",
            "Sport",
            "Wissen"
        ]
        
        # Für jede Kategorie eine spezifische Abfrage erstellen
        results = []
        
        # Vorbereiten der Datenbank
        embedding_function = OllamaEmbeddings(model="nomic-embed-text")
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        
        # Für jede Kategorie relevante Dokumente finden
        for category in CATEGORIES:
            query = f"aktuelle Nachrichten {category}"
            category_results = db.similarity_search(query, k=12)
            results.extend(category_results)
        
        # Duplikate entfernen
        unique_results = []
        seen_contents = set()
        for doc in results:
            if doc.page_content not in seen_contents:
                seen_contents.add(doc.page_content)
                unique_results.append(doc)
        
        # Kontext aus den Suchergebnissen extrahieren
        context_text = "\n\n---\n\n".join([doc.page_content for doc in unique_results])
        
        # Aktuelles Datum
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        # Prompt erstellen
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(
            context=context_text, 
            question="Erstelle einen aktuellen Nachrichtenüberblick für alle Kategorien",
            date=current_date
        )
        
        # Antwort generieren mit Ollama
        model = Ollama(model="deepseek-r1:14b")
        response_text = model.invoke(prompt)

        # Quellen aus den Metadaten extrahieren (für interne Nachverfolgung)
        sources = [doc.metadata.get("source", "Keine Quelle angegeben") for doc in unique_results]
        
        # Nur die Antwort ausgeben
        print(response_text)
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {str(e)}")

if __name__ == "__main__":
    main()