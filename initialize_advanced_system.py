#!/usr/bin/env python3
"""
IAON - Sistema Avançado de Inicialização
Inicializa banco de dados com todas as funcionalidades enterprise
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db, User, VoiceBiometry, Conversation, Message
    print("✅ Módulos importados com sucesso!")
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    sys.exit(1)

def initialize_database():
    """Inicializar banco de dados com estrutura avançada"""
    print("🚀 Iniciando sistema IAON avançado...")
    
    with app.app_context():
        try:
            # Remover tabelas existentes (desenvolvimento)
            print("🗑️  Removendo tabelas antigas...")
            db.drop_all()
            
            # Criar todas as tabelas
            print("🏗️  Criando estrutura do banco de dados...")
            db.create_all()
            
            # Verificar se tabelas foram criadas
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Tabelas criadas: {', '.join(tables)}")
            
            # Criar usuário administrador padrão
            print("👤 Criando usuário administrador...")
            admin_user = User(
                username='admin',
                email='admin@iaon.ai',
                full_name='Administrador IAON',
                preferred_name='Admin',
                password_hash=generate_password_hash('AdminIAON2024!', method='pbkdf2:sha256:100000'),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True,
                is_admin=True,
                language_preference='pt-BR',
                theme_preference='dark',
                notification_preferences={
                    'email': True,
                    'push': True,
                    'sms': False
                },
                privacy_settings={
                    'profile_visibility': 'private',
                    'data_sharing': False,
                    'analytics': True
                },
                security_settings={
                    'two_factor_enabled': False,
                    'session_timeout': 3600,
                    'login_alerts': True
                }
            )
            
            db.session.add(admin_user)
            
            # Criar usuário de demonstração
            print("🧪 Criando usuário de demonstração...")
            demo_user = User(
                username='demo',
                email='demo@iaon.ai',
                full_name='Usuário Demonstração',
                preferred_name='Demo',
                password_hash=generate_password_hash('DemoIAON2024!', method='pbkdf2:sha256:100000'),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True,
                language_preference='pt-BR',
                theme_preference='auto',
                bio='Conta de demonstração do sistema IAON',
                notification_preferences={
                    'email': True,
                    'push': True,
                    'sms': False
                },
                privacy_settings={
                    'profile_visibility': 'public',
                    'data_sharing': True,
                    'analytics': True
                },
                security_settings={
                    'two_factor_enabled': False,
                    'session_timeout': 1800,
                    'login_alerts': True
                }
            )
            
            db.session.add(demo_user)
            
            # Commit das alterações
            db.session.commit()
            
            print("✅ Banco de dados inicializado com sucesso!")
            print(f"👤 Usuário Admin: admin@iaon.ai / AdminIAON2024!")
            print(f"🧪 Usuário Demo: demo@iaon.ai / DemoIAON2024!")
            
            # Verificar dados inseridos
            users_count = User.query.count()
            print(f"📊 Total de usuários criados: {users_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            db.session.rollback()
            return False

def test_api_endpoints():
    """Testar endpoints básicos da API"""
    print("\n🧪 Testando endpoints da API...")
    
    with app.test_client() as client:
        try:
            # Testar endpoint de health check
            response = client.get('/')
            print(f"📡 Endpoint raiz: {response.status_code}")
            
            # Testar endpoint de verificação de auth
            response = client.get('/api/auth/check')
            print(f"🔐 Endpoint auth check: {response.status_code}")
            
            # Testar endpoint de validação de senha
            response = client.post('/api/auth/validate-password', 
                                 json={'password': 'TestPassword123!'})
            print(f"🔒 Endpoint validação senha: {response.status_code}")
            
            print("✅ Testes básicos da API concluídos!")
            
        except Exception as e:
            print(f"❌ Erro nos testes: {e}")

def display_system_info():
    """Exibir informações do sistema"""
    print("\n" + "="*60)
    print("🚀 IAON - SISTEMA ENTERPRISE INICIALIZADO")
    print("="*60)
    print("📍 Localização: c:\\Users\\carol\\Downloads\\iaon")
    print("🐍 Python:", sys.version.split()[0])
    print("🌐 Flask:", app.config.get('VERSION', 'latest'))
    print("💾 Banco de dados: SQLite (iaon.db)")
    print("🔐 Autenticação: PBKDF2-SHA256")
    print("🎯 Status: Funcional e Avançado")
    print("="*60)
    print("\n🚀 Para iniciar o servidor:")
    print("   python app.py")
    print("\n🌐 Acesso local:")
    print("   http://localhost:5000")
    print("\n📊 Recursos disponíveis:")
    print("   • Autenticação avançada com validação em tempo real")
    print("   • Análise de sentimentos e emoções")
    print("   • Sistema de biometria vocal")
    print("   • Protocolo de emergência integrado")
    print("   • Interface responsiva com Tailwind CSS")
    print("   • Sistema de logging avançado")
    print("="*60)

if __name__ == '__main__':
    print("🎯 IAON - Inicialização do Sistema Enterprise")
    print("Desenvolvido para máxima funcionalidade e sofisticação\n")
    
    # Inicializar banco de dados
    if initialize_database():
        # Testar endpoints
        test_api_endpoints()
        
        # Exibir informações do sistema
        display_system_info()
        
        print("\n✅ Sistema IAON pronto para uso!")
        print("🚀 Execute 'python app.py' para iniciar o servidor")
        
    else:
        print("\n❌ Falha na inicialização do sistema")
        sys.exit(1)
