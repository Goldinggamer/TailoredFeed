import os
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma


DATA_PATH = "data/alle_news.txt"
CHROMA_PATH = "chroma_db/"

# Lade txt Daten aus dem data Ordner
def load_documents():
    doc_loader = TextLoader(DATA_PATH, encoding="utf-8")
    return doc_loader.load()

# Teile den Text in der txt Datei in kleine Chunks, sodass diese später in der Vektor-Datenbank verarbeitet werden können
def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=1000,
        length_function=len,
        add_start_index=True,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    document = chunks[10]
    print(document.page_content)
    print(document.metadata)

    return chunks


def save_to_chroma(chunks: list[Document]):
    # Alte DB wird gelöscht
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    
    # Instanz des OllamaEmbeddings wird erstellt
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Erstellt eine Chroma DB basierend auf den chunks
    db = Chroma.from_documents(chunks,embeddings,persist_directory=CHROMA_PATH)
    
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")


if __name__ == "__main__":
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)
