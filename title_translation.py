import ollama


ollama_host = 'http://127.0.0.1:11434' 
ollama_client = ollama.Client(host=ollama_host)

def translate_with_ollama(text, target_language='German', model='phi4'): 
    if target_language == "Deutsch":
        return text

    prompt = f'Translate the following sentence to {target_language}. Respond only with the translation and NOTHING else:\n{text}'
    response = ollama_client.chat(model=model, messages=[
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']


