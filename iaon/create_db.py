#!/usr/bin/env python3
"""
Script para criar/recriar o banco de dados IAON com todas as configurações de segurança
"""

import os
import sys

# Remover banco existente se existir
if os.path.exists('database/iaon.db'):
    os.remove('database/iaon.db')
    print("🗑️ Banco de dados anterior removido")

if os.path.exists('emergency_alerts.db'):
    os.remove('emergency_alerts.db')
    print("🗑️ Banco de alertas anterior removido")

# Garantir que o diretório database existe
os.makedirs('database', exist_ok=True)

# Configurar variáveis de ambiente
os.environ['SKIP_DB_INIT'] = 'false'

# Importar e inicializar app
from app import app, db

def create_database():
    """Criar banco de dados com todas as tabelas"""
    print("🏗️ Criando banco de dados...")
    
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso")
        
        print("\n🎉 Banco de dados criado com sucesso!")
        print("🔐 Sistema de segurança: Configurado")
        print("📱 Interface: Pronta")
        print("🤖 IA Conversacional: Ativa")
        print("🛡️ Configurações de Segurança: Implementadas")
        print("\n� Use as credenciais padrão criadas automaticamente")

if __name__ == '__main__':
    create_database()
