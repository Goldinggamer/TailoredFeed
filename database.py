import os
import shutil
import sys
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain.schema import Document  
from langchain_community.document_loaders import JSONLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

DATA_PATH = "./data/alle_news_json.json"
CHROMA_PATH = "chroma_db/"

# Metadaten der json file extrahieren
def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["kategorie"] = record.get("kategorie")
    metadata["title"] = record.get("title")
    metadata["image"] = record.get("image") 
    return metadata

# Json file reinladen
def load_documents():
    try:
        doc_loader = JSONLoader(
            file_path=DATA_PATH,
            jq_schema='.news[]',  
            content_key="text",   # text ist das was später dann gechunkt werden soll
            metadata_func=metadata_func  # metadaten laden
        )
        documents = doc_loader.load()
        print(f"Loaded {len(documents)} documents from {DATA_PATH}")
        return documents
    except ImportError:
        print("Error: Missing required package. Please run: pip install jq")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading documents: {str(e)}")
        sys.exit(1)

# Teilt den Text in chunks während die Metadaten erhalten bleiben
def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=250,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # text ob korrekt gechunkt wird
    if chunks:
        sample = chunks[0]
        print("\nSample chunk:")
        print(f"Content: {sample.page_content[:100]}...")
        print(f"Metadata: {sample.metadata}")

    return chunks

def save_to_chroma(chunks: list[Document]):
    try:
        # Lösche die alte DB, falls sie existiert
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
    

        # kreire eine Ollama embedding instanz mit dem Server
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",  
            base_url="http://127.0.0.1:11434"  
        )
        
        # Kreiert eine Chroma DB anhand der chunks die generiert wurden
        db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PATH
        )
        
        print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
    except Exception as e:
        print(f"Error saving to Chroma: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)