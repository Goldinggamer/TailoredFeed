from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_session import Session
import os
import tempfile
import json
from datetime import datetime
import subprocess
import shutil
from test_copy import main as generate_feed  

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

# Verfügbare Kategorien
CATEGORIES = {
    'politik': 'Politik',
    'wissenschaft': 'Wissenschaft/Forschung',
    'wissenswertes': 'Wissenswertes',  
    'wirtschaft': 'Wirtschaft und Finanzen',
    'gesundheit': 'Gesundheit und Medizin',
    'muenchen': 'München aktuell',
    'technologie': 'Technologie und IT',
    'sport': 'Sport',
    'reisen': 'Reisen und Lifestyle'
}

@app.route('/')
def prepare():
    # Reset der Session beim Start
    session.clear()
    return render_template('prepare.html')

@app.route('/start')
def index():
    return render_template('index.html')

@app.route('/user_input')
def user_input():
    return render_template('user_input.html')

@app.route('/categories')
def categories():
    # Überprüfen, ob die Benutzerdaten bereits vorhanden sind
    if 'user_info' not in session:
        return redirect(url_for('user_input'))
    return render_template('categories.html')

@app.route('/feed')
def feed():
    if 'news_data' not in session:
        print("Keine news_data in session gefunden, redirect zu generating_news")
        return redirect(url_for('generating_news'))
    
    if 'user_info' not in session:
        print("Keine user_info in session gefunden, redirect zu user_input")
        return redirect(url_for('user_input'))
    
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
        now=datetime.now()
    )

@app.route('/submit-user-info', methods=['POST'])
def submit_user_info():
    age_group = request.form.get('age_group', '')
    gender = request.form.get('gender', '')
    language = request.form.get('language', 'Deutsch')  # Default zu Deutsch
    dialect = request.form.get('dialect', '')
    
    # Validierung: Mindestens Altersgruppe und Geschlecht müssen angegeben sein
    if not age_group or not gender:
        return jsonify({'success': False, 'message': 'Bitte wähle Altersgruppe und Geschlecht aus.'})
    
    # Speichern in der Session
    session['user_info'] = {
        'age_group': age_group,
        'gender': gender,
        'language': language,
        'dialect': dialect
    }
    
    # Log der gesammelten Daten
    log_data('user_info', session['user_info'])
    
    return jsonify({'success': True})

@app.route('/submit-categories', methods=['POST'])
def submit_categories():
    categories_json = request.form.get('categories', '[]')
    format_value = request.form.get('format', '')
    
    try:
        selected_categories = json.loads(categories_json)
    except json.JSONDecodeError:
        selected_categories = []
    
    # Validierung: Mindestens eine Kategorie und ein Format müssen ausgewählt sein
    if not selected_categories or not format_value:
        return jsonify({
            'success': False, 
            'message': 'Bitte wähle mindestens eine Kategorie und ein Newsformat aus.'
        })
    
    session['categories'] = selected_categories
    session['format'] = format_value
    
    return jsonify({'success': True})

@app.route('/generating_news')
def generating_news():
    if 'user_info' not in session or 'categories' not in session:
        return redirect(url_for('index'))
    return render_template('generating_news.html')

@app.route('/generate_news')
def generate_news():
    try:
        if 'user_info' not in session:
            raise ValueError('Keine Benutzerinformationen gefunden')
        
        # User info erweitern mit den Kategorien und dem Format
        user_info = session['user_info'].copy()
        user_info['categories'] = session.get('categories', [])
        user_info['format'] = session.get('format', '')
        
        print(f"User info being passed to generate_feed: {user_info}")  # Debug
        
        # Log der tatsächlich verwendeten Daten
        log_data('request_data', user_info)
        
        # Übergebe das erweiterte user_info an die generate_feed Funktion
        news_data = generate_feed(user_info)
        
        print(f"Type of news_data: {type(news_data)}")  # Debug
        print(f"Generated news_data: {news_data}")  # Debug
        
        if not news_data:
            raise ValueError('Keine News konnten generiert werden')
            
        # Strukturierte News in Session speichern
        session['news_data'] = news_data
        
        # Log der generierten News
        log_data('generated_news', {'data': news_data})
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error generating news: {str(e)}")
        import traceback
        traceback.print_exc()  # Vollständiger Stacktrace
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/update_news')
def update_news():
    return render_template('update_news.html')

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
        
        # Clean up existing database completely
        chroma_path = os.path.join(script_dir, "chroma_db")
        if os.path.exists(chroma_path):
            shutil.rmtree(chroma_path)
            
        # Wait a moment to ensure cleanup is complete
        import time
        time.sleep(1)
        
        # Create fresh directory
        os.makedirs(chroma_path, exist_ok=True)
        
        python_path = "/opt/homebrew/bin/python3.10"  # Korrekter Python-Pfad für M1 Mac
        # python_path = "python"  # Windows Python-Pfad (nutzt Python from PATH)
        
        # Run database.py with full path and environment variables
        result = subprocess.run(
            [python_path, os.path.join(script_dir, "database.py")],
            capture_output=True,
            text=True,
            cwd=script_dir,  # Set working directory explicitly
            env={
                **os.environ,
                'PYTHONPATH': script_dir,
                'CHROMA_PATH': chroma_path
            }
        )
        
        if result.returncode != 0:
            print("Database Error:", result.stderr)
            return jsonify({
                "success": False,
                "error": f"Database initialization failed: {result.stderr}"
            }), 500
            
        # Verify database was created
        if not os.path.exists(os.path.join(chroma_path, "chroma.sqlite3")):
            return jsonify({
                "success": False,
                "error": "Database file not created"
            }), 500
            
        return jsonify({"success": True})
        
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
    return redirect('/')

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

# Zusätzliche Template für den Feed
@app.route('/create_feed_template')
def create_feed_template():
    """Erstellt eine neue Feed-Template-Datei für die Anzeige des personalisierten Nachrichteninhalts"""
    template = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TailoredFeed - Dein Feed</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
  <style>
    .news-content {
      text-align: left;
      background: rgba(50,50,50,0.7);
      padding: 20px;
      border-radius: 10px;
      margin: 20px 0;
      line-height: 1.5;
    }
    .news-category {
      font-weight: bold;
      color: #4CAF50;
      margin: 20px 0 10px 0;
      font-size: 1.2em;
    }
    .category-content {
      margin-bottom: 15px;
      line-height: 1.6;
    }
    .news-images {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin: 10px 0;
    }
    .news-image {
      max-width: 150px;
      max-height: 150px;
      border-radius: 8px;
      object-fit: cover;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .user-settings {
      text-align: left;
      background: rgba(50,50,50,0.7);
      padding: 20px;
      border-radius: 10px;
      margin: 20px 0;
      font-size: 0.9em;
    }
    .user-settings details {
      margin-bottom: 10px;
    }
    .user-settings summary {
      cursor: pointer;
      color: #4CAF50;
    }
  </style>
</head>
<body>
  <div class="background"></div>
  <div class="stars"></div>
  
  <div class="container">
    <div class="brand">tailoredfeed</div>
    
    <div class="section-heading">Dein personalisierter Feed</div>
    
    <div class="user-settings">
      <details>
        <summary>Deine Einstellungen anzeigen</summary>
        <p><strong>Altersgruppe:</strong> {{ user_info.age_group }}</p>
        <p><strong>Geschlecht:</strong> {{ user_info.gender }}</p>
        <p><strong>Sprache:</strong> {{ user_info.language }}</p>
        {% if user_info.dialect %}
        <p><strong>Dialekt:</strong> {{ user_info.dialect }}</p>
        {% endif %}
        
        <h4>Ausgewählte Kategorien:</h4>
        <ul>
        {% for category in categories %}
          <li>{{ category }}</li>
        {% endfor %}
        </ul>
        
        <p><strong>Newsformat:</strong> {{ format }}</p>
      </details>
    </div>
    
    <div class="news-content">
      {% if news_data %}
        {% for news_item in news_data %}
          <div class="news-category">{{ news_item.category }}:</div>
          <div class="category-content">{{ news_item.content }}</div>
          
          {% if news_item.images %}
          <div class="news-images">
            {% for image_url in news_item.images %}
              <img src="{{ image_url }}" alt="Nachrichtenbild" class="news-image" loading="lazy">
            {% endfor %}
          </div>
          {% endif %}
        {% endfor %}
      {% else %}
        <p>Keine Nachrichten verfügbar.</p>
        <p>Debug: news_data = {{ news_data }}</p>
      {% endif %}
    </div>
    
    <a href="{{ url_for('index') }}">
      <button class="cta-button">Zurück zum Start</button>
    </a>
  </div>
  
  <div class="location">📍 München - Maxvorstadt</div>
  <div class="date">{{ now|format_date }}</div>
  
  <script src="{{ url_for('static', filename='scripts.js') }}"></script>
</body>
</html>"""
    
    return template

if __name__ == '__main__':
    # Feed-Template erstellen
    with open('templates/feed.html', 'w', encoding='utf-8') as f:
        f.write(create_feed_template())
    
    app.run(debug=True)