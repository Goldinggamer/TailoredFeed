# import os
# import shutil
# import sys
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain.schema import Document  
from langchain_community.document_loaders import JSONLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from ApiNews import main as fetchNews

# DATA_PATH = "./data/alle_news_json.json"
# # In-Memory ChromaDB - kein persistenter Pfad
# CHROMA_PATH = None
embedding_function = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://127.0.0.1:11434"
)

db = None


def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["kategorie"] = record.get("kategorie")
    metadata["title"] = record.get("title")
    metadata["image"] = record.get("image") 
    return metadata


def create_in_memory_chroma_db():
    global db
    fetchNews()
    print("CHROMA_CREATE - init")

    """
    Erstellt eine In-Memory ChromaDB aus den News-Daten
    """
    try:
        print("CHROMA_CREATE - try")

        # Metadaten der json file extrahieren - gleiche Funktion wie in database.py
        
        # Json file laden - gleich wie database.py
        doc_loader = JSONLoader(
            file_path="./data/alle_news_json.json",
            jq_schema='.news[]',  
            content_key="text",   # text ist das was später dann gechunkt werden soll
            metadata_func=metadata_func  # metadaten laden
        )
        print("JSON LOADER")
        documents = doc_loader.load()
        print("CHROMA_CREATE - documents loaded")
        # Text chunking - gleich wie database.py
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=250,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print("CHROMA_CREATE - chunks splitted")
        
      # In-Memory ChromaDB erstellen (ohne persist_directory)
        
        # try:
        #     db.reset_collection()     
        # except:
        #     print()   
        
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embedding_function,
            
            # Kein persist_directory = In-Memory
        )
        
        print(f"Created in-memory ChromaDB with {len(chunks)} chunks.")
        
    except Exception as e:
        print(f"Error creating in-memory ChromaDB: {str(e)}")



def update_db(): 
    create_in_memory_chroma_db()


if db is None:
    create_in_memory_chroma_db()










# # Metadaten der json file extrahieren
# def metadata_func(record: dict, metadata: dict) -> dict:
#     metadata["kategorie"] = record.get("kategorie")
#     metadata["title"] = record.get("title")
#     metadata["image"] = record.get("image") 
#     return metadata

# # Json file reinladen
# def load_documents():
#     try:
#         doc_loader = JSONLoader(
#             file_path=DATA_PATH,
#             jq_schema='.news[]',  
#             content_key="text",   # text ist das was später dann gechunkt werden soll
#             metadata_func=metadata_func  # metadaten laden
#         )
#         documents = doc_loader.load()
#         print(f"Loaded {len(documents)} documents from {DATA_PATH}")
#         return documents
#     except ImportError:
#         print("Error: Missing required package. Please run: pip install jq")
#         sys.exit(1)
#     except Exception as e:
#         print(f"Error loading documents: {str(e)}")
#         sys.exit(1)

# # Teilt den Text in chunks während die Metadaten erhalten bleiben
# def split_text(documents: list[Document]):
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1500,
#         chunk_overlap=250,
#         length_function=len,
#         add_start_index=True,
#     )
    
#     chunks = text_splitter.split_documents(documents)
#     print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

#     # text ob korrekt gechunkt wird
#     if chunks:
#         sample = chunks[0]
#         # print("\nSample chunk:")
#         # print(f"Content: {sample.page_content[:100]}...")
#         # print(f"Metadata: {sample.metadata}")

#     return chunks

# def save_to_chroma(chunks: list[Document]):
#     try:
#         # Keine Festplatten-DB mehr - verwende In-Memory
#         # Alte DB-Cleanup nicht mehr nötig
        
#         # Kreiere eine Ollama embedding instanz mit dem Server
#         embeddings = OllamaEmbeddings(
#             model="nomic-embed-text",  
#             base_url="http://127.0.0.1:11434"  
#         )
        
#         # Kreiert eine Chroma DB im Arbeitsspeicher (ohne persist_directory)
#         db = Chroma.from_documents(
#             documents=chunks,
#             embedding=embeddings,
#             # persist_directory entfernt - läuft jetzt im RAM
#         )
        
#         print(f"Saved {len(chunks)} chunks to in-memory ChromaDB.")
        
#         # Wichtig: DB-Referenz für anderen Code verfügbar machen
#         # Speichere die DB-Instanz global oder gib sie zurück
#         global chroma_db_instance
#         chroma_db_instance = db
        
#         return db
        
#     except Exception as e:
#         print(f"Error saving to Chroma: {str(e)}")
#         sys.exit(1)


# # Globale Variable für die In-Memory DB
# chroma_db_instance = None

# if __name__ == "__main__":
#     documents = load_documents()
#     chunks = split_text(documents)
#     db = save_to_chroma(chunks)