#!/usr/bin/env python3
"""
Script simples para inicializar o banco de dados
"""

from app import app, db
from datetime import datetime

def init_database():
    """Inicializar banco de dados"""
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Banco de dados inicializado com sucesso!")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tabelas criadas: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco de dados: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = init_database()
    if success:
        print("🎉 Inicialização concluída!")
    else:
        print("💥 Falha na inicialização!")
