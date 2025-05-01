import ollama

client = ollama.Client(host='http://10.40.15.6:80')  # VPN-IP und Port 80

response = client.chat(
    model='deepseek-r1:70b',  # oder das Modell, das du geladen hast
    messages=[
        {'role': 'user', 'content': 'Was ist Quantenverschränkung?'}
    ]
)

print(response['message']['content'])
