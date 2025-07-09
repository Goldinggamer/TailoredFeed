import sqlite3
import json

def inspect_sqlite_db():
    db_path = "chroma_db/chroma.sqlite3"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Zeige alle Tabellen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Verfügbare Tabellen:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Zeige die Struktur der embeddings-Tabelle
        cursor.execute("PRAGMA table_info(embeddings);")
        columns = cursor.fetchall()
        print(f"\nStruktur der 'embeddings' Tabelle:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Zeige Collection-Informationen
        cursor.execute("SELECT * FROM collections LIMIT 5;")
        collections = cursor.fetchall()
        print(f"\nCollections ({len(collections)}):")
        for collection in collections:
            print(f"  - {collection}")
        
        # Zeige Embedding-Informationen mit korrekten Spaltennamen
        cursor.execute("SELECT * FROM embeddings LIMIT 5;")
        embeddings = cursor.fetchall()
        print(f"\nBeispiel-Embeddings ({len(embeddings)}):")
        for emb in embeddings:
            print(f"  Embedding-Datensatz: {emb}")
            print()
        
        # Prüfe embedding_metadata Tabelle
        cursor.execute("PRAGMA table_info(embedding_metadata);")
        meta_columns = cursor.fetchall()
        print(f"\nStruktur der 'embedding_metadata' Tabelle:")
        for col in meta_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Zeige Metadaten
        cursor.execute("SELECT * FROM embedding_metadata LIMIT 10;")
        metadata = cursor.fetchall()
        print(f"\nBeispiel-Metadaten ({len(metadata)}):")
        for meta in metadata:
            print(f"  - {meta}")
        
        # Prüfe segments Tabelle
        cursor.execute("SELECT * FROM segments LIMIT 5;")
        segments = cursor.fetchall()
        print(f"\nSegmente ({len(segments)}):")
        for segment in segments:
            print(f"  - {segment}")
        
        # Zähle Gesamtanzahl der Embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings;")
        count = cursor.fetchone()[0]
        print(f"\nGesamtanzahl Embeddings: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Fehler beim SQLite-Zugriff: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_sqlite_db()