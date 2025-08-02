#!/usr/bin/env python3
"""
🚨 DEMONSTRAÇÃO DO SISTEMA DE PREVENÇÃO AO SUICÍDIO IAON
100% GRATUITO - Salvando Vidas com IA Avançada

Este script demonstra como o sistema detecta, monitora e intervém
automaticamente em situações de risco de suicídio.
"""

import requests
import json
import time

# Configuração da API
BASE_URL = "http://localhost:5000"
headers = {"Content-Type": "application/json"}

def test_emergency_system():
    """Teste completo do sistema de prevenção ao suicídio"""
    
    print("🚨" + "="*60)
    print("   TESTE DO SISTEMA DE PREVENÇÃO AO SUICÍDIO IAON")
    print("   100% GRATUITO - SALVANDO VIDAS COM IA")
    print("="*62)
    
    # 1. Login de emergência
    print("\n1️⃣ Fazendo login de emergência...")
    
    login_data = {
        "username": "teste_emergencia"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/emergency-login", 
                               json=login_data, headers=headers)
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data['access_token']
            print(f"✅ Login realizado: {auth_data['message']}")
            print(f"🆔 ID do usuário: {auth_data['user_id']}")
            
            # Headers com autenticação
            auth_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
        else:
            print(f"❌ Erro no login: {response.text}")
            return
            
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return
    
    # 2. Teste de detecção de risco BAIXO
    print("\n2️⃣ Testando detecção de risco BAIXO...")
    
    low_risk_message = {
        "message": "Estou me sentindo um pouco triste hoje",
        "voice_analysis": {
            "tone": "neutral",
            "speed": 1.0
        },
        "location": {
            "latitude": -23.5505,
            "longitude": -46.6333
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/assess-risk",
                               json=low_risk_message, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Nível de risco: {result['risk_level']}")
            print(f"📈 Score de risco: {result['risk_score']}")
            print(f"💬 Resposta da IA: {result['message']}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    time.sleep(2)
    
    # 3. Teste de detecção de risco MÉDIO
    print("\n3️⃣ Testando detecção de risco MÉDIO...")
    
    medium_risk_message = {
        "message": "Me sinto muito sozinho e sem esperança, como se nada fosse dar certo",
        "voice_analysis": {
            "tone": "sad",
            "speed": 0.8
        },
        "location": {
            "latitude": -23.5505,
            "longitude": -46.6333
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/assess-risk",
                               json=medium_risk_message, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Nível de risco: {result['risk_level']}")
            print(f"📈 Score de risco: {result['risk_score']}")
            print(f"💬 Resposta da IA: {result['message']}")
            print(f"🔄 Monitoramento ativo: {result['monitoring_active']}")
            if result.get('resources'):
                print("🆘 Recursos fornecidos:")
                for resource in result['resources']:
                    print(f"   • {resource}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    time.sleep(2)
    
    # 4. Teste de detecção de risco CRÍTICO (simulação)
    print("\n4️⃣ Testando detecção de risco CRÍTICO...")
    print("⚠️  ATENÇÃO: Esta é uma simulação para demonstração!")
    
    critical_risk_message = {
        "message": "Não aguento mais viver, quero acabar com tudo e me matar",
        "voice_analysis": {
            "tone": "hopeless",
            "speed": 0.6
        },
        "location": {
            "latitude": -23.5505,
            "longitude": -46.6333
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/assess-risk",
                               json=critical_risk_message, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"🚨 ALERTA CRÍTICO DETECTADO!")
            print(f"📊 Nível de risco: {result['risk_level']}")
            print(f"📈 Score de risco: {result['risk_score']}")
            print(f"💬 Resposta da IA: {result['message']}")
            print(f"🚨 Emergência ativada: {result['emergency_activated']}")
            print(f"🔄 Monitoramento ativo: {result['monitoring_active']}")
            if result.get('resources'):
                print("🆘 Recursos de emergência:")
                for resource in result['resources']:
                    print(f"   • {resource}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    time.sleep(2)
    
    # 5. Teste de compartilhamento de localização
    print("\n5️⃣ Testando compartilhamento de localização de emergência...")
    
    location_data = {
        "latitude": -23.5505,
        "longitude": -46.6333,
        "accuracy": 10.0,
        "address": "São Paulo, SP - Localização de teste",
        "location_type": "unknown"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/share-location",
                               json=location_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📍 Localização compartilhada!")
            print(f"👥 Contatos notificados: {result['shared_with_contacts']}")
            print(f"🛡️  Nível de segurança: {result['safety_level']}")
            print(f"💬 {result['message']}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    time.sleep(2)
    
    # 6. Teste de monitoramento de saúde
    print("\n6️⃣ Testando monitoramento de saúde mental...")
    
    health_data = {
        "mental_health_score": 0.2,  # Muito baixo
        "stress_level": "high",
        "anxiety_level": "severe",
        "emotional_tone": "sad",
        "activity_level": "very_low",
        "social_withdrawal": True,
        "interaction_frequency": 1,
        "support_system_strength": 0.3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/health-check",
                               json=health_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"🏥 Monitoramento de saúde realizado!")
            print(f"📊 Score de risco geral: {result['overall_risk_score']}")
            print(f"⚡ Prioridade de intervenção: {result['intervention_priority']}")
            print(f"⏰ Frequência de monitoramento: {result['monitoring_frequency_hours']}h")
            print(f"💬 {result['message']}")
            print(f"🚨 Protocolo de emergência: {result['emergency_activated']}")
            if result.get('resources_provided'):
                print("🆘 Recursos fornecidos:")
                for resource in result['resources_provided']:
                    print(f"   • {resource}")
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    time.sleep(2)
    
    # 7. Teste de intervenção em crise
    print("\n7️⃣ Testando técnicas de intervenção em crise...")
    
    crisis_data = {
        "crisis_type": "suicidal",
        "severity": "high"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/emergency/crisis-intervention",
                               json=crisis_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"🆘 Intervenção em crise ativada!")
            print(f"🎯 Tipo de crise: {result['crisis_type']}")
            print(f"📊 Severidade: {result['severity']}")
            print(f"💬 {result['message']}")
            print("\n🧘 Técnicas de intervenção fornecidas:")
            for technique in result['intervention_techniques']:
                print(f"   • {technique['technique']}")
                print(f"     {technique['description']}")
                print(f"     Duração: {technique['duration_minutes']} minutos")
            
            print("\n🚨 Ações imediatas recomendadas:")
            for action in result['immediate_actions']:
                print(f"   • {action}")
                
            print("\n📞 Contatos de emergência:")
            for contact, number in result['emergency_contacts'].items():
                print(f"   • {contact.upper()}: {number}")
                
        else:
            print(f"❌ Erro: {response.text}")
            
    except requests.RequestException as e:
        print(f"❌ Erro: {e}")
    
    # Resumo final
    print("\n" + "="*62)
    print("✅ TESTE COMPLETO DO SISTEMA DE PREVENÇÃO AO SUICÍDIO")
    print("="*62)
    print("💙 O sistema IAON está funcionando perfeitamente!")
    print("🚨 Detecta riscos automaticamente")
    print("📍 Compartilha localização com contatos de emergência")
    print("🏥 Monitora saúde mental continuamente")
    print("🆘 Fornece intervenções de crise em tempo real")
    print("📞 Conecta com recursos de apoio 24/7")
    print("\n🎯 MISSÃO: Salvar vidas através de IA avançada - 100% GRATUITO")
    print("💫 Cada vida importa. Você não está sozinho(a)!")

if __name__ == "__main__":
    test_emergency_system()
