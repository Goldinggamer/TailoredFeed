import os
import requests
import json

def retrieve_mediastack_news(api_key):
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Mediastack API endpoint for live news
    url = f'http://api.mediastack.com/v1/news'
    
    # Parameters for the API request
    params = {
        'access_key': api_key,  # Replace with your actual API key
        'countries': 'de',      # Focusing on German news
        'limit': 100            # Retrieve up to 100 news articles
    }
    
    try:
        # Send GET request to Mediastack API
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Parse the JSON response
        news_data = response.json()
        
        # Define the file path
        file_path = 'data/All_News_Mediastack.json'
        
        # Write the JSON data to a file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=4)
        
        print(f"News data successfully saved to {file_path}")
        print(f"Total articles retrieved: {len(news_data.get('data', []))}")
        
        return news_data
    
    except requests.RequestException as e:
        print(f"Error retrieving news data: {e}")
    except json.JSONDecodeError:
        print("Error parsing JSON response")

# Replace 'YOUR_ACCESS_KEY' with the actual API key you received
api_key = '2c49280aa9da55903e2756bd171a705e'
news_data = retrieve_mediastack_news(api_key)