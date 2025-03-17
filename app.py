from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Für die Session-Verwaltung

# Speicherort für gesammelte Daten
DATA_DIR = 'user_data'
os.makedirs(DATA_DIR, exist_ok=True)

# Verfügbare Kategorien
CATEGORIES = {
    'politik': 'Politik',
    'wissenschaft': 'Wissenschaft/Forschung',
    'unterhaltung': 'Unterhaltung',
    'wirtschaft': 'Wirtschaft und Finanzen',
    'gesundheit': 'Gesundheit und Medizin',
    'gaming': 'Gaming',
    'technologie': 'Technologie und IT',
    'sport': 'Sport',
    'reisen': 'Reisen und Lifestyle'
}

@app.route('/')
def index():
    # Reset der Session beim Start
    session.clear()
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
    # Überprüfen, ob alle notwendigen Daten vorhanden sind
    if 'user_info' not in session or 'categories' not in session:
        return redirect(url_for('index'))
    
    user_info = session['user_info']
    selected_categories = session['categories']
    news_format = session['format']
    
    # Hier würde normalerweise die Logik zur Generierung des personalisierten Feeds stehen
    # Platzhalter für die Implementierung
    
    # Debug-Informationen anzeigen
    return render_template(
        'feed_placeholder.html', 
        user_info=user_info,
        categories=selected_categories,
        format=news_format
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
    
    # Speichern in der Session
    session['categories'] = selected_categories
    session['format'] = format_value
    
    # Log der gesammelten Daten
    log_data('categories', {
        'selected_categories': selected_categories,
        'format': format_value
    })
    
    return jsonify({'success': True})

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
    return now.strftime('%A, %-d.%m.%Y')

# Zusätzliche Template für den Feed-Platzhalter
@app.route('/feed_placeholder_template')
def generate_feed_template():
    """Generiert eine einfache Feed-Vorlage zur Anzeige der gesammelten Daten"""
    template = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>TailoredFeed - Dein Feed</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
    <body>
      <div class="background"></div>
      <div class="stars"></div>
      
      <div class="container">
        <div class="brand">tailoredfeed</div>
        
        <div class="section-heading">Dein personalisierter Feed</div>
        
        <div style="text-align: left; background: rgba(50,50,50,0.7); padding: 20px; border-radius: 10px; margin: 20px 0;">
          <h3>Deine Einstellungen:</h3>
          <p><strong>Altersgruppe:</strong> {{ user_info.age_group }}</p>
          <p><strong>Geschlecht:</strong> {{ user_info.gender }}</p>
          <p><strong>Sprache:</strong> {{ user_info.language }}</p>
          {% if user_info.dialect %}
          <p><strong>Dialekt:</strong> {{ user_info.dialect }}</p>
          {% endif %}
          
          <h3>Ausgewählte Kategorien:</h3>
          <ul>
          {% for category in categories %}
            <li>{{ category }}</li>
          {% endfor %}
          </ul>
          
          <p><strong>Newsformat:</strong> {{ format }}</p>
        </div>
        
        <div class="section-heading">
          Hier würden deine personalisierten Nachrichten erscheinen!
        </div>
        
        <a href="{{ url_for('index') }}">
          <button class="cta-button">Zurück zum Start</button>
        </a>
      </div>
      
      <div class="location">📍 München - Maxvorstadt</div>
      <div class="date">{{ now|format_date }}</div>
      
      <script src="{{ url_for('static', filename='scripts.js') }}"></script>
    </body>
    </html>
    """
    
    # Diese Funktion gibt nur das Template zurück, sie wird nicht direkt aufgerufen
    return template

if __name__ == '__main__':
    # Zusätzlichen Feed-Platzhalter erstellen
    with open('templates/feed_placeholder.html', 'w', encoding='utf-8') as f:
        f.write(generate_feed_template())
    
    app.run(debug=True)
