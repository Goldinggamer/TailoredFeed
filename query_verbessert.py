from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
import sys
import io
import json


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CHROMA_PATH = "chroma_db/"

PROMPT_TEMPLATE = """

Du bist ein journalistisches KI-System, das Nachrichten für einen öffentlichen Bildschirm im Univiertel in München kuratiert. Dieser Ort wird hauptsächlich von Studenten der Ludwig-Maximilians-Universität und intellektuell aufgeschlossenen Menschen besucht. Deine Aufgabe ist es, einen ausgewogenen, faktisch korrekten und relevanten Nachrichtenüberblick zu erstellen.

1. Verwende NUR die bereitgestellten Informationen aus den folgenden vertrauenswürdigen Quellen:
{context}

2. Stelle Nachrichten in einem ausgewogenen Kontext dar, ohne politische Verzerrung
3. Berücksichtige unterschiedliche Perspektiven zu kontroversen Themen
4. Präsentiere Fakten ohne manipulative Sprache oder emotionale Färbung
5. Verzichte auf reißerische oder polarisierende Formulierungen
6. Stelle die lokale Relevanz für München und Bayern in den Vordergrund
7. Bei unsicheren Informationen kennzeichne diese entsprechend
8. Die Sprache in der die Nachrichten erfolgen müssen ist ausschließlich Deutsch
9. Generiere KEINE Informationen, die nicht in den bereitgestellten Quellen enthalten sind

Für jede Kategorie:
- Wähle die relevantesten und aktuellsten Informationen aus
- Fasse sie in 1-3 prägnanten Sätzen zusammen
- Achte auf eine klare, verständliche, neutrale und deutsche Sprache
- Berücksichtige die Zielgruppe: Studierende und Bewohner in der Nähe der Universität



"""


json_file = open("./data/alle_news_json.json", "r", encoding="utf-8")
news_json_arr = json.load(json_file)['news']

def main():

    #arr = ["München","Wirtschaft", "Inland", "Ausland", "Sport", "Wissen"]
    arr = [
    "Nachrichten aus München",
    "Nachrichten aus Deutschland (Wirtschaft)",
    "Nachrichten aus Deutschland (Politik)",
    "Internationale Nachrichten",
    "Aktuelle Sportnachrichten",
    "Wissenschaft und Forschung"
    ]


    for Kategorie in arr:
        news = query_rag(Kategorie)

        for chunk in news:
            text = prompt(chunk["text"])

            if "</think" in text:
                thinking, final_text = text.split("</think>")
            else:
                final_text = text
            print("\n" * 5)
            print(chunk["kategorie"] + Kategorie + ": " + final_text.strip())

# Kontext der DB und prompt template werden von dem LLM bearbeitet
def prompt(text):
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    prompt = prompt_template.format(context=text)

    model = Ollama(model="deepseek-r1:14b")
    response_text = model.invoke(prompt)

    return response_text

def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = OllamaEmbeddings(model="nomic-embed-text")

    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=2) 

    news_arr = []

    for [d, score] in results:
        title = d.metadata['title']
        article = [x for x in news_json_arr if x["title"] == title][0]
        news_arr.append(article)
    
    return news_arr

if __name__ == "__main__":
    main()



    # Beantworte AUSSCHLIESSLICH die folgende Anfrage basierend auf den bereitgestellten Informationen: {question}
    # Aktuelles Datum: {date}
    # Erstelle einen strukturierten Nachrichtenüberblick mit folgenden Kategorien:
    # 1. München aktuell (höchste Priorität)
    # 2. Politik
    # 3. Wirtschaft
    # 4. Inland 
    # 5. Ausland
    # 6. Sport
    # 7. Wissen

    # query_text = "Nachrichten zu den Kategorien München, Politik, Wirschaft, Inland, Ausland, Sport und Wissen"
    # query_text = "ich interessiere mich für corona und krieg und elon musk"

    # eigene funktion
    # prompt: "du kriegst einen string und musst ihn in alle kategorien/bestandteile teilen. [str, str, str, str]"
    # llm splittet den text in eine boolean query
