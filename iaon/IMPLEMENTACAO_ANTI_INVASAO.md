# 🏠 Implementação do Sistema Anti-Invasão Domiciliar - Guia Técnico

## 🎯 Funcionalidades Implementadas

### 1. **Detecção por Palavra-Chave de Voz**
- **Reconhecimento contínuo** de frases de pânico
- **Operação silenciosa** sem indicações visuais
- **Baixo consumo de bateria** com processamento otimizado

### 2. **Sistema de Alerta Silencioso**
- **Mensagem automática**: "ENTRARAM NA MINHA CASA E ESTOU DE REFÉM, ME AJUDE!"
- **Dados de localização** em tempo real
- **Evidências automáticas**: fotos e áudio discretos

### 3. **Chamadas Automáticas Inteligentes**
- **Timer de 1 minuto** antes de iniciar chamadas
- **Áudio unidirecional**: contato ouve tudo, usuário não ouve nada
- **Persistência**: continua ligando até alguém atender

## 🔧 Implementação Técnica

### **Service Worker (sw.js)**

```javascript
// Frases de pânico monitoradas
this.homeInvasionDetection = {
    panicPhrases: [
        'socorro tem gente aqui',
        'tem ladrão na minha casa', 
        'estou sendo assaltado em casa',
        'invasão socorro',
        'me ajuda tem bandido aqui'
    ]
};

// Reconhecimento de voz contínuo
async setupContinuousVoiceRecognition() {
    const SpeechRecognition = self.SpeechRecognition || self.webkitSpeechRecognition;
    this.speechRecognition = new SpeechRecognition();
    
    this.speechRecognition.continuous = true;
    this.speechRecognition.interimResults = true;
    this.speechRecognition.lang = 'pt-BR';
    
    this.speechRecognition.onresult = (event) => {
        this.processSpeechResult(event);
    };
}

// Processar resultado de voz
processSpeechResult(event) {
    const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
    
    for (const phrase of this.homeInvasionDetection.panicPhrases) {
        if (transcript.includes(phrase)) {
            this.activateHomeInvasionAlert(phrase, transcript);
            break;
        }
    }
}
```

### **Backend Flask (app.py)**

```python
@app.route('/api/emergency/home-invasion', methods=['POST'])
def home_invasion_alert():
    """API para alertas de invasão domiciliar"""
    data = request.get_json()
    
    # Enviar mensagens silenciosas para contatos
    emergency_contacts = get_emergency_contacts(user_id)
    
    for contact in emergency_contacts:
        send_silent_message(contact, {
            'message': 'ENTRARAM NA MINHA CASA E ESTOU DE REFÉM, ME AJUDE!',
            'location': data.get('location'),
            'timestamp': data.get('timestamp'),
            'evidence': data.get('photos', [])
        })
    
    return jsonify({
        'success': True,
        'emergencyContacts': emergency_contacts
    })

@app.route('/api/emergency/make-call', methods=['POST'])
def make_emergency_call():
    """Fazer chamada automática de emergência"""
    data = request.get_json()
    
    # Integrar com Twilio, Vonage, ou similar
    call_id = initiate_emergency_call(
        phone_number=data.get('phoneNumber'),
        user_location=data.get('location'),
        silent_mode=True
    )
    
    return jsonify({
        'success': True,
        'callId': call_id,
        'status': 'calling'
    })
```

## 🚀 Integração com Serviços de Produção

### **1. SMS/WhatsApp (Twilio)**

```python
from twilio.rest import Client

def send_silent_message(contact, alert_data):
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f"🚨 EMERGÊNCIA: {alert_data['message']}\n📍 {alert_data['location']}\n⏰ {alert_data['timestamp']}",
        from_='+5511999999999',
        to=contact['phone']
    )
    
    return message.sid
```

### **2. Chamadas de Voz (Twilio Voice)**

```python
def initiate_emergency_call(phone_number, user_location, silent_mode=True):
    client = Client(account_sid, auth_token)
    
    # TwiML para configurar chamada unidirecional
    twiml = f'''
    <Response>
        <Say voice="alice" language="pt-BR">
            Alerta de emergência. Invasão domiciliar detectada.
            Localização: {user_location}. 
            Você ouvirá o áudio ao vivo do local.
            NÃO ligue de volta para não colocar a vítima em risco.
        </Say>
        <Dial>
            <Stream url="wss://seu-servidor.com/audio-stream"/>
        </Dial>
    </Response>
    '''
    
    call = client.calls.create(
        twiml=twiml,
        to=phone_number,
        from_='+5511888888888'
    )
    
    return call.sid
```

### **3. Streaming de Áudio (WebRTC)**

```javascript
// Transmitir áudio ambiente para contato
startAudioTransmission(stream, contactId) {
    const mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (event) => {
        // Enviar chunks para WebSocket
        websocket.send(JSON.stringify({
            type: 'audio_chunk',
            contactId: contactId,
            data: event.data,
            timestamp: Date.now()
        }));
    };
    
    mediaRecorder.start(1000); // Chunks de 1 segundo
}
```

## 📱 Configuração de Permissões

### **1. Manifesto PWA (manifest.json)**

```json
{
    "name": "IAON Security",
    "permissions": [
        "microphone",
        "camera", 
        "geolocation",
        "background-sync",
        "push"
    ],
    "background": {
        "persistent": true
    }
}
```

### **2. Permissões JavaScript**

```javascript
// Solicitar permissões necessárias
async function requestPermissions() {
    // Microfone para reconhecimento de voz
    await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Câmera para evidências
    await navigator.mediaDevices.getUserMedia({ video: true });
    
    // Localização
    navigator.geolocation.getCurrentPosition(() => {});
    
    // Notificações
    await Notification.requestPermission();
}
```

## 🔒 Considerações de Segurança

### **1. Criptografia de Dados**
```javascript
// Criptografar evidências antes de enviar
async function encryptEvidence(data) {
    const key = await crypto.subtle.generateKey(
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
    );
    
    const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: new Uint8Array(12) },
        key,
        new TextEncoder().encode(data)
    );
    
    return encrypted;
}
```

### **2. Validação de Autenticidade**
```python
import hashlib
import hmac

def validate_emergency_request(data, signature):
    expected = hmac.new(
        SECRET_KEY.encode(),
        json.dumps(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

## 🔧 Configuração de Infraestrutura

### **1. WebSocket Server (Node.js)**

```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    ws.on('message', (data) => {
        const message = JSON.parse(data);
        
        if (message.type === 'audio_chunk') {
            // Retransmitir para contato de emergência
            broadcastToContact(message.contactId, message.data);
        }
    });
});
```

### **2. Database Schema (PostgreSQL)**

```sql
CREATE TABLE emergency_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    trigger_phrase TEXT,
    location JSONB,
    evidence JSONB,
    contacts_notified JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE emergency_calls (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES emergency_alerts(id),
    contact_id INTEGER NOT NULL,
    phone_number VARCHAR(20),
    call_sid VARCHAR(100),
    status VARCHAR(20),
    answered_at TIMESTAMP,
    duration INTEGER
);
```

## 🌐 Deploy e Produção

### **1. Vercel Configuration**

```json
{
    "version": 2,
    "builds": [
        {
            "src": "app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/api/emergency/(.*)",
            "dest": "/app.py"
        }
    ]
}
```

### **2. Environment Variables**

```bash
# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+5511999999999

# Security
SECRET_KEY=your_secret_key
ENCRYPTION_KEY=your_encryption_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
```

## 🚨 Protocolos de Emergência

### **1. Fluxo de Resposta**
1. **Detecção** → Frase de pânico identificada
2. **Evidência** → Fotos e áudio capturados silenciosamente  
3. **Alerta** → Mensagem enviada para contatos
4. **Timer** → Aguarda 60 segundos
5. **Chamadas** → Liga automaticamente para contatos
6. **Áudio** → Transmite som ambiente em tempo real

### **2. Orientações para Contatos**
- ❌ **NÃO ligar de volta** imediatamente
- ✅ **Chamar a polícia** com informações fornecidas
- ✅ **Escutar o áudio** para avaliar situação
- ✅ **Coordenar com autoridades** para resgate

## 📊 Métricas e Monitoramento

### **1. Logs de Segurança**
```python
import logging

security_logger = logging.getLogger('security')

def log_emergency_event(event_type, user_id, data):
    security_logger.critical(f"EMERGENCY: {event_type}", extra={
        'user_id': user_id,
        'event_data': data,
        'timestamp': time.time()
    })
```

### **2. Dashboard de Monitoramento**
- Taxa de alertas falsos
- Tempo de resposta dos contatos  
- Eficácia das chamadas automáticas
- Qualidade do áudio transmitido

---

## ⚠️ **AVISO LEGAL**

Este sistema é uma **ferramenta de apoio à segurança pessoal**. Em situações de emergência real:

1. **Sempre chame a polícia** pelo 190
2. **Procure ajuda profissional** imediatamente
3. **Use o sistema como complemento**, não substituto

**A implementação deve seguir todas as leis locais de privacidade e gravação.**

---

### 🎯 **Resultado Final**

Com esta implementação, o usuário tem proteção **silenciosa e automática** contra invasões domiciliares, com:

- ✅ **Detecção por voz** sem interação manual
- ✅ **Alertas silenciosos** que não comprometem a segurança
- ✅ **Chamadas automáticas** com áudio unidirecional
- ✅ **Evidências automáticas** para autoridades
- ✅ **Operação 24/7** com baixo consumo de bateria

**"Tecnologia que salva vidas de forma silenciosa e inteligente."** 🛡️
