"""
🧪 TESTE LOCAL ANTES DO RAILWAY
Execute este script para verificar se tudo está funcionando antes do deploy
"""
import os
import subprocess
import sys
import requests
import time

def verificar_dependencias():
    """Verificar se todas as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    try:
        import flask
        import flask_cors
        import flask_sqlalchemy
        import gunicorn
        import phonenumbers
        import bcrypt
        print("✅ Todas as dependências estão instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False

def testar_app_local():
    """Testar se a aplicação roda localmente"""
    print("\n🚀 Testando aplicação local...")
    
    # Definir variáveis de ambiente para teste
    os.environ['FLASK_ENV'] = 'development'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    try:
        # Importar a aplicação
        from app import app
        
        # Testar se a aplicação inicializa
        with app.test_client() as client:
            # Testar health check
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health check funcionando")
            else:
                print(f"❌ Health check falhou: {response.status_code}")
                return False
            
            # Testar página principal
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Página principal funcionando")
            else:
                print(f"❌ Página principal falhou: {response.status_code}")
                return False
                
        print("✅ Aplicação funcionando localmente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar aplicação: {e}")
        return False

def verificar_arquivos_railway():
    """Verificar se os arquivos de configuração do Railway estão presentes"""
    print("\n📋 Verificando arquivos de configuração...")
    
    arquivos_necessarios = [
        'railway.json',
        'requirements.txt',
        'app.py'
    ]
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo} encontrado")
        else:
            print(f"❌ {arquivo} não encontrado")
            return False
    
    return True

def exibir_checklist_railway():
    """Exibir checklist para deploy no Railway"""
    print("\n" + "="*50)
    print("🚂 CHECKLIST PARA RAILWAY")
    print("="*50)
    
    checklist = [
        "✅ Cadastrar em https://railway.app",
        "✅ Conectar conta GitHub",
        "✅ Criar novo projeto",
        "✅ Selecionar repositório IAON",
        "✅ Adicionar PostgreSQL",
        "✅ Configurar variáveis de ambiente:",
        "   - PORT=8000",
        "   - FLASK_ENV=production", 
        "   - SECRET_KEY=iaon-railway-secret-key-2025",
        "   - DATABASE_URL=${{Postgres.DATABASE_URL}}",
        "   - RAILWAY_ENVIRONMENT=production",
        "✅ Aguardar deploy (2-3 minutos)",
        "✅ Testar URL gerada pelo Railway"
    ]
    
    for item in checklist:
        print(item)
    
    print("\n💰 CUSTOS:")
    print("🆓 Primeiro mês: GRÁTIS (500 horas)")
    print("💳 Depois: R$ 25/mês (vs R$ 100 Vercel)")
    print("💾 PostgreSQL: INCLUÍDO (vs R$ 50 extra Vercel)")

def main():
    """Função principal do teste"""
    print("🧪 TESTE PRÉ-DEPLOY RAILWAY")
    print("="*30)
    
    # Verificar dependências
    if not verificar_dependencias():
        return
    
    # Verificar arquivos
    if not verificar_arquivos_railway():
        return
    
    # Testar aplicação
    if not testar_app_local():
        return
    
    # Exibir checklist
    exibir_checklist_railway()
    
    print("\n🎉 TUDO PRONTO PARA O RAILWAY!")
    print("👉 Acesse: https://railway.app")
    print("📖 Guia completo: GUIA_RAILWAY_COMPLETO.md")

if __name__ == "__main__":
    main()
