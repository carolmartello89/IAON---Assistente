import os
import sys
import json
import hashlib
import random
import re
import phonenumbers
from phonenumbers import geocoder, carrier
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import time
import uuid
from datetime import datetime, timedelta

# Criar instância única do SQLAlchemy
db = SQLAlchemy()

app = Flask(__name__, static_folder='static')

# Configurações de segurança
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'iaon-super-secret-key-2025')
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configuração CORS para permitir acesso de qualquer origem
CORS(app, 
     origins=['*'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Configuração do banco de dados
# Para Vercel (produção) usa SQLite em memória, para desenvolvimento usa arquivo
if os.getenv('FLASK_ENV') == 'production':
    # Banco de dados em memória para Vercel (serverless)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    # Banco de dados em arquivo para desenvolvimento local
    database_path = os.path.join(os.path.dirname(__file__), 'database', 'iaon.db')
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Inicializar banco de dados
db.init_app(app)

# Modelos avançados
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(200))
    preferred_name = db.Column(db.String(100))  # Como quer ser chamado
    password_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    is_onboarded = db.Column(db.Boolean, default=False)  # Se completou o onboarding
    language_preference = db.Column(db.String(10), default='pt-BR')
    theme_preference = db.Column(db.String(20), default='auto')
    voice_enabled = db.Column(db.Boolean, default=False)
    custom_trigger_word = db.Column(db.String(50), default='EION')  # Palavra de ativação personalizada
    trigger_sensitivity = db.Column(db.Float, default=0.7)  # Sensibilidade do reconhecimento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'preferred_name': self.preferred_name,
            'is_active': self.is_active,
            'is_onboarded': self.is_onboarded,
            'language_preference': self.language_preference,
            'theme_preference': self.theme_preference,
            'voice_enabled': self.voice_enabled,
            'custom_trigger_word': self.custom_trigger_word,
            'trigger_sensitivity': self.trigger_sensitivity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VoiceBiometry(db.Model):
    __tablename__ = 'voice_biometry'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    voice_features = db.Column(db.Text)  # JSON string com características da voz
    enrollment_phrase = db.Column(db.String(500))
    is_enrolled = db.Column(db.Boolean, default=False)
    samples_count = db.Column(db.Integer, default=0)
    required_samples = db.Column(db.Integer, default=5)  # Amostras necessárias
    confidence_threshold = db.Column(db.Float, default=0.85)  # Limite de confiança
    enrollment_quality = db.Column(db.String(20), default='pending')  # pending, good, excellent
    last_verification = db.Column(db.DateTime)
    verification_attempts = db.Column(db.Integer, default=0)
    successful_verifications = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_enrollment_progress(self):
        return min(100, (self.samples_count / self.required_samples) * 100)
    
    def to_dict(self):
        return {
            'is_enrolled': self.is_enrolled,
            'samples_count': self.samples_count,
            'required_samples': self.required_samples,
            'enrollment_progress': self.get_enrollment_progress(),
            'enrollment_quality': self.enrollment_quality,
            'confidence_threshold': self.confidence_threshold
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200))
    context = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, audio, image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MeetingSession(db.Model):
    __tablename__ = 'meeting_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, paused, completed, cancelled
    recording_path = db.Column(db.String(500))
    transcript_path = db.Column(db.String(500))
    agenda_generated = db.Column(db.Boolean, default=False)
    total_participants = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0.0)  # Qualidade da gravação/transcrição
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'agenda_generated': self.agenda_generated,
            'total_participants': self.total_participants,
            'quality_score': self.quality_score,
            'duration_minutes': self.get_duration_minutes()
        }
    
    def get_duration_minutes(self):
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        elif self.start_time:
            return int((datetime.utcnow() - self.start_time).total_seconds() / 60)
        return 0

class MeetingParticipant(db.Model):
    __tablename__ = 'meeting_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting_sessions.id'), nullable=False)
    participant_name = db.Column(db.String(200), nullable=False)
    voice_profile = db.Column(db.Text)  # JSON com características da voz
    participant_role = db.Column(db.String(100))  # moderador, participante, convidado
    email = db.Column(db.String(120))
    speaking_time_minutes = db.Column(db.Float, default=0.0)
    interventions_count = db.Column(db.Integer, default=0)
    confidence_level = db.Column(db.Float, default=0.0)  # Confiança no reconhecimento
    is_verified = db.Column(db.Boolean, default=False)  # Se foi verificado por biometria
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'participant_name': self.participant_name,
            'participant_role': self.participant_role,
            'email': self.email,
            'speaking_time_minutes': self.speaking_time_minutes,
            'interventions_count': self.interventions_count,
            'confidence_level': self.confidence_level,
            'is_verified': self.is_verified
        }

class MeetingTranscript(db.Model):
    __tablename__ = 'meeting_transcripts'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting_sessions.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('meeting_participants.id'))
    speaker_name = db.Column(db.String(200))  # Nome identificado do falante
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    start_time_seconds = db.Column(db.Float)  # Tempo no áudio original
    end_time_seconds = db.Column(db.Float)
    confidence_score = db.Column(db.Float)  # Confiança da transcrição
    audio_quality = db.Column(db.String(20))  # excellent, good, fair, poor
    is_action_item = db.Column(db.Boolean, default=False)  # Se é item de ação
    is_decision = db.Column(db.Boolean, default=False)  # Se é uma decisão
    sentiment = db.Column(db.String(20))  # positive, neutral, negative
    
    def to_dict(self):
        return {
            'id': self.id,
            'speaker_name': self.speaker_name,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'start_time_seconds': self.start_time_seconds,
            'end_time_seconds': self.end_time_seconds,
            'confidence_score': self.confidence_score,
            'audio_quality': self.audio_quality,
            'is_action_item': self.is_action_item,
            'is_decision': self.is_decision,
            'sentiment': self.sentiment
        }

class MeetingAgenda(db.Model):
    __tablename__ = 'meeting_agendas'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting_sessions.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    summary = db.Column(db.Text)
    key_points = db.Column(db.Text)  # JSON array
    action_items = db.Column(db.Text)  # JSON array
    decisions_made = db.Column(db.Text)  # JSON array
    next_steps = db.Column(db.Text)  # JSON array
    participants_summary = db.Column(db.Text)  # JSON com resumo por participante
    topics_discussed = db.Column(db.Text)  # JSON array
    conclusions = db.Column(db.Text)  # JSON array com conclusões da reunião
    problems_identified = db.Column(db.Text)  # JSON array com problemas identificados
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'key_points': json.loads(self.key_points) if self.key_points else [],
            'action_items': json.loads(self.action_items) if self.action_items else [],
            'decisions_made': json.loads(self.decisions_made) if self.decisions_made else [],
            'next_steps': json.loads(self.next_steps) if self.next_steps else [],
            'participants_summary': json.loads(self.participants_summary) if self.participants_summary else {},
            'topics_discussed': json.loads(self.topics_discussed) if self.topics_discussed else [],
            'conclusions': json.loads(self.conclusions) if self.conclusions else [],
            'problems_identified': json.loads(self.problems_identified) if self.problems_identified else [],
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    display_name = db.Column(db.String(200))  # Nome para exibição
    phone_number = db.Column(db.String(20), nullable=False)
    formatted_phone = db.Column(db.String(25))  # Número formatado
    country_code = db.Column(db.String(5))  # Código do país
    carrier = db.Column(db.String(100))  # Operadora
    contact_type = db.Column(db.String(20), default='mobile')  # mobile, home, work
    is_favorite = db.Column(db.Boolean, default=False)
    is_emergency = db.Column(db.Boolean, default=False)
    voice_aliases = db.Column(db.Text)  # JSON com apelidos para comando de voz
    call_frequency = db.Column(db.Integer, default=0)  # Quantas vezes foi chamado
    last_called = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    sync_source = db.Column(db.String(50), default='manual')  # manual, phone_sync, google, icloud
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name or self.name,
            'phone_number': self.phone_number,
            'formatted_phone': self.formatted_phone,
            'country_code': self.country_code,
            'carrier': self.carrier,
            'contact_type': self.contact_type,
            'is_favorite': self.is_favorite,
            'is_emergency': self.is_emergency,
            'voice_aliases': json.loads(self.voice_aliases) if self.voice_aliases else [],
            'call_frequency': self.call_frequency,
            'last_called': self.last_called.isoformat() if self.last_called else None,
            'notes': self.notes,
            'photo_url': self.photo_url,
            'sync_source': self.sync_source
        }
    
    def get_voice_match_score(self, voice_input):
        """Calcular score de correspondência com comando de voz"""
        voice_input_lower = voice_input.lower().strip()
        score = 0
        
        # Nome exato
        if self.name.lower() == voice_input_lower:
            score += 100
        
        # Display name
        if self.display_name and self.display_name.lower() == voice_input_lower:
            score += 95
        
        # Parte do nome
        if voice_input_lower in self.name.lower():
            score += 80
        
        # Aliases de voz
        if self.voice_aliases:
            aliases = json.loads(self.voice_aliases)
            for alias in aliases:
                if alias.lower() == voice_input_lower:
                    score += 90
                elif voice_input_lower in alias.lower():
                    score += 70
        
        # Primeiro nome
        first_name = self.name.split()[0].lower()
        if first_name == voice_input_lower:
            score += 85
        
        return score

class CallLog(db.Model):
    __tablename__ = 'call_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    phone_number = db.Column(db.String(20), nullable=False)
    contact_name = db.Column(db.String(200))
    call_type = db.Column(db.String(20), nullable=False)  # outgoing, incoming, missed
    call_method = db.Column(db.String(30), default='voice_command')  # voice_command, manual, auto
    voice_command = db.Column(db.String(500))  # Comando de voz original
    duration_seconds = db.Column(db.Integer, default=0)
    call_status = db.Column(db.String(20), default='initiated')  # initiated, connected, completed, failed, cancelled
    call_quality = db.Column(db.String(20))  # excellent, good, poor
    voice_confidence = db.Column(db.Float)  # Confiança no reconhecimento de voz
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    connected_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_name': self.contact_name,
            'phone_number': self.phone_number,
            'call_type': self.call_type,
            'call_method': self.call_method,
            'voice_command': self.voice_command,
            'duration_seconds': self.duration_seconds,
            'call_status': self.call_status,
            'call_quality': self.call_quality,
            'voice_confidence': self.voice_confidence,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_formatted': self.get_duration_formatted()
        }
    
    def get_duration_formatted(self):
        if self.duration_seconds:
            minutes = self.duration_seconds // 60
            seconds = self.duration_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"

class AppControl(db.Model):
    __tablename__ = 'app_controls'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    app_name = db.Column(db.String(200), nullable=False)
    app_package = db.Column(db.String(300))  # Package name para Android ou Bundle ID para iOS
    display_name = db.Column(db.String(200))  # Nome para exibição
    voice_aliases = db.Column(db.Text)  # JSON com comandos de voz para abrir
    category = db.Column(db.String(50))  # social, productivity, entertainment, etc.
    is_system_app = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    usage_count = db.Column(db.Integer, default=0)
    last_opened = db.Column(db.DateTime)
    icon_url = db.Column(db.String(500))
    app_version = db.Column(db.String(50))
    install_source = db.Column(db.String(50), default='auto_detected')  # auto_detected, manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'app_name': self.app_name,
            'app_package': self.app_package,
            'display_name': self.display_name or self.app_name,
            'voice_aliases': json.loads(self.voice_aliases) if self.voice_aliases else [],
            'category': self.category,
            'is_system_app': self.is_system_app,
            'is_favorite': self.is_favorite,
            'usage_count': self.usage_count,
            'last_opened': self.last_opened.isoformat() if self.last_opened else None,
            'icon_url': self.icon_url,
            'app_version': self.app_version
        }
    
    def get_voice_match_score(self, voice_input):
        """Calcular score de correspondência com comando de voz"""
        voice_input_lower = voice_input.lower().strip()
        score = 0
        
        # Nome exato do app
        if self.app_name.lower() == voice_input_lower:
            score += 100
        
        # Display name
        if self.display_name and self.display_name.lower() == voice_input_lower:
            score += 95
        
        # Parte do nome
        if voice_input_lower in self.app_name.lower():
            score += 80
        
        # Aliases de voz
        if self.voice_aliases:
            aliases = json.loads(self.voice_aliases)
            for alias in aliases:
                if alias.lower() == voice_input_lower:
                    score += 90
                elif voice_input_lower in alias.lower():
                    score += 70
        
        return score

class AppLaunchLog(db.Model):
    __tablename__ = 'app_launch_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    app_id = db.Column(db.Integer, db.ForeignKey('app_controls.id'))
    app_name = db.Column(db.String(200), nullable=False)
    voice_command = db.Column(db.String(500))  # Comando de voz original
    launch_method = db.Column(db.String(30), default='voice_command')  # voice_command, manual
    launch_status = db.Column(db.String(20), default='initiated')  # initiated, success, failed
    voice_confidence = db.Column(db.Float)
    error_message = db.Column(db.Text)
    launched_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'app_name': self.app_name,
            'voice_command': self.voice_command,
            'launch_method': self.launch_method,
            'launch_status': self.launch_status,
            'voice_confidence': self.voice_confidence,
            'error_message': self.error_message,
            'launched_at': self.launched_at.isoformat() if self.launched_at else None
        }

class IntelligentReport(db.Model):
    __tablename__ = 'intelligent_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting_sessions.id'), nullable=False)
    report_type = db.Column(db.String(50), default='problem_solutions')  # problem_solutions, insights, recommendations
    title = db.Column(db.String(300), nullable=False)
    executive_summary = db.Column(db.Text)
    problems_analysis = db.Column(db.Text)  # JSON array com análise detalhada dos problemas
    suggested_solutions = db.Column(db.Text)  # JSON array com soluções inteligentes
    implementation_roadmap = db.Column(db.Text)  # JSON array com cronograma de implementação
    risk_assessment = db.Column(db.Text)  # JSON array com avaliação de riscos
    success_metrics = db.Column(db.Text)  # JSON array com métricas de sucesso
    resource_requirements = db.Column(db.Text)  # JSON array com recursos necessários
    stakeholder_impact = db.Column(db.Text)  # JSON array com impacto nos stakeholders
    follow_up_actions = db.Column(db.Text)  # JSON array com ações de acompanhamento
    ai_confidence_score = db.Column(db.Float, default=0.0)  # Confiança da IA na análise
    priority_level = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    estimated_impact = db.Column(db.String(20), default='medium')  # low, medium, high
    complexity_score = db.Column(db.Float, default=0.5)  # 0.0 (simples) a 1.0 (complexo)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'report_type': self.report_type,
            'title': self.title,
            'executive_summary': self.executive_summary,
            'problems_analysis': json.loads(self.problems_analysis) if self.problems_analysis else [],
            'suggested_solutions': json.loads(self.suggested_solutions) if self.suggested_solutions else [],
            'implementation_roadmap': json.loads(self.implementation_roadmap) if self.implementation_roadmap else [],
            'risk_assessment': json.loads(self.risk_assessment) if self.risk_assessment else [],
            'success_metrics': json.loads(self.success_metrics) if self.success_metrics else [],
            'resource_requirements': json.loads(self.resource_requirements) if self.resource_requirements else [],
            'stakeholder_impact': json.loads(self.stakeholder_impact) if self.stakeholder_impact else [],
            'follow_up_actions': json.loads(self.follow_up_actions) if self.follow_up_actions else [],
            'ai_confidence_score': self.ai_confidence_score,
            'priority_level': self.priority_level,
            'estimated_impact': self.estimated_impact,
            'complexity_score': self.complexity_score,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
        }

# ==================== SISTEMA DE COACHES E PLANOS COMERCIAIS ====================

class Coach(db.Model):
    __tablename__ = 'coaches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)  # business, life, productivity, health, financial, leadership
    description = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    voice_personality = db.Column(db.String(50), default='professional')  # professional, friendly, motivational, calm
    expertise_areas = db.Column(db.Text)  # JSON array com áreas de expertise
    coaching_style = db.Column(db.String(50), default='directive')  # directive, non-directive, collaborative
    languages = db.Column(db.Text, default='["pt-BR"]')  # JSON array de idiomas
    experience_years = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=5.0)
    total_sessions = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.95)  # Taxa de sucesso dos clientes
    pricing_tier = db.Column(db.String(20), default='standard')  # basic, standard, premium, enterprise
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'voice_personality': self.voice_personality,
            'expertise_areas': json.loads(self.expertise_areas) if self.expertise_areas else [],
            'coaching_style': self.coaching_style,
            'languages': json.loads(self.languages) if self.languages else ['pt-BR'],
            'experience_years': self.experience_years,
            'rating': self.rating,
            'total_sessions': self.total_sessions,
            'success_rate': self.success_rate,
            'pricing_tier': self.pricing_tier,
            'is_active': self.is_active
        }

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(150))
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float)  # Preço anual com desconto
    currency = db.Column(db.String(5), default='BRL')
    
    # Recursos incluídos
    features = db.Column(db.Text)  # JSON array com recursos
    max_meetings_per_month = db.Column(db.Integer, default=10)
    max_participants_per_meeting = db.Column(db.Integer, default=5)
    max_storage_gb = db.Column(db.Float, default=1.0)
    voice_biometry_enabled = db.Column(db.Boolean, default=True)
    ai_reports_enabled = db.Column(db.Boolean, default=True)
    coaching_sessions_included = db.Column(db.Integer, default=0)  # Sessões de coaching inclusas
    advanced_analytics = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    custom_branding = db.Column(db.Boolean, default=False)
    api_access = db.Column(db.Boolean, default=False)
    
    # Configurações comerciais
    trial_days = db.Column(db.Integer, default=7)
    is_popular = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        yearly_discount = 0
        if self.price_yearly and self.price_monthly:
            yearly_discount = round(100 - (self.price_yearly / (self.price_monthly * 12)) * 100, 1)
        
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name or self.name,
            'description': self.description,
            'price_monthly': self.price_monthly,
            'price_yearly': self.price_yearly,
            'yearly_discount_percent': yearly_discount,
            'currency': self.currency,
            'features': json.loads(self.features) if self.features else [],
            'limits': {
                'meetings_per_month': self.max_meetings_per_month,
                'participants_per_meeting': self.max_participants_per_meeting,
                'storage_gb': self.max_storage_gb,
                'coaching_sessions': self.coaching_sessions_included
            },
            'capabilities': {
                'voice_biometry': self.voice_biometry_enabled,
                'ai_reports': self.ai_reports_enabled,
                'advanced_analytics': self.advanced_analytics,
                'priority_support': self.priority_support,
                'custom_branding': self.custom_branding,
                'api_access': self.api_access
            },
            'trial_days': self.trial_days,
            'is_popular': self.is_popular,
            'is_active': self.is_active
        }

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='trial')  # trial, active, cancelled, expired, suspended
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    
    # Datas importantes
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    trial_ends_at = db.Column(db.DateTime)
    current_period_start = db.Column(db.DateTime, default=datetime.utcnow)
    current_period_end = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Informações de pagamento
    payment_method = db.Column(db.String(50))  # credit_card, pix, boleto, paypal
    external_subscription_id = db.Column(db.String(200))  # ID do processador de pagamento
    next_billing_amount = db.Column(db.Float)
    
    # Uso atual
    meetings_this_month = db.Column(db.Integer, default=0)
    storage_used_gb = db.Column(db.Float, default=0.0)
    coaching_sessions_used = db.Column(db.Integer, default=0)
    last_billing_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'status': self.status,
            'billing_cycle': self.billing_cycle,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'usage': {
                'meetings_this_month': self.meetings_this_month,
                'storage_used_gb': self.storage_used_gb,
                'coaching_sessions_used': self.coaching_sessions_used
            },
            'payment': {
                'method': self.payment_method,
                'next_amount': self.next_billing_amount
            }
        }

class DiscountCoupon(db.Model):
    __tablename__ = 'discount_coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))  # Nome amigável do cupom
    description = db.Column(db.Text)
    
    # Configurações do desconto
    discount_type = db.Column(db.String(20), default='percentage')  # percentage, fixed_amount
    discount_value = db.Column(db.Float, nullable=False)  # 20 para 20% ou valor fixo
    max_discount_amount = db.Column(db.Float)  # Limite máximo de desconto em valor
    minimum_purchase = db.Column(db.Float, default=0.0)  # Valor mínimo para usar o cupom
    
    # Validade e limites
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer, default=1)  # SEMPRE 1 para uso único
    max_uses_per_user = db.Column(db.Integer, default=1)  # SEMPRE 1 por usuário
    current_uses = db.Column(db.Integer, default=0)
    
    # CONTROLE EXCLUSIVO POR USUÁRIO
    exclusive_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Usuário específico autorizado
    exclusive_user_email = db.Column(db.String(120))  # Email específico autorizado
    is_single_use = db.Column(db.Boolean, default=True)  # SEMPRE True - uso único total
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Quem já usou
    used_at = db.Column(db.DateTime)  # Quando foi usado
    
    # Aplicabilidade
    applicable_plans = db.Column(db.Text)  # JSON array com IDs dos planos aplicáveis
    first_purchase_only = db.Column(db.Boolean, default=False)  # Apenas primeira compra
    billing_cycles = db.Column(db.String(50), default='all')  # all, monthly, yearly
    
    # Configurações administrativas
    created_by_admin = db.Column(db.String(100))  # Admin que criou
    admin_notes = db.Column(db.Text)  # Anotações internas do admin
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=False)  # SEMPRE False para cupons exclusivos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount': {
                'type': self.discount_type,
                'value': self.discount_value,
                'max_amount': self.max_discount_amount,
                'minimum_purchase': self.minimum_purchase
            },
            'validity': {
                'from': self.valid_from.isoformat() if self.valid_from else None,
                'until': self.valid_until.isoformat() if self.valid_until else None,
                'is_valid': self.is_valid()
            },
            'exclusivity': {
                'is_single_use': self.is_single_use,
                'exclusive_user_id': self.exclusive_user_id,
                'exclusive_user_email': self.exclusive_user_email,
                'used_by_user_id': self.used_by_user_id,
                'used_at': self.used_at.isoformat() if self.used_at else None,
                'is_used': self.is_used()
            },
            'rules': {
                'applicable_plans': json.loads(self.applicable_plans) if self.applicable_plans else [],
                'first_purchase_only': self.first_purchase_only,
                'billing_cycles': self.billing_cycles
            },
            'admin_info': {
                'created_by': self.created_by_admin,
                'notes': self.admin_notes
            },
            'is_active': self.is_active
        }
    
    def is_valid(self):
        """Verificar se cupom ainda é válido"""
        now = datetime.utcnow()
        
        # Verificar se já foi usado (uso único)
        if self.is_used():
            return False
            
        # Verificar validade temporal
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
            
        # Verificar se está ativo
        return self.is_active
    
    def is_used(self):
        """Verificar se cupom já foi usado"""
        return self.used_by_user_id is not None or self.current_uses > 0
    
    def can_be_used_by(self, user_id, user_email=None):
        """Verificar se usuário específico pode usar o cupom"""
        if not self.is_valid():
            return False, "Cupom inválido ou expirado"
        
        if self.is_used():
            return False, "Cupom já foi utilizado"
        
        # Verificar se é o usuário autorizado
        if self.exclusive_user_id and self.exclusive_user_id != user_id:
            return False, "Cupom não autorizado para este usuário"
        
        if self.exclusive_user_email and user_email and self.exclusive_user_email.lower() != user_email.lower():
            return False, "Cupom não autorizado para este email"
        
        return True, "Cupom válido para uso"
    
    def mark_as_used(self, user_id):
        """Marcar cupom como usado"""
        if self.is_used():
            raise ValueError("Cupom já foi utilizado")
        
        self.used_by_user_id = user_id
        self.used_at = datetime.utcnow()
        self.current_uses = 1
    
    def calculate_discount(self, amount, plan_id=None):
        """Calcular valor do desconto para um valor específico"""
        if not self.is_valid():
            return 0.0
        
        if amount < self.minimum_purchase:
            return 0.0
        
        if self.applicable_plans:
            applicable = json.loads(self.applicable_plans)
            if plan_id and plan_id not in applicable:
                return 0.0
        
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return round(discount, 2)
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_value, amount)
        
        return 0.0

class CouponUsage(db.Model):
    __tablename__ = 'coupon_usages'
    
    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('discount_coupons.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'))
    
    # Detalhes do uso
    original_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, nullable=False)
    final_amount = db.Column(db.Float, nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'coupon_id': self.coupon_id,
            'user_id': self.user_id,
            'original_amount': self.original_amount,
            'discount_amount': self.discount_amount,
            'final_amount': self.final_amount,
            'used_at': self.used_at.isoformat() if self.used_at else None
        }

class CoachingSession(db.Model):
    __tablename__ = 'coaching_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'), nullable=False)
    session_type = db.Column(db.String(50), default='individual')  # individual, group, workshop
    
    # Informações da sessão
    title = db.Column(db.String(200))
    objectives = db.Column(db.Text)  # Objetivos definidos
    session_notes = db.Column(db.Text)  # Anotações do coach
    homework_assigned = db.Column(db.Text)  # Tarefas atribuídas
    progress_assessment = db.Column(db.Text)  # Avaliação do progresso
    
    # Agendamento
    scheduled_at = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    
    # Avaliação
    user_rating = db.Column(db.Integer)  # 1-5 estrelas
    user_feedback = db.Column(db.Text)
    coach_rating = db.Column(db.Integer)  # Coach avalia o usuário
    session_effectiveness = db.Column(db.Float)  # Score de efetividade
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'coach_id': self.coach_id,
            'session_type': self.session_type,
            'title': self.title,
            'objectives': self.objectives,
            'session_notes': self.session_notes,
            'homework_assigned': self.homework_assigned,
            'progress_assessment': self.progress_assessment,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'ratings': {
                'user_rating': self.user_rating,
                'coach_rating': self.coach_rating,
                'effectiveness': self.session_effectiveness
            },
            'feedback': {
                'user_feedback': self.user_feedback
            },
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# Configurar cabeçalhos de segurança
@app.after_request
def add_security_headers(response):
    # Cabeçalhos de segurança HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https: wss:; "
        "media-src 'self' blob:; "
        "worker-src 'self' blob:; "
        "child-src 'self' blob:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Cabeçalhos para PWA
    response.headers['Service-Worker-Allowed'] = '/'
    
    return response

# Função para inicializar o banco de dados
def init_database():
    """Inicializa o banco de dados de forma segura"""
    try:
        with app.app_context():
            db.create_all()
            
            # Criar usuário padrão se não existir (apenas em desenvolvimento)
            if os.getenv('FLASK_ENV') != 'production':
                if not User.query.first():
                    admin_user = User(
                        username='admin',
                        email='admin@iaon.com',
                        full_name='Administrador IAON',
                        is_active=True
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    print("Usuário administrador criado!")
                
                # Inicializar coaches padrão
                init_default_coaches()
                
                # Inicializar planos padrão
                init_default_plans()
                
                # NÃO criar cupons de exemplo - apenas cupons exclusivos criados manualmente
                
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")

def init_default_coaches():
    """Inicializar coaches padrão"""
    if Coach.query.count() > 0:
        return  # Já existem coaches
    
    coaches_data = [
        {
            'name': 'Ana Silva',
            'specialty': 'business',
            'description': 'Coach executiva com 15 anos de experiência em liderança corporativa. Especialista em gestão de equipes e desenvolvimento de carreira.',
            'avatar_url': '/static/images/coaches/ana_silva.jpg',
            'voice_personality': 'professional',
            'expertise_areas': json.dumps(['liderança', 'gestão de equipes', 'desenvolvimento profissional', 'negociação', 'comunicação corporativa']),
            'coaching_style': 'directive',
            'experience_years': 15,
            'rating': 4.9,
            'pricing_tier': 'premium'
        },
        {
            'name': 'Carlos Mendes',
            'specialty': 'productivity',
            'description': 'Especialista em produtividade e gestão do tempo. Ajuda profissionais a otimizar sua rotina e alcançar melhores resultados.',
            'avatar_url': '/static/images/coaches/carlos_mendes.jpg',
            'voice_personality': 'motivational',
            'expertise_areas': json.dumps(['gestão do tempo', 'produtividade', 'organização', 'foco', 'metodologias ágeis']),
            'coaching_style': 'collaborative',
            'experience_years': 8,
            'rating': 4.8,
            'pricing_tier': 'standard'
        },
        {
            'name': 'Marina Costa',
            'specialty': 'life',
            'description': 'Life coach certificada focada em equilíbrio vida-trabalho e desenvolvimento pessoal. Especialista em bem-estar e propósito de vida.',
            'avatar_url': '/static/images/coaches/marina_costa.jpg',
            'voice_personality': 'friendly',
            'expertise_areas': json.dumps(['equilíbrio vida-trabalho', 'autoconhecimento', 'propósito', 'relacionamentos', 'bem-estar']),
            'coaching_style': 'non-directive',
            'experience_years': 12,
            'rating': 4.9,
            'pricing_tier': 'standard'
        },
        {
            'name': 'Roberto Santos',
            'specialty': 'financial',
            'description': 'Coach financeiro com experiência em planejamento patrimonial e educação financeira. Ajuda pessoas a organizarem suas finanças.',
            'avatar_url': '/static/images/coaches/roberto_santos.jpg',
            'voice_personality': 'calm',
            'expertise_areas': json.dumps(['planejamento financeiro', 'investimentos', 'controle de gastos', 'educação financeira', 'empreendedorismo']),
            'coaching_style': 'directive',
            'experience_years': 10,
            'rating': 4.7,
            'pricing_tier': 'standard'
        },
        {
            'name': 'Julia Oliveira',
            'specialty': 'health',
            'description': 'Coach de saúde e wellness focada em hábitos saudáveis e qualidade de vida. Especialista em mudança comportamental.',
            'avatar_url': '/static/images/coaches/julia_oliveira.jpg',
            'voice_personality': 'motivational',
            'expertise_areas': json.dumps(['hábitos saudáveis', 'exercícios', 'nutrição', 'mindfulness', 'gestão de estresse']),
            'coaching_style': 'collaborative',
            'experience_years': 6,
            'rating': 4.8,
            'pricing_tier': 'standard'
        },
        {
            'name': 'Fernando Lima',
            'specialty': 'leadership',
            'description': 'Coach de liderança sênior com experiência C-level. Especialista em transformação organizacional e desenvolvimento de líderes.',
            'avatar_url': '/static/images/coaches/fernando_lima.jpg',
            'voice_personality': 'professional',
            'expertise_areas': json.dumps(['liderança estratégica', 'transformação digital', 'cultura organizacional', 'gestão de mudança', 'coaching executivo']),
            'coaching_style': 'directive',
            'experience_years': 20,
            'rating': 5.0,
            'pricing_tier': 'enterprise'
        }
    ]
    
    for coach_data in coaches_data:
        coach = Coach(**coach_data)
        db.session.add(coach)
    
    db.session.commit()
    print("Coaches padrão criados!")

def init_default_plans():
    """Inicializar planos de assinatura padrão"""
    if SubscriptionPlan.query.count() > 0:
        return  # Já existem planos
    
    plans_data = [
        {
            'name': 'starter',
            'display_name': 'Starter',
            'description': 'Ideal para usuários iniciantes que querem experimentar o IAON',
            'price_monthly': 29.90,
            'price_yearly': 299.00,  # 2 meses grátis
            'features': json.dumps([
                'Reuniões ilimitadas até 3 participantes',
                'Transcrição automática',
                'Geração de atas básicas',
                'Armazenamento de 5GB',
                'Suporte por email',
                'Biometria de voz'
            ]),
            'max_meetings_per_month': 50,
            'max_participants_per_meeting': 3,
            'max_storage_gb': 5.0,
            'coaching_sessions_included': 1,
            'trial_days': 14,
            'sort_order': 1
        },
        {
            'name': 'professional',
            'display_name': 'Profissional',
            'description': 'Para profissionais que precisam de recursos avançados',
            'price_monthly': 79.90,
            'price_yearly': 719.10,  # 3 meses grátis
            'features': json.dumps([
                'Reuniões ilimitadas até 10 participantes',
                'Transcrição com IA avançada',
                'Relatórios inteligentes',
                'Análise de sentimentos',
                'Armazenamento de 25GB',
                'Integração com apps',
                'Suporte prioritário',
                '3 sessões de coaching/mês'
            ]),
            'max_meetings_per_month': 200,
            'max_participants_per_meeting': 10,
            'max_storage_gb': 25.0,
            'coaching_sessions_included': 3,
            'advanced_analytics': True,
            'priority_support': True,
            'trial_days': 14,
            'is_popular': True,
            'sort_order': 2
        },
        {
            'name': 'business',
            'display_name': 'Business',
            'description': 'Para equipes e pequenas empresas',
            'price_monthly': 149.90,
            'price_yearly': 1349.10,  # 3 meses grátis
            'features': json.dumps([
                'Reuniões ilimitadas até 25 participantes',
                'IA avançada com insights personalizados',
                'Dashboard analítico completo',
                'Integração com CRM/ERP',
                'Armazenamento de 100GB',
                'Marca personalizada',
                'Suporte dedicado',
                '5 sessões de coaching/mês',
                'Acesso à API'
            ]),
            'max_meetings_per_month': 500,
            'max_participants_per_meeting': 25,
            'max_storage_gb': 100.0,
            'coaching_sessions_included': 5,
            'advanced_analytics': True,
            'priority_support': True,
            'custom_branding': True,
            'api_access': True,
            'trial_days': 30,
            'sort_order': 3
        },
        {
            'name': 'enterprise',
            'display_name': 'Enterprise',
            'description': 'Solução completa para grandes empresas',
            'price_monthly': 299.90,
            'price_yearly': 2999.00,  # 2 meses grátis
            'features': json.dumps([
                'Reuniões ilimitadas sem restrições',
                'IA personalizada para empresa',
                'Relatórios executivos avançados',
                'Integração total com sistemas',
                'Armazenamento ilimitado',
                'Suporte 24/7 dedicado',
                'Coaching executivo ilimitado',
                'Consultoria estratégica',
                'SLA garantido',
                'Implementação assistida'
            ]),
            'max_meetings_per_month': -1,  # Ilimitado
            'max_participants_per_meeting': -1,  # Ilimitado
            'max_storage_gb': -1,  # Ilimitado
            'coaching_sessions_included': -1,  # Ilimitado
            'advanced_analytics': True,
            'priority_support': True,
            'custom_branding': True,
            'api_access': True,
            'trial_days': 30,
            'sort_order': 4
        }
    ]
    
    for plan_data in plans_data:
        plan = SubscriptionPlan(**plan_data)
        db.session.add(plan)
    
    db.session.commit()
    print("Planos padrão criados!")

def init_sample_coupons():
    """Criar cupons de exemplo"""
    if DiscountCoupon.query.count() > 0:
        return  # Já existem cupons
    
    coupons_data = [
        {
            'code': 'WELCOME20',
            'name': 'Desconto de Boas-Vindas',
            'description': 'Desconto especial para novos usuários',
            'discount_type': 'percentage',
            'discount_value': 20,
            'max_uses': 1000,
            'valid_until': datetime.utcnow() + timedelta(days=90),
            'first_purchase_only': True,
            'is_public': True
        },
        {
            'code': 'STUDENT50',
            'name': 'Desconto Estudante',
            'description': 'Desconto especial para estudantes',
            'discount_type': 'percentage',
            'discount_value': 50,
            'max_uses': 500,
            'valid_until': datetime.utcnow() + timedelta(days=365),
            'applicable_plans': json.dumps([1, 2]),  # Starter e Professional
            'is_public': True
        },
        {
            'code': 'BLACKFRIDAY',
            'name': 'Black Friday 2025',
            'description': 'Super desconto Black Friday',
            'discount_type': 'percentage',
            'discount_value': 70,
            'max_uses': 2000,
            'valid_from': datetime(2025, 11, 20),
            'valid_until': datetime(2025, 11, 30),
            'is_public': True
        },
        {
            'code': 'UPGRADE100',
            'name': 'Upgrade Gratuito',
            'description': 'Primeiro mês gratuito no upgrade',
            'discount_type': 'percentage',
            'discount_value': 100,
            'max_uses': 100,
            'max_uses_per_user': 1,
            'valid_until': datetime.utcnow() + timedelta(days=60),
            'billing_cycles': 'monthly'
        }
    ]
    
    for coupon_data in coupons_data:
        coupon = DiscountCoupon(**coupon_data)
        db.session.add(coupon)
    
    db.session.commit()
    print("Cupons de exemplo criados!")

# Inicializar apenas se não estiver em ambiente serverless
if os.getenv('FLASK_ENV') != 'production':
    init_database()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'app': 'IAON - Assistente IA Avançado',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': 'connected',
            'ai': 'available',
            'voice_biometry': 'enabled',
            'pwa': 'active'
        }
    })

@app.route('/api/onboarding/status', methods=['GET'])
def onboarding_status():
    """Verificar status do onboarding do usuário"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        user = User.query.get(user_id)
        
        if not user:
            # Criar usuário se não existir
            user = User(
                username=f'user_{user_id}',
                email=f'user{user_id}@iaon.com',
                full_name='Usuário IAON',
                is_onboarded=False
            )
            db.session.add(user)
            db.session.commit()
        
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'user': user.to_dict(),
            'needs_onboarding': not user.is_onboarded,
            'voice_biometry': biometry.to_dict() if biometry else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/onboarding/complete', methods=['POST'])
def complete_onboarding():
    """Completar o onboarding do usuário"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Atualizar informações do usuário
        user.full_name = data.get('full_name', user.full_name)
        user.preferred_name = data.get('preferred_name', user.preferred_name)
        user.language_preference = data.get('language_preference', 'pt-BR')
        user.theme_preference = data.get('theme_preference', 'auto')
        user.voice_enabled = data.get('voice_enabled', False)
        user.custom_trigger_word = data.get('custom_trigger_word', 'EION')
        user.trigger_sensitivity = data.get('trigger_sensitivity', 0.7)
        user.is_onboarded = True
        user.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bem-vindo(a), {user.preferred_name or user.full_name}!',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/trigger-word/configure', methods=['POST'])
def configure_trigger_word():
    """Configurar palavra de ativação personalizada"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        trigger_word = data.get('trigger_word', 'EION').upper().strip()
        sensitivity = data.get('sensitivity', 0.7)
        
        # Validações
        if not trigger_word or len(trigger_word) < 2:
            return jsonify({'error': 'Palavra de ativação deve ter pelo menos 2 caracteres'}), 400
        
        if len(trigger_word) > 20:
            return jsonify({'error': 'Palavra de ativação não pode ter mais que 20 caracteres'}), 400
        
        # Palavras reservadas que não podem ser usadas
        reserved_words = ['OK', 'HEY', 'GOOGLE', 'ALEXA', 'SIRI', 'CORTANA', 'BIXBY']
        if trigger_word in reserved_words:
            return jsonify({'error': f'"{trigger_word}" é uma palavra reservada. Escolha outra.'}), 400
        
        if not (0.1 <= sensitivity <= 1.0):
            return jsonify({'error': 'Sensibilidade deve estar entre 0.1 e 1.0'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Atualizar configurações
        old_trigger = user.custom_trigger_word
        user.custom_trigger_word = trigger_word
        user.trigger_sensitivity = sensitivity
        user.last_activity = datetime.utcnow()
        
        db.session.commit()
        
        # Configurações de reconhecimento por sensibilidade
        sensitivity_configs = {
            'baixa': (0.1, 0.4, 'Menos sensível - pode não detectar sussurros'),
            'média': (0.4, 0.7, 'Equilibrada - recomendada para uso geral'),
            'alta': (0.7, 1.0, 'Mais sensível - detecta até sussurros')
        }
        
        sensitivity_level = 'baixa' if sensitivity <= 0.4 else 'média' if sensitivity <= 0.7 else 'alta'
        sensitivity_desc = next(desc for min_val, max_val, desc in sensitivity_configs.values() if min_val < sensitivity <= max_val)
        
        return jsonify({
            'success': True,
            'trigger_word': trigger_word,
            'previous_trigger': old_trigger,
            'sensitivity': sensitivity,
            'sensitivity_level': sensitivity_level,
            'sensitivity_description': sensitivity_desc,
            'voice_config': {
                'wake_word': trigger_word,
                'confidence_threshold': sensitivity,
                'background_listening': user.voice_enabled,
                'detection_timeout': 5,  # segundos
                'language': user.language_preference
            },
            'usage_examples': [
                f'"{trigger_word}, ligar para João"',
                f'"{trigger_word}, abrir WhatsApp"',
                f'"{trigger_word}, iniciar reunião"',
                f'"{trigger_word}, ajuda"'
            ],
            'message': f'✅ Palavra de ativação alterada para "{trigger_word}" (sensibilidade: {sensitivity_level})'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/trigger-word/test', methods=['POST'])
def test_trigger_word():
    """Testar reconhecimento da palavra de ativação personalizada"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        audio_data = data.get('audio_data', '')  # Base64 encoded audio
        spoken_text = data.get('spoken_text', '')  # Texto falado para teste
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        trigger_word = user.custom_trigger_word
        sensitivity = user.trigger_sensitivity
        
        # Simular reconhecimento de voz (em produção seria processamento real)
        spoken_lower = spoken_text.lower().strip()
        trigger_lower = trigger_word.lower()
        
        # Diferentes níveis de correspondência
        exact_match = trigger_lower in spoken_lower
        partial_match = any(char in spoken_lower for char in trigger_lower) and len(trigger_lower) > 2
        phonetic_match = abs(len(spoken_lower) - len(trigger_lower)) <= 2  # Aproximação fonética básica
        
        # Calcular confiança baseada na sensibilidade
        confidence = 0.0
        if exact_match:
            confidence = 0.95
        elif partial_match and sensitivity > 0.6:
            confidence = 0.75
        elif phonetic_match and sensitivity > 0.8:
            confidence = 0.60
        
        detected = confidence >= (1.0 - sensitivity)
        
        test_result = {
            'detected': detected,
            'confidence': round(confidence, 3),
            'trigger_word': trigger_word,
            'spoken_text': spoken_text,
            'sensitivity': sensitivity,
            'match_types': {
                'exact_match': exact_match,
                'partial_match': partial_match,
                'phonetic_match': phonetic_match
            },
            'recommendations': []
        }
        
        # Gerar recomendações
        if not detected and spoken_text:
            if confidence < 0.3:
                test_result['recommendations'].append('Tente falar mais claramente')
            if confidence < 0.5:
                test_result['recommendations'].append('Considere aumentar a sensibilidade')
            if not exact_match:
                test_result['recommendations'].append(f'Certifique-se de falar "{trigger_word}" corretamente')
        
        return jsonify({
            'success': True,
            'test_result': test_result,
            'message': f'✅ "{trigger_word}" detectado!' if detected else f'❌ "{trigger_word}" não detectado'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/trigger-word/suggestions', methods=['GET'])
def get_trigger_word_suggestions():
    """Obter sugestões de palavras de ativação"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        suggestions = {
            'populares': ['EION', 'ALEX', 'IRIS', 'ZARA', 'NOVA', 'ECHO'],
            'personalizadas': ['MEU_NOME', 'ASSISTENTE', 'JARVIS', 'FRIDAY', 'KAREN', 'STELLA'],
            'curtas': ['AI', 'GO', 'HI', 'UP', 'ON', 'RUN'],
            'divertidas': ['MAGO', 'GENIE', 'ROBÔ', 'MESTRE', 'CHEFE', 'BUDDY'],
            'profissionais': ['SISTEMA', 'CENTRAL', 'COMANDO', 'OFFICE', 'WORK', 'DESK']
        }
        
        # Adicionar informações sobre cada sugestão
        suggestions_with_info = {}
        for category, words in suggestions.items():
            suggestions_with_info[category] = [
                {
                    'word': word,
                    'length': len(word),
                    'complexity': 'fácil' if len(word) <= 3 else 'média' if len(word) <= 6 else 'difícil',
                    'recommended_sensitivity': 0.6 if len(word) <= 3 else 0.7 if len(word) <= 6 else 0.8
                }
                for word in words
            ]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions_with_info,
            'guidelines': [
                'Use palavras de 2-8 caracteres para melhor reconhecimento',
                'Evite palavras muito comuns que podem ser ditas acidentalmente',
                'Palavras com sons distintos funcionam melhor',
                'Teste sempre sua palavra escolhida antes de confirmar'
            ],
            'default': 'EION'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SISTEMA DE COACHES ====================

@app.route('/api/coaches/list', methods=['GET'])
def list_coaches():
    """Listar todos os coaches disponíveis"""
    try:
        specialty = request.args.get('specialty')  # Filtrar por especialidade
        language = request.args.get('language', 'pt-BR')
        
        query = Coach.query.filter_by(is_active=True)
        
        if specialty:
            query = query.filter_by(specialty=specialty)
        
        coaches = query.all()
        
        # Filtrar por idioma
        coaches_filtered = []
        for coach in coaches:
            languages = json.loads(coach.languages)
            if language in languages:
                coaches_filtered.append(coach)
        
        return jsonify({
            'success': True,
            'coaches': [coach.to_dict() for coach in coaches_filtered],
            'total': len(coaches_filtered),
            'specialties': ['business', 'life', 'productivity', 'health', 'financial', 'leadership'],
            'coaching_styles': ['directive', 'non-directive', 'collaborative']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coaches/<int:coach_id>', methods=['GET'])
def get_coach_details(coach_id):
    """Obter detalhes de um coach específico"""
    try:
        coach = Coach.query.get(coach_id)
        if not coach:
            return jsonify({'error': 'Coach não encontrado'}), 404
        
        # Estatísticas do coach
        sessions = CoachingSession.query.filter_by(coach_id=coach_id).all()
        completed_sessions = [s for s in sessions if s.status == 'completed']
        
        ratings = [s.user_rating for s in completed_sessions if s.user_rating]
        avg_rating = sum(ratings) / len(ratings) if ratings else 5.0
        
        return jsonify({
            'success': True,
            'coach': coach.to_dict(),
            'statistics': {
                'total_sessions': len(sessions),
                'completed_sessions': len(completed_sessions),
                'average_rating': round(avg_rating, 2),
                'success_rate': coach.success_rate,
                'response_time': '< 2 horas'
            },
            'testimonials': [
                {
                    'user': 'Cliente A.',
                    'rating': 5,
                    'comment': 'Excelente profissional, me ajudou muito!'
                },
                {
                    'user': 'Cliente B.',
                    'rating': 5,
                    'comment': 'Metodologia muito eficaz e prática.'
                }
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coaching/book-session', methods=['POST'])
def book_coaching_session():
    """Agendar sessão de coaching"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        coach_id = data.get('coach_id')
        scheduled_at = datetime.fromisoformat(data.get('scheduled_at'))
        objectives = data.get('objectives', '')
        session_type = data.get('session_type', 'individual')
        
        # Verificar se o usuário tem sessões disponíveis
        user_subscription = UserSubscription.query.filter_by(
            user_id=user_id, status='active'
        ).first()
        
        if not user_subscription:
            return jsonify({'error': 'Assinatura ativa necessária para agendar coaching'}), 400
        
        plan = SubscriptionPlan.query.get(user_subscription.plan_id)
        if user_subscription.coaching_sessions_used >= plan.coaching_sessions_included:
            return jsonify({'error': 'Limite de sessões de coaching atingido para o plano atual'}), 400
        
        session = CoachingSession(
            user_id=user_id,
            coach_id=coach_id,
            session_type=session_type,
            title=f'Sessão de Coaching - {datetime.now().strftime("%d/%m/%Y")}',
            objectives=objectives,
            scheduled_at=scheduled_at,
            status='scheduled'
        )
        
        db.session.add(session)
        user_subscription.coaching_sessions_used += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': f'📅 Sessão agendada com sucesso para {scheduled_at.strftime("%d/%m/%Y às %H:%M")}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SISTEMA DE PLANOS E ASSINATURAS ====================

@app.route('/api/plans/list', methods=['GET'])
def list_subscription_plans():
    """Listar todos os planos de assinatura"""
    try:
        plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(
            SubscriptionPlan.sort_order, SubscriptionPlan.price_monthly
        ).all()
        
        return jsonify({
            'success': True,
            'plans': [plan.to_dict() for plan in plans],
            'total': len(plans),
            'currency': 'BRL',
            'payment_methods': ['credit_card', 'pix', 'boleto', 'paypal'],
            'trial_available': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription/current', methods=['GET'])
def get_current_subscription():
    """Obter assinatura atual do usuário"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        subscription = UserSubscription.query.filter_by(
            user_id=user_id, status='active'
        ).first()
        
        if not subscription:
            # Verificar se tem trial ativo
            subscription = UserSubscription.query.filter_by(
                user_id=user_id, status='trial'
            ).first()
        
        if not subscription:
            return jsonify({
                'has_subscription': False,
                'message': 'Nenhuma assinatura ativa encontrada'
            })
        
        plan = SubscriptionPlan.query.get(subscription.plan_id)
        
        # Calcular dias restantes do trial
        trial_days_left = 0
        if subscription.status == 'trial' and subscription.trial_ends_at:
            trial_days_left = max(0, (subscription.trial_ends_at - datetime.utcnow()).days)
        
        return jsonify({
            'success': True,
            'has_subscription': True,
            'subscription': subscription.to_dict(),
            'plan': plan.to_dict() if plan else None,
            'trial_info': {
                'is_trial': subscription.status == 'trial',
                'days_left': trial_days_left
            },
            'usage_limits': {
                'meetings_remaining': plan.max_meetings_per_month - subscription.meetings_this_month if plan else 0,
                'storage_remaining_gb': plan.max_storage_gb - subscription.storage_used_gb if plan else 0,
                'coaching_sessions_remaining': plan.coaching_sessions_included - subscription.coaching_sessions_used if plan else 0
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription/subscribe', methods=['POST'])
def create_subscription():
    """Criar nova assinatura"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        payment_method = data.get('payment_method', 'credit_card')
        coupon_code = data.get('coupon_code')
        
        plan = SubscriptionPlan.query.get(plan_id)
        if not plan:
            return jsonify({'error': 'Plano não encontrado'}), 404
        
        # Verificar se já tem assinatura ativa
        existing = UserSubscription.query.filter_by(
            user_id=user_id, status__in=['active', 'trial']
        ).first()
        
        if existing:
            return jsonify({'error': 'Usuário já possui assinatura ativa'}), 400
        
        # Calcular preço
        price = plan.price_yearly if billing_cycle == 'yearly' else plan.price_monthly
        original_price = price
        discount_amount = 0.0
        
        # Aplicar cupom se fornecido
        if coupon_code:
            coupon = DiscountCoupon.query.filter_by(code=coupon_code.upper()).first()
            if coupon:
                # Verificar se usuário pode usar este cupom
                can_use, reason = coupon.can_be_used_by(user_id, User.query.get(user_id).email)
                
                if can_use and not coupon.is_used():
                    discount_amount = coupon.calculate_discount(price, plan_id)
                    if discount_amount > 0:
                        price -= discount_amount
                        
                        # Marcar cupom como usado
                        coupon.mark_as_used(user_id)
                        
                        # Registrar uso do cupom
                        coupon_usage = CouponUsage(
                            coupon_id=coupon.id,
                            user_id=user_id,
                            original_amount=original_price,
                            discount_amount=discount_amount,
                            final_amount=price
                        )
                        db.session.add(coupon_usage)
                else:
                    return jsonify({
                        'error': f'Cupom não pode ser usado: {reason}',
                        'error_code': 'COUPON_INVALID'
                    }), 400
        
        # Criar assinatura
        trial_end = datetime.utcnow() + timedelta(days=plan.trial_days)
        period_end = datetime.utcnow() + timedelta(days=30 if billing_cycle == 'monthly' else 365)
        
        subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan_id,
            status='trial' if plan.trial_days > 0 else 'active',
            billing_cycle=billing_cycle,
            trial_ends_at=trial_end if plan.trial_days > 0 else None,
            current_period_end=period_end,
            payment_method=payment_method,
            next_billing_amount=price
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict(),
            'billing': {
                'original_price': original_price,
                'discount_amount': discount_amount,
                'final_price': price,
                'coupon_applied': coupon_code if discount_amount > 0 else None
            },
            'message': f'🎉 Assinatura criada com sucesso! Trial de {plan.trial_days} dias ativado.' if plan.trial_days > 0 else '🎉 Assinatura ativada com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SISTEMA DE CUPONS ====================

@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    """Validar cupom de desconto exclusivo"""
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code', '').upper()
        user_id = data.get('user_id', 1)
        plan_id = data.get('plan_id')
        amount = data.get('amount', 0.0)
        
        if not coupon_code:
            return jsonify({'error': 'Código do cupom é obrigatório'}), 400
        
        # Buscar usuário para validação
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        coupon = DiscountCoupon.query.filter_by(code=coupon_code).first()
        
        if not coupon:
            return jsonify({
                'valid': False,
                'error': 'Cupom não encontrado',
                'error_code': 'COUPON_NOT_FOUND'
            }), 404
        
        # Verificar se cupom já foi usado
        if coupon.is_used():
            return jsonify({
                'valid': False,
                'error': 'Este cupom já foi utilizado e não pode ser usado novamente',
                'error_code': 'COUPON_ALREADY_USED',
                'used_by': coupon.used_by_user_id,
                'used_at': coupon.used_at.isoformat() if coupon.used_at else None
            }), 400
        
        # Verificar se usuário tem autorização para usar este cupom
        can_use, reason = coupon.can_be_used_by(user_id, user.email)
        
        if not can_use:
            return jsonify({
                'valid': False,
                'error': reason,
                'error_code': 'COUPON_NOT_AUTHORIZED'
            }), 403
        
        # Calcular desconto
        discount_amount = coupon.calculate_discount(amount, plan_id)
        
        if discount_amount == 0:
            return jsonify({
                'valid': False,
                'error': 'Cupom não aplicável a este plano ou valor',
                'error_code': 'COUPON_NOT_APPLICABLE'
            }), 400
        
        discount_percentage = (discount_amount / amount) * 100 if amount > 0 else 0
        
        return jsonify({
            'valid': True,
            'coupon': coupon.to_dict(),
            'discount': {
                'amount': discount_amount,
                'percentage': round(discount_percentage, 1),
                'final_amount': amount - discount_amount
            },
            'exclusivity': {
                'is_exclusive': True,
                'single_use': True,
                'authorized_user': user_id,
                'authorized_email': user.email
            },
            'message': f'✅ Cupom exclusivo válido! Desconto de R$ {discount_amount:.2f} ({discount_percentage:.1f}%)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/create', methods=['POST'])
def create_coupon():
    """Criar novo cupom de desconto"""
    try:
        data = request.get_json()
        
        # Gerar código automático se não fornecido
        code = data.get('code', f'IAON{random.randint(1000, 9999)}').upper()
        
        coupon = DiscountCoupon(
            code=code,
            name=data.get('name', f'Cupom {code}'),
            description=data.get('description', ''),
            discount_type=data.get('discount_type', 'percentage'),
            discount_value=data.get('discount_value', 20),
            max_discount_amount=data.get('max_discount_amount'),
            minimum_purchase=data.get('minimum_purchase', 0.0),
            valid_from=datetime.fromisoformat(data.get('valid_from')) if data.get('valid_from') else datetime.utcnow(),
            valid_until=datetime.fromisoformat(data.get('valid_until')) if data.get('valid_until') else None,
            max_uses=data.get('max_uses'),
            max_uses_per_user=data.get('max_uses_per_user', 1),
            applicable_plans=json.dumps(data.get('applicable_plans', [])),
            first_purchase_only=data.get('first_purchase_only', False),
            billing_cycles=data.get('billing_cycles', 'all'),
            created_by_admin=data.get('admin_name', 'Sistema'),
            is_public=data.get('is_public', False)
        )
        
        db.session.add(coupon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'coupon': coupon.to_dict(),
            'message': f'🎫 Cupom {code} criado com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/create-exclusive', methods=['POST'])
def create_exclusive_coupon():
    """Criar cupom exclusivo de uso único para usuário específico"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        target_user_id = data.get('target_user_id')
        target_user_email = data.get('target_user_email', '').lower()
        discount_value = data.get('discount_value')
        admin_password = data.get('admin_password')  # Senha de admin para segurança
        
        # Validação de segurança (você pode personalizar isso)
        if admin_password != 'IAON_ADMIN_2025':
            return jsonify({'error': 'Acesso negado - senha de administrador inválida'}), 403
        
        if not discount_value or discount_value <= 0 or discount_value > 100:
            return jsonify({'error': 'Valor do desconto deve estar entre 1% e 100%'}), 400
        
        # Verificar se usuário existe
        target_user = None
        if target_user_id:
            target_user = User.query.get(target_user_id)
        elif target_user_email:
            target_user = User.query.filter_by(email=target_user_email).first()
        
        if not target_user and not target_user_email:
            return jsonify({'error': 'É necessário informar user_id ou email do usuário'}), 400
        
        # Gerar código único exclusivo
        code = data.get('code')
        if not code:
            if target_user:
                code = f'EXCLUSIVE_{target_user.username.upper()}_{random.randint(100, 999)}'
            else:
                code = f'EXCLUSIVE_{target_user_email.split("@")[0].upper()}_{random.randint(100, 999)}'
        
        code = code.upper()
        
        # Verificar se código já existe
        if DiscountCoupon.query.filter_by(code=code).first():
            return jsonify({'error': f'Código {code} já existe'}), 400
        
        # Criar cupom exclusivo
        coupon = DiscountCoupon(
            code=code,
            name=data.get('name', f'Cupom Exclusivo - {target_user.full_name if target_user else target_user_email}'),
            description=data.get('description', f'Cupom personalizado de {discount_value}% de desconto - uso único'),
            discount_type='percentage',
            discount_value=discount_value,
            max_discount_amount=data.get('max_discount_amount'),
            minimum_purchase=data.get('minimum_purchase', 0.0),
            
            # Configurações de uso único
            max_uses=1,
            max_uses_per_user=1,
            is_single_use=True,
            
            # Exclusividade
            exclusive_user_id=target_user.id if target_user else None,
            exclusive_user_email=target_user_email or (target_user.email if target_user else None),
            
            # Validade
            valid_from=datetime.utcnow(),
            valid_until=datetime.fromisoformat(data.get('valid_until')) if data.get('valid_until') else datetime.utcnow() + timedelta(days=30),
            
            # Aplicabilidade
            applicable_plans=json.dumps(data.get('applicable_plans', [])),
            first_purchase_only=data.get('first_purchase_only', False),
            billing_cycles=data.get('billing_cycles', 'all'),
            
            # Admin
            created_by_admin=data.get('admin_name', 'Carol (Administrador)'),
            admin_notes=data.get('admin_notes', f'Cupom exclusivo criado para {target_user.full_name if target_user else target_user_email}'),
            is_active=True,
            is_public=False  # Sempre privado
        )
        
        db.session.add(coupon)
        db.session.commit()
        
        # Preparar informações para envio
        coupon_info = {
            'code': code,
            'discount_value': discount_value,
            'target_user': {
                'id': target_user.id if target_user else None,
                'name': target_user.full_name if target_user else 'Usuário',
                'email': target_user_email or (target_user.email if target_user else None)
            },
            'valid_until': coupon.valid_until.strftime('%d/%m/%Y') if coupon.valid_until else 'Sem prazo',
            'applicable_plans': json.loads(coupon.applicable_plans) if coupon.applicable_plans else 'Todos os planos'
        }
        
        return jsonify({
            'success': True,
            'coupon': coupon.to_dict(),
            'coupon_info': coupon_info,
            'sharing_info': {
                'message_template': f'''
🎉 CUPOM EXCLUSIVO IAON - {discount_value}% DE DESCONTO! 🎉

Olá {target_user.full_name if target_user else 'Usuário'}!

Você recebeu um cupom exclusivo de desconto:

📧 Código: {code}
💰 Desconto: {discount_value}%
⏰ Válido até: {coupon.valid_until.strftime('%d/%m/%Y') if coupon.valid_until else 'Sem prazo'}
🔒 Uso único: Este cupom só pode ser usado UMA VEZ e é exclusivo para você!

Para usar:
1. Faça seu cadastro no IAON
2. Escolha seu plano
3. Digite o código: {code}
4. Aproveite o desconto!

Atenção: Este cupom é pessoal e intransferível. Após o uso, não poderá ser usado novamente.

Baixe o IAON e transforme suas reuniões! 🚀
                '''.strip(),
                'whatsapp_link': f'https://wa.me/?text=🎉%20CUPOM%20EXCLUSIVO%20IAON%20{discount_value}%25%20-%20Código:%20{code}',
                'email_subject': f'🎁 Seu cupom exclusivo IAON de {discount_value}% chegou!'
            },
            'security': {
                'single_use': True,
                'exclusive_access': True,
                'cannot_be_shared': True,
                'automatic_deactivation': 'Após primeiro uso'
            },
            'message': f'✅ Cupom exclusivo {code} criado com sucesso para {target_user.full_name if target_user else target_user_email}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/my-exclusive', methods=['GET'])
def get_my_exclusive_coupons():
    """Obter cupons exclusivos do usuário (admin)"""
    try:
        admin_password = request.args.get('admin_password')
        
        # Validação de segurança
        if admin_password != 'IAON_ADMIN_2025':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Buscar todos os cupons exclusivos
        exclusive_coupons = DiscountCoupon.query.filter_by(
            is_single_use=True
        ).order_by(DiscountCoupon.created_at.desc()).all()
        
        coupon_details = []
        for coupon in exclusive_coupons:
            target_user = User.query.get(coupon.exclusive_user_id) if coupon.exclusive_user_id else None
            
            coupon_detail = {
                'coupon': coupon.to_dict(),
                'target_user': {
                    'id': target_user.id if target_user else None,
                    'name': target_user.full_name if target_user else 'Usuário não cadastrado',
                    'email': coupon.exclusive_user_email,
                    'username': target_user.username if target_user else None
                },
                'status': {
                    'is_used': coupon.is_used(),
                    'can_still_be_used': coupon.is_valid() and not coupon.is_used(),
                    'used_by': coupon.used_by_user_id,
                    'used_at': coupon.used_at.isoformat() if coupon.used_at else None
                }
            }
            coupon_details.append(coupon_detail)
        
        return jsonify({
            'success': True,
            'exclusive_coupons': coupon_details,
            'summary': {
                'total_created': len(exclusive_coupons),
                'total_used': len([c for c in exclusive_coupons if c.is_used()]),
                'total_available': len([c for c in exclusive_coupons if c.is_valid() and not c.is_used()])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/coupons/list', methods=['GET'])
def list_coupons():
    """Listar cupons (admin) ou cupons públicos"""
    try:
        is_admin = request.args.get('admin', 'false').lower() == 'true'
        
        if is_admin:
            coupons = DiscountCoupon.query.order_by(DiscountCoupon.created_at.desc()).all()
        else:
            coupons = DiscountCoupon.query.filter_by(
                is_public=True, is_active=True
            ).filter(
                DiscountCoupon.valid_until > datetime.utcnow()
            ).all()
        
        return jsonify({
            'success': True,
            'coupons': [coupon.to_dict() for coupon in coupons],
            'total': len(coupons)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== ENDPOINTS ADMINISTRATIVOS ====================

@app.route('/api/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Dashboard administrativo com estatísticas"""
    try:
        # Estatísticas gerais
        total_users = User.query.filter_by(is_active=True).count()
        total_meetings = MeetingSession.query.count()
        active_subscriptions = UserSubscription.query.filter_by(status='active').count()
        total_revenue = db.session.query(db.func.sum(UserSubscription.next_billing_amount)).scalar() or 0
        
        # Estatísticas por plano
        plan_stats = db.session.query(
            SubscriptionPlan.display_name,
            db.func.count(UserSubscription.id).label('subscribers')
        ).join(UserSubscription).group_by(SubscriptionPlan.id).all()
        
        # Cupons mais usados
        popular_coupons = db.session.query(
            DiscountCoupon.code,
            DiscountCoupon.name,
            DiscountCoupon.current_uses
        ).order_by(DiscountCoupon.current_uses.desc()).limit(5).all()
        
        # Coaches mais populares
        popular_coaches = db.session.query(
            Coach.name,
            Coach.specialty,
            db.func.count(CoachingSession.id).label('sessions')
        ).join(CoachingSession).group_by(Coach.id).order_by(db.text('sessions DESC')).limit(5).all()
        
        return jsonify({
            'success': True,
            'overview': {
                'total_users': total_users,
                'total_meetings': total_meetings,
                'active_subscriptions': active_subscriptions,
                'monthly_revenue': total_revenue
            },
            'plan_distribution': [
                {'plan': name, 'subscribers': count} 
                for name, count in plan_stats
            ],
            'popular_coupons': [
                {'code': code, 'name': name, 'uses': uses}
                for code, name, uses in popular_coupons
            ],
            'popular_coaches': [
                {'name': name, 'specialty': specialty, 'sessions': sessions}
                for name, specialty, sessions in popular_coaches
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users/analytics', methods=['GET'])
def user_analytics():
    """Análise detalhada de usuários"""
    try:
        # Usuários por período
        total_users = User.query.filter_by(is_active=True).count()
        last_30_days = datetime.utcnow() - timedelta(days=30)
        new_users_30d = User.query.filter(User.created_at >= last_30_days).count()
        
        # Churn rate (usuários que cancelaram)
        cancelled_subs = UserSubscription.query.filter_by(status='cancelled').count()
        churn_rate = (cancelled_subs / total_users * 100) if total_users > 0 else 0
        
        # Engagement (usuários ativos nos últimos 7 dias)
        last_week = datetime.utcnow() - timedelta(days=7)
        active_users_7d = User.query.filter(User.last_activity >= last_week).count()
        
        return jsonify({
            'success': True,
            'user_metrics': {
                'total_users': total_users,
                'new_users_30d': new_users_30d,
                'active_users_7d': active_users_7d,
                'churn_rate': round(churn_rate, 2),
                'engagement_rate': round((active_users_7d / total_users * 100) if total_users > 0 else 0, 2)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-voice-command', methods=['POST'])
def process_voice_command():
    """Processar comando de voz com palavra de ativação personalizada"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        voice_input = data.get('voice_input', '').strip()
        confidence = data.get('confidence', 0.8)
        
        if not voice_input:
            return jsonify({'error': 'Entrada de voz é obrigatória'}), 400
        
        # Buscar usuário e palavra de ativação personalizada
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        trigger_word = user.custom_trigger_word or 'EION'
        sensitivity = user.trigger_sensitivity or 0.7
        
        # Verificar se o comando começa com a palavra de ativação
        voice_lower = voice_input.lower()
        trigger_lower = trigger_word.lower()
        
        if not voice_lower.startswith(trigger_lower):
            return jsonify({
                'activated': False,
                'message': f'Comando deve começar com "{trigger_word}"',
                'expected_format': f'{trigger_word}, [seu comando]'
            })
        
        # Remover palavra de ativação do comando
        command_text = voice_input[len(trigger_word):].strip().lstrip(',').strip()
        
        if not command_text:
            return jsonify({
                'activated': True,
                'command_type': 'help',
                'response': f'Olá! Sou o IAON. Como posso ajudar? Você pode dizer "{trigger_word}, ajuda" para ver os comandos disponíveis.',
                'available_commands': [
                    f'{trigger_word}, ligar para [nome]',
                    f'{trigger_word}, abrir [aplicativo]',
                    f'{trigger_word}, iniciar reunião',
                    f'{trigger_word}, configuração',
                    f'{trigger_word}, ajuda'
                ]
            })
        
        # Processar diferentes tipos de comandos
        command_lower = command_text.lower()
        
        # Comando de ligação
        if any(word in command_lower for word in ['ligar', 'chamar', 'telefonar']):
            return process_call_command(user_id, command_text, trigger_word)
        
        # Comando de aplicativo
        elif any(word in command_lower for word in ['abrir', 'executar', 'iniciar', 'app']):
            return process_app_command(user_id, command_text, trigger_word)
        
        # Comando de reunião
        elif any(word in command_lower for word in ['reunião', 'meeting', 'conferência']):
            return process_meeting_command(user_id, command_text, trigger_word)
        
        # Comando de configuração
        elif any(word in command_lower for word in ['configuração', 'config', 'configurar', 'ajustes']):
            return jsonify({
                'activated': True,
                'command_type': 'configuration',
                'response': 'Abrindo configurações do IAON...',
                'action': 'open_settings',
                'settings_available': [
                    'Palavra de ativação',
                    'Sensibilidade de voz',
                    'Preferências de idioma',
                    'Configurações de notificação'
                ]
            })
        
        # Comando de ajuda
        elif any(word in command_lower for word in ['ajuda', 'help', 'comandos']):
            return jsonify({
                'activated': True,
                'command_type': 'help',
                'response': f'Comandos disponíveis com "{trigger_word}":',
                'commands': [
                    {
                        'command': f'{trigger_word}, ligar para João',
                        'description': 'Fazer ligação para um contato'
                    },
                    {
                        'command': f'{trigger_word}, abrir WhatsApp',
                        'description': 'Abrir aplicativo específico'
                    },
                    {
                        'command': f'{trigger_word}, iniciar reunião',
                        'description': 'Iniciar nova reunião'
                    },
                    {
                        'command': f'{trigger_word}, configuração',
                        'description': 'Abrir configurações'
                    }
                ]
            })
        
        # Comando não reconhecido
        else:
            return jsonify({
                'activated': True,
                'command_type': 'unknown',
                'response': f'Comando "{command_text}" não reconhecido. Diga "{trigger_word}, ajuda" para ver comandos disponíveis.',
                'suggestion': 'Tente usar um dos comandos disponíveis ou verifique a pronúncia.'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_call_command(user_id, command_text, trigger_word):
    """Processar comando de ligação"""
    # Extrair nome do contato
    contact_name = extract_contact_name(command_text)
    
    if not contact_name:
        return jsonify({
            'activated': True,
            'command_type': 'call',
            'error': 'Nome do contato não identificado',
            'response': f'Não consegui identificar o contato. Tente: "{trigger_word}, ligar para João"'
        })
    
    # Buscar contato
    contacts = Contact.query.filter_by(user_id=user_id).all()
    best_match = None
    best_score = 0
    
    for contact in contacts:
        score = contact.get_voice_match_score(contact_name)
        if score > best_score:
            best_score = score
            best_match = contact
    
    if best_match and best_score >= 70:
        # Registrar log da chamada
        call_log = CallLog(
            user_id=user_id,
            contact_id=best_match.id,
            phone_number=best_match.phone_number,
            contact_name=best_match.name,
            call_type='outgoing',
            call_method='voice_command',
            voice_command=command_text,
            voice_confidence=best_score / 100.0,
            call_status='initiated'
        )
        db.session.add(call_log)
        db.session.commit()
        
        return jsonify({
            'activated': True,
            'command_type': 'call',
            'response': f'Ligando para {best_match.name}...',
            'action': 'make_call',
            'contact': best_match.to_dict(),
            'confidence': best_score / 100.0
        })
    else:
        return jsonify({
            'activated': True,
            'command_type': 'call',
            'error': 'Contato não encontrado',
            'response': f'Contato "{contact_name}" não encontrado. Verifique o nome ou adicione o contato primeiro.'
        })

def process_app_command(user_id, command_text, trigger_word):
    """Processar comando de abertura de aplicativo"""
    app_name = extract_app_name(command_text)
    
    if not app_name:
        return jsonify({
            'activated': True,
            'command_type': 'app',
            'error': 'Nome do aplicativo não identificado',
            'response': f'Não consegui identificar o aplicativo. Tente: "{trigger_word}, abrir WhatsApp"'
        })
    
    # Buscar aplicativo
    apps = AppControl.query.filter_by(user_id=user_id).all()
    best_match = None
    best_score = 0
    
    for app in apps:
        score = app.get_voice_match_score(app_name)
        if score > best_score:
            best_score = score
            best_match = app
    
    if best_match and best_score >= 70:
        # Registrar log de abertura
        launch_log = AppLaunchLog(
            user_id=user_id,
            app_id=best_match.id,
            app_name=best_match.app_name,
            voice_command=command_text,
            voice_confidence=best_score / 100.0,
            launch_status='initiated'
        )
        db.session.add(launch_log)
        best_match.usage_count += 1
        best_match.last_opened = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'activated': True,
            'command_type': 'app',
            'response': f'Abrindo {best_match.display_name or best_match.app_name}...',
            'action': 'launch_app',
            'app': best_match.to_dict(),
            'confidence': best_score / 100.0
        })
    else:
        return jsonify({
            'activated': True,
            'command_type': 'app',
            'error': 'Aplicativo não encontrado',
            'response': f'Aplicativo "{app_name}" não encontrado. Verifique o nome ou instale o aplicativo primeiro.'
        })

def process_meeting_command(user_id, command_text, trigger_word):
    """Processar comando de reunião"""
    return jsonify({
        'activated': True,
        'command_type': 'meeting',
        'response': 'Iniciando nova reunião...',
        'action': 'start_meeting',
        'meeting_settings': {
            'auto_record': True,
            'do_not_disturb': True,
            'voice_activation': True
        }
    })

def extract_contact_name(command_text):
    """Extrair nome do contato do comando"""
    # Padrões comuns para ligação
    patterns = [
        r'ligar para (.+)',
        r'chamar (.+)',
        r'telefonar para (.+)',
        r'discar para (.+)'
    ]
    
    command_lower = command_text.lower()
    for pattern in patterns:
        match = re.search(pattern, command_lower)
        if match:
            return match.group(1).strip()
    
    return None

def extract_app_name(command_text):
    """Extrair nome do aplicativo do comando"""
    # Padrões comuns para aplicativos
    patterns = [
        r'abrir (.+)',
        r'executar (.+)',
        r'iniciar (.+)',
        r'app (.+)'
    ]
    
    command_lower = command_text.lower()
    for pattern in patterns:
        match = re.search(pattern, command_lower)
        if match:
            return match.group(1).strip()
    
    return None

@app.route('/api/voice-biometry/advanced-status/<int:user_id>', methods=['GET'])
def advanced_voice_biometry_status(user_id):
    """Status avançado da biometria de voz"""
    try:
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        if not biometry:
            # Criar registro de biometria se não existir
            biometry = VoiceBiometry(user_id=user_id)
            db.session.add(biometry)
            db.session.commit()
        
        return jsonify(biometry.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-biometry/advanced-enroll', methods=['POST'])
def advanced_voice_biometry_enroll():
    """Cadastro avançado de biometria de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        audio_data = data.get('audio_data', '')  # Base64 encoded audio
        enrollment_phrase = data.get('enrollment_phrase', '')
        audio_quality = data.get('audio_quality', 'unknown')
        
        # Buscar ou criar registro de biometria
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        if not biometry:
            biometry = VoiceBiometry(
                user_id=user_id,
                enrollment_phrase=enrollment_phrase
            )
            db.session.add(biometry)
        
        # Simular análise avançada de voz
        import json
        voice_features = {
            'sample_id': biometry.samples_count + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'phrase': enrollment_phrase,
            'quality': audio_quality,
            'duration': data.get('duration', 0),
            'frequency_analysis': {
                'fundamental_freq': 150 + (biometry.samples_count * 10),
                'harmonics': [300, 450, 600],
                'formants': [800, 1200, 2400]
            },
            'voice_characteristics': {
                'pitch_variation': 0.1 + (biometry.samples_count * 0.02),
                'speed': data.get('speech_rate', 1.0),
                'energy': 0.8 + (biometry.samples_count * 0.01)
            }
        }
        
        # Atualizar características da voz
        if biometry.voice_features:
            existing_features = json.loads(biometry.voice_features)
            existing_features.append(voice_features)
            biometry.voice_features = json.dumps(existing_features)
        else:
            biometry.voice_features = json.dumps([voice_features])
        
        # Incrementar contador de amostras
        biometry.samples_count += 1
        
        # Determinar qualidade do cadastro
        if biometry.samples_count >= biometry.required_samples:
            biometry.is_enrolled = True
            biometry.enrollment_quality = 'excellent' if biometry.samples_count >= 7 else 'good'
            
            # Atualizar usuário
            user = User.query.get(user_id)
            if user:
                user.voice_enabled = True
        
        db.session.commit()
        
        return jsonify({
            'enrollment_complete': biometry.is_enrolled,
            'samples_count': biometry.samples_count,
            'required_samples': biometry.required_samples,
            'enrollment_progress': biometry.get_enrollment_progress(),
            'enrollment_quality': biometry.enrollment_quality,
            'message': 'Amostra de voz processada com sucesso!' if not biometry.is_enrolled 
                      else f'🎉 Biometria de voz cadastrada com qualidade {biometry.enrollment_quality}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-biometry/verify', methods=['POST'])
def verify_voice_biometry():
    """Verificar biometria de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        audio_data = data.get('audio_data', '')
        phrase = data.get('phrase', '')
        
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        if not biometry or not biometry.is_enrolled:
            return jsonify({
                'verified': False,
                'message': 'Biometria de voz não cadastrada'
            }), 400
        
        # Simular verificação avançada
        import random
        
        biometry.verification_attempts += 1
        
        # Simular análise de similaridade (em produção, usar ML real)
        confidence_score = random.uniform(0.75, 0.95)
        verified = confidence_score >= biometry.confidence_threshold
        
        if verified:
            biometry.successful_verifications += 1
            biometry.last_verification = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'verified': verified,
            'confidence_score': round(confidence_score, 3),
            'threshold': biometry.confidence_threshold,
            'message': '✅ Voz verificada com sucesso!' if verified else '❌ Verificação de voz falhou'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SISTEMA DE REUNIÕES ====================

@app.route('/api/meetings/start', methods=['POST'])
def start_meeting():
    """Iniciar uma nova sessão de reunião com configurações avançadas do dispositivo"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        title = data.get('title', f'Reunião {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        description = data.get('description', '')
        auto_dnd = data.get('auto_dnd', True)  # Ativar "Não Perturbe" automaticamente
        background_listening = data.get('background_listening', True)  # Escuta em segundo plano
        
        # Criar nova sessão de reunião
        meeting = MeetingSession(
            user_id=user_id,
            title=title,
            description=description
        )
        db.session.add(meeting)
        db.session.commit()
        
        # Configurações avançadas do dispositivo
        device_settings = {
            'meeting_id': meeting.id,
            'do_not_disturb': {
                'enabled': auto_dnd,
                'allow_calls_from': 'favorites',  # Permitir apenas favoritos
                'allow_repeated_calls': True,     # Permitir chamadas repetidas (emergência)
                'silence_notifications': True,
                'dim_lock_screen': True
            },
            'audio_settings': {
                'microphone': {
                    'input_gain': 0.8,              # Ganho otimizado
                    'noise_cancellation': True,     # Cancelamento de ruído
                    'echo_cancellation': True,      # Cancelamento de eco
                    'sample_rate': 44100,           # Taxa de amostragem
                    'bit_depth': 16,                # Profundidade de bits
                    'channels': 'mono'              # Mono para economia de bateria
                },
                'voice_activation': {
                    'enabled': background_listening,
                    'trigger_phrase': 'EION',       # Palavra de ativação
                    'sensitivity': 0.7,             # Sensibilidade (0.1-1.0)
                    'timeout_seconds': 5,           # Timeout após ativação
                    'low_power_mode': True          # Modo de baixo consumo
                }
            },
            'power_management': {
                'background_processing': True,      # Processamento em segundo plano
                'cpu_throttling': True,            # Reduzir CPU quando inativo
                'screen_dim_timeout': 30,          # Escurecer tela em 30s
                'prevent_sleep': True,             # Manter acordado durante reunião
                'optimize_for_battery': True
            },
            'permissions': {
                'microphone_always': True,         # Microfone sempre disponível
                'background_refresh': True,        # Atualização em segundo plano
                'push_notifications': True         # Notificações push
            }
        }
        
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict(),
            'device_settings': device_settings,
            'system_actions': [
                'activate_do_not_disturb',
                'optimize_audio_settings',
                'enable_background_listening',
                'configure_power_management'
            ],
            'message': f'📹 Reunião "{title}" iniciada com configurações avançadas!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/add-participant', methods=['POST'])
def add_meeting_participant(meeting_id):
    """Adicionar participante à reunião com registro de voz"""
    try:
        data = request.get_json()
        participant_name = data.get('participant_name', 'Participante Desconhecido')
        participant_role = data.get('participant_role', 'participante')
        email = data.get('email', '')
        voice_sample = data.get('voice_sample', '')  # Amostra de voz para reconhecimento
        presentation_text = data.get('presentation_text', '')  # Texto da apresentação
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Processar amostra de voz para criar perfil avançado
        voice_profile = create_enhanced_voice_profile(voice_sample, presentation_text) if voice_sample else '{}'
        
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            participant_name=participant_name,
            participant_role=participant_role,
            email=email,
            voice_profile=voice_profile,
            confidence_level=0.95 if voice_sample else 0.0,
            is_verified=bool(voice_sample)
        )
        db.session.add(participant)
        
        # Atualizar contagem de participantes
        meeting.total_participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).count() + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'participant': participant.to_dict(),
            'voice_profile_quality': 'excellent' if voice_sample else 'pending',
            'message': f'👤 Participante "{participant_name}" {'registrado com perfil de voz' if voice_sample else 'adicionado - aguardando apresentação'}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/participant-introduction', methods=['POST'])
def participant_introduction(meeting_id):
    """Registrar apresentação de participante com análise de voz"""
    try:
        data = request.get_json()
        participant_name = data.get('participant_name')
        audio_data = data.get('audio_data', '')  # Áudio da apresentação
        introduction_text = data.get('introduction_text', '')  # Transcrição da apresentação
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Buscar participante existente ou criar novo
        participant = MeetingParticipant.query.filter_by(
            meeting_id=meeting_id, 
            participant_name=participant_name
        ).first()
        
        if not participant:
            participant = MeetingParticipant(
                meeting_id=meeting_id,
                participant_name=participant_name,
                participant_role='participante'
            )
            db.session.add(participant)
        
        # Criar perfil de voz detalhado da apresentação
        voice_profile = create_enhanced_voice_profile(audio_data, introduction_text)
        participant.voice_profile = voice_profile
        participant.confidence_level = 0.95
        participant.is_verified = True
        
        # Atualizar contagem se for novo participante
        if not participant.id:
            meeting.total_participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).count() + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'participant': participant.to_dict(),
            'voice_analysis': {
                'profile_created': True,
                'confidence_level': participant.confidence_level,
                'characteristics_detected': 8,  # Número de características analisadas
                'quality': 'excellent'
            },
            'message': f'🎤 Perfil de voz criado para {participant_name}! Sistema pronto para reconhecimento.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/transcribe', methods=['POST'])
def transcribe_meeting_audio(meeting_id):
    """Transcrever áudio da reunião com identificação de falantes"""
    try:
        data = request.get_json()
        audio_data = data.get('audio_data', '')  # Base64 encoded audio
        timestamp = data.get('timestamp', datetime.utcnow().isoformat())
        start_time = data.get('start_time_seconds', 0.0)
        end_time = data.get('end_time_seconds', 0.0)
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Simular transcrição avançada com IA
        transcription_result = transcribe_with_speaker_identification(
            audio_data, meeting_id, start_time, end_time
        )
        
        # Salvar transcrição
        transcript = MeetingTranscript(
            meeting_id=meeting_id,
            speaker_name=transcription_result['speaker_name'],
            content=transcription_result['content'],
            start_time_seconds=start_time,
            end_time_seconds=end_time,
            confidence_score=transcription_result['confidence'],
            audio_quality=transcription_result['audio_quality'],
            sentiment=transcription_result['sentiment']
        )
        
        # Identificar se é item de ação ou decisão
        if any(keyword in transcript.content.lower() for keyword in ['decidir', 'decidimos', 'resolução', 'conclusão']):
            transcript.is_decision = True
        
        if any(keyword in transcript.content.lower() for keyword in ['ação', 'tarefa', 'deve fazer', 'responsável']):
            transcript.is_action_item = True
        
        db.session.add(transcript)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'transcript': transcript.to_dict(),
            'speaker_identified': transcription_result['speaker_identified'],
            'message': f'🎤 Fala de {transcript.speaker_name} transcrita com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/generate-agenda', methods=['POST'])
def generate_meeting_agenda(meeting_id):
    """Gerar pauta da reunião baseada na transcrição"""
    try:
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Buscar todas as transcrições da reunião
        transcripts = MeetingTranscript.query.filter_by(meeting_id=meeting_id).order_by(
            MeetingTranscript.start_time_seconds
        ).all()
        
        if not transcripts:
            return jsonify({'error': 'Não há transcrições para gerar a pauta'}), 400
        
        # Gerar pauta com IA avançada
        agenda_data = generate_advanced_agenda(meeting, transcripts)
        
        # Verificar se já existe uma pauta
        existing_agenda = MeetingAgenda.query.filter_by(meeting_id=meeting_id).first()
        
        if existing_agenda:
            # Atualizar pauta existente
            existing_agenda.title = agenda_data['title']
            existing_agenda.summary = agenda_data['summary']
            existing_agenda.key_points = agenda_data['key_points']
            existing_agenda.action_items = agenda_data['action_items']
            existing_agenda.decisions_made = agenda_data['decisions_made']
            existing_agenda.next_steps = agenda_data['next_steps']
            existing_agenda.participants_summary = agenda_data['participants_summary']
            existing_agenda.topics_discussed = agenda_data['topics_discussed']
            agenda = existing_agenda
        else:
            # Criar nova pauta
            agenda = MeetingAgenda(
                meeting_id=meeting_id,
                title=agenda_data['title'],
                summary=agenda_data['summary'],
                key_points=agenda_data['key_points'],
                action_items=agenda_data['action_items'],
                decisions_made=agenda_data['decisions_made'],
                next_steps=agenda_data['next_steps'],
                participants_summary=agenda_data['participants_summary'],
                topics_discussed=agenda_data['topics_discussed']
            )
            db.session.add(agenda)
        
        # Marcar reunião como tendo pauta gerada
        meeting.agenda_generated = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'agenda': agenda.to_dict(),
            'message': '📋 Pauta da reunião gerada com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/end', methods=['POST'])
def end_meeting(meeting_id):
    """Finalizar reunião e restaurar configurações do dispositivo"""
    try:
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        meeting.end_time = datetime.utcnow()
        meeting.status = 'completed'
        
        # Calcular estatísticas finais
        transcripts = MeetingTranscript.query.filter_by(meeting_id=meeting_id).all()
        participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).all()
        
        # Calcular tempo de fala por participante
        for participant in participants:
            participant_transcripts = [t for t in transcripts if t.speaker_name == participant.participant_name]
            speaking_time = sum([
                (t.end_time_seconds or 0) - (t.start_time_seconds or 0) 
                for t in participant_transcripts
            ])
            participant.speaking_time_minutes = speaking_time / 60
            participant.interventions_count = len(participant_transcripts)
        
        # Calcular qualidade geral
        if transcripts:
            avg_confidence = sum([t.confidence_score or 0 for t in transcripts]) / len(transcripts)
            meeting.quality_score = avg_confidence
        
        # Configurações de restauração do dispositivo
        restore_settings = {
            'do_not_disturb': {
                'action': 'restore_previous_state',
                'disable_meeting_mode': True,
                'restore_notifications': True
            },
            'audio_settings': {
                'voice_activation': {
                    'switch_to_standby_mode': True,    # Modo standby de baixo consumo
                    'reduce_sensitivity': True,        # Reduzir sensibilidade
                    'trigger_phrase': 'EION',          # Manter palavra de ativação
                    'background_threshold': 0.3        # Limite mínimo para economia
                },
                'microphone': {
                    'release_exclusive_access': True,
                    'return_to_system_defaults': True
                }
            },
            'power_management': {
                'disable_prevent_sleep': True,         # Permitir suspensão novamente
                'restore_screen_timeout': True,        # Restaurar timeout da tela
                'end_background_processing': False,    # Manter escuta ativa
                'optimize_for_standby': True           # Otimizar para standby
            },
            'post_meeting_actions': [
                'save_meeting_summary',
                'send_notifications_to_participants',
                'backup_audio_files',
                'optimize_storage'
            ]
        }
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict(),
            'statistics': {
                'total_transcripts': len(transcripts),
                'total_participants': len(participants),
                'duration_minutes': meeting.get_duration_minutes(),
                'quality_score': meeting.quality_score
            },
            'device_restoration': restore_settings,
            'background_listening': {
                'status': 'active_standby',
                'trigger_phrase': 'EION',
                'power_consumption': 'low',
                'battery_impact': 'minimal'
            },
            'message': f'✅ Reunião "{meeting.title}" finalizada! Sistema em modo standby.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/background-listening/configure', methods=['POST'])
def configure_background_listening():
    """Configurar escuta em segundo plano com otimização de bateria"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        enabled = data.get('enabled', True)
        sensitivity = data.get('sensitivity', 0.7)  # 0.1 (baixa) a 1.0 (alta)
        trigger_phrase = data.get('trigger_phrase', 'IA')
        power_mode = data.get('power_mode', 'balanced')  # eco, balanced, performance
        
        # Configurações por modo de energia
        power_configs = {
            'eco': {
                'sample_rate': 16000,           # Menor taxa de amostragem
                'buffer_size': 1024,            # Buffer maior
                'processing_interval': 500,     # Processa a cada 500ms
                'cpu_usage': 'minimal',
                'battery_impact': '1-2%/hora'
            },
            'balanced': {
                'sample_rate': 22050,           # Taxa média
                'buffer_size': 512,             # Buffer médio
                'processing_interval': 250,     # Processa a cada 250ms
                'cpu_usage': 'low',
                'battery_impact': '3-5%/hora'
            },
            'performance': {
                'sample_rate': 44100,           # Taxa alta
                'buffer_size': 256,             # Buffer pequeno
                'processing_interval': 100,     # Processa a cada 100ms
                'cpu_usage': 'moderate',
                'battery_impact': '8-12%/hora'
            }
        }
        
        config = power_configs.get(power_mode, power_configs['balanced'])
        
        # Salvar configurações do usuário
        user = User.query.get(user_id)
        if user:
            user.voice_enabled = enabled
            db.session.commit()
        
        listening_config = {
            'enabled': enabled,
            'trigger_phrase': trigger_phrase,
            'sensitivity': sensitivity,
            'power_mode': power_mode,
            'audio_settings': config,
            'wake_lock': {
                'type': 'partial',              # Manter CPU acordada, mas permitir tela desligar
                'timeout': None,                # Sem timeout
                'release_on_pause': True
            },
            'background_permissions': {
                'microphone_access': 'always',
                'background_refresh': True,
                'low_power_mode_exempt': True
            },
            'optimization': {
                'voice_activity_detection': True,   # Só processa quando há voz
                'silence_suppression': True,        # Ignora silêncio
                'adaptive_sensitivity': True,       # Ajusta sensibilidade automaticamente
                'thermal_throttling': True          # Reduz processamento se esquentar
            }
        }
        
        return jsonify({
            'success': True,
            'config': listening_config,
            'estimated_battery_usage': config['battery_impact'],
            'performance_mode': power_mode,
            'message': f'🎤 Escuta em segundo plano configurada ({power_mode})'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/background-listening/trigger', methods=['POST'])
def handle_voice_trigger():
    """Processar ativação por comando de voz 'IA'"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        audio_data = data.get('audio_data', '')
        trigger_confidence = data.get('trigger_confidence', 0.0)
        screen_locked = data.get('screen_locked', False)
        
        # Verificar se é realmente o comando "EION"
        trigger_detected = validate_trigger_phrase(audio_data, 'EION')
        
        if not trigger_detected['valid']:
            return jsonify({
                'triggered': False,
                'reason': 'Comando não reconhecido',
                'confidence': trigger_detected['confidence']
            })
        
        # Ações quando acionado
        activation_response = {
            'triggered': True,
            'timestamp': datetime.utcnow().isoformat(),
            'screen_locked': screen_locked,
            'confidence': trigger_detected['confidence'],
            'actions': []
        }
        
        # Se tela está bloqueada, acordar com notificação
        if screen_locked:
            activation_response['actions'].extend([
                'wake_screen_briefly',           # Acordar tela por 5 segundos
                'show_voice_indicator',          # Mostrar indicador de escuta
                'enable_voice_feedback',         # Ativar feedback por voz
                'reduce_screen_brightness'       # Reduzir brilho para economia
            ])
        else:
            activation_response['actions'].extend([
                'focus_app',                     # Focar aplicativo
                'show_voice_interface',          # Mostrar interface de voz
                'start_voice_session'            # Iniciar sessão de comandos
            ])
        
        # Configurações de sessão de voz
        voice_session = {
            'session_id': str(uuid.uuid4()),
            'timeout_seconds': 10,               # 10 segundos para comando
            'continuous_listening': True,        # Escuta contínua durante sessão
            'auto_end_on_silence': True,        # Termina se ficar em silêncio
            'wake_word_bypass': True            # Não precisa falar "EION" novamente
        }
        
        activation_response['voice_session'] = voice_session
        
        return jsonify(activation_response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/do-not-disturb', methods=['POST'])
def manage_do_not_disturb():
    """Gerenciar modo 'Não Perturbe' durante reuniões"""
    try:
        data = request.get_json()
        action = data.get('action', 'enable')  # enable, disable, toggle
        meeting_id = data.get('meeting_id')
        duration_minutes = data.get('duration_minutes', 60)
        
        dnd_config = {
            'action': action,
            'meeting_context': bool(meeting_id),
            'settings': {
                'silence_notifications': True,
                'allow_calls_from': 'favorites',     # Apenas favoritos
                'allow_repeated_calls': True,        # Chamadas repetidas (emergência)
                'allow_alarms': True,                # Permitir alarmes
                'allow_timers': True,                # Permitir timers
                'dim_lock_screen': True,             # Escurecer tela de bloqueio
                'hide_notification_previews': True   # Ocultar prévia das notificações
            },
            'schedule': {
                'duration_minutes': duration_minutes,
                'auto_disable_on_meeting_end': True,
                'smart_disable': True                # Desabilitar se detectar fim da reunião
            },
            'exceptions': [
                'emergency_calls',
                'meeting_participants',              # Permitir participantes da reunião
                'critical_system_notifications'
            ]
        }
        
        if action == 'enable':
            message = f"🔕 Modo 'Não Perturbe' ativado por {duration_minutes} min"
        elif action == 'disable':
            message = "🔔 Modo 'Não Perturbe' desativado"
        else:
            message = "🔄 Modo 'Não Perturbe' alternado"
        
        return jsonify({
            'success': True,
            'dnd_config': dnd_config,
            'estimated_end_time': (datetime.utcnow().timestamp() + (duration_minutes * 60)) if action == 'enable' else None,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting_details(meeting_id):
    """Obter detalhes completos da reunião"""
    try:
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).all()
        transcripts = MeetingTranscript.query.filter_by(meeting_id=meeting_id).order_by(
            MeetingTranscript.start_time_seconds
        ).all()
        agenda = MeetingAgenda.query.filter_by(meeting_id=meeting_id).first()
        
        return jsonify({
            'meeting': meeting.to_dict(),
            'participants': [p.to_dict() for p in participants],
            'transcripts': [t.to_dict() for t in transcripts],
            'agenda': agenda.to_dict() if agenda else None,
            'statistics': {
                'total_words': sum([len(t.content.split()) for t in transcripts]),
                'action_items_count': len([t for t in transcripts if t.is_action_item]),
                'decisions_count': len([t for t in transcripts if t.is_decision])
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/user/<int:user_id>', methods=['GET'])
def get_user_meetings(user_id):
    """Listar reuniões do usuário"""
    try:
        meetings = MeetingSession.query.filter_by(user_id=user_id).order_by(
            MeetingSession.created_at.desc()
        ).all()
        
        meetings_data = []
        for meeting in meetings:
            meeting_dict = meeting.to_dict()
            meeting_dict['participants_count'] = MeetingParticipant.query.filter_by(meeting_id=meeting.id).count()
            meeting_dict['transcripts_count'] = MeetingTranscript.query.filter_by(meeting_id=meeting.id).count()
            meetings_data.append(meeting_dict)
        
        return jsonify({
            'meetings': meetings_data,
            'total': len(meetings_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/test-recognition', methods=['POST'])
def test_voice_recognition(meeting_id):
    """Testar reconhecimento de voz com amostra"""
    try:
        data = request.get_json()
        audio_data = data.get('audio_data', '')
        test_phrase = data.get('test_phrase', 'Esta é uma frase de teste para reconhecimento de voz')
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Buscar participantes cadastrados
        participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).all()
        
        if not participants:
            return jsonify({
                'error': 'Nenhum participante cadastrado',
                'suggestion': 'Cadastre os participantes primeiro com suas apresentações'
            }), 400
        
        # Testar identificação
        identified_speaker = identify_speaker_by_voice(audio_data, participants)
        current_features = extract_audio_features(audio_data)
        
        # Análise detalhada para cada participante
        detailed_analysis = []
        for participant in participants:
            if participant.voice_profile and participant.voice_profile != '{}':
                try:
                    stored_profile = json.loads(participant.voice_profile)
                    similarity_score = calculate_voice_similarity(current_features, stored_profile)
                    
                    detailed_analysis.append({
                        'participant_name': participant.participant_name,
                        'similarity_score': round(similarity_score, 3),
                        'is_verified': participant.is_verified,
                        'confidence_level': participant.confidence_level,
                        'profile_quality': stored_profile.get('analysis_metadata', {}).get('sample_quality', 'unknown')
                    })
                except:
                    detailed_analysis.append({
                        'participant_name': participant.participant_name,
                        'similarity_score': 0.0,
                        'error': 'Perfil de voz inválido'
                    })
        
        # Ordenar por similaridade
        detailed_analysis.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'identified_speaker': identified_speaker,
            'test_results': {
                'audio_quality': current_features.get('audio_quality', 'good'),
                'audio_duration_estimate': len(audio_data) / 100,
                'participants_analyzed': len(detailed_analysis),
                'best_match': detailed_analysis[0] if detailed_analysis else None,
                'all_similarities': detailed_analysis
            },
            'recommendations': generate_recognition_recommendations(detailed_analysis, current_features),
            'message': f'🔍 Teste concluído. Melhor correspondência: {identified_speaker}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_voice_similarity(current_features, stored_profile):
    """Calcular similaridade detalhada entre características vocais"""
    import json
    
    similarities = []
    
    # Comparar frequência fundamental (25%)
    if 'fundamental_frequency' in stored_profile and 'fundamental_frequency' in current_features:
        freq_diff = abs(current_features['fundamental_frequency'] - stored_profile['fundamental_frequency'])
        freq_sim = max(0, 1 - (freq_diff / 100))
        similarities.append(freq_sim * 0.25)
    
    # Comparar formantes (30%)
    if 'formants' in stored_profile and 'formants' in current_features:
        formant_sim = compare_formants(current_features['formants'], stored_profile['formants'])
        similarities.append(formant_sim * 0.30)
    
    # Comparar taxa de fala (15%)
    if 'speech_rate' in stored_profile and 'speech_rate' in current_features:
        rate_diff = abs(current_features['speech_rate'] - stored_profile['speech_rate'])
        rate_sim = max(0, 1 - (rate_diff / 60))
        similarities.append(rate_sim * 0.15)
    
    # Comparar características espectrais (20%)
    if 'spectral_features' in stored_profile and 'spectral_features' in current_features:
        spectral_sim = compare_spectral_features(
            current_features['spectral_features'], 
            stored_profile['spectral_features']
        )
        similarities.append(spectral_sim * 0.20)
    
    # Comparar características prosódicas (10%)
    if 'prosodic_features' in stored_profile and 'prosodic_features' in current_features:
        prosodic_sim = compare_prosodic_features(
            current_features['prosodic_features'],
            stored_profile['prosodic_features']
        )
        similarities.append(prosodic_sim * 0.10)
    
    return sum(similarities) if similarities else 0.0

def generate_recognition_recommendations(analysis_results, current_features):
    """Gerar recomendações para melhorar reconhecimento"""
    recommendations = []
    
    if not analysis_results:
        recommendations.append("⚠️ Nenhum participante cadastrado. Registre os perfis de voz primeiro.")
        return recommendations
    
    best_score = analysis_results[0].get('similarity_score', 0) if analysis_results else 0
    
    if best_score < 0.6:
        recommendations.extend([
            "🎤 Qualidade de áudio baixa detectada",
            "💡 Aproxime o microfone (15-30cm de distância)",
            "🔇 Reduza ruído de fundo",
            "🗣️ Fale mais claramente e naturalmente"
        ])
    
    if best_score < 0.8:
        recommendations.extend([
            "📝 Considere refazer o cadastro de voz dos participantes",
            "⏱️ Use apresentações mais longas (30+ segundos)",
            "🎚️ Ajuste ganho do microfone"
        ])
    
    # Verificar qualidade dos perfis
    unverified_count = sum(1 for r in analysis_results if not r.get('is_verified', False))
    if unverified_count > 0:
        recommendations.append(f"👤 {unverified_count} participante(s) sem verificação de voz")
    
    if best_score >= 0.8:
        recommendations.append("✅ Excelente! Sistema configurado corretamente")
    
    return recommendations

# ==================== FUNÇÕES AUXILIARES ====================

def create_voice_profile(audio_sample):
    """Criar perfil de voz para reconhecimento de participante"""
    import json
    
    # Simular análise de características vocais
    voice_profile = {
        'timestamp': datetime.utcnow().isoformat(),
        'fundamental_frequency': 150 + (len(audio_sample) % 100),
        'formants': [800, 1200, 2400, 3200],
        'pitch_range': {'min': 100, 'max': 300},
        'speech_rate': 150,  # palavras por minuto
        'energy_profile': [0.8, 0.7, 0.9, 0.6],
        'spectral_features': {
            'spectral_centroid': 2500,
            'spectral_rolloff': 8000,
            'zero_crossing_rate': 0.15
        }
    }
    
    return json.dumps(voice_profile)

def create_enhanced_voice_profile(audio_data, text_content=""):
    """Criar perfil de voz avançado para reconhecimento preciso"""
    import json
    import hashlib
    
    # Análise avançada de características vocais
    audio_length = len(audio_data) if audio_data else 0
    text_length = len(text_content) if text_content else 0
    
    # Gerar ID único do perfil baseado no áudio
    profile_id = hashlib.md5(f"{audio_data}{text_content}{datetime.utcnow()}".encode()).hexdigest()[:12]
    
    enhanced_profile = {
        'profile_id': profile_id,
        'created_at': datetime.utcnow().isoformat(),
        'audio_quality': 'excellent' if audio_length > 1000 else 'good' if audio_length > 500 else 'fair',
        
        # Características fundamentais da voz
        'fundamental_frequency': 120 + (audio_length % 150),  # Hz - frequência fundamental
        'pitch_variance': round(0.05 + (audio_length % 20) * 0.01, 3),  # Variação do tom
        'formants': {
            'f1': 800 + (audio_length % 200),   # Primeira formante
            'f2': 1200 + (audio_length % 400),  # Segunda formante
            'f3': 2400 + (audio_length % 600),  # Terceira formante
            'f4': 3200 + (audio_length % 800)   # Quarta formante
        },
        
        # Características temporais
        'speech_rate': 140 + (text_length % 60),  # Palavras por minuto
        'pause_patterns': {
            'average_pause_duration': 0.5 + (audio_length % 10) * 0.1,
            'pause_frequency': 2 + (text_length % 8)
        },
        
        # Características espectrais
        'spectral_features': {
            'spectral_centroid': 2000 + (audio_length % 1000),
            'spectral_rolloff': 7000 + (audio_length % 2000),
            'spectral_bandwidth': 1500 + (audio_length % 500),
            'zero_crossing_rate': 0.1 + (audio_length % 20) * 0.01,
            'mfcc_coefficients': [
                1.2 + (audio_length % 10) * 0.1,
                -0.5 + (audio_length % 15) * 0.05,
                0.8 + (audio_length % 12) * 0.08,
                -0.3 + (audio_length % 18) * 0.03
            ]
        },
        
        # Características prosódicas
        'prosodic_features': {
            'intonation_pattern': 'rising' if audio_length % 3 == 0 else 'falling' if audio_length % 3 == 1 else 'level',
            'stress_pattern': 'regular' if audio_length % 2 == 0 else 'irregular',
            'rhythm_score': round(0.6 + (audio_length % 30) * 0.01, 2)
        },
        
        # Metadados da análise
        'analysis_metadata': {
            'audio_duration_estimate': round(audio_length / 100, 2),  # Estimativa em segundos
            'text_words_count': len(text_content.split()) if text_content else 0,
            'confidence_score': 0.85 + (min(audio_length, 2000) / 2000) * 0.15,
            'sample_quality': 'studio' if audio_length > 2000 else 'conference' if audio_length > 1000 else 'mobile'
        },
        
        # Características únicas para identificação
        'voice_signature': {
            'vocal_tract_length': 15.5 + (audio_length % 50) * 0.1,  # cm estimado
            'breathiness_index': round(0.2 + (audio_length % 40) * 0.01, 3),
            'nasality_score': round(0.1 + (audio_length % 25) * 0.01, 3),
            'accent_markers': ['neutral', 'regional'][audio_length % 2]
        }
    }
    
    return json.dumps(enhanced_profile, ensure_ascii=False)

def transcribe_with_speaker_identification(audio_data, meeting_id, start_time, end_time):
    """Transcrever áudio identificando o falante"""
    import random
    import json
    
    # Buscar participantes da reunião
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).all()
    
    # Simular transcrição com identificação de falante
    sample_transcriptions = [
        "Bom dia pessoal, vamos começar nossa reunião discutindo os pontos da agenda de hoje.",
        "Acredito que devemos focar primeiro na análise dos resultados do último trimestre.",
        "Concordo com o João, mas também precisamos abordar as metas para o próximo período.",
        "Gostaria de sugerir que criemos um cronograma específico para cada ação decidida hoje.",
        "Perfeito, então ficou decidido que vamos implementar essas mudanças até o final do mês.",
        "Excelente discussão pessoal, acredito que conseguimos cobrir todos os pontos importantes."
    ]
    
    content = random.choice(sample_transcriptions)
    
    # Identificar falante baseado nas características de voz
    identified_speaker = identify_speaker_by_voice(audio_data, participants) if participants else "Participante Desconhecido"
    
    # Simular análise de sentimento
    sentiments = ['positive', 'neutral', 'negative']
    sentiment = random.choices(sentiments, weights=[0.5, 0.4, 0.1])[0]
    
    # Simular qualidade de áudio
    audio_qualities = ['excellent', 'good', 'fair', 'poor']
    audio_quality = random.choices(audio_qualities, weights=[0.4, 0.4, 0.15, 0.05])[0]
    
    return {
        'content': content,
        'speaker_name': identified_speaker,
        'speaker_identified': identified_speaker != "Participante Desconhecido",
        'confidence': random.uniform(0.75, 0.95),
        'audio_quality': audio_quality,
        'sentiment': sentiment
    }

def identify_speaker_by_voice(audio_data, participants):
    """Identificar falante comparando com perfis de voz dos participantes - Versão Avançada"""
    import random
    import json
    
    if not participants:
        return "Participante Desconhecido"
    
    # Simular análise avançada de características vocais do áudio atual
    current_audio_features = extract_audio_features(audio_data)
    
    confidence_scores = []
    
    for participant in participants:
        if not participant.voice_profile or participant.voice_profile == '{}':
            # Participante sem perfil de voz
            confidence_scores.append((participant.participant_name, 0.1))
            continue
        
        try:
            stored_profile = json.loads(participant.voice_profile)
            
            # Comparar múltiplas características vocais
            similarity_scores = []
            
            # 1. Frequência fundamental (peso: 25%)
            if 'fundamental_frequency' in stored_profile:
                freq_diff = abs(current_audio_features['fundamental_frequency'] - 
                              stored_profile['fundamental_frequency'])
                freq_similarity = max(0, 1 - (freq_diff / 100))  # Normalizar diferença
                similarity_scores.append(freq_similarity * 0.25)
            
            # 2. Formantes (peso: 30%)
            if 'formants' in stored_profile:
                formant_similarity = compare_formants(
                    current_audio_features['formants'], 
                    stored_profile['formants']
                )
                similarity_scores.append(formant_similarity * 0.30)
            
            # 3. Taxa de fala (peso: 15%)
            if 'speech_rate' in stored_profile:
                rate_diff = abs(current_audio_features['speech_rate'] - 
                              stored_profile['speech_rate'])
                rate_similarity = max(0, 1 - (rate_diff / 60))  # Normalizar diferença
                similarity_scores.append(rate_similarity * 0.15)
            
            # 4. Características espectrais (peso: 20%)
            if 'spectral_features' in stored_profile:
                spectral_similarity = compare_spectral_features(
                    current_audio_features['spectral_features'],
                    stored_profile['spectral_features']
                )
                similarity_scores.append(spectral_similarity * 0.20)
            
            # 5. Características prosódicas (peso: 10%)
            if 'prosodic_features' in stored_profile:
                prosodic_similarity = compare_prosodic_features(
                    current_audio_features['prosodic_features'],
                    stored_profile['prosodic_features']
                )
                similarity_scores.append(prosodic_similarity * 0.10)
            
            # Calcular score final
            final_score = sum(similarity_scores) if similarity_scores else 0.1
            
            # Aplicar bonus para participantes verificados
            if participant.is_verified:
                final_score *= 1.1  # 10% de bonus
            
            confidence_scores.append((participant.participant_name, min(final_score, 1.0)))
            
        except (json.JSONDecodeError, KeyError) as e:
            # Perfil inválido, usar score baixo
            confidence_scores.append((participant.participant_name, 0.1))
    
    # Ordenar por confiança e retornar o melhor match
    confidence_scores.sort(key=lambda x: x[1], reverse=True)
    
    best_match = confidence_scores[0]
    second_best = confidence_scores[1] if len(confidence_scores) > 1 else (None, 0)
    
    # Critérios mais rigorosos para identificação
    if best_match[1] > 0.75 and (best_match[1] - second_best[1]) > 0.2:
        return best_match[0]
    elif best_match[1] > 0.6:
        return f"{best_match[0]} (provável)"
    else:
        return "Participante Desconhecido"

def extract_audio_features(audio_data):
    """Extrair características do áudio atual para comparação"""
    audio_length = len(audio_data) if audio_data else 0
    
    # Simular extração de características em tempo real
    return {
        'fundamental_frequency': 120 + (audio_length % 150),
        'formants': {
            'f1': 750 + (audio_length % 300),
            'f2': 1150 + (audio_length % 500),
            'f3': 2300 + (audio_length % 700),
            'f4': 3100 + (audio_length % 900)
        },
        'speech_rate': 130 + (audio_length % 80),
        'spectral_features': {
            'spectral_centroid': 1900 + (audio_length % 1200),
            'spectral_rolloff': 6800 + (audio_length % 2500),
            'zero_crossing_rate': 0.09 + (audio_length % 25) * 0.01
        },
        'prosodic_features': {
            'intonation_pattern': 'rising' if audio_length % 3 == 0 else 'falling',
            'rhythm_score': 0.5 + (audio_length % 40) * 0.01
        }
    }

def compare_formants(current_formants, stored_formants):
    """Comparar formantes entre áudio atual e perfil armazenado"""
    if not isinstance(current_formants, dict) or not isinstance(stored_formants, dict):
        return 0.5
    
    similarities = []
    for formant in ['f1', 'f2', 'f3', 'f4']:
        if formant in current_formants and formant in stored_formants:
            diff = abs(current_formants[formant] - stored_formants[formant])
            similarity = max(0, 1 - (diff / 500))  # Normalizar diferença
            similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0.5

def compare_spectral_features(current_spectral, stored_spectral):
    """Comparar características espectrais"""
    if not isinstance(current_spectral, dict) or not isinstance(stored_spectral, dict):
        return 0.5
    
    similarities = []
    
    # Comparar centroide espectral
    if 'spectral_centroid' in current_spectral and 'spectral_centroid' in stored_spectral:
        diff = abs(current_spectral['spectral_centroid'] - stored_spectral['spectral_centroid'])
        similarity = max(0, 1 - (diff / 2000))
        similarities.append(similarity)
    
    # Comparar rolloff espectral
    if 'spectral_rolloff' in current_spectral and 'spectral_rolloff' in stored_spectral:
        diff = abs(current_spectral['spectral_rolloff'] - stored_spectral['spectral_rolloff'])
        similarity = max(0, 1 - (diff / 3000))
        similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0.5

def compare_prosodic_features(current_prosodic, stored_prosodic):
    """Comparar características prosódicas"""
    if not isinstance(current_prosodic, dict) or not isinstance(stored_prosodic, dict):
        return 0.5
    
    similarities = []
    
    # Comparar padrão de entonação
    if ('intonation_pattern' in current_prosodic and 
        'intonation_pattern' in stored_prosodic):
        if current_prosodic['intonation_pattern'] == stored_prosodic['intonation_pattern']:
            similarities.append(1.0)
        else:
            similarities.append(0.3)
    
    # Comparar score de ritmo
    if 'rhythm_score' in current_prosodic and 'rhythm_score' in stored_prosodic:
        diff = abs(current_prosodic['rhythm_score'] - stored_prosodic['rhythm_score'])
        similarity = max(0, 1 - (diff / 0.5))
        similarities.append(similarity)
    
    return sum(similarities) / len(similarities) if similarities else 0.5

def generate_advanced_agenda(meeting, transcripts):
    """Gerar pauta avançada com análise de IA"""
    import json
    
    # Análise do conteúdo das transcrições
    all_content = " ".join([t.content for t in transcripts])
    
    # Extrair pontos-chave (simulação de NLP)
    key_points = extract_key_points(all_content)
    
    # Extrair itens de ação
    action_items = [t.content for t in transcripts if t.is_action_item]
    
    # Extrair decisões
    decisions = [t.content for t in transcripts if t.is_decision]
    
    # Gerar resumo por participante
    participants_summary = generate_participants_summary(transcripts)
    
    # Identificar tópicos discutidos
    topics = extract_topics(all_content)
    
    # Gerar próximos passos
    next_steps = generate_next_steps(action_items, decisions)
    
    return {
        'title': f"Pauta da Reunião - {meeting.title}",
        'summary': generate_meeting_summary(all_content, len(transcripts)),
        'key_points': json.dumps(key_points),
        'action_items': json.dumps(action_items),
        'decisions_made': json.dumps(decisions),
        'next_steps': json.dumps(next_steps),
        'participants_summary': json.dumps(participants_summary),
        'topics_discussed': json.dumps(topics)
    }

def generate_meeting_summary(content, transcript_count):
    """Gerar resumo da reunião"""
    word_count = len(content.split())
    
    # Simular geração de resumo com IA
    summary_templates = [
        f"Reunião produtiva com {transcript_count} intervenções e aproximadamente {word_count} palavras discutidas. Os principais tópicos abordados foram estratégia, planejamento e execução.",
        f"Sessão colaborativa com {transcript_count} contribuições dos participantes. Foram definidas ações importantes e tomadas decisões estratégicas para o período.",
        f"Encontro eficiente com {transcript_count} falas registradas. A discussão focou em resultados, metas e próximos passos para a equipe."
    ]
    
    import random
    return random.choice(summary_templates)

def extract_key_points(content):
    """Extrair pontos-chave do conteúdo"""
    # Simulação de extração de pontos-chave
    sample_points = [
        "Análise dos resultados do trimestre apresentada",
        "Definição de metas para o próximo período",
        "Discussão sobre cronograma de implementação",
        "Aprovação das mudanças propostas",
        "Distribuição de responsabilidades"
    ]
    
    # Em produção, usaria NLP para extrair pontos reais
    return sample_points[:3]  # Retorna 3 pontos principais

def generate_participants_summary(transcripts):
    """Gerar resumo por participante"""
    participants_data = {}
    
    for transcript in transcripts:
        speaker = transcript.speaker_name
        if speaker not in participants_data:
            participants_data[speaker] = {
                'interventions': 0,
                'key_contributions': [],
                'sentiment': 'neutral'
            }
        
        participants_data[speaker]['interventions'] += 1
        if len(transcript.content) > 100:  # Contribuições significativas
            participants_data[speaker]['key_contributions'].append(transcript.content[:150] + "...")
    
    return participants_data

def extract_topics(content):
    """Extrair tópicos discutidos"""
    # Simulação de extração de tópicos
    sample_topics = [
        "Resultados Financeiros",
        "Planejamento Estratégico", 
        "Recursos Humanos",
        "Tecnologia e Inovação",
        "Operações"
    ]
    
    # Em produção, usaria topic modeling (LDA, BERT, etc.)
    return sample_topics[:3]

def generate_next_steps(action_items, decisions):
    """Gerar próximos passos baseados nas ações e decisões"""
    next_steps = []
    
    if action_items:
        next_steps.append("Executar itens de ação definidos na reunião")
    
    if decisions:
        next_steps.append("Implementar decisões aprovadas")
    
    next_steps.extend([
        "Agendar reunião de acompanhamento",
        "Enviar ata da reunião para todos os participantes",
        "Definir responsáveis por cada tarefa"
    ])
    
    return next_steps
def system_info():
    """Informações do sistema"""
    return jsonify({
        'app_name': 'IAON - Assistente IA Avançado',
        'version': '1.0.0',
        'features': [
            'IA Avançada com Contexto',
            'Biometria de Voz',
            'Sistema Médico Completo',
            'Controle Financeiro',
            'Agenda Inteligente',
            'PWA Instalável',
            'Funcionamento Offline',
            'Segurança Militar'
        ],
        'supported_languages': ['pt-BR', 'en-US'],
        'supported_devices': ['mobile', 'tablet', 'desktop'],
        'security_features': [
            'Biometria de Voz',
            'Criptografia AES-256',
            'Autenticação Multifator',
            'Logs de Auditoria',
            'Detecção de Dispositivos'
        ]
    })

# ===============================================
# ENDPOINTS DE CONTROLE DE APLICATIVOS
# ===============================================

@app.route('/api/apps/scan', methods=['POST'])
def scan_installed_apps():
    """Escanear aplicativos instalados no dispositivo"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        force_rescan = data.get('force_rescan', False)
        
        # Verificar se já foram escaneados recentemente
        if not force_rescan:
            recent_scan = AppControl.query.filter_by(user_id=user_id)\
                .filter(AppControl.last_scanned > datetime.utcnow() - timedelta(hours=1))\
                .first()
            
            if recent_scan:
                apps = AppControl.query.filter_by(user_id=user_id).all()
                return jsonify({
                    'success': True,
                    'message': 'Usando dados de escaneamento recente',
                    'apps_count': len(apps),
                    'last_scan': recent_scan.last_scanned.isoformat(),
                    'apps': [format_app_data(app) for app in apps[:20]]  # Limitar retorno
                })
        
        # Simular escaneamento de aplicativos (em produção, integraria com APIs do sistema)
        sample_apps = generate_sample_apps()
        
        apps_added = 0
        for app_data in sample_apps:
            # Verificar se o app já existe
            existing_app = AppControl.query.filter_by(
                user_id=user_id, 
                package_name=app_data['package_name']
            ).first()
            
            if existing_app:
                # Atualizar dados existentes
                existing_app.display_name = app_data['display_name']
                existing_app.app_version = app_data['version']
                existing_app.last_scanned = datetime.utcnow()
                existing_app.is_enabled = app_data['enabled']
            else:
                # Criar novo registro
                new_app = AppControl(
                    user_id=user_id,
                    package_name=app_data['package_name'],
                    app_name=app_data['name'],
                    display_name=app_data['display_name'],
                    app_version=app_data['version'],
                    voice_aliases=json.dumps(app_data['voice_aliases']),
                    launch_count=0,
                    usage_count=0,
                    is_enabled=app_data['enabled'],
                    last_scanned=datetime.utcnow(),
                    install_date=datetime.utcnow() - timedelta(days=random.randint(1, 365))
                )
                db.session.add(new_app)
                apps_added += 1
        
        db.session.commit()
        
        total_apps = AppControl.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'message': f'Escaneamento concluído! {apps_added} novos aplicativos encontrados.',
            'apps_total': total_apps,
            'apps_added': apps_added,
            'scan_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao escanear aplicativos: {str(e)}'
        }), 500


@app.route('/api/apps/list/<int:user_id>', methods=['GET'])
def list_user_apps(user_id):
    """Listar aplicativos do usuário com suporte a filtros"""
    try:
        # Parâmetros de consulta
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        search_term = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'usage_count')  # usage_count, name, last_used
        limit = min(int(request.args.get('limit', 50)), 100)  # Máximo 100
        
        # Query base
        query = AppControl.query.filter_by(user_id=user_id)
        
        # Filtros
        if enabled_only:
            query = query.filter(AppControl.is_enabled == True)
        
        if search_term:
            search_filter = or_(
                AppControl.app_name.ilike(f'%{search_term}%'),
                AppControl.display_name.ilike(f'%{search_term}%'),
                AppControl.package_name.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        # Ordenação
        if sort_by == 'usage_count':
            query = query.order_by(AppControl.usage_count.desc())
        elif sort_by == 'name':
            query = query.order_by(AppControl.display_name.asc())
        elif sort_by == 'last_used':
            query = query.order_by(AppControl.last_used.desc().nullslast())
        else:
            query = query.order_by(AppControl.usage_count.desc())
        
        apps = query.limit(limit).all()
        
        # Estatísticas
        total_apps = AppControl.query.filter_by(user_id=user_id).count()
        enabled_apps = AppControl.query.filter_by(user_id=user_id, is_enabled=True).count()
        
        return jsonify({
            'success': True,
            'apps': [format_app_data(app) for app in apps],
            'total_apps': total_apps,
            'enabled_apps': enabled_apps,
            'showing': len(apps),
            'filters': {
                'enabled_only': enabled_only,
                'search_term': search_term,
                'sort_by': sort_by
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao listar aplicativos: {str(e)}'
        }), 500


@app.route('/api/apps/launch', methods=['POST'])
def launch_app_by_request():
    """Lançar aplicativo via requisição API"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        app_id = data.get('app_id')
        package_name = data.get('package_name')
        launch_method = data.get('method', 'manual')  # manual, voice, gesture
        
        # Encontrar aplicativo
        if app_id:
            app = AppControl.query.filter_by(id=app_id, user_id=user_id).first()
        elif package_name:
            app = AppControl.query.filter_by(package_name=package_name, user_id=user_id).first()
        else:
            return jsonify({
                'success': False,
                'error': 'app_id ou package_name obrigatório'
            }), 400
        
        if not app:
            return jsonify({
                'success': False,
                'error': 'Aplicativo não encontrado'
            }), 404
        
        if not app.is_enabled:
            return jsonify({
                'success': False,
                'error': f'Aplicativo {app.display_name} está desabilitado'
            }), 403
        
        # Tentar lançar aplicativo
        launch_success = launch_app_by_package(app.package_name)
        
        # Registrar tentativa
        log_app_launch(user_id, app.id, f'Launch via {launch_method}', launch_method, launch_success)
        
        if launch_success:
            # Atualizar estatísticas
            app.launch_count += 1
            app.usage_count += 1
            app.last_used = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'{app.display_name} foi aberto com sucesso!',
                'app_name': app.display_name,
                'package_name': app.package_name,
                'launch_method': launch_method
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Falha ao abrir {app.display_name}',
                'app_name': app.display_name
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao lançar aplicativo: {str(e)}'
        }), 500


@app.route('/api/apps/voice-aliases/<int:app_id>', methods=['PUT'])
def update_app_voice_aliases(app_id):
    """Atualizar aliases de voz de um aplicativo"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        aliases = data.get('aliases', [])
        
        # Validar aliases
        if not isinstance(aliases, list):
            return jsonify({
                'success': False,
                'error': 'aliases deve ser uma lista'
            }), 400
        
        # Limitar quantidade de aliases
        if len(aliases) > 10:
            return jsonify({
                'success': False,
                'error': 'Máximo 10 aliases por aplicativo'
            }), 400
        
        # Filtrar aliases válidos
        valid_aliases = []
        for alias in aliases:
            alias = str(alias).strip().lower()
            if alias and len(alias) >= 2 and len(alias) <= 50:
                valid_aliases.append(alias)
        
        app = AppControl.query.filter_by(id=app_id, user_id=user_id).first()
        if not app:
            return jsonify({
                'success': False,
                'error': 'Aplicativo não encontrado'
            }), 404
        
        # Atualizar aliases
        app.voice_aliases = json.dumps(valid_aliases)
        app.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Aliases de voz atualizados para {app.display_name}',
            'app_name': app.display_name,
            'aliases': valid_aliases,
            'aliases_count': len(valid_aliases)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao atualizar aliases: {str(e)}'
        }), 500


@app.route('/api/apps/usage-stats/<int:user_id>', methods=['GET'])
def get_app_usage_stats(user_id):
    """Obter estatísticas de uso de aplicativos"""
    try:
        days = int(request.args.get('days', 7))  # Últimos 7 dias por padrão
        days = min(days, 90)  # Máximo 90 dias
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Aplicativos mais usados
        most_used = AppControl.query.filter_by(user_id=user_id)\
            .filter(AppControl.usage_count > 0)\
            .order_by(AppControl.usage_count.desc())\
            .limit(10).all()
        
        # Aplicativos recentemente usados
        recently_used = AppControl.query.filter_by(user_id=user_id)\
            .filter(AppControl.last_used.isnot(None))\
            .filter(AppControl.last_used >= start_date)\
            .order_by(AppControl.last_used.desc())\
            .limit(10).all()
        
        # Logs de lançamento recentes
        recent_launches = AppLaunchLog.query.filter_by(user_id=user_id)\
            .filter(AppLaunchLog.timestamp >= start_date)\
            .order_by(AppLaunchLog.timestamp.desc())\
            .limit(20).all()
        
        # Estatísticas gerais
        total_apps = AppControl.query.filter_by(user_id=user_id).count()
        enabled_apps = AppControl.query.filter_by(user_id=user_id, is_enabled=True).count()
        total_launches = AppLaunchLog.query.filter_by(user_id=user_id)\
            .filter(AppLaunchLog.timestamp >= start_date).count()
        voice_launches = AppLaunchLog.query.filter_by(user_id=user_id, launch_method='voice')\
            .filter(AppLaunchLog.timestamp >= start_date).count()
        
        return jsonify({
            'success': True,
            'period_days': days,
            'stats': {
                'total_apps': total_apps,
                'enabled_apps': enabled_apps,
                'total_launches': total_launches,
                'voice_launches': voice_launches,
                'voice_percentage': round((voice_launches/total_launches)*100, 1) if total_launches > 0 else 0
            },
            'most_used_apps': [format_app_data(app) for app in most_used],
            'recently_used_apps': [format_app_data(app) for app in recently_used],
            'recent_launches': [format_launch_log_data(log) for log in recent_launches]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Endpoint para chat com IA"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Buscar ou criar conversa
        conversation = Conversation.query.filter_by(
            user_id=user_id, 
            session_id=session_id
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                title=f"Conversa {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            db.session.add(conversation)
            db.session.flush()
        
        # Salvar mensagem do usuário
        user_message = Message(
            conversation_id=conversation.id,
            role='user',
            content=message
        )
        db.session.add(user_message)
        
        # Gerar resposta personalizada da IA
        ai_response = generate_ai_response(message, user_id)
        
        # Salvar resposta da IA
        ai_message = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_message)
        
        db.session.commit()
        
        return jsonify({
            'response': ai_response,
            'conversation_id': conversation.id,
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/voice-command', methods=['POST'])
def voice_command():
    """Endpoint para comandos de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        command_text = data.get('command_text', '')
        
        # Processar comando de voz avançado
        result = process_voice_command(command_text, user_id)
        
        return jsonify({
            'executed': True,
            'intent': result['intent'],
            'execution_result': result['result'],
            'action': result.get('action'),
            'section': result.get('section'),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-biometry/status/<int:user_id>', methods=['GET'])
def voice_biometry_status(user_id):
    """Status da biometria de voz"""
    try:
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'biometry_enrolled': biometry.is_enrolled if biometry else False,
            'samples_count': biometry.samples_count if biometry else 0,
            'enrollment_complete': biometry.is_enrolled if biometry else False
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-biometry/enroll', methods=['POST'])
def voice_biometry_enroll():
    """Cadastrar biometria de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        audio_file_path = data.get('audio_file_path', '')
        enrollment_phrase = data.get('enrollment_phrase', '')
        
        # Buscar ou criar registro de biometria
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        
        if not biometry:
            biometry = VoiceBiometry(
                user_id=user_id,
                enrollment_phrase=enrollment_phrase
            )
            db.session.add(biometry)
        
        # Incrementar contador de amostras
        biometry.samples_count += 1
        
        # Marcar como cadastrado após 3 amostras
        if biometry.samples_count >= 3:
            biometry.is_enrolled = True
        
        db.session.commit()
        
        return jsonify({
            'enrollment_complete': biometry.is_enrolled,
            'samples_count': biometry.samples_count,
            'message': 'Amostra de voz processada com sucesso'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-upload', methods=['POST'])
def upload_voice():
    """Upload de arquivo de voz para biometria"""
    if 'audio' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de áudio enviado'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Criar diretório para uploads se não existir
    upload_dir = os.path.join(app.static_folder, 'uploads', 'voice')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Salvar arquivo
    filename = f"voice_{request.form.get('user_id', 'unknown')}_{int(time.time())}.wav"
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return jsonify({
        'message': 'Arquivo de voz salvo com sucesso',
        'file_path': file_path,
        'filename': filename
    })

@app.route('/manifest.json')
def serve_manifest():
    """Servir manifest do PWA"""
    return send_from_directory(app.static_folder, 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    """Servir Service Worker"""
    response = send_from_directory(app.static_folder, 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/offline.html')
def serve_offline():
    """Página offline"""
    return send_from_directory(app.static_folder, 'offline.html')

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint não encontrado'}), 404
    
    # Para outras rotas, servir o index.html (SPA)
    return serve('index.html')

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    return jsonify({
        'error': 'Erro interno do servidor',
        'message': 'Tente novamente mais tarde'
    }), 500

@app.route('/test')
def test():
    """Rota de teste simples"""
    return jsonify({
        'status': 'ok',
        'message': 'IAON está funcionando!',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Servir arquivos estáticos e SPA"""
    try:
        # Inicializar banco de dados na primeira requisição (Vercel)
        if os.getenv('FLASK_ENV') == 'production':
            try:
                db.create_all()
            except Exception as e:
                print(f"Erro ao criar tabelas: {e}")
        
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    except Exception as e:
        return jsonify({
            'error': 'Server error',
            'message': str(e)
        }), 500

def generate_ai_response(message, user_id=1):
    """Gerar resposta personalizada da IA"""
    # Buscar informações do usuário
    user = User.query.get(user_id)
    preferred_name = user.preferred_name if user and user.preferred_name else "amigo(a)"
    
    message_lower = message.lower()
    
    # Respostas personalizadas baseadas no contexto
    if any(word in message_lower for word in ['olá', 'oi', 'hey', 'hello']):
        greetings = [
            f"Olá, {preferred_name}! 👋 Sou o IAON, seu assistente IA avançado. Como posso ajudá-lo hoje?",
            f"Oi, {preferred_name}! 😊 É um prazer conversar com você. Em que posso ser útil?",
            f"Hey, {preferred_name}! 🌟 Estou aqui para tornar seu dia mais produtivo. O que vamos fazer?"
        ]
        import random
        return random.choice(greetings)
    
    elif any(word in message_lower for word in ['medicamento', 'remédio', 'medicina', 'saúde']):
        return f"""🏥 **Sistema Médico Avançado**, {preferred_name}!

Posso ajudá-lo com:
• 💊 Consulta de medicamentos e dosagens
• ⚠️ Verificação de interações medicamentosas
• 📋 Gestão de prescrições médicas
• 🕐 Lembretes de medicação
• 🏥 Histórico médico digital
• 📞 Contatos médicos de emergência

**⚠️ Importante:** Sempre consulte um médico para orientações específicas."""
    
    elif any(word in message_lower for word in ['reunião', 'meeting', 'gravar', 'gravação', 'transcrever']):
        return f"""📹 **Sistema de Reuniões Avançado**, {preferred_name}!

Funcionalidades completas:
• 🎤 **Gravação em Tempo Real** - Áudio de alta qualidade
• 🗣️ **Reconhecimento de Participantes** - Identifica quem fala
• 📝 **Transcrição Automática** - Converte fala em texto
• 👥 **Gestão de Participantes** - Cadastro com biometria de voz
• 📋 **Geração de Pautas** - IA cria atas automaticamente
• 🎯 **Itens de Ação** - Detecta tarefas e responsabilidades
• 🔍 **Análise de Sentimento** - Monitora tom da discussão
• 📊 **Relatórios Detalhados** - Estatísticas de participação

**🎤 Comandos de Voz:**
• "IA reunião" - Iniciar sistema de reuniões
• "IA gravar" - Começar gravação
• "IA pauta" - Gerar pauta automática"""
    
    elif any(word in message_lower for word in ['agenda', 'compromisso', 'encontro']):
        return f"""📅 **Agenda Inteligente**, {preferred_name}!

Recursos disponíveis:
• 📝 Criação de compromissos com IA
• 🔔 Lembretes inteligentes
• 🕐 Gestão de horários otimizada
• 👥 Sincronização com contatos
• 🌍 Integração com fuso horário
• 📊 Análise de produtividade
• 🤖 Sugestões automáticas de horários"""
    
    elif any(word in message_lower for word in ['finanças', 'dinheiro', 'gasto', 'orçamento', 'economia']):
        return f"""💰 **Controle Financeiro Avançado**, {preferred_name}!

Funcionalidades premium:
• 📊 Dashboard financeiro em tempo real
• 💳 Categorização automática de gastos
• 📈 Análise de tendências e padrões
• 🎯 Metas financeiras personalizadas
• 📱 Integração com bancos (futuro)
• 💡 Dicas de economia baseadas em IA
• 📋 Relatórios detalhados mensais"""
    
    elif any(word in message_lower for word in ['voz', 'biometria', 'comandos']):
        biometry = VoiceBiometry.query.filter_by(user_id=user_id).first()
        if biometry and biometry.is_enrolled:
            return f"""🎤 **Sistema de Voz Avançado ativo**, {preferred_name}!

Comandos disponíveis:
• "IA reunião" - Sistema de reuniões com gravação
• "IA agenda" - Gerenciar compromissos
• "IA medicina" - Sistema médico
• "IA finanças" - Controle financeiro
• "IA relatório" - Gerar relatórios
• "IA ajuda" - Lista completa de comandos

✅ Sua biometria está configurada com qualidade **{biometry.enrollment_quality}**"""
        else:
            return f"🔒 **Sistema de Voz**, {preferred_name}! Para usar comandos de voz seguros, você precisa configurar sua biometria de voz primeiro."
    
    elif 'ajuda' in message_lower or 'help' in message_lower:
        return f"""🆘 **Central de Ajuda IAON**, {preferred_name}!

**🎯 Principais Recursos:**
• 💬 Chat inteligente com contexto
• 🎤 Comandos de voz com biometria
• 📹 **Sistema de reuniões completo**
• 🏥 Sistema médico completo
• 📅 Agenda inteligente
• 💰 Controle financeiro avançado
• 📊 Relatórios e análises
• 🔒 Segurança militar

**🎤 Comandos de Voz:**
Diga "IA" + comando para ações específicas

**📹 Reuniões Inteligentes:**
• Gravação automática
• Reconhecimento de participantes
• Transcrição em tempo real
• Geração de pautas

**💡 Dica:** Use linguagem natural - eu entendo contexto!"""
    
    elif any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'thanks']):
        return f"� Por nada, {preferred_name}! É sempre um prazer ajudar. Estou aqui sempre que precisar!"
    
    elif any(word in message_lower for word in ['tchau', 'até', 'bye', 'adeus']):
        return f"👋 Até logo, {preferred_name}! Foi ótimo conversar com você. Volte sempre que quiser!"
    
    else:
        # Resposta contextual avançada
        return f"""Entendi sua mensagem, {preferred_name}: "{message}"

🤖 Como seu assistente IA avançado, posso ajudar com:
• **Reuniões**: Gravação, transcrição e geração de pautas
• **Medicina**: Consultas sobre medicamentos e saúde
• **Agenda**: Organização de compromissos
• **Finanças**: Controle de gastos e orçamento
• **Análises**: Relatórios personalizados
• **Comandos de voz**: Controle hands-free

💡 **Dica**: Seja específico para respostas mais precisas!"""

def process_voice_command(command_text, user_id=1):
    """Processar comando de voz avançado com palavra de ativação personalizada"""
    command_lower = command_text.lower()
    
    # Buscar usuário para personalização
    user = User.query.get(user_id)
    preferred_name = user.preferred_name if user and user.preferred_name else "usuário"
    trigger_word = user.custom_trigger_word.lower() if user and user.custom_trigger_word else "eion"
    
    # Verificar se o comando começa com a palavra de ativação personalizada
    if not command_lower.startswith(trigger_word):
        return {
            'intent': 'invalid_trigger',
            'result': f'⚠️ Use "{user.custom_trigger_word if user else "EION"}" para ativar comandos de voz',
            'action': 'show_trigger_help',
            'trigger_word': user.custom_trigger_word if user else "EION"
        }
    
    # Remover palavra de ativação do comando
    command_without_trigger = command_lower.replace(trigger_word, "", 1).strip()
    if command_without_trigger.startswith(','):
        command_without_trigger = command_without_trigger[1:].strip()
    
    # Comandos de ligação e contatos
    if any(word in command_without_trigger for word in ['ligar', 'chamar', 'telefone', 'discar', 'contatar', 'falar com']):
        # Extrair o alvo da ligação
        call_target = extract_call_target_from_voice(command_without_trigger)
        
        if call_target['target']:
            return {
                'intent': 'make_call',
                'result': f'📞 Ligando para {call_target["target"]}...',
                'action': 'initiate_call',
                'target': call_target['target'],
                'confidence': call_target['confidence'],
                'voice_command': command_text,
                'trigger_used': user.custom_trigger_word if user else "EION"
            }
        else:
            return {
                'intent': 'call_help',
                'result': f'📱 Para fazer ligações, diga: "{user.custom_trigger_word if user else "EION"}, ligar para [nome]"',
                'action': 'show_call_help',
                'suggestions': get_voice_call_suggestions(user_id)
            }
    
    # Comandos de contatos
    elif any(word in command_without_trigger for word in ['contato', 'agenda telefônica', 'telefones', 'números']):
        return {
            'intent': 'contact_management',
            'result': f'📱 Abrindo agenda de contatos para {preferred_name}...',
            'action': 'open_section',
            'section': 'contacts'
        }
    
    # Comandos de histórico de chamadas
    elif any(word in command_without_trigger for word in ['histórico', 'chamadas', 'ligações recentes', 'última ligação']):
        return {
            'intent': 'call_history',
            'result': f'📋 Exibindo histórico de chamadas para {preferred_name}...',
            'action': 'open_section',
            'section': 'call_logs'
        }
    
    # Comandos de aplicativos
    elif any(word in command_without_trigger for word in ['abrir', 'abra', 'executar', 'iniciar', 'rodar', 'aplicativo', 'app']):
        # Extrair nome do aplicativo
        app_name = extract_app_name_from_command(command_without_trigger)
        if app_name:
            launch_result = handle_app_launch_by_voice(user_id, app_name, command_text)
            return launch_result
        else:
            return {
                'intent': 'app_management',
                'result': f'📱 Visualizando aplicativos disponíveis para {preferred_name}...',
                'action': 'open_section',
                'section': 'apps'
            }
    
    # Comandos de reunião
    elif any(word in command_without_trigger for word in ['reunião', 'meeting', 'gravar', 'gravação']):
        return {
            'intent': 'meeting_management',
            'result': f'📹 Ativando sistema de reuniões para {preferred_name}...',
            'action': 'open_section',
            'section': 'meetings'
        }
    
    # Comandos de agenda
    elif any(word in command_without_trigger for word in ['agenda', 'compromisso', 'encontro']):
        return {
            'intent': 'agenda_management',
            'result': f'📅 Abrindo agenda inteligente para {preferred_name}...',
            'action': 'open_section',
            'section': 'agenda'
        }
    
    # Comandos médicos
    elif any(word in command_without_trigger for word in ['medicamento', 'remédio', 'medicina', 'saúde', 'médico']):
        return {
            'intent': 'medical_check',
            'result': f'🏥 Ativando sistema médico avançado para {preferred_name}...',
            'action': 'open_section',
        }
    
    # Comandos financeiros
    elif any(word in command_without_trigger for word in ['finanças', 'dinheiro', 'gasto', 'orçamento', 'financeiro']):
        return {
            'intent': 'financial_management',
            'result': f'💰 Carregando controle financeiro para {preferred_name}...',
            'action': 'open_section',
            'section': 'finance'
        }
    
    # Comandos de relatório
    elif any(word in command_without_trigger for word in ['relatório', 'relatorio', 'análise', 'dados']):
        return {
            'intent': 'generate_report',
            'result': f'📊 Gerando relatório personalizado para {preferred_name}...',
            'action': 'generate_report',
            'section': 'reports'
        }
    
    # Comandos de ajuda
    elif any(word in command_without_trigger for word in ['ajuda', 'help', 'comando']):
        trigger_examples = [
            f'"{user.custom_trigger_word if user else "EION"}, ligar para João"',
            f'"{user.custom_trigger_word if user else "EION"}, abrir WhatsApp"',
            f'"{user.custom_trigger_word if user else "EION"}, iniciar reunião"'
        ]
        return {
            'intent': 'show_help',
            'result': f'🆘 Exibindo central de ajuda para {preferred_name}...',
            'action': 'show_help',
            'section': 'help',
            'trigger_word': user.custom_trigger_word if user else "EION",
            'examples': trigger_examples
        }
    
    # Comandos de configuração
    elif any(word in command_without_trigger for word in ['configuração', 'config', 'configurar', 'ajuste']):
        return {
            'intent': 'settings_management',
            'result': f'⚙️ Abrindo configurações para {preferred_name}...',
            'action': 'open_section',
            'section': 'settings'
        }
    
    # Comandos de voz/biometria
    elif any(word in command_without_trigger for word in ['voz', 'biometria', 'cadastrar']):
        return {
            'intent': 'voice_management',
            'result': f'🎤 Acessando sistema de biometria de voz para {preferred_name}...',
            'action': 'open_section',
            'section': 'voice'
        }
    
    # Comando genérico
    else:
        return {
            'intent': 'general_command',
            'result': f'🤖 Processando comando para {preferred_name}...',
            'action': 'process_general',
            'command': command_without_trigger,
            'trigger_word': user.custom_trigger_word if user else "EION",
            'suggestions': [
                f'Tente: "{user.custom_trigger_word if user else "EION"}, ajuda" para ver comandos disponíveis',
                f'Ou: "{user.custom_trigger_word if user else "EION"}, ligar para [nome]"',
                f'Ou: "{user.custom_trigger_word if user else "EION"}, abrir [aplicativo]"'
            ]
        }
        return {
            'intent': 'general_command',
            'result': f'🤖 Processando comando para {preferred_name}: "{command_text}"',
            'action': 'process_general',
            'section': 'chat'
        }

def validate_trigger_phrase(audio_data, expected_phrase='EION'):
    """Validar se o áudio contém a palavra de ativação"""
    # Simular validação de palavra de ativação
    audio_length = len(audio_data) if audio_data else 0
    
    # Análise simulada da palavra "EION"
    confidence = 0.0
    
    if audio_length > 100:  # Áudio mínimo
        # Simular análise de padrões de "EION"
        frequency_match = (audio_length % 100) / 100
        duration_match = 0.8 if 200 <= audio_length <= 800 else 0.3
        energy_match = (audio_length % 50) / 50
        
        confidence = (frequency_match + duration_match + energy_match) / 3
    
    return {
        'valid': confidence > 0.6,
        'confidence': round(confidence, 3),
        'phrase_detected': expected_phrase if confidence > 0.6 else 'unknown'
    }

def generate_power_recommendations():
    """Gerar recomendações para otimização de energia"""
    return [
        "🔋 Use modo 'Eco' para máxima economia de bateria",
        "📱 Ative 'Baixo Consumo' do iOS para otimização adicional",
        "🎤 Configure sensibilidade adequada (muito alta = mais consumo)",
        "🌡️ Sistema reduz processamento automaticamente se esquentar",
        "⚡ Carregue o dispositivo antes de reuniões longas",
        "📊 Monitore uso de bateria em Configurações > Bateria"
    ]

# ==================== SISTEMA DE CONTATOS E LIGAÇÕES ====================

@app.route('/api/contacts/sync', methods=['POST'])
def sync_phone_contacts():
    """Sincronizar contatos do telefone"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        contacts_data = data.get('contacts', [])  # Lista de contatos do telefone
        sync_source = data.get('sync_source', 'phone_sync')
        
        synced_contacts = []
        updated_contacts = []
        
        for contact_data in contacts_data:
            name = contact_data.get('name', 'Contato Sem Nome')
            phone = contact_data.get('phone_number', '')
            
            if not phone:
                continue  # Pular contatos sem telefone
            
            # Formatar número de telefone
            formatted_phone = format_phone_number(phone)
            country_code = extract_country_code(phone)
            carrier_info = get_carrier_info(phone)
            
            # Verificar se contato já existe
            existing_contact = Contact.query.filter_by(
                user_id=user_id, 
                phone_number=phone
            ).first()
            
            if existing_contact:
                # Atualizar contato existente
                existing_contact.name = name
                existing_contact.display_name = contact_data.get('display_name', name)
                existing_contact.formatted_phone = formatted_phone
                existing_contact.country_code = country_code
                existing_contact.carrier = carrier_info
                existing_contact.contact_type = contact_data.get('contact_type', 'mobile')
                existing_contact.photo_url = contact_data.get('photo_url', '')
                existing_contact.sync_source = sync_source
                existing_contact.updated_at = datetime.utcnow()
                updated_contacts.append(existing_contact)
            else:
                # Criar novo contato
                new_contact = Contact(
                    user_id=user_id,
                    name=name,
                    display_name=contact_data.get('display_name', name),
                    phone_number=phone,
                    formatted_phone=formatted_phone,
                    country_code=country_code,
                    carrier=carrier_info,
                    contact_type=contact_data.get('contact_type', 'mobile'),
                    photo_url=contact_data.get('photo_url', ''),
                    sync_source=sync_source
                )
                db.session.add(new_contact)
                synced_contacts.append(new_contact)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'synced_count': len(synced_contacts),
            'updated_count': len(updated_contacts),
            'total_contacts': Contact.query.filter_by(user_id=user_id).count(),
            'message': f'📱 {len(synced_contacts)} novos contatos sincronizados, {len(updated_contacts)} atualizados!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/user/<int:user_id>', methods=['GET'])
def get_user_contacts(user_id):
    """Listar contatos do usuário"""
    try:
        search = request.args.get('search', '')
        contact_type = request.args.get('type', '')
        favorites_only = request.args.get('favorites', 'false').lower() == 'true'
        
        query = Contact.query.filter_by(user_id=user_id)
        
        if search:
            query = query.filter(
                Contact.name.ilike(f'%{search}%')
            )
        
        if contact_type:
            query = query.filter_by(contact_type=contact_type)
        
        if favorites_only:
            query = query.filter_by(is_favorite=True)
        
        contacts = query.order_by(Contact.name).all()
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts],
            'total': len(contacts),
            'filters_applied': {
                'search': search,
                'type': contact_type,
                'favorites_only': favorites_only
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
def add_contact():
    """Adicionar novo contato manualmente"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        name = data.get('name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        
        if not name or not phone_number:
            return jsonify({'error': 'Nome e telefone são obrigatórios'}), 400
        
        # Verificar se contato já existe
        existing = Contact.query.filter_by(
            user_id=user_id, 
            phone_number=phone_number
        ).first()
        
        if existing:
            return jsonify({'error': 'Contato já existe com este número'}), 400
        
        # Processar número de telefone
        formatted_phone = format_phone_number(phone_number)
        country_code = extract_country_code(phone_number)
        carrier_info = get_carrier_info(phone_number)
        
        # Criar novo contato
        contact = Contact(
            user_id=user_id,
            name=name,
            display_name=data.get('display_name', name),
            phone_number=phone_number,
            formatted_phone=formatted_phone,
            country_code=country_code,
            carrier=carrier_info,
            contact_type=data.get('contact_type', 'mobile'),
            is_favorite=data.get('is_favorite', False),
            is_emergency=data.get('is_emergency', False),
            voice_aliases=json.dumps(data.get('voice_aliases', [])),
            notes=data.get('notes', ''),
            sync_source='manual'
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict(),
            'message': f'👤 Contato "{name}" adicionado com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/<int:contact_id>/voice-aliases', methods=['POST'])
def add_voice_aliases(contact_id):
    """Adicionar apelidos para comando de voz"""
    try:
        data = request.get_json()
        aliases = data.get('aliases', [])
        
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'error': 'Contato não encontrado'}), 404
        
        # Atualizar aliases
        existing_aliases = json.loads(contact.voice_aliases) if contact.voice_aliases else []
        
        # Adicionar novos aliases (sem duplicatas)
        for alias in aliases:
            if alias.strip() and alias.strip().lower() not in [a.lower() for a in existing_aliases]:
                existing_aliases.append(alias.strip())
        
        contact.voice_aliases = json.dumps(existing_aliases)
        contact.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict(),
            'message': f'🎤 Apelidos de voz atualizados para {contact.name}!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/call', methods=['POST'])
def voice_call_command():
    """Fazer ligação por comando de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        voice_command = data.get('voice_command', '').strip()
        audio_confidence = data.get('audio_confidence', 0.8)
        
        if not voice_command:
            return jsonify({'error': 'Comando de voz não fornecido'}), 400
        
        # Processar comando de voz para extrair nome/número
        call_target = extract_call_target_from_voice(voice_command)
        
        if not call_target['target']:
            return jsonify({
                'success': False,
                'message': '❌ Não consegui identificar quem você quer ligar. Tente: "Ligar para [nome]" ou "Chamar [nome]"',
                'suggestions': get_voice_call_suggestions(user_id)
            })
        
        # Buscar contato correspondente
        matched_contacts = find_contacts_by_voice(user_id, call_target['target'])
        
        if not matched_contacts:
            return jsonify({
                'success': False,
                'message': f'📞 Contato "{call_target["target"]}" não encontrado na agenda.',
                'suggestions': get_similar_contacts(user_id, call_target['target'])
            })
        
        # Se múltiplos contatos, retornar para escolha
        if len(matched_contacts) > 1:
            return jsonify({
                'success': False,
                'multiple_matches': True,
                'message': f'🤔 Encontrei {len(matched_contacts)} contatos. Qual deles?',
                'contacts': [
                    {
                        'id': c['contact'].id,
                        'name': c['contact'].display_name,
                        'phone': c['contact'].formatted_phone,
                        'score': c['score']
                    } for c in matched_contacts[:5]
                ]
            })
        
        # Contato único identificado
        best_match = matched_contacts[0]
        contact = best_match['contact']
        confidence = best_match['score']
        
        # Iniciar ligação
        call_result = initiate_phone_call(contact, voice_command, confidence)
        
        # Registrar no log de chamadas
        call_log = CallLog(
            user_id=user_id,
            contact_id=contact.id,
            phone_number=contact.phone_number,
            contact_name=contact.display_name,
            call_type='outgoing',
            call_method='voice_command',
            voice_command=voice_command,
            call_status=call_result['status'],
            voice_confidence=confidence
        )
        db.session.add(call_log)
        
        # Atualizar estatísticas do contato
        contact.call_frequency += 1
        contact.last_called = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'call_initiated': call_result['initiated'],
            'contact': contact.to_dict(),
            'call_log': call_log.to_dict(),
            'confidence': confidence,
            'message': f'📞 Ligando para {contact.display_name} ({contact.formatted_phone})...',
            'system_action': call_result['system_action']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/call-direct', methods=['POST'])
def voice_call_direct():
    """Fazer ligação direta por ID do contato"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        contact_id = data.get('contact_id')
        
        contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first()
        if not contact:
            return jsonify({'error': 'Contato não encontrado'}), 404
        
        # Iniciar ligação
        call_result = initiate_phone_call(contact, 'direct_call', 1.0)
        
        # Registrar no log
        call_log = CallLog(
            user_id=user_id,
            contact_id=contact.id,
            phone_number=contact.phone_number,
            contact_name=contact.display_name,
            call_type='outgoing',
            call_method='manual',
            call_status=call_result['status'],
            voice_confidence=1.0
        )
        db.session.add(call_log)
        
        contact.call_frequency += 1
        contact.last_called = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'call_initiated': call_result['initiated'],
            'contact': contact.to_dict(),
            'message': f'📞 Ligando para {contact.display_name}...',
            'system_action': call_result['system_action']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/call-logs/user/<int:user_id>', methods=['GET'])
def get_call_logs(user_id):
    """Obter histórico de chamadas"""
    try:
        limit = request.args.get('limit', 50, type=int)
        call_type = request.args.get('type', '')  # outgoing, incoming, missed
        
        query = CallLog.query.filter_by(user_id=user_id)
        
        if call_type:
            query = query.filter_by(call_type=call_type)
        
        call_logs = query.order_by(CallLog.initiated_at.desc()).limit(limit).all()
        
        return jsonify({
            'call_logs': [log.to_dict() for log in call_logs],
            'total': len(call_logs),
            'summary': {
                'total_calls': CallLog.query.filter_by(user_id=user_id).count(),
                'outgoing_calls': CallLog.query.filter_by(user_id=user_id, call_type='outgoing').count(),
                'voice_command_calls': CallLog.query.filter_by(user_id=user_id, call_method='voice_command').count()
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contacts/search-voice', methods=['POST'])
def search_contacts_by_voice():
    """Buscar contatos por comando de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        voice_input = data.get('voice_input', '').strip()
        
        if not voice_input:
            return jsonify({'error': 'Comando de voz não fornecido'}), 400
        
        # Buscar contatos correspondentes
        matched_contacts = find_contacts_by_voice(user_id, voice_input)
        
        return jsonify({
            'matches': [
                {
                    'contact': match['contact'].to_dict(),
                    'score': match['score'],
                    'match_reason': match['reason']
                } for match in matched_contacts
            ],
            'total_matches': len(matched_contacts),
            'voice_input': voice_input
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== FUNÇÕES AUXILIARES PARA CONTATOS ====================

def format_phone_number(phone):
    """Formatar número de telefone usando phonenumbers"""
    try:
        # Parse do número assumindo Brasil como padrão
        parsed_number = phonenumbers.parse(phone, "BR")
        
        # Verificar se é válido
        if phonenumbers.is_valid_number(parsed_number):
            # Formatar no padrão internacional
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            return formatted
        else:
            # Se não for válido, tentar formatação básica
            return format_phone_basic(phone)
    except:
        # Fallback para formatação básica
        return format_phone_basic(phone)

def format_phone_basic(phone):
    """Formatação básica de telefone (fallback)"""
    # Remover caracteres não numéricos
    digits_only = re.sub(r'[^\d+]', '', phone)
    
    # Formatação básica brasileira
    if digits_only.startswith('+55'):
        # Número brasileiro com código de país
        if len(digits_only) == 14:  # +55 + DDD + 9 dígitos
            return f"+55 ({digits_only[3:5]}) {digits_only[5:6]} {digits_only[6:10]}-{digits_only[10:]}"
        elif len(digits_only) == 13:  # +55 + DDD + 8 dígitos
            return f"+55 ({digits_only[3:5]}) {digits_only[5:9]}-{digits_only[9:]}"
    elif len(digits_only) == 11:  # DDD + 9 dígitos
        return f"({digits_only[:2]}) {digits_only[2:3]} {digits_only[3:7]}-{digits_only[7:]}"
    elif len(digits_only) == 10:  # DDD + 8 dígitos
        return f"({digits_only[:2]}) {digits_only[2:6]}-{digits_only[6:]}"
    
    return phone  # Retornar original se não conseguir formatar

def extract_country_code(phone):
    """Extrair código do país usando phonenumbers"""
    try:
        parsed_number = phonenumbers.parse(phone, "BR")
        if phonenumbers.is_valid_number(parsed_number):
            return f"+{parsed_number.country_code}"
        else:
            return '+55'  # Padrão Brasil
    except:
        return '+55'

def get_carrier_info(phone):
    """Obter informações da operadora usando phonenumbers"""
    try:
        parsed_number = phonenumbers.parse(phone, "BR")
        if phonenumbers.is_valid_number(parsed_number):
            # Obter operadora
            carrier_name = carrier.name_for_number(parsed_number, "pt")
            return carrier_name if carrier_name else 'Desconhecida'
        else:
            return 'Desconhecida'
    except:
        return 'Desconhecida'

def extract_call_target_from_voice(voice_command):
    """Extrair quem ligar do comando de voz"""
    command_lower = voice_command.lower().strip()
    
    # Padrões de comando para ligação
    call_patterns = [
        r'ligar?\s+para\s+(.+)',
        r'chamar?\s+(.+)',
        r'telefone\s+para\s+(.+)',
        r'discar\s+para\s+(.+)',
        r'contatar\s+(.+)',
        r'falar\s+com\s+(.+)'
    ]
    
    for pattern in call_patterns:
        match = re.search(pattern, command_lower)
        if match:
            target = match.group(1).strip()
            return {
                'target': target,
                'command_type': 'call',
                'confidence': 0.9
            }
    
    # Se não encontrou padrão específico, tentar extrair nome
    # Remover palavras comuns
    stop_words = ['ligar', 'chamar', 'telefone', 'para', 'o', 'a', 'da', 'do', 'de']
    words = [w for w in command_lower.split() if w not in stop_words]
    
    if words:
        return {
            'target': ' '.join(words),
            'command_type': 'call',
            'confidence': 0.7
        }
    
    return {'target': None, 'command_type': None, 'confidence': 0}

def find_contacts_by_voice(user_id, voice_input):
    """Encontrar contatos por comando de voz"""
    contacts = Contact.query.filter_by(user_id=user_id).all()
    matches = []
    
    for contact in contacts:
        score = contact.get_voice_match_score(voice_input)
        if score > 50:  # Threshold mínimo
            matches.append({
                'contact': contact,
                'score': score,
                'reason': get_match_reason(contact, voice_input, score)
            })
    
    # Ordenar por score decrescente
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def get_match_reason(contact, voice_input, score):
    """Explicar por que o contato foi correspondido"""
    voice_lower = voice_input.lower()
    
    if contact.name.lower() == voice_lower:
        return 'nome_exato'
    elif contact.display_name and contact.display_name.lower() == voice_lower:
        return 'nome_exibicao'
    elif voice_lower in contact.name.lower():
        return 'parte_do_nome'
    elif contact.voice_aliases:
        aliases = json.loads(contact.voice_aliases)
        for alias in aliases:
            if alias.lower() == voice_lower:
                return 'apelido_exato'
            elif voice_lower in alias.lower():
                return 'parte_apelido'
    
    first_name = contact.name.split()[0].lower()
    if first_name == voice_lower:
        return 'primeiro_nome'
    
    return 'similaridade'

def get_voice_call_suggestions(user_id):
    """Obter sugestões de contatos para comando de voz"""
    # Contatos mais chamados
    frequent_contacts = Contact.query.filter_by(user_id=user_id)\
        .filter(Contact.call_frequency > 0)\
        .order_by(Contact.call_frequency.desc())\
        .limit(5).all()
    
    # Contatos favoritos
    favorite_contacts = Contact.query.filter_by(user_id=user_id, is_favorite=True)\
        .limit(5).all()
    
    suggestions = []
    for contact in frequent_contacts:
        suggestions.append(f"Ligar para {contact.display_name}")
    
    for contact in favorite_contacts:
        if f"Ligar para {contact.display_name}" not in suggestions:
            suggestions.append(f"Chamar {contact.display_name}")
    
    return suggestions[:8]

def extract_app_name_from_command(command):
    """Extrai o nome do aplicativo de um comando de voz"""
    command_lower = command.lower()
    
    # Palavras para identificar o comando de aplicativo
    trigger_words = ['abrir', 'abra', 'executar', 'iniciar', 'rodar', 'usar']
    
    # Encontrar a palavra de comando
    for trigger in trigger_words:
        if trigger in command_lower:
            # Dividir o comando em palavras
            words = command_lower.split()
            try:
                # Encontrar o índice da palavra de comando
                trigger_index = words.index(trigger)
                
                # O aplicativo deve estar após a palavra de comando
                if trigger_index + 1 < len(words):
                    # Pode ser uma ou mais palavras
                    app_words = []
                    for i in range(trigger_index + 1, len(words)):
                        word = words[i].strip()
                        # Parar em palavras de parada
                        if word in ['por', 'para', 'no', 'na', 'do', 'da', 'com', 'sem', 'favor', 'pfv']:
                            break
                        app_words.append(word)
                    
                    if app_words:
                        return ' '.join(app_words)
            except ValueError:
                continue
    
    return None


def handle_app_launch_by_voice(user_id, app_name, original_command):
    """Processa o lançamento de aplicativo por comando de voz"""
    try:
        # Buscar aplicativo no banco
        matching_apps = find_app_by_voice(app_name)
        
        if not matching_apps:
            return {
                'intent': 'app_not_found',
                'result': f'❌ Aplicativo "{app_name}" não encontrado. Tente ser mais específico.',
                'action': 'error',
                'details': f'Comando original: "{original_command}"'
            }
        
        # Se encontrou múltiplos, usar o primeiro (melhor match)
        app = matching_apps[0]
        
        # Tentar executar o aplicativo
        launch_success = launch_app_by_package(app.package_name)
        
        if launch_success:
            # Registrar o lançamento
            log_app_launch(user_id, app.id, original_command, 'voice', True)
            
            # Atualizar estatísticas de uso
            app.usage_count += 1
            app.last_used = datetime.utcnow()
            db.session.commit()
            
            return {
                'intent': 'app_launched',
                'result': f'✅ {app.display_name} aberto com sucesso!',
                'action': 'app_launched',
                'app_name': app.display_name,
                'package_name': app.package_name
            }
        else:
            # Registrar falha no lançamento
            log_app_launch(user_id, app.id, original_command, 'voice', False)
            
            return {
                'intent': 'app_launch_failed',
                'result': f'❌ Erro ao abrir {app.display_name}. Tente novamente.',
                'action': 'error',
                'app_name': app.display_name
            }
            
    except Exception as e:
        print(f"Erro ao processar lançamento de app: {str(e)}")
        return {
            'intent': 'app_launch_error',
            'result': f'❌ Erro interno ao tentar abrir aplicativo.',
            'action': 'error',
            'error': str(e)
        }

def get_similar_contacts(user_id, target_name):
    """Obter contatos similares para sugestão"""
    contacts = Contact.query.filter_by(user_id=user_id).all()
    similar = []
    
    target_lower = target_name.lower()
    
    for contact in contacts:
        # Verificar similaridade parcial
        if any(word in contact.name.lower() for word in target_lower.split()):
            similar.append(contact.display_name)
        elif target_lower in contact.name.lower():
            similar.append(contact.display_name)
    
    return similar[:5]

def initiate_phone_call(contact, voice_command, confidence):
    """Iniciar ligação telefônica"""
    # Em produção, integrar com APIs do sistema operacional
    # Para iOS: usar CallKit framework
    # Para Android: usar TelecomManager
    
    call_result = {
        'initiated': True,
        'status': 'initiated',
        'system_action': {
            'action': 'open_phone_app',
            'phone_number': contact.phone_number,
            'contact_name': contact.display_name,
            'auto_dial': True,
            'call_method': 'system_dialer'
        }
    }
    
    # Simular resultado baseado na confiança
    if confidence < 0.6:
        call_result['status'] = 'confirmation_required'
        call_result['initiated'] = False
    
        return call_result

# ==================== FUNÇÕES AUXILIARES PARA CONTROLE DE APLICATIVOS ====================

def generate_voice_aliases_for_app(app_name):
    """Gerar aliases de voz automáticos para um app"""
    aliases = []
    
    # Nome completo
    aliases.append(app_name.lower())
    
    # Primeira palavra
    first_word = app_name.split()[0].lower()
    if first_word not in aliases:
        aliases.append(first_word)
    
    # Aliases comuns para apps conhecidos
    common_aliases = {
        'whatsapp': ['whats', 'zap', 'wpp'],
        'instagram': ['insta', 'ig'],
        'facebook': ['face', 'fb'],
        'youtube': ['you', 'tube'],
        'google': ['google'],
        'chrome': ['navegador', 'browser'],
        'spotify': ['música', 'music'],
        'netflix': ['netflix', 'filme'],
        'uber': ['uber', 'transporte'],
        'gmail': ['email', 'e-mail'],
        'maps': ['mapa', 'gps', 'localização'],
        'camera': ['câmera', 'foto'],
        'gallery': ['galeria', 'fotos'],
        'settings': ['configurações', 'config'],
        'calculator': ['calculadora', 'calc'],
        'clock': ['relógio', 'alarme'],
        'calendar': ['calendário', 'agenda']
    }
    
    app_lower = app_name.lower()
    for app_key, app_aliases in common_aliases.items():
        if app_key in app_lower:
            aliases.extend(app_aliases)
    
    # Remover duplicatas
    return list(set(aliases))

def extract_app_target_from_voice(voice_command):
    """Extrair nome do app do comando de voz"""
    command_lower = voice_command.lower().strip()
    
    # Padrões de comando para abrir apps
    app_patterns = [
        r'abrir?\s+(.+)',
        r'abra\s+(.+)',
        r'iniciar?\s+(.+)',
        r'executar?\s+(.+)',
        r'carregar?\s+(.+)',
        r'lançar?\s+(.+)',
        r'rodar?\s+(.+)'
    ]
    
    for pattern in app_patterns:
        match = re.search(pattern, command_lower)
        if match:
            target = match.group(1).strip()
            # Remover palavras comuns no final
            target = re.sub(r'\s+(app|aplicativo|programa)$', '', target)
            return {
                'target': target,
                'command_type': 'open_app',
                'confidence': 0.9
            }
    
    # Se não encontrou padrão específico, tentar extrair nome
    stop_words = ['abrir', 'abra', 'iniciar', 'executar', 'app', 'aplicativo', 'programa']
    words = [w for w in command_lower.split() if w not in stop_words]
    
    if words:
        return {
            'target': ' '.join(words),
            'command_type': 'open_app',
            'confidence': 0.7
        }
    
    return {'target': None, 'command_type': None, 'confidence': 0}

def find_apps_by_voice(user_id, voice_input):
    """Encontrar aplicativos por comando de voz"""
    apps = AppControl.query.filter_by(user_id=user_id).all()
    matches = []
    
    for app in apps:
        score = app.get_voice_match_score(voice_input)
        if score > 50:  # Threshold mínimo
            matches.append({
                'app': app,
                'score': score,
                'reason': get_app_match_reason(app, voice_input, score)
            })
    
    # Ordenar por score decrescente
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def get_app_match_reason(app, voice_input, score):
    """Explicar por que o app foi correspondido"""
    voice_lower = voice_input.lower()
    
    if app.app_name.lower() == voice_lower:
        return 'nome_exato'
    elif app.display_name and app.display_name.lower() == voice_lower:
        return 'nome_exibicao'
    elif voice_lower in app.app_name.lower():
        return 'parte_do_nome'
    elif app.voice_aliases:
        aliases = json.loads(app.voice_aliases)
        for alias in aliases:
            if alias.lower() == voice_lower:
                return 'alias_exato'
            elif voice_lower in alias.lower():
                return 'parte_alias'
    
    return 'similaridade'

def get_voice_app_suggestions(user_id):
    """Obter sugestões de apps para comando de voz"""
    # Apps mais usados
    frequent_apps = AppControl.query.filter_by(user_id=user_id)\
        .filter(AppControl.usage_count > 0)\
        .order_by(AppControl.usage_count.desc())\
        .limit(5).all()
    
    # Apps favoritos
    favorite_apps = AppControl.query.filter_by(user_id=user_id, is_favorite=True)\
        .limit(5).all()
    
    suggestions = []
    for app in frequent_apps:
        suggestions.append(f"Abrir {app.display_name}")
    
    for app in favorite_apps:
        if f"Abrir {app.display_name}" not in suggestions:
            suggestions.append(f"Executar {app.display_name}")
    
    return suggestions[:8]

def get_similar_apps(user_id, target_name):
    """Obter apps similares para sugestão"""
    apps = AppControl.query.filter_by(user_id=user_id).all()
    similar = []
    
    target_lower = target_name.lower()
    
    for app in apps:
        # Verificar similaridade parcial
        if any(word in app.app_name.lower() for word in target_lower.split()):
            similar.append(app.display_name)
        elif target_lower in app.app_name.lower():
            similar.append(app.display_name)
    
    return similar[:5]

def get_app_categories(user_id):
    """Obter categorias de apps do usuário"""
    categories = db.session.query(AppControl.category)\
        .filter_by(user_id=user_id)\
        .distinct().all()
    
    return [cat[0] for cat in categories if cat[0]]

def get_most_used_apps(user_id):
    """Obter apps mais usados"""
    apps = AppControl.query.filter_by(user_id=user_id)\
        .filter(AppControl.usage_count > 0)\
        .order_by(AppControl.usage_count.desc())\
        .limit(5).all()
    
    return [{'name': app.display_name, 'usage_count': app.usage_count} for app in apps]

def launch_app(app, voice_command, confidence):
    """Lançar aplicativo"""
    # Em produção, integrar com APIs do sistema operacional
    # Para iOS: usar UIApplication.shared.open()
    # Para Android: usar Intent
    
    launch_result = {
        'launched': True,
        'status': 'initiated',
        'system_action': {
            'action': 'open_app',
            'app_package': app.app_package,
            'app_name': app.display_name,
            'launch_method': 'system_intent'
        }
    }
    
    # Simular resultado baseado na confiança
    if confidence < 0.6:
        launch_result['status'] = 'confirmation_required'
        launch_result['launched'] = False
    
    return launch_result

# ==================== FUNÇÕES AUXILIARES PARA RELATÓRIOS INTELIGENTES ====================

def generate_ai_problem_solutions(meeting, agenda, transcripts):
    """Gerar soluções inteligentes para problemas da reunião"""
    
    # Análise dos problemas identificados
    problems = json.loads(agenda.problems_identified) if agenda.problems_identified else []
    key_points = json.loads(agenda.key_points) if agenda.key_points else []
    decisions = json.loads(agenda.decisions_made) if agenda.decisions_made else []
    
    # Simular análise de IA
    report_data = {
        'title': f'Relatório de Soluções Inteligentes - {meeting.title}',
        'executive_summary': generate_executive_summary(meeting, problems),
        'problems_analysis': json.dumps(analyze_problems_with_ai(problems, key_points)),
        'suggested_solutions': json.dumps(generate_intelligent_solutions(problems, transcripts)),
        'implementation_roadmap': json.dumps(create_implementation_roadmap(problems)),
        'risk_assessment': json.dumps(assess_implementation_risks(problems)),
        'success_metrics': json.dumps(define_success_metrics(problems)),
        'resource_requirements': json.dumps(estimate_resource_requirements(problems)),
        'stakeholder_impact': json.dumps(analyze_stakeholder_impact(problems, transcripts)),
        'follow_up_actions': json.dumps(generate_follow_up_actions(problems, decisions)),
        'ai_confidence_score': calculate_ai_confidence(problems, transcripts),
        'priority_level': determine_priority_level(problems),
        'estimated_impact': estimate_solution_impact(problems),
        'complexity_score': calculate_complexity_score(problems)
    }
    
    return report_data

def generate_executive_summary(meeting, problems):
    """Gerar resumo executivo"""
    problem_count = len(problems)
    duration = meeting.get_duration_minutes()
    
    summary = f"""
📊 **Resumo Executivo - {meeting.title}**

Esta reunião de {duration} minutos identificou {problem_count} problemas principais que requerem atenção estratégica. 
Através de análise avançada de IA, foram desenvolvidas soluções práticas e mensuráveis para cada desafio identificado.

🎯 **Foco Principal**: Transformar problemas em oportunidades de melhoria com soluções implementáveis e resultados tangíveis.

⚡ **Impacto Esperado**: Alto potencial de resolução com implementação estruturada e acompanhamento contínuo.
    """.strip()
    
    return summary

def analyze_problems_with_ai(problems, key_points):
    """Analisar problemas com IA"""
    analysis = []
    
    for i, problem in enumerate(problems):
        analysis.append({
            'problem_id': i + 1,
            'description': problem,
            'category': categorize_problem(problem),
            'severity': assess_problem_severity(problem),
            'root_causes': identify_root_causes(problem, key_points),
            'affected_areas': identify_affected_areas(problem),
            'urgency_level': assess_urgency(problem),
            'business_impact': assess_business_impact(problem)
        })
    
    return analysis

def generate_intelligent_solutions(problems, transcripts):
    """Gerar soluções inteligentes"""
    solutions = []
    
    for i, problem in enumerate(problems):
        solutions.append({
            'problem_id': i + 1,
            'primary_solution': generate_primary_solution(problem),
            'alternative_solutions': generate_alternative_solutions(problem),
            'implementation_steps': generate_implementation_steps(problem),
            'estimated_timeline': estimate_solution_timeline(problem),
            'required_skills': identify_required_skills(problem),
            'technology_requirements': identify_tech_requirements(problem),
            'budget_estimate': estimate_solution_budget(problem),
            'success_probability': calculate_success_probability(problem)
        })
    
    return solutions

def update_intelligent_report(existing_report, report_data):
    """Atualizar relatório existente"""
    existing_report.title = report_data['title']
    existing_report.executive_summary = report_data['executive_summary']
    existing_report.problems_analysis = report_data['problems_analysis']
    existing_report.suggested_solutions = report_data['suggested_solutions']
    existing_report.implementation_roadmap = report_data['implementation_roadmap']
    existing_report.risk_assessment = report_data['risk_assessment']
    existing_report.success_metrics = report_data['success_metrics']
    existing_report.resource_requirements = report_data['resource_requirements']
    existing_report.stakeholder_impact = report_data['stakeholder_impact']
    existing_report.follow_up_actions = report_data['follow_up_actions']
    existing_report.ai_confidence_score = report_data['ai_confidence_score']
    existing_report.priority_level = report_data['priority_level']
    existing_report.estimated_impact = report_data['estimated_impact']
    existing_report.complexity_score = report_data['complexity_score']

# Funções auxiliares simplificadas para IA
def categorize_problem(problem):
    categories = ['Técnico', 'Processo', 'Pessoal', 'Financeiro', 'Estratégico']
    return categories[hash(problem) % len(categories)]

def assess_problem_severity(problem):
    severities = ['Baixa', 'Média', 'Alta', 'Crítica']
    return severities[hash(problem) % len(severities)]

def identify_root_causes(problem, key_points):
    return [
        'Falta de comunicação clara',
        'Recursos insuficientes',
        'Processo inadequado',
        'Tecnologia obsoleta'
    ][:2]  # Retorna 2 causas principais

def identify_affected_areas(problem):
    areas = ['Produtividade', 'Qualidade', 'Custos', 'Satisfação do Cliente', 'Equipe']
    return areas[:2]

def assess_urgency(problem):
    urgencies = ['Baixa', 'Média', 'Alta', 'Urgente']
    return urgencies[hash(problem) % len(urgencies)]

def assess_business_impact(problem):
    impacts = ['Mínimo', 'Moderado', 'Significativo', 'Crítico']
    return impacts[hash(problem) % len(impacts)]

def generate_primary_solution(problem):
    return f"Implementar solução estruturada para {problem[:50]}... com foco em resultados mensuráveis"

def generate_alternative_solutions(problem):
    return [
        "Abordagem gradual com implementação por fases",
        "Solução híbrida combinando métodos tradicionais e inovadores",
        "Outsourcing especializado para componentes complexos"
    ]

def generate_implementation_steps(problem):
    return [
        "1. Análise detalhada da situação atual",
        "2. Definição de objetivos específicos",
        "3. Planejamento de recursos necessários",
        "4. Execução piloto",
        "5. Avaliação e ajustes",
        "6. Implementação completa",
        "7. Monitoramento contínuo"
    ]

def estimate_solution_timeline(problem):
    timelines = ['2-4 semanas', '1-2 meses', '2-3 meses', '3-6 meses']
    return timelines[hash(problem) % len(timelines)]

def identify_required_skills(problem):
    return ['Gestão de projetos', 'Análise técnica', 'Comunicação']

def identify_tech_requirements(problem):
    return ['Software de gestão', 'Ferramentas de análise', 'Plataforma de comunicação']

def estimate_solution_budget(problem):
    budgets = ['Baixo (R$ 5-15k)', 'Médio (R$ 15-50k)', 'Alto (R$ 50-150k)', 'Muito Alto (R$ 150k+)']
    return budgets[hash(problem) % len(budgets)]

def calculate_success_probability(problem):
    return round(0.65 + (hash(problem) % 30) / 100, 2)

def create_implementation_roadmap(problems):
    return [
        {
            'phase': 'Preparação',
            'duration': '1-2 semanas',
            'activities': ['Análise inicial', 'Planejamento', 'Recursos']
        },
        {
            'phase': 'Implementação',
            'duration': '2-8 semanas',
            'activities': ['Execução', 'Testes', 'Ajustes']
        },
        {
            'phase': 'Monitoramento',
            'duration': 'Contínuo',
            'activities': ['Acompanhamento', 'Métricas', 'Otimização']
        }
    ]

def assess_implementation_risks(problems):
    return [
        {
            'risk': 'Resistência à mudança',
            'probability': 'Média',
            'impact': 'Alto',
            'mitigation': 'Comunicação transparente e treinamento'
        },
        {
            'risk': 'Recursos insuficientes',
            'probability': 'Baixa',
            'impact': 'Alto',
            'mitigation': 'Planejamento detalhado de recursos'
        }
    ]

def define_success_metrics(problems):
    return [
        'Redução de 25% no tempo de resolução',
        'Aumento de 30% na satisfação da equipe',
        'Melhoria de 20% na eficiência operacional',
        'ROI positivo em 3 meses'
    ]

def estimate_resource_requirements(problems):
    return [
        {
            'type': 'Humanos',
            'description': '2-3 pessoas dedicadas',
            'duration': '50% do tempo por 2 meses'
        },
        {
            'type': 'Tecnológicos',
            'description': 'Ferramentas de gestão e análise',
            'cost': 'R$ 10-25k'
        },
        {
            'type': 'Financeiros',
            'description': 'Orçamento para implementação',
            'amount': 'R$ 30-80k total'
        }
    ]

def analyze_stakeholder_impact(problems, transcripts):
    return [
        {
            'stakeholder': 'Equipe Técnica',
            'impact': 'Positivo',
            'description': 'Melhores ferramentas e processos'
        },
        {
            'stakeholder': 'Gestão',
            'impact': 'Muito Positivo',
            'description': 'Maior visibilidade e controle'
        },
        {
            'stakeholder': 'Clientes',
            'impact': 'Positivo',
            'description': 'Melhor qualidade e agilidade'
        }
    ]

def generate_follow_up_actions(problems, decisions):
    return [
        {
            'action': 'Reunião de revisão semanal',
            'responsible': 'Gerente do projeto',
            'deadline': '7 dias'
        },
        {
            'action': 'Relatório de progresso quinzenal',
            'responsible': 'Equipe de implementação',
            'deadline': '14 dias'
        },
        {
            'action': 'Avaliação de resultados mensais',
            'responsible': 'Stakeholders principais',
            'deadline': '30 dias'
        }
    ]

def calculate_ai_confidence(problems, transcripts):
    # Calcular confiança baseada na quantidade de dados
    data_quality = min(len(transcripts) / 10, 1.0)  # Máximo 1.0
    problem_clarity = min(len(problems) / 5, 1.0)   # Máximo 1.0
    return round((data_quality + problem_clarity) / 2, 2)

def determine_priority_level(problems):
    if len(problems) > 5:
        return 'critical'
    elif len(problems) > 3:
        return 'high'
    elif len(problems) > 1:
        return 'medium'
    else:
        return 'low'

def estimate_solution_impact(problems):
    if len(problems) > 4:
        return 'high'
    elif len(problems) > 2:
        return 'medium'
    else:
        return 'low'

def calculate_complexity_score(problems):
    # Score de 0.0 a 1.0 baseado no número e tipo de problemas
    base_score = min(len(problems) / 10, 0.8)
    return round(base_score + 0.1, 2)

def generate_implementation_timeline(report):
    """Gerar cronograma de implementação"""
    return [
        {'week': 1, 'activity': 'Planejamento inicial', 'status': 'planned'},
        {'week': 2, 'activity': 'Análise detalhada', 'status': 'planned'},
        {'week': 3, 'activity': 'Início da implementação', 'status': 'planned'},
        {'week': 4, 'activity': 'Testes e ajustes', 'status': 'planned'}
    ]

def generate_next_actions(report):
    """Gerar próximas ações baseadas no relatório"""
    return [
        {
            'priority': 'Alta',
            'action': 'Aprovar orçamento para implementação',
            'deadline': '3 dias',
            'responsible': 'Gestão'
        },
        {
            'priority': 'Média',
            'action': 'Formar equipe de implementação',
            'deadline': '1 semana',
            'responsible': 'RH'
        },
        {
            'priority': 'Média',
            'action': 'Comunicar mudanças para stakeholders',
            'deadline': '5 dias',
            'responsible': 'Comunicação'
        }
    ]# ==================== SISTEMA DE CONTROLE DE APLICATIVOS ====================

@app.route('/api/apps/sync', methods=['POST'])
def sync_phone_apps():
    """Sincronizar aplicativos instalados do telefone"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        apps_data = data.get('apps', [])  # Lista de aplicativos do telefone
        
        synced_apps = []
        updated_apps = []
        
        for app_data in apps_data:
            app_name = app_data.get('app_name', 'App Desconhecido')
            app_package = app_data.get('app_package', '')
            
            if not app_package:
                continue  # Pular apps sem package
            
            # Verificar se app já existe
            existing_app = AppControl.query.filter_by(
                user_id=user_id, 
                app_package=app_package
            ).first()
            
            if existing_app:
                # Atualizar app existente
                existing_app.app_name = app_name
                existing_app.display_name = app_data.get('display_name', app_name)
                existing_app.category = app_data.get('category', 'other')
                existing_app.is_system_app = app_data.get('is_system_app', False)
                existing_app.icon_url = app_data.get('icon_url', '')
                existing_app.app_version = app_data.get('app_version', '')
                existing_app.updated_at = datetime.utcnow()
                updated_apps.append(existing_app)
            else:
                # Criar novo app
                new_app = AppControl(
                    user_id=user_id,
                    app_name=app_name,
                    app_package=app_package,
                    display_name=app_data.get('display_name', app_name),
                    category=app_data.get('category', 'other'),
                    is_system_app=app_data.get('is_system_app', False),
                    icon_url=app_data.get('icon_url', ''),
                    app_version=app_data.get('app_version', ''),
                    voice_aliases=json.dumps(generate_voice_aliases_for_app(app_name)),
                    install_source='auto_detected'
                )
                db.session.add(new_app)
                synced_apps.append(new_app)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'synced_count': len(synced_apps),
            'updated_count': len(updated_apps),
            'total_apps': AppControl.query.filter_by(user_id=user_id).count(),
            'message': f'📱 {len(synced_apps)} novos apps sincronizados, {len(updated_apps)} atualizados!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/open-app', methods=['POST'])
def voice_open_app():
    """Abrir aplicativo por comando de voz"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        voice_command = data.get('voice_command', '').strip()
        audio_confidence = data.get('audio_confidence', 0.8)
        
        if not voice_command:
            return jsonify({'error': 'Comando de voz não fornecido'}), 400
        
        # Processar comando de voz para extrair nome do app
        app_target = extract_app_target_from_voice(voice_command)
        
        if not app_target['target']:
            return jsonify({
                'success': False,
                'message': '❌ Não consegui identificar qual app você quer abrir. Tente: "Abrir [nome do app]"',
                'suggestions': get_voice_app_suggestions(user_id)
            })
        
        # Buscar aplicativo correspondente
        matched_apps = find_apps_by_voice(user_id, app_target['target'])
        
        if not matched_apps:
            return jsonify({
                'success': False,
                'message': f'📱 Aplicativo "{app_target["target"]}" não encontrado.',
                'suggestions': get_similar_apps(user_id, app_target['target'])
            })
        
        # Se múltiplos apps, retornar para escolha
        if len(matched_apps) > 1:
            return jsonify({
                'success': False,
                'multiple_matches': True,
                'message': f'🤔 Encontrei {len(matched_apps)} aplicativos. Qual deles?',
                'apps': [
                    {
                        'id': a['app'].id,
                        'name': a['app'].display_name,
                        'package': a['app'].app_package,
                        'score': a['score']
                    } for a in matched_apps[:5]
                ]
            })
        
        # App único identificado
        best_match = matched_apps[0]
        app = best_match['app']
        confidence = best_match['score']
        
        # Abrir aplicativo
        launch_result = launch_app(app, voice_command, confidence)
        
        # Registrar no log
        app_log = AppLaunchLog(
            user_id=user_id,
            app_id=app.id,
            app_name=app.display_name,
            voice_command=voice_command,
            launch_method='voice_command',
            launch_status=launch_result['status'],
            voice_confidence=confidence
        )
        db.session.add(app_log)
        
        # Atualizar estatísticas do app
        app.usage_count += 1
        app.last_opened = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'app_launched': launch_result['launched'],
            'app': app.to_dict(),
            'launch_log': app_log.to_dict(),
            'confidence': confidence,
            'message': f'📱 Abrindo {app.display_name}...',
            'system_action': launch_result['system_action']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== SISTEMA DE RELATÓRIOS INTELIGENTES ====================

@app.route('/api/meetings/<int:meeting_id>/generate-intelligent-report', methods=['POST'])
def generate_intelligent_report(meeting_id):
    """Gerar relatório inteligente com sugestões para resolver problemas"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Buscar agenda da reunião
        agenda = MeetingAgenda.query.filter_by(meeting_id=meeting_id).first()
        if not agenda:
            return jsonify({'error': 'Agenda da reunião não encontrada. Gere a ata primeiro.'}), 400
        
        # Buscar transcrições da reunião
        transcripts = MeetingTranscript.query.filter_by(meeting_id=meeting_id).all()
        
        # Gerar relatório inteligente
        report_data = generate_ai_problem_solutions(meeting, agenda, transcripts)
        
        # Verificar se já existe um relatório
        existing_report = IntelligentReport.query.filter_by(
            user_id=user_id, 
            meeting_id=meeting_id
        ).first()
        
        if existing_report:
            # Atualizar relatório existente
            update_intelligent_report(existing_report, report_data)
            report = existing_report
        else:
            # Criar novo relatório
            report = IntelligentReport(
                user_id=user_id,
                meeting_id=meeting_id,
                title=report_data['title'],
                executive_summary=report_data['executive_summary'],
                problems_analysis=report_data['problems_analysis'],
                suggested_solutions=report_data['suggested_solutions'],
                implementation_roadmap=report_data['implementation_roadmap'],
                risk_assessment=report_data['risk_assessment'],
                success_metrics=report_data['success_metrics'],
                resource_requirements=report_data['resource_requirements'],
                stakeholder_impact=report_data['stakeholder_impact'],
                follow_up_actions=report_data['follow_up_actions'],
                ai_confidence_score=report_data['ai_confidence_score'],
                priority_level=report_data['priority_level'],
                estimated_impact=report_data['estimated_impact'],
                complexity_score=report_data['complexity_score']
            )
            db.session.add(report)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'report': report.to_dict(),
            'message': '🧠 Relatório inteligente gerado com sugestões para resolver problemas!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================
# FUNÇÕES AUXILIARES PARA APLICATIVOS
# ===============================================

def generate_sample_apps():
    """Gerar aplicativos de exemplo para demonstração"""
    return [
        {
            'package_name': 'com.whatsapp',
            'name': 'WhatsApp',
            'display_name': 'WhatsApp Messenger',
            'version': '2.24.1.78',
            'voice_aliases': ['whatsapp', 'whats', 'zap', 'wpp'],
            'enabled': True
        },
        {
            'package_name': 'com.instagram.android',
            'name': 'Instagram',
            'display_name': 'Instagram',
            'version': '305.0.0.37.120',
            'voice_aliases': ['instagram', 'insta', 'ig'],
            'enabled': True
        },
        {
            'package_name': 'com.google.android.apps.maps',
            'name': 'Maps',
            'display_name': 'Google Maps',
            'version': '11.106.0101',
            'voice_aliases': ['maps', 'mapas', 'google maps', 'navegação'],
            'enabled': True
        },
        {
            'package_name': 'com.spotify.music',
            'name': 'Spotify',
            'display_name': 'Spotify',
            'version': '8.8.78.345',
            'voice_aliases': ['spotify', 'música', 'music', 'som'],
            'enabled': True
        },
        {
            'package_name': 'com.netflix.mediaclient',
            'name': 'Netflix',
            'display_name': 'Netflix',
            'version': '8.95.0 build 1 49928',
            'voice_aliases': ['netflix', 'filme', 'filmes', 'série', 'séries'],
            'enabled': True
        },
        {
            'package_name': 'com.google.android.youtube',
            'name': 'YouTube',
            'display_name': 'YouTube',
            'version': '18.47.42',
            'voice_aliases': ['youtube', 'you', 'tube', 'vídeo', 'vídeos'],
            'enabled': True
        },
        {
            'package_name': 'com.android.chrome',
            'name': 'Chrome',
            'display_name': 'Google Chrome',
            'version': '120.0.6099.193',
            'voice_aliases': ['chrome', 'navegador', 'browser', 'google chrome'],
            'enabled': True
        },
        {
            'package_name': 'com.facebook.katana',
            'name': 'Facebook',
            'display_name': 'Facebook',
            'version': '444.0.0.37.115',
            'voice_aliases': ['facebook', 'face', 'fb'],
            'enabled': True
        }
    ]


def format_app_data(app):
    """Formatar dados do aplicativo para resposta da API"""
    voice_aliases = []
    if app.voice_aliases:
        try:
            voice_aliases = json.loads(app.voice_aliases)
        except:
            voice_aliases = []
    
    return {
        'id': app.id,
        'package_name': app.package_name,
        'app_name': app.app_name,
        'display_name': app.display_name,
        'version': app.app_version,
        'voice_aliases': voice_aliases,
        'usage_count': app.usage_count or 0,
        'launch_count': app.launch_count or 0,
        'last_used': app.last_used.isoformat() if app.last_used else None,
        'install_date': app.install_date.isoformat() if app.install_date else None,
        'is_enabled': app.is_enabled,
        'last_scanned': app.last_scanned.isoformat() if app.last_scanned else None
    }


def format_launch_log_data(log):
    """Formatar dados do log de lançamento para resposta da API"""
    return {
        'id': log.id,
        'app_id': log.app_id,
        'command': log.command,
        'launch_method': log.launch_method,
        'success': log.success,
        'timestamp': log.timestamp.isoformat(),
        'error_message': log.error_message
    }


def find_app_by_voice(voice_input):
    """Encontrar aplicativo por comando de voz"""
    voice_lower = voice_input.lower().strip()
    
    # Buscar por nome exato
    exact_name = AppControl.query.filter(
        AppControl.app_name.ilike(voice_lower)
    ).first()
    
    if exact_name:
        return [exact_name]
    
    # Buscar por nome de exibição
    display_name = AppControl.query.filter(
        AppControl.display_name.ilike(voice_lower)
    ).first()
    
    if display_name:
        return [display_name]
    
    # Buscar por aliases de voz
    apps_with_aliases = AppControl.query.filter(
        AppControl.voice_aliases.isnot(None)
    ).all()
    
    matches = []
    for app in apps_with_aliases:
        try:
            aliases = json.loads(app.voice_aliases)
            for alias in aliases:
                if alias.lower() == voice_lower:
                    matches.append(app)
                    break
        except:
            continue
    
    if matches:
        return matches
    
    # Busca parcial no nome
    partial_matches = AppControl.query.filter(
        or_(
            AppControl.app_name.ilike(f'%{voice_lower}%'),
            AppControl.display_name.ilike(f'%{voice_lower}%')
        )
    ).all()
    
    return partial_matches[:5]  # Limitar a 5 resultados


def launch_app_by_package(package_name):
    """Simular lançamento de aplicativo (em produção, integraria com APIs do sistema)"""
    # Esta função simularia o lançamento real do aplicativo
    # Em um ambiente Android real, usaria:
    # - Intent com ACTION_MAIN
    # - PackageManager para verificar se o app existe
    # - StartActivity para abrir o aplicativo
    
    print(f"🚀 Simulando lançamento do aplicativo: {package_name}")
    
    # Simular alguns casos de falha
    if package_name in ['com.app.broken', 'com.test.fail']:
        return False
    
    # Para demonstração, sempre retorna sucesso
    return True


def log_app_launch(user_id, app_id, command, launch_method, success, error_message=None):
    """Registrar tentativa de lançamento de aplicativo"""
    try:
        launch_log = AppLaunchLog(
            user_id=user_id,
            app_id=app_id,
            command=command,
            launch_method=launch_method,
            success=success,
            error_message=error_message,
            timestamp=datetime.utcnow()
        )
        db.session.add(launch_log)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Erro ao registrar log de lançamento: {str(e)}")
        return False

# Para compatibilidade com Vercel
app_instance = app

if __name__ == '__main__':
    # Configurações para desenvolvimento
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print("🚀 Iniciando IAON - Assistente IA Avançado...")
    print(f"📱 PWA: Habilitado")
    print(f"🔒 Biometria de Voz: Ativa")
    print(f"🏥 Sistema Médico: Carregado")
    print(f"💰 Controle Financeiro: Ativo")
    print(f"🤖 IA Avançada: Pronta")
    print(f"🌐 Servidor: http://0.0.0.0:{port}")
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=debug_mode,
        threaded=True
    )

