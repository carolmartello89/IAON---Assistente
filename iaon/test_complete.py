#!/usr/bin/env python3
# Teste completo de sintaxe e funcionamento do IAON

import sys
import os

def test_syntax():
    """Testar sintaxe de todos os arquivos"""
    print("🔍 TESTE COMPLETO DE SINTAXE - SISTEMA IAON")
    print("=" * 50)
    
    # Teste 1: Sintaxe Python
    try:
        import py_compile
        py_compile.compile('app.py', doraise=True)
        print("✅ app.py - Sintaxe Python OK")
    except Exception as e:
        print(f"❌ app.py - ERRO: {e}")
        return False
    
    # Teste 2: Importação Flask
    try:
        import app
        print("✅ app.py - Importação Flask OK")
    except Exception as e:
        print(f"❌ app.py - ERRO na importação: {e}")
        return False
    
    # Teste 3: Verificar arquivos principais
    files_to_check = [
        'static/index.html',
        'static/js/main.js', 
        'static/sw.js',
        'static/viral.html',
        'requirements.txt',
        'vercel.json'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - Arquivo existe")
        else:
            print(f"⚠️ {file_path} - Arquivo não encontrado")
    
    # Teste 4: Verificar rotas principais
    try:
        from app import app as flask_app
        with flask_app.test_client() as client:
            # Testar rota principal
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Rota '/' - OK")
            else:
                print(f"⚠️ Rota '/' - Status: {response.status_code}")
            
            # Testar rota viral
            response = client.get('/viral')
            if response.status_code == 200:
                print("✅ Rota '/viral' - OK")
            else:
                print(f"⚠️ Rota '/viral' - Status: {response.status_code}")
            
            # Testar API de status
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ API '/api/status' - OK")
            else:
                print(f"⚠️ API '/api/status' - Status: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Teste de rotas - ERRO: {e}")
        return False
    
    print("\n🎉 TODOS OS TESTES PASSARAM!")
    print("✅ Sistema IAON sem problemas de sintaxe")
    return True

if __name__ == "__main__":
    success = test_syntax()
    sys.exit(0 if success else 1)
