from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_session import Session
import os
import tempfile
import json
from datetime import datetime
import subprocess
import shutil
from test_copy import main as generate_feed
from translations import get_text, get_all_texts

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure server-side sessions
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = tempfile.mkdtemp()
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'tailoredfeed:'

Session(app)

# Speicherort für gesammelte Daten
DATA_DIR = 'user_data'
os.makedirs(DATA_DIR, exist_ok=True)

@app.route('/')
def root():
    # Set default language if not set
    if 'ui_language' not in session:
        session['ui_language'] = 'de'
    return render_template('update_news.html', texts=get_all_texts(session.get('ui_language', 'de')))

@app.route('/start')
def index():
    # Set default language if not set
    if 'ui_language' not in session:
        session['ui_language'] = 'de'
    return render_template('index.html', texts=get_all_texts(session.get('ui_language', 'de')))

@app.route('/submit-complete-user-info', methods=['POST'])
def submit_complete_user_info():
    data = request.get_json()
    
    complexity_level = data.get('complexity_level', '')
    language = data.get('language', 'Deutsch')
    categories = data.get('categories', [])
    format_value = data.get('format', '')
    custom_search_term = data.get('custom_search_term', '')
    
    # Validierung: Alle Pflichtfelder müssen ausgefüllt sein
    if not complexity_level:
        return jsonify({'success': False, 'message': 'Bitte wähle eine Sprachkomplexität aus.'})
    
    if not language:
        return jsonify({'success': False, 'message': 'Bitte wähle eine Sprache aus.'})
    
    if not categories or len(categories) == 0:
        return jsonify({'success': False, 'message': 'Bitte wähle mindestens eine Kategorie aus.'})
    
    if len(categories) > 1:
        return jsonify({'success': False, 'message': 'Du kannst maximal 1 Kategorie auswählen.'})
    
    if not format_value:
        return jsonify({'success': False, 'message': 'Bitte wähle ein Artikelformat aus.'})
    
    # Validierung für Custom-Suche
    if 'custom' in categories and not custom_search_term.strip():
        return jsonify({'success': False, 'message': 'Bitte gib einen Suchbegriff für die Custom Suche ein.'})
    
    # Speichern in der Session
    session['user_info'] = {
        'complexity_level': complexity_level,
        'language': language
    }
    session['categories'] = categories
    session['format'] = format_value
    session['custom_search_term'] = custom_search_term.strip()
    
    # Log der gesammelten Daten
    current_time = datetime.now()
    session['user_data'] = {
        'timestamp': current_time.strftime('%Y%m%d_%H%M%S'),
        'date': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_info': session['user_info'],
        'categories': categories,
        'format': format_value,
        'custom_search_term': custom_search_term
    }
    
    return jsonify({'success': True})

@app.route('/switch_language')
def switch_language():
    """Switch between German and English UI language"""
    current_lang = session.get('ui_language', 'de')
    new_lang = 'en' if current_lang == 'de' else 'de'
    session['ui_language'] = new_lang
    
    # Redirect back to the referring page or index
    referrer = request.referrer
    if referrer and any(route in referrer for route in ['/start', '/feed', '/generating_news']):
        return redirect(referrer)
    else:
        return redirect(url_for('index'))

@app.route('/feed')
def feed():
    if 'news_data' not in session:
        print("Keine news_data in session gefunden, redirect zu generating_news")
        return redirect(url_for('generating_news'))
    
    if 'user_info' not in session:
        print("Keine user_info in session gefunden, redirect zu index")
        return redirect(url_for('index'))
    
    print(f"Rendering feed with news_data: {session['news_data']}")
    
    # Daten für Template extrahieren
    news_data = session['news_data']
    user_info = session['user_info']
    categories = session.get('categories', [])
    format_type = session.get('format', '')
    
    # Große Daten aus Session entfernen NACH dem Rendern
    if 'news_data' in session:
        del session['news_data']
    
    return render_template(
        'feed.html',
        news_data=news_data,
        user_info=user_info,
        categories=categories,
        format=format_type,
        now=datetime.now(),
        texts=get_all_texts(session.get('ui_language', 'de'))
    )

@app.route('/generating_news')
def generating_news():
    if 'user_info' not in session or 'categories' not in session:
        return redirect(url_for('index'))
    return render_template('generating_news.html', texts=get_all_texts(session.get('ui_language', 'de')))

@app.route('/generate_news')
def generate_news():
    try:
        if 'user_info' not in session:
            raise ValueError('Keine Benutzerinformationen gefunden')
        
        # User info erweitern mit den Kategorien und dem Format
        user_info = session['user_info'].copy()
        user_info['categories'] = session.get('categories', [])
        user_info['format'] = session.get('format', '')
        user_info['custom_search_term'] = session.get('custom_search_term', '')
        
        print(f"User info being passed to generate_feed: {user_info}")  # Debug
        
        # Übergebe das erweiterte user_info an die generate_feed Funktion
        news_data = generate_feed(user_info)
        
        print(f"Type of news_data: {type(news_data)}")  # Debug
        print(f"Generated news_data: {news_data}")  # Debug
        
        if not news_data:
            raise ValueError('Keine News konnten generiert werden')
            
        # Strukturierte News in Session speichern
        session['news_data'] = news_data
        
        # Kombinierte Daten für komplette Session-Info
        complete_session_data = session.get('user_data', {})
        complete_session_data['generated_news'] = {'data': news_data}
        
        # Log der kombinierten Daten
        log_data('complete_session', complete_session_data)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error generating news: {str(e)}")
        import traceback
        traceback.print_exc()  # Vollständiger Stacktrace
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/update_api_news')
def update_api_news():
    try:
        subprocess.run(['python', 'ApiNews.py'], check=True)
        return jsonify({"success": True})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/update_database')
def update_database():
    try:
        # Get absolute path to the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Change to script directory before running database.py
        os.chdir(script_dir)
        
        # Keine Festplatten-DB mehr - cleanup nicht mehr nötig
        # In-Memory ChromaDB löst Windows-Dateisperrung
        
        python_path = "python"  # Windows Python-Pfad (nutzt Python from PATH)
        #python_path = "opt/homebrew/bin/python3.10"  # macOS m1 Homebrew Python-Pfad
        
        # Run database.py with full path and environment variables
        result = subprocess.run(
            [python_path, os.path.join(script_dir, "database.py")],
            capture_output=True,
            text=True,
            cwd=script_dir,  # Set working directory explicitly
            env={
                **os.environ,
                'PYTHONPATH': script_dir
            }
        )
        
        if result.returncode != 0:
            print("Database Error:", result.stderr)
            return jsonify({
                "success": False,
                "error": f"Database initialization failed: {result.stderr}"
            }), 500
            
        # In-Memory DB - keine Datei-Validierung mehr nötig
        print("In-Memory ChromaDB successfully initialized")
        return jsonify({"success": True})
        
    except Exception as e:
        print("Exception:", str(e))
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    except Exception as e:
        print("Exception:", str(e))
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cleanup_session')
def cleanup_session():
    """Clean up session data to reduce cookie size"""
    # Keep only essential data
    essential_keys = ['user_id', 'language']
    session_copy = {k: v for k, v in session.items() if k in essential_keys}
    session.clear()
    session.update(session_copy)
    return redirect('/')

@app.route('/reset_session')
def reset_session():
    """Completely reset the session"""
    session.clear()
    return redirect(url_for('root'))  # Ändere das redirect zur Startseite

@app.route('/restart')
def restart():
    """Restart the application by clearing session and redirecting to start page"""
    session.clear()
    return redirect(url_for('/generating_news'))  # Ändere von 'index' zu 'root'

@app.route('/api/news-images')
def get_news_images():
    """API endpoint to get news images from alle_news_json.json"""
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'alle_news_json.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract images from news articles
        images = []
        for article in data.get('news', []):
            if 'image' in article and article['image']:
                images.append({
                    'url': article['image'],
                    'title': article.get('title', ''),
                    'kategorie': article.get('kategorie', '')
                })
        
        return jsonify({'success': True, 'images': images})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def log_data(data_type, data):
    """
    Speichert die gesammelten Daten zur späteren Analyse
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user_id = session.get('user_id', timestamp)
    
    # User ID in der Session speichern, falls noch nicht vorhanden
    if 'user_id' not in session:
        session['user_id'] = user_id
    
    filename = f"{DATA_DIR}/{user_id}_{data_type}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.template_filter('format_date')
def format_date(value):
    """Format date for display in templates"""
    now = datetime.now()
    # Windows-compatible date format (removed the - from %-d)
    return now.strftime('%A, %d.%m.%Y')


if __name__ == '__main__':
    
    app.run(debug=True)