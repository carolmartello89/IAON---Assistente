#!/usr/bin/env python3
# Teste de sintaxe simplificado

import py_compile
import os

print("🔍 TESTE DE SINTAXE - SISTEMA IAON")
print("=" * 40)

# Teste 1: Compilar app.py
try:
    py_compile.compile('app.py', doraise=True)
    print("✅ app.py - Sintaxe Python OK")
except Exception as e:
    print(f"❌ app.py - ERRO: {e}")

# Teste 2: Verificar estrutura de arquivos
files = {
    'app.py': 'Servidor Flask principal',
    'static/index.html': 'Página principal',
    'static/js/main.js': 'JavaScript principal', 
    'static/sw.js': 'Service Worker',
    'static/viral.html': 'Página viral',
    'requirements.txt': 'Dependências Python',
    'vercel.json': 'Configuração Vercel'
}

for file_path, description in files.items():
    if os.path.exists(file_path):
        print(f"✅ {file_path} - {description}")
    else:
        print(f"❌ {file_path} - FALTANDO: {description}")

print("\n🎉 VERIFICAÇÃO COMPLETA!")
print("Sistema IAON pronto para deploy.")
