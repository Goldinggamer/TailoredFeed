# translations.py
# Translation system for TailoredFeed

translations = {
    'de': {
        # Navigation
        'back': '←',
        'new_start': 'Neu starten',
        'language_switch': 'English',
        
        # Index page
        'headline': 'Genervt von irrelevanten Nachrichten?',
        'subheadline': 'Dann teste jetzt deinen maßgeschneiderten Newsfeed mit',
        'brand': 'tailoredfeed!',
        'personal_settings': 'Persönliche Einstellungen',
        
        # Form fields
        'complexity_level': 'Sprachkomplexität',
        'complexity_simple': 'Einfach - Einfache und verständliche Sprache',
        'complexity_standard': 'Standard - Ausgewogene Sprache',
        'complexity_detailed': 'Detailliert - Detaillierte Fachsprache',
        'language': 'Sprache',
        'categories': 'Interessenskategorien (max. 1)',
        'format': 'Artikelformat',
        'format_short': 'Kurze Artikel',
        'format_detailed': 'Ausführliche Artikel (dauert 2x so lange wie kurze Artikel!)',
        'custom_search_placeholder': 'z.B. Fußball WM, Bitcoin, Künstliche Intelligenz...',
        'create_feed': 'Feed erstellen',
        'please_select': 'Bitte wählen',
        
        # Categories
        'cat_politics': 'Politik',
        'cat_science': 'Wissenschaft und Forschung',
        'cat_knowledge': 'Wissenswertes',
        'cat_economy': 'Wirtschaft und Finanzen',
        'cat_health': 'Gesundheit und Medizin',
        'cat_munich': 'München aktuell',
        'cat_technology': 'Technologie und Innovation',
        'cat_sports': 'Sport',
        'cat_custom': 'Custom Suche',
        
        # Error messages
        'error_complexity': 'Bitte wähle eine Sprachkomplexität aus',
        'error_language': 'Bitte wähle eine Sprache aus',
        'error_categories': 'Bitte wähle mindestens eine Kategorie aus',
        'error_categories_max': 'Du kannst maximal 1 Kategorie auswählen',
        'error_custom_search': 'Bitte gib einen Suchbegriff für die Custom Suche ein',
        'error_format': 'Bitte wähle ein Artikelformat aus',
        
        # Generating news page
        'generating_news': 'Deine News werden generiert...',
        'estimated_wait_time': 'Geschätzte Wartezeit: Max. 30 Sekunden bei kurzen Artikeln / 60 Sekunden bei ausführlichen Artikeln',
        
        # Update news page
        'updating_news': 'Aktualisiere News...',
        'api_success': '✓ News erfolgreich via API geladen',
        'db_success': '✓ News in Vektordatenbank gespeichert',
        'error_update': '❌ Fehler beim Update',
        
        # Feed page
        'personalized_feed': 'Dein personalisierter Nachrichtenfeed',
        'categories_label': 'Kategorien:',
        'profile_label': 'Profil:',
        'help_research_title': 'Helfen Sie bitte meiner Forschung!',
        'help_research_text1': 'Ihre Meinung ist wichtig! Diese App ist Teil einer wissenschaftlichen Studie im Rahmen einer Bachelorarbeit über das Vertrauen in LLM-personalisierte Nachrichten.',
        'help_research_text2': 'Scannen Sie den QR-Code mit Ihrem Smartphone, um an meiner kurzen Umfrage teilzunehmen. Ihre Teilnahme hilft mir dabei, die Technologie zu verbessern.',
        'survey_benefits': [
            '📋 Nur 3-5 Minuten',
            '🔒 Vollständig anonym',
            '🎓 Unterstützt Forschung',
            '💡 Verbessert die Technologie'
        ],
        
        # News ticker
        'news_ticker': [
            '🎭 Heute in der Maxvorstadt: 3 neue Ausstellungen eröffnet',
            '🍽️ Die 5 besten neuen Restaurants in München',
            '🚇 MVV: U3/U6 Sperrung am Wochenende',
            '⚽ FC Bayern: Neuzugang im Anflug',
            '🌦️ Wetterwarnung für morgen: Starkregen'
        ],
        
        # Location and time
        'location': '📍 München',
    },
    
    'en': {
        # Navigation
        'back': '←',
        'new_start': 'Start over',
        'language_switch': 'Deutsch',
        
        # Index page
        'headline': 'Tired of irrelevant news?',
        'subheadline': 'Then try your personalized news feed with',
        'brand': 'tailoredfeed!',
        'personal_settings': 'Personal Settings',
        
        # Form fields
        'complexity_level': 'Language Complexity',
        'complexity_simple': 'Simple - Easy and understandable language',
        'complexity_standard': 'Standard - Balanced language',
        'complexity_detailed': 'Detailed - Detailed technical language',
        'language': 'Language',
        'categories': 'Interest Categories (max. 2)',
        'format': 'Article Format',
        'format_short': 'Short Articles',
        'format_detailed': 'Detailed Articles (takes 2x as long as short articles!)',
        'custom_search_placeholder': 'e.g. World Cup, Bitcoin, Artificial Intelligence...',
        'create_feed': 'Create Feed',
        'please_select': 'Please select',
        
        # Categories
        'cat_politics': 'Politics',
        'cat_science': 'Science and Research',
        'cat_knowledge': 'Interesting Facts',
        'cat_economy': 'Economy and Finance',
        'cat_health': 'Health and Medicine',
        'cat_munich': 'Munich News',
        'cat_technology': 'Technology and Innovation',
        'cat_sports': 'Sports',
        'cat_custom': 'Custom Search (works only in German)',
        
        # Error messages
        'error_complexity': 'Please select a language complexity',
        'error_language': 'Please select a language',
        'error_categories': 'Please select at least one category',
        'error_categories_max': 'You can select a maximum of 2 categories',
        'error_custom_search': 'Please enter a search term for Custom Search',
        'error_format': 'Please select an article format',
        
        # Generating news page
        'generating_news': 'Your news is being generated...',
        'estimated_wait_time': 'Estimated wait time: max. 30 seconds for short articles / 60 seconds for detailed articles',
        
        # Update news page
        'updating_news': 'Updating news...',
        'api_success': '✓ News successfully loaded via API',
        'db_success': '✓ News saved to vector database',
        'error_update': '❌ Error during update',
        
        # Feed page
        'personalized_feed': 'Your personalized news feed',
        'categories_label': 'Categories:',
        'profile_label': 'Profile:',
        'help_research_title': 'Please help my research!',
        'help_research_text1': 'Your opinion matters! This app is part of a scientific study for a bachelor thesis about trust in LLM-personalized news.',
        'help_research_text2': 'Scan the QR code with your smartphone to participate in my short survey. Your participation helps me improve the technology.',
        'survey_benefits': [
            '📋 Only 3-5 minutes',
            '🔒 Completely anonymous',
            '🎓 Supports research',
            '💡 Improves technology'
        ],
        
        # News ticker
        'news_ticker': [
            '🎭 Today in Maxvorstadt: 3 new exhibitions opened',
            '🍽️ The 5 best new restaurants in Munich',
            '🚇 MVV: U3/U6 closure on weekend',
            '⚽ FC Bayern: New signing incoming',
            '🌦️ Weather warning for tomorrow: Heavy rain'
        ],
        
        # Location and time
        'location': '📍 Munich',
    }
}

def get_text(key, lang='de'):
    """Get translated text for a given key and language"""
    return translations.get(lang, {}).get(key, translations['de'].get(key, key))

def get_all_texts(lang='de'):
    """Get all translations for a given language"""
    return translations.get(lang, translations['de'])