import requests
import json

# Usar session para manter cookies
session = requests.Session()

# Primeiro fazer login
login_data = {
    'email': 'admin@iaon.com',
    'password': 'admin123'
}

print("🔐 Fazendo login...")
login_response = session.post('http://localhost:5000/api/auth/login', 
                             json=login_data,
                             headers={'Content-Type': 'application/json'})

print(f"Status do login: {login_response.status_code}")
print(f"Response: {json.dumps(login_response.json(), indent=2)}")

if login_response.status_code == 200:
    print("\n✅ Login realizado com sucesso!")
    
    # Agora verificar se está autenticado
    print("\n🔍 Verificando autenticação...")
    auth_check = session.get('http://localhost:5000/api/auth/check')
    print(f"Status auth check: {auth_check.status_code}")
    print(f"Response: {json.dumps(auth_check.json(), indent=2)}")
    
    # Tentar acessar configurações de segurança
    print("\n🛡️ Acessando configurações de segurança...")
    security_response = session.get('http://localhost:5000/api/security/settings')
    print(f"Status security: {security_response.status_code}")
    if security_response.status_code == 200:
        print(f"Response: {json.dumps(security_response.json(), indent=2)}")
    else:
        print(f"Erro: {security_response.text}")
        
else:
    print("❌ Erro no login!")
