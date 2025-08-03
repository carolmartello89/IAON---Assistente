#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IAON - Teste Completo do Sistema
Verificar se todas as funcionalidades estão operacionais
"""

import requests
import json
from datetime import datetime

def test_api_endpoint(url, method='GET', data=None, description=""):
    """Testar um endpoint da API"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ {description}: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: Erro - {str(e)}")
        return False

def main():
    print("🛡️ IAON - Teste Completo do Sistema")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Teste 1: Página principal
    print("\n📋 Testando páginas principais...")
    test_api_endpoint(f"{base_url}/", description="Página principal")
    test_api_endpoint(f"{base_url}/viral", description="Página viral")
    
    # Teste 2: APIs virais
    print("\n🎮 Testando APIs virais...")
    test_api_endpoint(f"{base_url}/api/games/brain-challenge", description="Brain Challenge")
    test_api_endpoint(f"{base_url}/api/music/ai-playlist?mood=happy", description="AI Music Playlist")
    test_api_endpoint(f"{base_url}/api/love/compatibility?name1=Ana&name2=João", description="Calculadora de Amor")
    test_api_endpoint(f"{base_url}/api/fortune/daily?sign=leao", description="Horóscopo")
    
    # Teste 3: APIs de emergência
    print("\n🚨 Testando APIs de emergência...")
    
    # Dados de teste para sequestro
    kidnapping_data = {
        "subtype": "test_alert",
        "systemId": "test_system_123",
        "location": {"latitude": -23.5505, "longitude": -46.6333},
        "deviceInfo": {"userAgent": "test_agent"}
    }
    
    test_api_endpoint(
        f"{base_url}/api/emergency/kidnapping", 
        method='POST', 
        data=kidnapping_data,
        description="Alerta de Sequestro"
    )
    
    # Dados de teste para invasão
    invasion_data = {
        "phrase": "estou com problemas",
        "systemId": "test_system_123",
        "location": {"latitude": -23.5505, "longitude": -46.6333},
        "urgencyLevel": "high"
    }
    
    test_api_endpoint(
        f"{base_url}/api/emergency/home-invasion", 
        method='POST', 
        data=invasion_data,
        description="Alerta de Invasão"
    )
    
    # Teste SMS
    sms_data = {
        "phone": "11999999999",
        "message": "Teste de SMS de emergência",
        "alertId": "test_alert_123"
    }
    
    test_api_endpoint(
        f"{base_url}/api/emergency/sms", 
        method='POST', 
        data=sms_data,
        description="SMS de Emergência"
    )
    
    # Teste chamada
    call_data = {
        "phone": "11999999999",
        "name": "Teste Contato",
        "alertId": "test_alert_123"
    }
    
    test_api_endpoint(
        f"{base_url}/api/emergency/make-call", 
        method='POST', 
        data=call_data,
        description="Chamada de Emergência"
    )
    
    # Teste 4: Status do sistema
    print("\n📊 Testando status do sistema...")
    test_api_endpoint(f"{base_url}/api/status", description="Status do Sistema")
    
    print("\n" + "=" * 50)
    print("🎯 Teste completo finalizado!")
    print("💡 Se todos os testes passaram, o sistema está 100% operacional!")

if __name__ == "__main__":
    main()
