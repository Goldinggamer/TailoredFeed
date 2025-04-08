import os
import requests
import json
import sys

def retrieve_newsapi_data(api_key):
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # NewsAPI endpoint
    url = 'https://newsapi.org/v2/top-headlines'
    
    # Compile sources from the image
    sources = [
        'ard', 
        'taz', 
        'waz', 
        'focus', 
        'die-welt', 
        'bild', 
        'sz', 
        'sat1'
    ]
    
    # Convert sources to comma-separated string
    sources_str = ','.join(sources)
    
    # Parameters for the API request
    params = {
        'apiKey': api_key,
        'sources': sources_str,
        'pageSize': 100
    }
    
    try:
        # Send GET request to NewsAPI
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        news_data = response.json()
        
        # Define the file path
        file_path = 'data/German_News_Sources.json'
        
        # Write the JSON data to a file with proper encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=4)
        
        print(f"News data successfully saved to {file_path}")
        print(f"Total articles retrieved: {news_data.get('totalResults', 0)}")
        
        # Print article details
        print("\nArticle Details:")
        for article in news_data['articles']:
            print(f"- Source: {article['source']['name']}")
            print(f"  Title: {article.get('title', 'No title')}")
            print(f"  URL: {article.get('url', 'No URL')}")
            print("---")
        
        return news_data
    
    except requests.RequestException as e:
        print(f"Error retrieving news data: {e}")
        return None

# Use the API key directly
api_key = '63a8b0cc821f43fbb73dca7d0a379aa2'
news_data = retrieve_newsapi_data(api_key)