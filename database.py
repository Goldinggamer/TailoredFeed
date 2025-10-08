from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain.schema import Document  
from langchain_community.document_loaders import JSONLoader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from ApiNews import main as fetchNews
import uuid
collection_name = f"news_collection_{uuid.uuid4().hex[:8]}"

embedding_function = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://127.0.0.1:11434"
)

# db = Chroma.from_documents(
#     documents=list([]),
#     embedding=embedding_function,
#     collection_name=collection_name

# )

db = Chroma(embedding_function=embedding_function)
complete_documents = list()


def metadata_func(record: dict, metadata: dict) -> dict:
    metadata["kategorie"] = record.get("kategorie")
    metadata["title"] = record.get("title")
    metadata["image"] = record.get("image") 
    return metadata


def create_in_memory_chroma_db():
    global complete_documents
    global db
    try:
        fetchNews()
    except:
        print("Fehler bei fetchApiNews. Nutze alte Nachrichten")
    print("CHROMA_CREATE - init")

    """
    Erstellt eine In-Memory ChromaDB aus den News-Daten
    """
    try:
        print("CHROMA_CREATE - try")


        # Json file laden
        doc_loader = JSONLoader(
            file_path="./data/alle_news_json.json",
            jq_schema='.news[]',  
            content_key="text",
            metadata_func=metadata_func
        )
        print("JSON LOADER")
        documents = doc_loader.load()
        complete_documents = documents
        print("CHROMA_CREATE - documents loaded")
        
        # Text chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        print("CHROMA_CREATE - chunks splitted")
        
        # Komplett neue ChromaDB-Instanz erstellen mit eindeutiger Collection
        db.reset_collection()
        # db.delete_collection()
        db.add_documents(chunks)
        
        # db = Chroma.from_documents(
        #     documents=chunks,
        #     embedding=embedding_function,
        #     collection_name=collection_name,  # Eindeutige Collection-ID
        #     # Kein persist_directory = In-Memory
        # )

        print(f"Created in-memory ChromaDB with {len(chunks)} chunks.")
        
    except Exception as e:
        print(f"Error creating in-memory ChromaDB: {str(e)}")



def update_db(): 
    create_in_memory_chroma_db()


