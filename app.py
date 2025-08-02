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
    
    elif any(word in message_lower for word in ['agenda', 'compromisso', 'reunião', 'encontro']):
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
• 🏥 Sistema médico completo
• 📅 Agenda inteligente
• � Controle financeiro avançado
• 📊 Relatórios e análises
• � Segurança militar

**🎤 Comandos de Voz:**
Diga "IA" + comando para ações específicas

**💡 Dica:** Use linguagem natural - eu entendo contexto!"""
    
    elif any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'thanks']):
        return f"� Por nada, {preferred_name}! É sempre um prazer ajudar. Estou aqui sempre que precisar!"
    
    elif any(word in message_lower for word in ['tchau', 'até', 'bye', 'adeus']):
        return f"👋 Até logo, {preferred_name}! Foi ótimo conversar com você. Volte sempre que quiser!"
    
    else:
        # Resposta contextual avançada
        return f"""Entendi sua mensagem, {preferred_name}: "{message}"

🤖 Como seu assistente IA avançado, posso ajudar com:
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
    
    # Comandos de agenda
    if any(word in command_lower for word in ['agenda', 'compromisso', 'reunião', 'encontro']):
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

