#!/usr/bin/env python3
import traceback
import sys

try:
    exec(open('app.py').read())
    print("✅ Código executa sem problemas")
except SyntaxError as e:
    print(f"❌ ERRO DE SINTAXE:")
    print(f"Linha {e.lineno}: {e.text}")
    print(f"Erro: {e.msg}")
    traceback.print_exc()
except Exception as e:
    print(f"⚠️ ERRO DE EXECUÇÃO:")
    print(f"Tipo: {type(e).__name__}")
    print(f"Mensagem: {e}")
    traceback.print_exc()
