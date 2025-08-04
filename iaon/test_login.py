import requests
import json

# Teste de login
url = 'http://localhost:5000/api/auth/login'
data = {
    'email': 'admin@iaon.com',
    'password': 'admin123'
}

headers = {
    'Content-Type': 'application/json'
}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Erro na requisição: {e}")
