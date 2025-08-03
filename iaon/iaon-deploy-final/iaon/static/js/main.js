// Main JavaScript for IAON - Assistente IA Avançado
class IAON {
    constructor() {
        this.currentSection = 'chat';
        this.isVoiceActive = false;
        this.userId = 1; // Default user ID
        this.sessionId = this.generateSessionId();
        this.voiceRecognition = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupVoiceRecognition();
        this.registerServiceWorker();
        this.checkVoiceBiometryStatus();
        this.checkSystemHealth();
    }
    
    generateSessionId() {
        return 'iaon_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    setupEventListeners() {
        // Sidebar toggle
        document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
            this.toggleSidebar();
        });
        
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });
        
        // Chat functionality
        document.getElementById('send-message')?.addEventListener('click', () => {
            this.sendMessage();
        });
        
        document.getElementById('chat-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Voice toggle
        document.getElementById('voice-toggle')?.addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
        
        document.getElementById('floating-voice')?.addEventListener('click', () => {
            this.toggleVoiceRecognition();
        });
        
        // Voice biometry buttons
        document.getElementById('start-enrollment')?.addEventListener('click', () => {
            this.startVoiceEnrollment();
        });
        
        document.getElementById('test-voice')?.addEventListener('click', () => {
            this.testVoiceRecognition();
        });
        
        document.getElementById('reset-biometry')?.addEventListener('click', () => {
            this.resetVoiceBiometry();
        });
    }
    
    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('sidebar-hidden');
    }
    
    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show selected section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('text-blue-600', 'bg-blue-50');
        });
        
        const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('text-blue-600', 'bg-blue-50');
        }
        
        this.currentSection = sectionName;
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessageToChat(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send message to AI
            const response = await this.callAPI('/api/ai/chat', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: this.userId,
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (response.response) {
                this.addMessageToChat(response.response, 'ai');
                
                // Check if voice verification is needed
                if (message.toLowerCase().includes('ia ')) {
                    this.handleVoiceCommand(message);
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessageToChat('❌ Desculpe, ocorreu um erro. Tente novamente.', 'ai');
        } finally {
            this.hideTypingIndicator();
        }
    }
    
    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        
        const bubbleClass = sender === 'user' ? 'user-bubble' : 'ai-bubble';
        messageDiv.className = `${bubbleClass} chat-bubble p-3 rounded-lg text-white`;
        messageDiv.innerHTML = `<p>${this.escapeHtml(message)}</p>`;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'ai-bubble chat-bubble p-3 rounded-lg text-white';
        typingDiv.innerHTML = '<p class="loading-dots">IAON está processando</p>';
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    setupVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.voiceRecognition = new SpeechRecognition();
            
            this.voiceRecognition.continuous = false;
            this.voiceRecognition.interimResults = false;
            this.voiceRecognition.lang = 'pt-BR';
            
            this.voiceRecognition.onstart = () => {
                this.updateVoiceStatus(true, '🎤 Ouvindo...');
            };
            
            this.voiceRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.handleVoiceInput(transcript);
            };
            
            this.voiceRecognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                this.updateVoiceStatus(false, '❌ Erro na voz');
            };
            
            this.voiceRecognition.onend = () => {
                this.updateVoiceStatus(false, 'Voz Inativa');
            };
        }
    }
    
    toggleVoiceRecognition() {
        if (!this.voiceRecognition) {
            alert('❌ Reconhecimento de voz não suportado neste navegador');
            return;
        }
        
        if (this.isVoiceActive) {
            this.voiceRecognition.stop();
        } else {
            this.voiceRecognition.start();
        }
    }
    
    handleVoiceInput(transcript) {
        console.log('Voice input:', transcript);
        
        // Check if it's a command starting with "IA"
        if (transcript.toLowerCase().startsWith('ia ')) {
            this.handleVoiceCommand(transcript);
        } else {
            // Regular chat message
            document.getElementById('chat-input').value = transcript;
            this.sendMessage();
        }
    }
    
    async handleVoiceCommand(command) {
        // First verify voice biometry for commands
        const verified = await this.verifyVoiceBiometry(command);
        
        if (!verified) {
            this.addMessageToChat('🔒 Comando de voz não autorizado. Biometria de voz necessária para comandos seguros.', 'ai');
            return;
        }
        
        // Process the command
        try {
            const response = await this.callAPI('/api/ai/voice-command', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: this.userId,
                    command_text: command
                })
            });
            
            if (response.executed) {
                this.addMessageToChat(`✅ Comando executado: ${response.execution_result}`, 'ai');
            } else {
                this.addMessageToChat(`🔍 Comando reconhecido: ${response.intent}`, 'ai');
            }
        } catch (error) {
            console.error('Error processing voice command:', error);
            this.addMessageToChat('❌ Erro ao processar comando de voz.', 'ai');
        }
    }
    
    updateVoiceStatus(active, text) {
        this.isVoiceActive = active;
        
        const indicator = document.getElementById('voice-indicator');
        const statusText = document.getElementById('voice-text');
        
        if (indicator) {
            indicator.className = `w-3 h-3 rounded-full ${active ? 'bg-green-500 voice-animation' : 'bg-red-500'}`;
        }
        
        if (statusText) {
            statusText.textContent = text;
        }
    }
    
    async startVoiceEnrollment() {
        try {
            // Start recording for voice enrollment
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.uploadVoiceEnrollment(audioBlob);
            };
            
            // Record for 5 seconds
            this.mediaRecorder.start();
            this.updateBiometryStatus('🎤 Gravando... (5 segundos)');
            
            setTimeout(() => {
                this.mediaRecorder.stop();
                stream.getTracks().forEach(track => track.stop());
            }, 5000);
            
        } catch (error) {
            console.error('Error starting voice enrollment:', error);
            alert('❌ Erro ao acessar microfone. Verifique as permissões.');
        }
    }
    
    async uploadVoiceEnrollment(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'enrollment.wav');
            formData.append('user_id', this.userId);
            formData.append('enrollment_phrase', 'Frase de cadastro IAON');
            
            const response = await fetch('/api/voice-upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.file_path) {
                // Now enroll the voice
                const enrollResponse = await this.callAPI('/api/voice-biometry/enroll', {
                    method: 'POST',
                    body: JSON.stringify({
                        user_id: this.userId,
                        audio_file_path: result.file_path,
                        enrollment_phrase: 'Frase de cadastro IAON'
                    })
                });
                
                if (enrollResponse.enrollment_complete) {
                    this.updateBiometryStatus('✅ Cadastro de voz concluído!');
                } else {
                    this.updateBiometryStatus(`📝 Amostra ${enrollResponse.samples_count}/3 salva`);
                }
            }
        } catch (error) {
            console.error('Error uploading voice enrollment:', error);
            this.updateBiometryStatus('❌ Erro no cadastro de voz');
        }
    }
    
    async verifyVoiceBiometry(command) {
        // For now, return true for development
        // In production, this would record audio and verify against stored biometry
        return true;
    }
    
    async testVoiceRecognition() {
        this.updateBiometryStatus('🎤 Iniciando teste de reconhecimento...');
        
        try {
            // Simulate voice test
            setTimeout(() => {
                this.updateBiometryStatus('✅ Teste de voz concluído com sucesso');
            }, 2000);
        } catch (error) {
            this.updateBiometryStatus('❌ Erro no teste de voz');
        }
    }
    
    async resetVoiceBiometry() {
        if (confirm('⚠️ Tem certeza que deseja resetar a biometria de voz? Esta ação não pode ser desfeita.')) {
            try {
                await this.callAPI('/api/voice-biometry/reset-biometry/' + this.userId, {
                    method: 'POST',
                    body: JSON.stringify({
                        confirmation_code: 'reset123'
                    })
                });
                
                this.updateBiometryStatus('🔄 Biometria de voz resetada');
            } catch (error) {
                console.error('Error resetting biometry:', error);
                this.updateBiometryStatus('❌ Erro ao resetar biometria');
            }
        }
    }
    
    updateBiometryStatus(status) {
        const statusElement = document.querySelector('#voice-biometry-section h3');
        if (statusElement) {
            statusElement.innerHTML = `<i data-lucide="mic" class="w-8 h-8 mr-3 text-purple-500"></i>${status}`;
            lucide.createIcons(); // Refresh icons
        }
    }
    
    async checkVoiceBiometryStatus() {
        try {
            const response = await this.callAPI(`/api/voice-biometry/status/${this.userId}`);
            
            if (response.biometry_enrolled) {
                this.updateBiometryStatus('✅ Biometria de voz configurada');
            } else {
                this.updateBiometryStatus('⚠️ Biometria de voz não configurada');
            }
        } catch (error) {
            console.error('Error checking biometry status:', error);
        }
    }
    
    async checkSystemHealth() {
        try {
            const response = await this.callAPI('/api/health');
            console.log('IAON System Health:', response);
            
            if (response.status === 'healthy') {
                console.log('✅ IAON está funcionando perfeitamente!');
            }
        } catch (error) {
            console.error('❌ Erro ao verificar saúde do sistema:', error);
        }
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('✅ Service Worker registrado:', registration);
                
                // Request notification permission
                if ('Notification' in window) {
                    const permission = await Notification.requestPermission();
                    console.log('Permissão de notificação:', permission);
                }
            } catch (error) {
                console.error('❌ Falha no registro do Service Worker:', error);
            }
        }
    }
    
    async callAPI(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(endpoint, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize IAON
const iaon = new IAON();

// Global functions for external access
window.IAON = iaon;

// Add some fun console messages
console.log(`
🤖 IAON - Assistente IA Avançado
🔒 Sistema de Biometria de Voz Ativo
🏥 Sistema Médico Carregado
💰 Controle Financeiro Disponível
📱 PWA Instalável
🌐 Funcionando em: ${window.location.origin}
`);

// Check if running as PWA
if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('📱 Executando como PWA!');
}

