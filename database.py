import os
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.document_loaders import JSONLoader
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

DATA_PATH = "./data/alle_news_json.json"
CHROMA_PATH = "chroma_db/"

# Metadaten der json file extrahieren
def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["kategorie"] = record.get("kategorie")
    metadata["title"] = record.get("title")
    return metadata

# Json file reinladen
def load_documents():
    doc_loader = JSONLoader(
        file_path=DATA_PATH,
        jq_schema='.news[]',  
        content_key="text",   # text ist das was später dann gechunkt werden soll
        metadata_func=metadata_func  # metadaten laden
    )
    documents = doc_loader.load()
    print(f"Loaded {len(documents)} documents from {DATA_PATH}")
    return documents

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
    # Lösche die alte DB, falls sie existiert
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    
    # kreire eine Ollama embedding instanz
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Kreiert eine Chroma DB anhand der chunks die generiert wurden
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

"""
import os
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction
import chromadb

DATA_PATH = "data/alle_news.txt"
CHROMA_PATH = "chroma_db/"

def load_documents():
    doc_loader = TextLoader(DATA_PATH, encoding="utf-8")
    return doc_loader.load()

def split_text(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,  
        chunk_overlap=1000,  
        length_function=len,
        add_start_index=True,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
    )
    
    return text_splitter.split_documents(documents)

def save_to_chroma(chunks):
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    
    ollama_ef = OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text:latest",
    )
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(
        name="news_collection",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"},
    )
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, chunk in enumerate(chunks):
        documents.append(chunk.page_content)
        metadatas.append(chunk.metadata)
        ids.append(f"chunk_{idx}")
    
    batch_size = 500
    
    for i in range(0, len(documents), batch_size):
        batch_end = min(i + batch_size, len(documents))
        
        collection.upsert(
            documents=documents[i:batch_end],
            metadatas=metadatas[i:batch_end],
            ids=ids[i:batch_end],
        )
    
    return collection

def main():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

if __name__ == "__main__":
    main()
"""