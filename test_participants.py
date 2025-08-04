# Script para testar o Sistema de Participantes Inteligente do IAON
# Este script cria dados de exemplo para demonstrar as funcionalidades

from app import app, db, KnownParticipant, User, MeetingSession, MeetingParticipant
from datetime import datetime, timedelta
import json
import random

def create_test_data():
    """Criar dados de teste para demonstrar o sistema de participantes"""
    
    with app.app_context():
        # Verificar se já existe usuário de teste
        user = User.query.filter_by(username='demo').first()
        if not user:
            # Criar usuário de teste
            user = User(
                username='demo',
                email='demo@iaon.app',
                full_name='Usuário Demo',
                preferred_name='Demo',
                password_hash='$2b$12$demo.hash.for.testing',
                is_onboarded=True,
                voice_enabled=True
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Usuário de teste criado: {user.username}")
        
        # Criar participantes conhecidos de exemplo
        participants_data = [
            {
                'name': 'Maria Silva',
                'email': 'maria.silva@empresa.com',
                'phone': '(11) 99999-1111',
                'company': 'Tech Solutions Ltda',
                'position': 'Gerente de Projetos',
                'default_role': 'moderador',
                'meeting_count': 8,
                'is_frequent': True,
                'notes': 'Sempre pontual e preparada. Especialista em metodologias ágeis.'
            },
            {
                'name': 'João Santos',
                'email': 'joao.santos@startup.io',
                'phone': '(11) 98888-2222',
                'company': 'StartupTech',
                'position': 'CTO',
                'default_role': 'apresentador',
                'meeting_count': 5,
                'is_frequent': True,
                'notes': 'Focado em soluções técnicas inovadoras.'
            },
            {
                'name': 'Ana Costa',
                'email': 'ana.costa@consultoria.com.br',
                'phone': '(11) 97777-3333',
                'company': 'Costa Consultoria',
                'position': 'Consultora Senior',
                'default_role': 'participante',
                'meeting_count': 12,
                'is_frequent': True,
                'notes': 'Excelente em análise de dados e relatórios estratégicos.'
            },
            {
                'name': 'Pedro Oliveira',
                'email': 'pedro.oliveira@freelancer.com',
                'phone': '(11) 96666-4444',
                'company': 'Freelancer',
                'position': 'Designer UX/UI',
                'default_role': 'participante',
                'meeting_count': 2,
                'is_frequent': False,
                'notes': 'Especialista em experiência do usuário.'
            },
            {
                'name': 'Carla Mendes',
                'email': 'carla.mendes@marketing.pro',
                'phone': '(11) 95555-5555',
                'company': 'Marketing Pro',
                'position': 'Diretora de Marketing',
                'default_role': 'participante',
                'meeting_count': 6,
                'is_frequent': True,
                'notes': 'Criativa e estratégica, sempre traz insights valiosos.'
            },
            {
                'name': 'Roberto Lima',
                'email': 'roberto.lima@vendas.corp',
                'phone': '(11) 94444-6666',
                'company': 'VendasCorp',
                'position': 'Gerente de Vendas',
                'default_role': 'participante',
                'meeting_count': 1,
                'is_frequent': False,
                'notes': 'Novo no time, mas muito experiente em vendas B2B.'
            }
        ]
        
        # Verificar se já existem participantes
        existing_count = KnownParticipant.query.filter_by(user_id=user.id).count()
        if existing_count == 0:
            for data in participants_data:
                # Criar perfil de voz fictício
                voice_profile = {
                    'pitch_mean': random.uniform(80, 300),
                    'pitch_std': random.uniform(10, 50),
                    'speaking_rate': random.uniform(140, 200),
                    'voice_quality': random.choice(['clear', 'deep', 'light', 'warm']),
                    'accent_region': random.choice(['sp', 'rj', 'mg', 'rs']),
                    'confidence_score': random.uniform(0.8, 0.95)
                }
                
                # Calcular data da última reunião
                if data['meeting_count'] > 0:
                    days_ago = random.randint(1, 30)
                    last_meeting = datetime.utcnow() - timedelta(days=days_ago)
                else:
                    last_meeting = None
                
                participant = KnownParticipant(
                    user_id=user.id,
                    name=data['name'],
                    email=data['email'],
                    phone=data['phone'],
                    company=data['company'],
                    position=data['position'],
                    default_role=data['default_role'],
                    voice_profile=json.dumps(voice_profile),
                    meeting_count=data['meeting_count'],
                    last_meeting_date=last_meeting,
                    is_frequent=data['is_frequent'],
                    notes=data['notes']
                )
                db.session.add(participant)
            
            db.session.commit()
            print(f"✅ {len(participants_data)} participantes conhecidos criados")
        else:
            print(f"ℹ️ Já existem {existing_count} participantes cadastrados")
        
        # Criar algumas reuniões de exemplo
        meetings_count = MeetingSession.query.filter_by(user_id=user.id).count()
        if meetings_count == 0:
            # Reunião passada
            past_meeting = MeetingSession(
                user_id=user.id,
                title='Reunião de Planejamento Q4',
                description='Planejamento estratégico para o último trimestre',
                start_time=datetime.utcnow() - timedelta(days=7),
                end_time=datetime.utcnow() - timedelta(days=7, hours=-2),
                status='completed',
                total_participants=3
            )
            db.session.add(past_meeting)
            
            # Reunião atual (ativa)
            current_meeting = MeetingSession(
                user_id=user.id,
                title='Sprint Review - Desenvolvimento IAON',
                description='Revisão do sprint atual e planejamento do próximo',
                start_time=datetime.utcnow() - timedelta(minutes=30),
                status='active',
                total_participants=0
            )
            db.session.add(current_meeting)
            
            db.session.commit()
            print("✅ Reuniões de exemplo criadas")
        
        print("\n🎉 Dados de teste criados com sucesso!")
        print("\n📋 Participantes disponíveis:")
        participants = KnownParticipant.query.filter_by(user_id=user.id).all()
        for p in participants:
            status = "⭐ Frequente" if p.is_frequent else "👤 Ocasional"
            print(f"  • {p.name} ({p.company}) - {p.meeting_count} reuniões - {status}")
        
        print(f"\n🔐 Para testar, faça login com:")
        print(f"  📧 Email: {user.email}")
        print(f"  🔑 Senha: demo123")
        print(f"\n🌐 Acesse: http://127.0.0.1:5000")
        print(f"📋 Vá para a seção 'Participantes' para testar o sistema!")

if __name__ == '__main__':
    create_test_data()
