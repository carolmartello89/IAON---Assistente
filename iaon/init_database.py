#!/usr/bin/env python3
"""
Script para inicializar o banco de dados com todas as tabelas necessárias
para o sistema de prevenção ao suicídio e anti-sequestro.
"""

from app import app, db, User, EmergencyContact, SecuritySettings
from datetime import datetime

def create_tables():
    """Criar todas as tabelas do banco de dados"""
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Todas as tabelas foram criadas com sucesso!")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n📊 Tabelas criadas ({len(tables)}):")
            for table in sorted(tables):
                print(f"  - {table}")
                
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            return False
            
    return True

def create_demo_data():
    """Criar dados de demonstração para testes"""
    with app.app_context():
        try:
            # Verificar se já existe usuário demo
            demo_user = User.query.filter_by(email='demo@iaon.com').first()
            
            if not demo_user:
                # Criar usuário demo
                demo_user = User(
                    username='demo_user',
                    email='demo@iaon.com',
                    full_name='Usuário Demonstração',
                    is_premium=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(demo_user)
                db.session.flush()  # Para obter o ID
                
                # Criar contatos de emergência
                emergency_contacts = [
                    EmergencyContact(
                        user_id=demo_user.id,
                        name='Família Principal',
                        phone='+5511999999999',
                        email='familia@exemplo.com',
                        relationship='family',
                        priority=1,
                        can_receive_location=True,
                        can_receive_photos=True,
                        can_receive_audio=True,
                        notification_methods='["whatsapp", "sms", "email"]'
                    ),
                    EmergencyContact(
                        user_id=demo_user.id,
                        name='Melhor Amigo(a)',
                        phone='+5511888888888',
                        email='amigo@exemplo.com',
                        relationship='friend',
                        priority=2,
                        can_receive_location=True,
                        can_receive_photos=False,
                        can_receive_audio=True,
                        notification_methods='["whatsapp", "sms"]'
                    ),
                    EmergencyContact(
                        user_id=demo_user.id,
                        name='Profissional de Saúde Mental',
                        phone='+5511777777777',
                        email='psicologo@clinica.com',
                        relationship='professional',
                        priority=3,
                        can_receive_location=False,
                        can_receive_photos=False,
                        can_receive_audio=False,
                        notification_methods='["email"]'
                    )
                ]
                
                for contact in emergency_contacts:
                    db.session.add(contact)
                
                # Criar configurações de segurança padrão
                security_settings = SecuritySettings(
                    user_id=demo_user.id,
                    auto_kidnapping_detection=True,
                    motion_sensitivity=0.7,
                    voice_trigger_enabled=True,
                    volume_button_trigger_enabled=True,
                    shake_pattern_trigger_enabled=True,
                    text_code_trigger_enabled=True,
                    panic_voice_phrases='["socorro", "me ajudem", "estou em perigo", "código vermelho"]',
                    panic_text_codes='["911", "SOS", "HELP", "PERIGO"]',
                    volume_button_sequence='volume_up_3x',
                    shake_pattern_threshold=0.8,
                    auto_photo_capture=True,
                    auto_audio_recording=True,
                    max_recording_duration_minutes=30,
                    photo_quality='high',
                    use_both_cameras=True,
                    silent_notifications_only=True,
                    notification_retry_attempts=5,
                    notification_retry_interval_minutes=2,
                    auto_contact_police=False,
                    precise_location_sharing=True,
                    continuous_location_tracking=True,
                    location_update_interval_seconds=30,
                    evidence_encryption_enabled=True,
                    auto_delete_evidence_days=30,
                    require_pin_to_disable=True,
                    stealth_mode=True
                )
                db.session.add(security_settings)
                
                db.session.commit()
                print("✅ Dados de demonstração criados com sucesso!")
                print(f"📧 Usuário demo: {demo_user.email}")
                print(f"👥 Contatos de emergência: {len(emergency_contacts)}")
                print("🔒 Configurações de segurança configuradas")
                
            else:
                print("ℹ️ Usuário demo já existe no banco de dados")
                
        except Exception as e:
            print(f"❌ Erro ao criar dados demo: {e}")
            db.session.rollback()
            return False
            
    return True

def verify_system():
    """Verificar se o sistema está funcionando corretamente"""
    with app.app_context():
        try:
            # Verificar usuários
            users_count = User.query.count()
            print(f"👤 Usuários no sistema: {users_count}")
            
            # Verificar contatos de emergência
            contacts_count = EmergencyContact.query.count()
            print(f"📞 Contatos de emergência: {contacts_count}")
            
            # Verificar configurações de segurança
            settings_count = SecuritySettings.query.count()
            print(f"⚙️ Configurações de segurança: {settings_count}")
            
            # Verificar se demo user tem configurações
            demo_user = User.query.filter_by(email='demo@iaon.com').first()
            if demo_user:
                user_contacts = EmergencyContact.query.filter_by(user_id=demo_user.id).count()
                user_settings = SecuritySettings.query.filter_by(user_id=demo_user.id).first()
                print(f"📋 Demo user - Contatos: {user_contacts}, Configurações: {'✅' if user_settings else '❌'}")
                
            return True
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            return False

if __name__ == '__main__':
    print("🚀 Inicializando banco de dados do IAON - Sistema Anti-Sequestro")
    print("=" * 60)
    
    # Passo 1: Criar tabelas
    print("\n1️⃣ Criando estrutura do banco de dados...")
    if not create_tables():
        exit(1)
    
    # Passo 2: Criar dados demo
    print("\n2️⃣ Criando dados de demonstração...")
    if not create_demo_data():
        exit(1)
    
    # Passo 3: Verificar sistema
    print("\n3️⃣ Verificando sistema...")
    if not verify_system():
        exit(1)
        
    print("\n" + "=" * 60)
    print("✅ Sistema inicializado com sucesso!")
    print("🔒 Sistema anti-sequestro ativo e operacional")
    print("📱 Acesse /security-demo para testar as funcionalidades")
    print("⚠️ LEMBRE-SE: Sistema opera em modo SILENCIOSO durante emergências")
