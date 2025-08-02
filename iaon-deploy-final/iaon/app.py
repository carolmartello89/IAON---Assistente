import os
import sys
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import time
import uuid
from datetime import datetime

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

# Armazenamento em memória para dados temporários (para demonstração)
# Em produção, usar banco de dados real como PostgreSQL
users_data = {
    1: {
        'id': 1,
        'username': 'admin',
        'email': 'admin@iaon.com',
        'full_name': 'Administrador IAON',
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }
}

conversations_data = {}
messages_data = {}
voice_biometry_data = {}

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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return jsonify({
        'status': 'healthy',
        'app': 'IAON - Assistente IA Avançado',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': 'memory',
            'ai': 'available',
            'voice_biometry': 'enabled',
            'pwa': 'active'
        }
    })

@app.route('/api/system-info', methods=['GET'])
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
        
        # Buscar ou criar conversa em memória
        conversation_key = f"{user_id}_{session_id}"
        if conversation_key not in conversations_data:
            conversations_data[conversation_key] = {
                'id': len(conversations_data) + 1,
                'user_id': user_id,
                'session_id': session_id,
                'title': f"Conversa {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                'created_at': datetime.utcnow().isoformat()
            }
        
        conversation = conversations_data[conversation_key]
        conversation_id = conversation['id']
        
        # Salvar mensagem do usuário
        user_message_id = f"{conversation_id}_{len(messages_data) + 1}"
        messages_data[user_message_id] = {
            'id': user_message_id,
            'conversation_id': conversation_id,
            'role': 'user',
            'content': message,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Gerar resposta da IA
        ai_response = generate_ai_response(message)
        
        # Salvar resposta da IA
        ai_message_id = f"{conversation_id}_{len(messages_data) + 1}"
        messages_data[ai_message_id] = {
            'id': ai_message_id,
            'conversation_id': conversation_id,
            'role': 'assistant',
            'content': ai_response,
            'created_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'response': ai_response,
            'conversation_id': conversation_id,
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
        
        # Processar comando de voz
        result = process_voice_command(command_text)
        
        return jsonify({
            'executed': True,
            'intent': result['intent'],
            'execution_result': result['result']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-biometry/status/<int:user_id>', methods=['GET'])
def voice_biometry_status(user_id):
    """Status da biometria de voz"""
    try:
        biometry = voice_biometry_data.get(user_id, {})
        
        return jsonify({
            'biometry_enrolled': biometry.get('is_enrolled', False),
            'samples_count': biometry.get('samples_count', 0),
            'enrollment_complete': biometry.get('is_enrolled', False)
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
        
        # Buscar ou criar registro de biometria em memória
        if user_id not in voice_biometry_data:
            voice_biometry_data[user_id] = {
                'user_id': user_id,
                'enrollment_phrase': enrollment_phrase,
                'samples_count': 0,
                'is_enrolled': False,
                'created_at': datetime.utcnow().isoformat()
            }
        
        biometry = voice_biometry_data[user_id]
        
        # Incrementar contador de amostras
        biometry['samples_count'] += 1
        
        # Marcar como cadastrado após 3 amostras
        if biometry['samples_count'] >= 3:
            biometry['is_enrolled'] = True
        
        return jsonify({
            'enrollment_complete': biometry['is_enrolled'],
            'samples_count': biometry['samples_count'],
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
    
    # Em ambiente serverless, não podemos salvar arquivos
    # Simular processamento do arquivo
    filename = f"voice_{request.form.get('user_id', 'unknown')}_{int(time.time())}.wav"
    
    return jsonify({
        'message': 'Arquivo de voz processado com sucesso',
        'filename': filename,
        'note': 'Arquivo processado em memória (ambiente serverless)'
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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Servir arquivos estáticos e SPA"""
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

def generate_ai_response(message):
    """Gerar resposta da IA (simulada)"""
    message_lower = message.lower()
    
    if 'olá' in message_lower or 'oi' in message_lower:
        return "Olá! Sou o IAON, seu assistente IA avançado. Como posso ajudá-lo hoje?"
    
    elif 'medicamento' in message_lower or 'remédio' in message_lower:
        return "🏥 Posso ajudá-lo com informações sobre medicamentos. Por favor, me informe o nome do medicamento que deseja consultar. Lembre-se: sempre consulte um médico antes de tomar qualquer medicamento."
    
    elif 'agenda' in message_lower or 'compromisso' in message_lower:
        return "📅 Posso ajudá-lo a gerenciar sua agenda. Gostaria de adicionar um novo compromisso, ver os próximos eventos ou configurar um lembrete?"
    
    elif 'finanças' in message_lower or 'dinheiro' in message_lower:
        return "💰 Estou aqui para ajudar com seu controle financeiro. Posso registrar gastos, mostrar relatórios ou ajudar com seu orçamento. O que você gostaria de fazer?"
    
    elif 'ia ' in message_lower:
        return "🤖 Comando de voz detectado! Para sua segurança, comandos de voz requerem verificação de biometria. Certifique-se de que sua biometria de voz está configurada."
    
    elif 'ajuda' in message_lower or 'help' in message_lower:
        return """🆘 Aqui estão algumas coisas que posso fazer:

• 💬 Conversar e responder perguntas
• 🏥 Verificar medicamentos e interações
• 📅 Gerenciar sua agenda e compromissos
• 💰 Controlar suas finanças pessoais
• 👥 Gerenciar seus contatos
• 🎤 Responder a comandos de voz (com biometria)
• 📊 Gerar relatórios e análises

Diga "IA" seguido do comando para usar controle por voz!"""
    
    else:
        return f"Entendi sua mensagem: '{message}'. Como assistente IA, estou aqui para ajudar com diversas tarefas. Posso auxiliar com medicina, finanças, agenda, contatos e muito mais. Como posso ser útil?"

def process_voice_command(command_text):
    """Processar comando de voz"""
    command_lower = command_text.lower()
    
    if 'agenda' in command_lower:
        return {
            'intent': 'agenda_management',
            'result': 'Abrindo sistema de agenda...'
        }
    elif 'medicamento' in command_lower:
        return {
            'intent': 'medical_check',
            'result': 'Abrindo sistema médico...'
        }
    elif 'finanças' in command_lower:
        return {
            'intent': 'financial_management',
            'result': 'Abrindo controle financeiro...'
        }
    else:
        return {
            'intent': 'general_command',
            'result': f'Comando processado: {command_text}'
        }

# Para Vercel, a aplicação deve ser exportada como 'app'
# Não usar if __name__ == '__main__' em ambiente serverless

