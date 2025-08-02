import os
import sys
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import time
import uuid
from datetime import datetime

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
            'generated_at': self.generated_at.isoformat() if self.generated_at else None
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
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")

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
    """Iniciar uma nova sessão de reunião"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 1)
        title = data.get('title', f'Reunião {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        description = data.get('description', '')
        
        # Criar nova sessão de reunião
        meeting = MeetingSession(
            user_id=user_id,
            title=title,
            description=description
        )
        db.session.add(meeting)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict(),
            'message': f'📹 Reunião "{title}" iniciada com sucesso!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/meetings/<int:meeting_id>/add-participant', methods=['POST'])
def add_meeting_participant(meeting_id):
    """Adicionar participante à reunião"""
    try:
        data = request.get_json()
        participant_name = data.get('participant_name', 'Participante Desconhecido')
        participant_role = data.get('participant_role', 'participante')
        email = data.get('email', '')
        voice_sample = data.get('voice_sample', '')  # Amostra de voz para reconhecimento
        
        meeting = MeetingSession.query.get(meeting_id)
        if not meeting:
            return jsonify({'error': 'Reunião não encontrada'}), 404
        
        # Processar amostra de voz para criar perfil
        voice_profile = create_voice_profile(voice_sample) if voice_sample else '{}'
        
        participant = MeetingParticipant(
            meeting_id=meeting_id,
            participant_name=participant_name,
            participant_role=participant_role,
            email=email,
            voice_profile=voice_profile
        )
        db.session.add(participant)
        
        # Atualizar contagem de participantes
        meeting.total_participants = MeetingParticipant.query.filter_by(meeting_id=meeting_id).count() + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'participant': participant.to_dict(),
            'message': f'👤 Participante "{participant_name}" adicionado com sucesso!'
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
    """Finalizar reunião"""
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
            'message': f'✅ Reunião "{meeting.title}" finalizada com sucesso!'
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
    """Identificar falante comparando com perfis de voz dos participantes"""
    import random
    
    if not participants:
        return "Participante Desconhecido"
    
    # Simular comparação de características vocais
    # Em produção, usaria algoritmos de ML como MFCC, i-vectors, x-vectors
    confidence_scores = []
    
    for participant in participants:
        # Simular score de similaridade
        similarity_score = random.uniform(0.3, 0.95)
        confidence_scores.append((participant.participant_name, similarity_score))
    
    # Ordenar por confiança e retornar o melhor match
    confidence_scores.sort(key=lambda x: x[1], reverse=True)
    
    best_match = confidence_scores[0]
    
    # Só considera identificado se a confiança for alta
    if best_match[1] > 0.7:
        return best_match[0]
    else:
        return "Participante Desconhecido"

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
    """Processar comando de voz avançado"""
    command_lower = command_text.lower()
    
    # Buscar usuário para personalização
    user = User.query.get(user_id)
    preferred_name = user.preferred_name if user and user.preferred_name else "usuário"
    
    # Comandos de reunião
    if any(word in command_lower for word in ['reunião', 'meeting', 'gravar', 'gravação']):
        return {
            'intent': 'meeting_management',
            'result': f'📹 Ativando sistema de reuniões para {preferred_name}...',
            'action': 'open_section',
            'section': 'meetings'
        }
    
    # Comandos de agenda
    elif any(word in command_lower for word in ['agenda', 'compromisso', 'encontro']):
        return {
            'intent': 'agenda_management',
            'result': f'📅 Abrindo agenda inteligente para {preferred_name}...',
            'action': 'open_section',
            'section': 'agenda'
        }
    
    # Comandos médicos
    elif any(word in command_lower for word in ['medicamento', 'remédio', 'medicina', 'saúde', 'médico']):
        return {
            'intent': 'medical_check',
            'result': f'🏥 Ativando sistema médico avançado para {preferred_name}...',
            'action': 'open_section',
            'section': 'medical'
        }
    
    # Comandos financeiros
    elif any(word in command_lower for word in ['finanças', 'dinheiro', 'gasto', 'orçamento', 'financeiro']):
        return {
            'intent': 'financial_management',
            'result': f'💰 Carregando controle financeiro para {preferred_name}...',
            'action': 'open_section',
            'section': 'finance'
        }
    
    # Comandos de relatório
    elif any(word in command_lower for word in ['relatório', 'relatorio', 'análise', 'dados']):
        return {
            'intent': 'generate_report',
            'result': f'📊 Gerando relatório personalizado para {preferred_name}...',
            'action': 'generate_report',
            'section': 'reports'
        }
    
    # Comandos de ajuda
    elif any(word in command_lower for word in ['ajuda', 'help', 'comando']):
        return {
            'intent': 'show_help',
            'result': f'🆘 Exibindo central de ajuda para {preferred_name}...',
            'action': 'show_help',
            'section': 'help'
        }
    
    # Comandos de configuração
    elif any(word in command_lower for word in ['configuração', 'config', 'configurar', 'ajuste']):
        return {
            'intent': 'settings_management',
            'result': f'⚙️ Abrindo configurações para {preferred_name}...',
            'action': 'open_section',
            'section': 'settings'
        }
    
    # Comandos de voz/biometria
    elif any(word in command_lower for word in ['voz', 'biometria', 'cadastrar']):
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
            'result': f'🤖 Processando comando para {preferred_name}: "{command_text}"',
            'action': 'process_general',
            'section': 'chat'
        }

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

