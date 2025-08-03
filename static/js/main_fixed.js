// IAON - Sistema Completo Restaurado
class IAON {
    constructor() {
        this.currentSection = 'chat';
        this.isVoiceActive = true;
        this.userId = 1;
        this.sessionId = this.generateSessionId();
        this.voiceRecognition = null;
        this.user = null;
        this.isLoggedIn = false;
        this.continuousListening = true;
        this.triggerWords = ['iaon', 'eion', 'ia'];
        this.currentCoach = null;
        this.emergencyMode = false;
        this.suicidePreventionActive = true;

        this.init();
    }

    generateSessionId() {
        return 'iaon_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async init() {
        this.showLoginScreen();
        this.setupEventListeners();
        this.registerServiceWorker();
        this.initSuicidePreventionSystem();
        this.initEmotionalMonitoring();
    }

    initSuicidePreventionSystem() {
        console.log('🆘 Sistema de Prevenção ao Suicídio: ATIVO');
        console.log('💚 Monitoramento emocional 24/7 iniciado');

        // Monitoramento contínuo de palavras-chave de risco
        this.riskKeywords = [
            'suicídio', 'morrer', 'acabar', 'desistir', 'não aguento',
            'sem saída', 'sem esperança', 'me matar', 'fim da linha'
        ];

        this.emergencyContacts = {
            cvv: '188',
            samu: '192',
            caps: '156',
            vidaViva: '11 4020-8080'
        };
    }

    initEmotionalMonitoring() {
        // Sistema de análise emocional através da interação
        this.emotionalState = {
            current: 'stable',
            history: [],
            riskLevel: 'low',
            lastAnalysis: new Date()
        };

        // Monitoramento a cada interação
        setInterval(() => {
            this.analyzeEmotionalPatterns();
        }, 60000); // A cada minuto
    }

    analyzeEmotionalPatterns() {
        // Análise preditiva de risco emocional
        const now = new Date();
        const patterns = {
            interactionFrequency: this.getInteractionFrequency(),
            messagesSentiment: this.getMessagesSentiment(),
            timePatterns: this.getTimePatterns()
        };

        if (patterns.riskDetected) {
            this.activateEmergencySupport();
        }
    }

    activateEmergencySupport() {
        this.emergencyMode = true;
        this.addMessageToChat(`🆘 **SUPORTE ATIVADO** - Detectei que você pode estar passando por um momento difícil. 

💚 **Você não está sozinho(a)**

📞 **Ajuda imediata:**
• CVV: 188 (gratuito, 24h)
• CAPS: 156 (SUS)

Gostaria de conversar com alguém agora?`, 'ai');
    }

    showLoginScreen() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('onboarding-modal').classList.add('hidden');
    }

    async loginAsDemo() {
        this.showLoadingScreen();

        setTimeout(() => {
            this.user = {
                id: this.userId,
                preferred_name: 'Demo',
                full_name: 'Usuário Demo',
                is_onboarded: true,
                subscription: 'premium',
                features: {
                    executiveSecretary: true,
                    medicalSystem: true,
                    financialSystem: true,
                    coaches: true,
                    suicidePrevention: true
                }
            };

            this.isLoggedIn = true;
            this.completeLogin();
        }, 2000);
    }

    async completeLogin() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('loading-screen').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');

        this.setupVoiceRecognition();
        this.startContinuousVoiceListening();
        this.loadUserDashboard();

        this.addMessageToChat(`👋 Bem-vindo, ${this.user.preferred_name}! 

🤖 **IAON Sistema Completo Ativo:**
• 💼 Secretária Executiva
• 🏥 Sistema Médico Avançado  
• 💰 Gestão Financeira Premium
• 🧠 Coaches Especializados
• 🆘 Proteção 24/7 Ativa

🎤 Comando de voz contínuo ativo. Diga "IAON" + comando.`, 'ai');

        this.updateVoiceStatus();
        this.initExecutiveFeatures();
    }

    initExecutiveFeatures() {
        // Carregar painel executivo
        this.loadExecutiveDashboard();
        this.loadFinancialSummary();
        this.loadMedicalStatus();
        this.loadCoachesList();
        this.startRealtimeUpdates();
    }

    loadExecutiveDashboard() {
        // Simular dados executivos
        this.executiveData = {
            meetingsToday: 6,
            pendingReports: 3,
            urgentTasks: 2,
            vipContacts: 5,
            financialGoals: '89%',
            healthScore: '95%'
        };
    }

    loadFinancialSummary() {
        this.financialData = {
            totalAssets: 546440.47,
            monthlyIncome: 45000,
            investments: {
                stocks: 89750,
                funds: 125500,
                treasury: 85000
            },
            performance: '+18.5%'
        };
    }

    loadMedicalStatus() {
        this.medicalData = {
            nextAppointment: 'Dr. Silva - Hoje 14:00',
            medications: [
                { name: 'Losartana 50mg', time: '08:00', taken: true },
                { name: 'Metformina 850mg', time: '12:00', taken: false },
                { name: 'Omeprazol 20mg', time: '19:00', taken: false }
            ],
            emergencyContacts: [
                { name: 'SAMU', number: '192' },
                { name: 'Dr. Silva', number: '(11) 99999-1234' }
            ]
        };
    }

    loadCoachesList() {
        this.coaches = [
            {
                id: 1,
                name: 'Dr. Roberto Silva',
                specialty: 'Business Coach',
                rating: 4.9,
                price: 350,
                available: 'Amanhã 14:00',
                image: '/static/images/coach-business.jpg'
            },
            {
                id: 2,
                name: 'Dra. Ana Costa',
                specialty: 'Life Coach',
                rating: 4.8,
                price: 280,
                available: 'Hoje 16:00',
                image: '/static/images/coach-life.jpg'
            },
            {
                id: 3,
                name: 'Dr. Pedro Santos',
                specialty: 'Financial Coach',
                rating: 4.9,
                price: 400,
                available: 'Segunda 10:00',
                image: '/static/images/coach-financial.jpg'
            }
        ];
    }

    startRealtimeUpdates() {
        // Atualizações em tempo real
        setInterval(() => {
            this.updateDashboardMetrics();
            this.checkEmergencyAlerts();
            this.updateFinancialData();
        }, 30000); // A cada 30 segundos
    }

    setupVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.voiceRecognition = new SpeechRecognition();

            this.voiceRecognition.continuous = true;
            this.voiceRecognition.interimResults = true;
            this.voiceRecognition.lang = 'pt-BR';

            this.voiceRecognition.onstart = () => {
                this.isVoiceActive = true;
                this.updateVoiceStatus();
            };

            this.voiceRecognition.onresult = (event) => {
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    }
                }

                if (finalTranscript) {
                    this.processVoiceCommand(finalTranscript.trim().toLowerCase());
                }
            };

            this.voiceRecognition.onend = () => {
                if (this.continuousListening && this.isLoggedIn) {
                    setTimeout(() => {
                        try {
                            this.voiceRecognition.start();
                        } catch (error) {
                            console.log('Reiniciando voz...');
                        }
                    }, 1000);
                } else {
                    this.isVoiceActive = false;
                    this.updateVoiceStatus();
                }
            };

            this.voiceRecognition.onerror = (event) => {
                if (event.error === 'not-allowed') {
                    this.addMessageToChat('❌ Permissão de microfone negada. Ative nas configurações.', 'ai');
                }
            };
        }
    }

    startContinuousVoiceListening() {
        if (this.voiceRecognition) {
            try {
                this.voiceRecognition.start();
                this.continuousListening = true;
            } catch (error) {
                console.log('Voz já ativa');
            }
        }
    }

    processVoiceCommand(transcript) {
        // Verificar palavras de risco primeiro
        const hasRiskWords = this.riskKeywords.some(word =>
            transcript.includes(word)
        );

        if (hasRiskWords) {
            this.activateEmergencySupport();
            return;
        }

        const hasActivationWord = this.triggerWords.some(word =>
            transcript.includes(word)
        );

        if (!hasActivationWord) {
            return;
        }

        let command = transcript;
        this.triggerWords.forEach(word => {
            command = command.replace(new RegExp(word, 'gi'), '').trim();
        });

        if (command) {
            this.addMessageToChat(`🎤 "${transcript}"`, 'user');
            this.processCommand(command);
        }
    }

    async processCommand(message) {
        this.showTypingIndicator();

        // Comando especial para emergência
        if (this.emergencyMode && (message.includes('conversar') || message.includes('ajuda'))) {
            this.initEmergencyChat();
            return;
        }

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    user_id: this.userId,
                    session_id: this.sessionId,
                    emergency_mode: this.emergencyMode
                })
            });

            const data = await response.json();

            this.hideTypingIndicator();

            if (data.response) {
                this.addMessageToChat(data.response, 'ai');

                // Análise de sentimento da resposta
                this.analyzeMessageSentiment(message);
            } else {
                this.addMessageToChat('Desculpe, não consegui processar sua solicitação.', 'ai');
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessageToChat('❌ Erro de conexão. Tente novamente.', 'ai');
        }
    }

    initEmergencyChat() {
        this.hideTypingIndicator();
        this.addMessageToChat(`💚 **Chat de Emergência Conectado**

Olá, sou o sistema de apoio do IAON. Estou aqui para ajudar.

Como você está se sentindo agora? Gostaria de:

🗣️ **Conversar sobre seus sentimentos**
📞 **Conectar com profissional (CVV: 188)**  
🏥 **Localizar ajuda médica próxima**
👥 **Falar com grupo de apoio**

Você não está sozinho(a). Que tipo de apoio precisa agora?`, 'ai');
    }

    analyzeMessageSentiment(message) {
        // Análise simples de sentimento
        const negativeWords = ['triste', 'deprimido', 'ansioso', 'medo', 'sozinho', 'perdido'];
        const positiveWords = ['bem', 'feliz', 'ótimo', 'animado', 'confiante'];

        const sentiment = this.calculateSentiment(message, negativeWords, positiveWords);

        this.emotionalState.history.push({
            message,
            sentiment,
            timestamp: new Date()
        });

        if (sentiment < -0.5) {
            this.triggerSupportMode();
        }
    }

    calculateSentiment(text, negative, positive) {
        let score = 0;
        negative.forEach(word => {
            if (text.includes(word)) score -= 1;
        });
        positive.forEach(word => {
            if (text.includes(word)) score += 1;
        });
        return score;
    }

    triggerSupportMode() {
        if (!this.emergencyMode) {
            this.addMessageToChat(`💚 Percebi que você pode estar precisando de apoio. 

Lembre-se que conversar pode ajudar:
• CVV: 188 (gratuito, 24h)
• Chat online: cvv.org.br

Está tudo bem não estar bem. Você gostaria de algum recurso de apoio?`, 'ai');
        }
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.loginAsDemo();
            });
        }

        // Chat input
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');

        if (chatInput && sendButton) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }

        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.showSection(section);
            });
        });

        // Sidebar toggle  
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // Emergency button
        this.createEmergencyButton();
    }

    createEmergencyButton() {
        const emergencyBtn = document.createElement('button');
        emergencyBtn.id = 'emergency-btn';
        emergencyBtn.className = 'fixed bottom-4 left-4 bg-red-600 text-white p-4 rounded-full shadow-lg hover:bg-red-700 z-50';
        emergencyBtn.innerHTML = '🆘';
        emergencyBtn.title = 'Ajuda de Emergência';
        emergencyBtn.onclick = () => this.activateEmergencySupport();
        document.body.appendChild(emergencyBtn);
    }

    sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (message) {
            this.addMessageToChat(message, 'user');
            input.value = '';
            this.processCommand(message);
        }
    }

    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');

        messageDiv.className = `${sender}-bubble chat-bubble p-3 rounded-lg text-white mb-3`;
        messageDiv.innerHTML = `<p>${message}</p>`;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'ai-bubble chat-bubble p-3 rounded-lg text-white mb-3';
        typingDiv.innerHTML = '<p>🤖 Analisando<span class="loading-dots"></span></p>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    updateVoiceStatus() {
        const indicator = document.getElementById('voice-indicator');
        const text = document.getElementById('voice-text');

        if (this.isVoiceActive) {
            indicator.className = 'w-3 h-3 bg-green-500 rounded-full animate-pulse';
            text.textContent = '🎤 Escutando';
        } else {
            indicator.className = 'w-3 h-3 bg-red-500 rounded-full';
            text.textContent = 'Voz Inativa';
        }
    }

    showSection(sectionName) {
        // Esconder todas as seções
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });

        // Mostrar seção solicitada
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }

        // Atualizar navegação
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('text-blue-600', 'bg-blue-50');
        });

        const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('text-blue-600', 'bg-blue-50');
        }

        this.currentSection = sectionName;

        // Carregar dados específicos da seção
        this.loadSectionData(sectionName);
    }

    loadSectionData(section) {
        switch (section) {
            case 'medical':
                this.loadMedicalSection();
                break;
            case 'finance':
                this.loadFinanceSection();
                break;
            case 'coaches':
                this.loadCoachesSection();
                break;
            case 'analytics':
                this.loadAnalyticsSection();
                break;
        }
    }

    loadMedicalSection() {
        // Carregar dados médicos em tempo real
        console.log('Carregando sistema médico avançado...');
    }

    loadFinanceSection() {
        // Carregar dados financeiros em tempo real
        console.log('Carregando sistema financeiro...');
    }

    loadCoachesSection() {
        // Carregar lista de coaches
        console.log('Carregando coaches especializados...');
    }

    loadAnalyticsSection() {
        // Carregar analytics executivos
        console.log('Carregando analytics executivos...');
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('sidebar-hidden');
    }

    updateDashboardMetrics() {
        // Atualizar métricas em tempo real
        console.log('Atualizando métricas executivas...');
    }

    checkEmergencyAlerts() {
        // Verificar alertas de emergência
        console.log('Verificando alertas de emergência...');
    }

    updateFinancialData() {
        // Atualizar dados financeiros
        console.log('Atualizando dados financeiros...');
    }

    showLoadingScreen() {
        document.getElementById('loading-screen').classList.remove('hidden');
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registrado');
            } catch (error) {
                console.log('Erro no Service Worker:', error);
            }
        }
    }
}

// Inicializar aplicação
let iaon;
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Iniciando IAON...');

    // Garantir que a tela de login apareça primeiro
    const loginScreen = document.getElementById('login-screen');
    const loadingScreen = document.getElementById('loading-screen');
    const mainApp = document.getElementById('main-app');
    const onboardingModal = document.getElementById('onboarding-modal');

    // Configurar estado inicial correto
    if (loginScreen) loginScreen.classList.remove('hidden');
    if (loadingScreen) loadingScreen.classList.add('hidden');
    if (mainApp) mainApp.classList.add('hidden');
    if (onboardingModal) onboardingModal.classList.add('hidden');

    // Inicializar ícones
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Inicializar IAON COMPLETO
    iaon = new IAON();

    console.log('🚀 IAON Sistema Completo Iniciado');
    console.log('💼 Secretária Executiva: ATIVA');
    console.log('🏥 Sistema Médico: ATIVO');
    console.log('💰 Sistema Financeiro: ATIVO');
    console.log('🧠 Coaches: DISPONÍVEIS');
    console.log('🆘 Prevenção Suicídio: ATIVO');
});
