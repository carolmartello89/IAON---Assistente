# Script de inicialização para Vercel
import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

# Importar a aplicação
from app import app, init_database

# Inicializar banco de dados na primeira execução
if os.getenv('VERCEL') == '1':
    with app.app_context():
        init_database()

# Exportar a aplicação para o Vercel
application = app

if __name__ == '__main__':
    application.run()
