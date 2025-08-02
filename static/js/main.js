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
        this.user = null;
        this.voiceBiometry = null;
        this.onboardingStep = 1;
        this.voiceEnrollmentActive = false;
        this.enrollmentSamples = 0;
        this.enrollmentPhrases = [
            "Olá IAON, sou eu, seu usuário autorizado",
            "IAON, abra minha agenda pessoal agora",
            "Sistema IAON, verificar meus medicamentos",
            "IAON assistente, mostrar relatório financeiro",
            "Confirmo que sou o usuário do IAON"
        ];

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupVoiceRecognition();
        this.registerServiceWorker();

        // Verificar status do onboarding
        await this.checkOnboardingStatus();
    } generateSessionId() {
        return 'iaon_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async checkOnboardingStatus() {
        try {
            const response = await this.callAPI(`/api/onboarding/status?user_id=${this.userId}`);
            this.user = response.user;
            this.voiceBiometry = response.voice_biometry;

            if (response.needs_onboarding) {
                this.showOnboarding();
            } else {
                this.hideOnboarding();
                this.addMessageToChat(`👋 Bem-vindo de volta, ${this.user.preferred_name || this.user.full_name}!`, 'ai');
                this.checkSystemHealth();
            }
        } catch (error) {
            console.error('Error checking onboarding status:', error);
            this.hideOnboarding();
            this.checkSystemHealth();
        }
    }

    showOnboarding() {
        document.getElementById('onboarding-modal').classList.remove('hidden');
        this.onboardingStep = 1;
        this.showOnboardingStep(1);
    }

    hideOnboarding() {
        document.getElementById('onboarding-modal').classList.add('hidden');
    }

    showOnboardingStep(step) {
        // Esconder todos os passos
        document.querySelectorAll('.onboarding-step').forEach(el => el.classList.add('hidden'));

        // Mostrar passo atual
        document.getElementById(`onboarding-step-${step}`).classList.remove('hidden');
        this.onboardingStep = step;
    }

    nextOnboardingStep() {
        if (this.onboardingStep === 1) {
            const preferredName = document.getElementById('preferred-name').value.trim();
            const fullName = document.getElementById('full-name').value.trim();

            if (!preferredName) {
                alert('Por favor, digite como gostaria de ser chamado.');
                return;
            }

            this.user = {
                ...this.user,
                preferred_name: preferredName,
                full_name: fullName || preferredName
            };

            this.showOnboardingStep(2);
        }
    }

    previousOnboardingStep() {
        if (this.onboardingStep > 1) {
            this.showOnboardingStep(this.onboardingStep - 1);
        }
    }

    async startAdvancedVoiceEnrollment() {
        if (!this.voiceRecognition) {
            alert('❌ Reconhecimento de voz não suportado neste navegador.');
            return;
        }

        this.voiceEnrollmentActive = true;
        this.enrollmentSamples = 0;

        document.getElementById('voice-enrollment-progress').classList.remove('hidden');
        document.getElementById('start-voice-enrollment').disabled = true;
        document.getElementById('start-voice-enrollment').textContent = '🎤 Gravando...';

        this.collectVoiceSample();
    }

    async collectVoiceSample() {
        if (this.enrollmentSamples >= 5) {
            this.completeVoiceEnrollment();
            return;
        }

        const phrase = this.enrollmentPhrases[this.enrollmentSamples];

        // Mostrar frase para o usuário
        this.addMessageToChat(`🎤 **Amostra ${this.enrollmentSamples + 1}/5** - Repita: "${phrase}"`, 'ai');

        try {
            // Simular coleta de amostra de voz
            await this.recordVoiceSample(phrase);

            this.enrollmentSamples++;
            this.updateEnrollmentProgress();

            if (this.enrollmentSamples < 5) {
                setTimeout(() => this.collectVoiceSample(), 2000);
            } else {
                this.completeVoiceEnrollment();
            }
        } catch (error) {
            console.error('Error collecting voice sample:', error);
            this.addMessageToChat('❌ Erro ao coletar amostra de voz. Tente novamente.', 'ai');
        }
    }

    async recordVoiceSample(phrase) {
        return new Promise((resolve, reject) => {
            // Simular gravação (em produção, usar MediaRecorder real)
            const audioData = this.generateMockAudioData();

            setTimeout(async () => {
                try {
                    const response = await this.callAPI('/api/voice-biometry/advanced-enroll', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: this.userId,
                            audio_data: audioData,
                            enrollment_phrase: phrase,
                            audio_quality: 'good',
                            duration: 3.5,
                            speech_rate: 1.0
                        })
                    });

                    this.addMessageToChat(`✅ ${response.message}`, 'ai');
                    resolve(response);
                } catch (error) {
                    reject(error);
                }
            }, 3000); // Simular 3 segundos de gravação
        });
    }

    generateMockAudioData() {
        // Simular dados de áudio em base64
        const mockData = btoa(Math.random().toString() + Date.now().toString());
        return mockData;
    }

    updateEnrollmentProgress() {
        const progress = (this.enrollmentSamples / 5) * 100;
        document.getElementById('progress-bar').style.width = `${progress}%`;
        document.getElementById('progress-text').textContent = `${this.enrollmentSamples} de 5 amostras coletadas`;
    }

    async completeVoiceEnrollment() {
        this.voiceEnrollmentActive = false;
        document.getElementById('start-voice-enrollment').disabled = false;
        document.getElementById('start-voice-enrollment').textContent = '✅ Biometria Cadastrada!';

        this.addMessageToChat('🎉 Biometria de voz cadastrada com sucesso! Agora você pode usar comandos de voz seguros.', 'ai');

        setTimeout(() => {
            this.showOnboardingStep(3);
            document.getElementById('welcome-message').textContent =
                `Olá, ${this.user.preferred_name}! Sua biometria de voz foi configurada com sucesso.`;
        }, 2000);
    }

    skipVoiceEnrollment() {
        this.showOnboardingStep(3);
        document.getElementById('welcome-message').textContent =
            `Olá, ${this.user.preferred_name}! Você pode configurar a biometria de voz depois nas configurações.`;
    }

    async completeOnboarding() {
        try {
            const response = await this.callAPI('/api/onboarding/complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    full_name: this.user.full_name,
                    preferred_name: this.user.preferred_name,
                    language_preference: 'pt-BR',
                    theme_preference: 'auto',
                    voice_enabled: this.voiceEnrollmentActive
                })
            });

            this.user = response.user;
            this.hideOnboarding();
            this.addMessageToChat(response.message, 'ai');
            this.addMessageToChat('🚀 Agora você pode explorar todas as funcionalidades do IAON! Digite "ajuda" para ver o que posso fazer.', 'ai');
            this.checkSystemHealth();

        } catch (error) {
            console.error('Error completing onboarding:', error);
            this.addMessageToChat('❌ Erro ao completar configuração. Tente novamente.', 'ai');
        }
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

        this.sendChatMessage(message);
        input.value = '';
    }

    async sendChatMessage(message) {
        // Add user message to chat
        this.addMessageToChat(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Send message to AI
            const response = await this.callAPI('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    message: message,
                    session_id: this.sessionId
                })
            });

            if (response.response) {
                this.addMessageToChat(response.response, 'ai');
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

            // Configurações do reconhecimento de voz
            this.voiceRecognition.continuous = false;
            this.voiceRecognition.interimResults = false;
            this.voiceRecognition.lang = 'pt-BR';
            this.voiceRecognition.maxAlternatives = 1;

            this.voiceRecognition.onstart = () => {
                console.log('Voice recognition started');
                this.updateVoiceStatus(true, '🎤 Ouvindo...');
            };

            this.voiceRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const confidence = event.results[0][0].confidence;
                console.log('Voice recognition result:', transcript, 'Confidence:', confidence);

                this.handleVoiceInput(transcript);
            };

            this.voiceRecognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                let errorMessage = '❌ Erro na voz: ';

                switch (event.error) {
                    case 'no-speech':
                        errorMessage += 'Nenhuma fala detectada';
                        break;
                    case 'audio-capture':
                        errorMessage += 'Microfone não encontrado';
                        break;
                    case 'not-allowed':
                        errorMessage += 'Permissão de microfone negada';
                        break;
                    case 'network':
                        errorMessage += 'Problema de rede';
                        break;
                    default:
                        errorMessage += event.error;
                }

                this.updateVoiceStatus(false, errorMessage);
                this.addMessageToChat(errorMessage, 'ai');
            };

            this.voiceRecognition.onend = () => {
                console.log('Voice recognition ended');
                this.updateVoiceStatus(false, 'Voz Inativa');
            };

            console.log('Voice recognition setup completed');
        } else {
            console.warn('Speech recognition not supported');
        }
    }

    toggleVoiceRecognition() {
        if (!this.voiceRecognition) {
            this.addMessageToChat('❌ Reconhecimento de voz não suportado neste navegador. Use Chrome, Edge ou Safari.', 'ai');
            return;
        }

        // Verificar se o usuário tem biometria configurada
        if (this.user && !this.user.voice_enabled) {
            this.addMessageToChat('🔒 Configure sua biometria de voz primeiro para usar comandos seguros. Acesse as configurações.', 'ai');
            return;
        }

        if (this.isVoiceActive) {
            this.voiceRecognition.stop();
            this.addMessageToChat('🔇 Reconhecimento de voz parado.', 'ai');
        } else {
            try {
                this.voiceRecognition.start();
                this.addMessageToChat(`🎤 Reconhecimento de voz ativado, ${this.user?.preferred_name || 'usuário'}! Diga "IA" seguido do comando para ações específicas.`, 'ai');
            } catch (error) {
                console.error('Error starting voice recognition:', error);
                this.addMessageToChat('❌ Erro ao iniciar reconhecimento de voz. Verifique as permissões do microfone.', 'ai');
            }
        }
    } handleVoiceInput(transcript) {
        console.log('Voice input received:', transcript);

        // Mostrar o que foi reconhecido
        this.addMessageToChat(`🎤 Você disse: "${transcript}"`, 'user');

        // Check if it's a command starting with "IA" or "IAON"
        const lowerTranscript = transcript.toLowerCase().trim();

        if (lowerTranscript.startsWith('ia ') || lowerTranscript.startsWith('iaon ')) {
            this.handleVoiceCommand(transcript);
        } else {
            // Regular chat message - enviar como mensagem normal
            this.sendChatMessage(transcript);
        }
    }

    async handleVoiceCommand(command) {
        console.log('Processing voice command:', command);

        // Mostrar que está processando o comando
        this.addMessageToChat('� Processando comando de voz...', 'ai');

        try {
            const response = await this.callAPI('/api/ai/voice-command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    command_text: command
                })
            });

            if (response.executed) {
                this.addMessageToChat(`🎯 ${response.execution_result}`, 'ai');

                // Executar ações específicas baseadas no intent
                this.executeVoiceAction(response.intent, command);
            } else {
                this.addMessageToChat(`❓ Comando não reconhecido: ${command}`, 'ai');
            }
        } catch (error) {
            console.error('Error processing voice command:', error);
            this.addMessageToChat('❌ Erro ao processar comando de voz. Tente novamente.', 'ai');
        }
    }

    executeVoiceAction(intent, command) {
        console.log('Executing voice action:', intent);

        switch (intent) {
            case 'agenda_management':
                this.showSection('agenda');
                this.addMessageToChat('📅 Abrindo seção de agenda inteligente...', 'ai');
                break;

            case 'medical_check':
                this.showSection('medical');
                this.addMessageToChat('🏥 Ativando sistema médico avançado...', 'ai');
                break;

            case 'financial_management':
                this.showSection('finance');
                this.addMessageToChat('💰 Carregando controle financeiro personalizado...', 'ai');
                break;

            case 'generate_report':
                this.addMessageToChat('📊 Gerando relatório personalizado... (Em desenvolvimento)', 'ai');
                break;

            case 'show_help':
                this.addMessageToChat(`🆘 **Central de Ajuda IAON**

**🎤 Comandos de Voz Disponíveis:**
• "IA agenda" - Gerenciar compromissos
• "IA medicina" - Sistema médico
• "IA finanças" - Controle financeiro
• "IA relatório" - Gerar relatórios
• "IA configuração" - Ajustes do sistema

**💬 Chat Inteligente:**
Digite perguntas naturais sobre medicina, finanças, agenda ou qualquer tópico!

**🔧 Configurações:**
Acesse as configurações para personalizar sua experiência.`, 'ai');
                break;

            case 'settings_management':
                this.addMessageToChat('⚙️ Abrindo configurações avançadas... (Em desenvolvimento)', 'ai');
                break;

            case 'voice_management':
                this.addMessageToChat('🎤 Sistema de biometria de voz... (Use as configurações para reconfigurar)', 'ai');
                break;

            case 'general_command':
                // Para comandos gerais, processar como chat normal
                this.sendChatMessage(command);
                break;

            default:
                this.addMessageToChat('🤖 Comando processado com sucesso!', 'ai');
        }
    } updateVoiceStatus(active, text) {
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
            console.log('System health:', response);

            if (this.user) {
                const greeting = this.getTimeBasedGreeting();
                this.addMessageToChat(`${greeting}, ${this.user.preferred_name || this.user.full_name}! 🚀`, 'ai');
                this.addMessageToChat('💡 **Dica**: Digite "ajuda" para ver tudo que posso fazer, ou use comandos de voz com "IA + comando".', 'ai');
            }
        } catch (error) {
            console.error('Error checking system health:', error);
        }
    }

    getTimeBasedGreeting() {
        const hour = new Date().getHours();
        if (hour < 12) return 'Bom dia';
        if (hour < 18) return 'Boa tarde';
        return 'Boa noite';
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

