#!/usr/bin/env python3
"""
Script simples para inicializar o banco de dados
"""

from app import app, db
from datetime import datetime

def create_simple_db():
    """Criar banco de dados simples"""
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Banco de dados criado com sucesso!")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 {len(tables)} tabelas criadas:")
            for table in sorted(tables):
                print(f"  - {table}")
                
        except Exception as e:
            print(f"❌ Erro ao criar banco: {e}")

if __name__ == '__main__':
    create_simple_db()
