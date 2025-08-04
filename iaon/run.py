#!/usr/bin/env python3
"""
Script de inicialização para Railway
Funciona tanto no Linux (Railway) quanto Windows (desenvolvimento)
"""
import os
from app import app

if __name__ == "__main__":
    # No Railway, usar a porta fornecida pela plataforma
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"  # Railway requer bind em todas as interfaces
    
    print(f"🚀 Iniciando aplicação IAON na porta {port}")
    # Detectar ambiente de produção
    is_production = any([
        'RAILWAY_ENVIRONMENT' in os.environ,
        'RENDER' in os.environ,
        'HEROKU_APP_NAME' in os.environ
    ])
    
    ambiente = 'Produção' if is_production else 'Local'
    print(f"📡 Ambiente: {ambiente}")
    
    # Em produção, usar configuração otimizada
    if is_production:
        app.run(host=host, port=port, debug=False, threaded=True)
    else:
        # Desenvolvimento local
        app.run(host="127.0.0.1", port=port, debug=True)
