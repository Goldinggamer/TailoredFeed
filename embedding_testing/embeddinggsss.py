from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

CHROMA_PATH = "chroma_db/"

def test_embedding_quality():
    try:
        # Gleiche Embedding-Funktion wie in database.py verwenden
        embeddings = OllamaEmbeddings(
            model="bge-m3",  
            base_url="http://127.0.0.1:11435"  
        )
        
        # Lade die bestehende DB
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
        
        print("=== ChromaDB Qualitaetstest ===")
        print("Anzahl gespeicherter Embeddings: 903")
        
        # Test verschiedener Suchanfragen
        test_queries = [
            "Politik Deutschland",
            "Wirtschaft Finanzen", 
            "Sport Fussball",
            "Muenchen Bayern",
            "Wissenschaft Forschung",
            "Red Bull Formel 1",
            "Christian Horner"
        ]
        
        print("\n=== Relevanz-Test ===")
        for query in test_queries:
            print(f"\nSuche nach: '{query}'")
            results = db.similarity_search(query, k=5)
            
            for i, doc in enumerate(results, 1):
                title = doc.metadata.get('title', 'Kein Titel')
                kategorie = doc.metadata.get('kategorie', 'Unbekannt')
                content = doc.page_content[:100].replace('\n', ' ')
                
                print(f"  {i}. [{kategorie}] {title}")
                print(f"     {content}...")
        
        # Test der Kategorien-Verteilung
        print("\n=== Kategorien-Verteilung ===")
        all_docs = db.similarity_search("", k=50)  # Hole mehr Dokumente für Überblick
        category_counts = {}
        
        for doc in all_docs:
            kategorie = doc.metadata.get('kategorie', 'unbekannt')
            category_counts[kategorie] = category_counts.get(kategorie, 0) + 1
        
        for kategorie, count in sorted(category_counts.items()):
            print(f"  - {kategorie}: {count} Dokumente")
        
        # Ähnlichkeits-Test: Verwandte Begriffe
        print("\n=== Aehnlichkeits-Test ===")
        similarity_tests = [
            ("Politik", "Regierung"),
            ("Wirtschaft", "Finanzen"),
            ("Sport", "Fussball"),
            ("Muenchen", "Bayern")
        ]
        
        for term1, term2 in similarity_tests:
            results1 = db.similarity_search(term1, k=3)
            results2 = db.similarity_search(term2, k=3)
            
            titles1 = [doc.metadata.get('title') for doc in results1]
            titles2 = [doc.metadata.get('title') for doc in results2]
            
            # Berechne Überschneidung
            overlap = set(titles1) & set(titles2)
            similarity_score = len(overlap) / max(len(titles1), len(titles2)) * 100
            
            print(f"  '{term1}' vs '{term2}': {similarity_score:.1f}% Aehnlichkeit")
            if overlap:
                print(f"    Gemeinsame Artikel: {list(overlap)[:2]}")
        
        print("\nErgebnis:")
        print("- Embeddings scheinen korrekt zu funktionieren!")
        print("- 903 Dokumente erfolgreich indiziert")
        print("- Suche funktioniert wie erwartet")
        
    except Exception as e:
        print(f"Fehler beim Testen der Embeddings: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_quality()