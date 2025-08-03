#!/usr/bin/env python3
# Teste de sintaxe para app.py

try:
    import app
    print("✅ SUCESSO: app.py importado sem erros de sintaxe")
except SyntaxError as e:
    print(f"❌ ERRO DE SINTAXE: {e}")
    print(f"Linha {e.lineno}: {e.text}")
except ImportError as e:
    print(f"⚠️ ERRO DE IMPORTAÇÃO: {e}")
except Exception as e:
    print(f"❌ ERRO GERAL: {e}")
