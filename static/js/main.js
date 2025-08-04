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

        // Sistema de Reuniões
        this.currentMeeting = null;
        this.isRecording = false;
        this.meetingRecorder = null;
        this.meetingAudioChunks = [];
        this.meetingParticipants = [];
        this.transcriptionInterval = null;

        this.init();
    }

    // Obter palavra de ativação personalizada do usuário
    getTriggerWord() {
        return this.user?.custom_trigger_word || 'EION';
    }

    // Gerar exemplos de comandos com palavra personalizada
    getTriggerExamples() {
        const trigger = this.getTriggerWord();
        return [
            `"${trigger}, ligar para João"`,
            `"${trigger}, abrir WhatsApp"`,
            `"${trigger}, iniciar reunião"`,
            `"${trigger}, configuração"`,
            `"${trigger}, ajuda"`
        ];
    }

    async init() {
        this.setupEventListeners();
        this.setupVoiceRecognition();
        this.registerServiceWorker();

        // Verificar status do onboarding
        await this.checkOnboardingStatus();
    }

    generateSessionId() {
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

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'apps':
                await this.loadAppsData();
                break;
            case 'contacts':
                await this.loadContactsData();
                break;
            case 'call_logs':
                await this.loadCallLogsData();
                break;
            case 'meetings':
                await this.loadMeetingsData();
                break;
            case 'participants':
                await this.loadParticipantsData();
                break;
            default:
                // No specific data loading needed
                break;
        }
    }

    async loadAppsData() {
        try {
            const response = await this.callAPI(`/api/apps/list/${this.userId}?limit=20&sort_by=usage_count`);

            if (response.success) {
                this.displayAppsData(response.apps, response.total_apps, response.enabled_apps);
            } else {
                console.error('Error loading apps:', response.error);
            }
        } catch (error) {
            console.error('Error loading apps data:', error);
        }
    }

    async loadContactsData() {
        try {
            // Simular dados de contatos (em produção, integraria com API real)
            const contactsData = {
                contacts: [
                    { id: 1, name: 'João Silva', phone: '+55 11 99999-1234', is_favorite: true },
                    { id: 2, name: 'Maria Santos', phone: '+55 11 88888-5678', is_favorite: false },
                    { id: 3, name: 'Pedro Oliveira', phone: '+55 11 77777-9012', is_favorite: true }
                ],
                total: 3,
                favorites: 2
            };

            this.displayContactsData(contactsData.contacts, contactsData.total, contactsData.favorites);
        } catch (error) {
            console.error('Error loading contacts data:', error);
        }
    }

    async loadCallLogsData() {
        try {
            // Simular dados de histórico de chamadas
            const callLogsData = {
                calls: [
                    { id: 1, contact_name: 'João Silva', phone: '+55 11 99999-1234', type: 'outgoing', duration: '5:23', timestamp: new Date(Date.now() - 3600000) },
                    { id: 2, contact_name: 'Maria Santos', phone: '+55 11 88888-5678', type: 'incoming', duration: '2:15', timestamp: new Date(Date.now() - 7200000) },
                    { id: 3, contact_name: 'Pedro Oliveira', phone: '+55 11 77777-9012', type: 'missed', duration: '0:00', timestamp: new Date(Date.now() - 10800000) }
                ],
                total: 3
            };

            this.displayCallLogsData(callLogsData.calls, callLogsData.total);
        } catch (error) {
            console.error('Error loading call logs data:', error);
        }
    }

    async loadMeetingsData() {
        try {
            const response = await this.callAPI(`/api/meetings/user/${this.userId}`);

            if (response.success) {
                this.displayMeetingsData(response.meetings);
            } else {
                console.error('Error loading meetings:', response.error);
            }
        } catch (error) {
            console.error('Error loading meetings data:', error);
        }
    }

    async loadParticipantsData() {
        try {
            // Inicializar busca
            searchParticipants();

            // Carregar participantes
            loadParticipants();
        } catch (error) {
            console.error('Error loading participants data:', error);
        }
    }

    displayAppsData(apps, totalApps, enabledApps) {
        const container = document.getElementById('apps-list') || this.createAppsContainer();

        if (!apps || apps.length === 0) {
            container.innerHTML = `
                <div class="text-center p-8">
                    <div class="text-gray-400 text-6xl mb-4">📱</div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Nenhum aplicativo encontrado</h3>
                    <p class="text-gray-500">Execute um escaneamento para detectar aplicativos instalados.</p>
                    <button onclick="iaon.scanApps()" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        🔍 Escanear Aplicativos
                    </button>
                </div>
            `;
            return;
        }

        const appsHtml = apps.map(app => `
            <div class="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <span class="text-2xl">📱</span>
                        </div>
                        <div>
                            <h3 class="font-medium text-gray-900">${app.display_name}</h3>
                            <p class="text-sm text-gray-500">${app.package_name}</p>
                            <div class="flex items-center space-x-2 mt-1">
                                <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                    Usado ${app.usage_count || 0}x
                                </span>
                                ${app.voice_aliases && app.voice_aliases.length > 0 ?
                `<span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                                        🎤 ${app.voice_aliases.join(', ')}
                                    </span>` : ''
            }
                            </div>
                        </div>
                    </div>
                    <div class="flex flex-col items-end space-y-2">
                        <button onclick="iaon.launchApp(${app.id})" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                                ${!app.is_enabled ? 'disabled' : ''}>
                            🚀 Abrir
                        </button>
                        <div class="text-xs text-gray-400">
                            ${app.last_used ? new Date(app.last_used).toLocaleDateString() : 'Nunca usado'}
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">📱 Aplicativos Instalados</h2>
                    <button onclick="iaon.scanApps()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        🔍 Escanear Novos Apps
                    </button>
                </div>
                <div class="grid grid-cols-3 gap-4 text-center mb-6">
                    <div class="bg-blue-50 rounded-lg p-3">
                        <div class="text-2xl font-bold text-blue-600">${totalApps}</div>
                        <div class="text-sm text-gray-600">Total de Apps</div>
                    </div>
                    <div class="bg-green-50 rounded-lg p-3">
                        <div class="text-2xl font-bold text-green-600">${enabledApps}</div>
                        <div class="text-sm text-gray-600">Apps Habilitados</div>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-3">
                        <div class="text-2xl font-bold text-purple-600">${apps.filter(app => app.voice_aliases && app.voice_aliases.length > 0).length}</div>
                        <div class="text-sm text-gray-600">Com Comandos de Voz</div>
                    </div>
                </div>
            </div>
            <div class="space-y-3">${appsHtml}</div>
        `;
    }

    displayContactsData(contacts, total, favorites) {
        const container = document.getElementById('contacts-list') || this.createContactsContainer();
        const trigger = this.getTriggerWord();

        if (!contacts || contacts.length === 0) {
            container.innerHTML = `
                <div class="text-center p-8">
                    <div class="text-gray-400 text-6xl mb-4">📞</div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Nenhum contato encontrado</h3>
                    <p class="text-gray-500">Adicione contatos para usar comandos de voz.</p>
                </div>
            `;
            return;
        }

        const contactsHtml = contacts.map(contact => `
            <div class="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <span class="text-lg">👤</span>
                        </div>
                        <div>
                            <h3 class="font-medium text-gray-900">
                                ${contact.name}
                                ${contact.is_favorite ? '<span class="text-yellow-500">⭐</span>' : ''}
                            </h3>
                            <p class="text-sm text-gray-500">${contact.phone}</p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="iaon.callContact('${contact.phone}')" 
                                class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                            📞 Ligar
                        </button>
                        <button onclick="iaon.voiceCallContact('${contact.name}')" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                            🎤 Por Voz
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">📞 Agenda de Contatos</h2>
                    <div class="text-sm text-gray-500">
                        ${total} contatos • ${favorites} favoritos
                    </div>
                </div>
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <h3 class="font-medium text-yellow-800 mb-2">🎤 Comandos de Voz Disponíveis:</h3>
                    <p class="text-sm text-yellow-700">
                        • "${trigger}, ligar para [nome do contato]"<br>
                        • "${trigger}, chamar [nome do contato]"<br>
                        • "${trigger}, telefonar para [nome do contato]"
                    </p>
                    <div class="mt-2 text-xs text-yellow-600">
                        💡 Sua palavra de ativação atual: <strong>"${trigger}"</strong>
                    </div>
                </div>
            </div>
            <div class="space-y-3">${contactsHtml}</div>
        `;
    } displayCallLogsData(calls, total) {
        const container = document.getElementById('call-logs-list') || this.createCallLogsContainer();

        if (!calls || calls.length === 0) {
            container.innerHTML = `
                <div class="text-center p-8">
                    <div class="text-gray-400 text-6xl mb-4">📋</div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Nenhuma chamada registrada</h3>
                    <p class="text-gray-500">Suas ligações aparecerão aqui.</p>
                </div>
            `;
            return;
        }

        const getCallIcon = (type) => {
            switch (type) {
                case 'outgoing': return '📞';
                case 'incoming': return '📲';
                case 'missed': return '📵';
                default: return '📞';
            }
        };

        const getCallColor = (type) => {
            switch (type) {
                case 'outgoing': return 'text-blue-600';
                case 'incoming': return 'text-green-600';
                case 'missed': return 'text-red-600';
                default: return 'text-gray-600';
            }
        };

        const callsHtml = calls.map(call => `
            <div class="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-8 h-8 flex items-center justify-center">
                            <span class="text-xl ${getCallColor(call.type)}">${getCallIcon(call.type)}</span>
                        </div>
                        <div>
                            <h3 class="font-medium text-gray-900">${call.contact_name}</h3>
                            <p class="text-sm text-gray-500">${call.phone}</p>
                            <p class="text-xs text-gray-400">
                                ${call.timestamp.toLocaleString()} • ${call.duration}
                            </p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="iaon.callContact('${call.phone}')" 
                                class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                            📞 Religar
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="mb-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">📋 Histórico de Chamadas</h2>
                <div class="text-sm text-gray-500 mb-4">
                    ${total} chamadas registradas
                </div>
            </div>
            <div class="space-y-3">${callsHtml}</div>
        `;
    }

    displayMeetingsData(meetings) {
        const container = document.getElementById('meetings-list') || this.createMeetingsContainer();

        if (!meetings || meetings.length === 0) {
            container.innerHTML = `
                <div class="text-center p-8">
                    <div class="text-gray-400 text-6xl mb-4">📹</div>
                    <h3 class="text-lg font-medium text-gray-700 mb-2">Nenhuma reunião registrada</h3>
                    <p class="text-gray-500">Inicie uma nova reunião para começar.</p>
                    <button onclick="iaon.startNewMeeting()" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        📹 Nova Reunião
                    </button>
                </div>
            `;
            return;
        }

        const meetingsHtml = meetings.map(meeting => `
            <div class="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="font-medium text-gray-900">${meeting.title}</h3>
                        <p class="text-sm text-gray-500">${meeting.description || 'Sem descrição'}</p>
                        <p class="text-xs text-gray-400">
                            ${new Date(meeting.start_time).toLocaleString()}
                            ${meeting.end_time ? ' - ' + new Date(meeting.end_time).toLocaleString() : ' (Em andamento)'}
                        </p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="iaon.viewMeeting(${meeting.id})" 
                                class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                            👁️ Ver Detalhes
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="mb-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-800">📹 Reuniões</h2>
                    <button onclick="iaon.startNewMeeting()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        📹 Nova Reunião
                    </button>
                </div>
            </div>
            <div class="space-y-3">${meetingsHtml}</div>
        `;
    }

    createAppsContainer() {
        const appsSection = document.getElementById('apps-section');
        const container = document.createElement('div');
        container.id = 'apps-list';
        container.className = 'p-6';
        appsSection.appendChild(container);
        return container;
    }

    createContactsContainer() {
        const contactsSection = document.getElementById('contacts-section');
        const container = document.createElement('div');
        container.id = 'contacts-list';
        container.className = 'p-6';
        contactsSection.appendChild(container);
        return container;
    }

    createCallLogsContainer() {
        const callLogsSection = document.getElementById('call_logs-section');
        const container = document.createElement('div');
        container.id = 'call-logs-list';
        container.className = 'p-6';
        callLogsSection.appendChild(container);
        return container;
    }

    createMeetingsContainer() {
        const meetingsSection = document.getElementById('meetings-section');
        const container = document.createElement('div');
        container.id = 'meetings-list';
        container.className = 'p-6';
        meetingsSection.appendChild(container);
        return container;
    }

    // Métodos de ação para as novas funcionalidades
    async scanApps() {
        try {
            this.addMessageToChat('🔍 Escaneando aplicativos instalados...', 'ai');

            const response = await this.callAPI('/api/apps/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    force_rescan: true
                })
            });

            if (response.success) {
                this.addMessageToChat(`✅ Escaneamento concluído! ${response.apps_added} novos aplicativos encontrados.`, 'ai');
                await this.loadAppsData(); // Recarregar lista
            } else {
                this.addMessageToChat(`❌ Erro no escaneamento: ${response.error}`, 'ai');
            }
        } catch (error) {
            this.addMessageToChat('❌ Erro ao escanear aplicativos.', 'ai');
            console.error('Error scanning apps:', error);
        }
    }

    async launchApp(appId) {
        try {
            const response = await this.callAPI('/api/apps/launch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    app_id: appId,
                    method: 'manual'
                })
            });

            if (response.success) {
                this.addMessageToChat(`✅ ${response.message}`, 'ai');
            } else {
                this.addMessageToChat(`❌ ${response.error}`, 'ai');
            }
        } catch (error) {
            this.addMessageToChat('❌ Erro ao abrir aplicativo.', 'ai');
            console.error('Error launching app:', error);
        }
    }

    // Mostrar ajuda com palavra de ativação personalizada
    showHelpWithTriggerWord() {
        const trigger = this.getTriggerWord();

        this.addMessageToChat(`🆘 **Central de Ajuda IAON**

**🎤 Sua palavra de ativação: "${trigger}"**

**🎤 Comandos de Voz Disponíveis:**
• "${trigger} reunião" - Sistema de reuniões com gravação
• "${trigger} agenda" - Gerenciar compromissos
• "${trigger} medicina" - Sistema médico
• "${trigger} finanças" - Controle financeiro
• "${trigger} contatos" - Agenda telefônica com voz
• "${trigger} ligar para [contato]" - Fazer ligações por voz
• "${trigger} abrir [app]" - Abrir aplicativos por comando
• "${trigger} relatório" - Gerar relatórios inteligentes
• "${trigger} configuração" - Ajustes do sistema

**📱 Comandos de Aplicativos:**
• "${trigger} abrir WhatsApp" - Abre o WhatsApp
• "${trigger} executar Instagram" - Abre o Instagram
• "${trigger} rodar Spotify" - Inicia o Spotify
• "${trigger} iniciar Netflix" - Abre o Netflix

**📞 Comandos de Contatos:**
• "${trigger} ligar para [nome]" - Faz chamada por voz
• "${trigger} contatos" - Abre agenda telefônica
• "${trigger} histórico de chamadas" - Mostra ligações recentes

**📹 Sistema de Reuniões:**
• Gravação automática de alta qualidade
• Reconhecimento de participantes por voz
• Transcrição em tempo real com IA
• Geração automática de pautas e conclusões
• Relatórios inteligentes com sugestões

**💬 Chat Inteligente:**
Digite perguntas naturais sobre medicina, finanças, agenda ou qualquer tópico!

**🔧 Configurações:**
Acesse as configurações para personalizar sua palavra de ativação ("${trigger}") e outras preferências.

**💡 Dica:** Para alterar sua palavra de ativação, use os endpoints:
• \`/api/voice/trigger-word/configure\` - Configurar nova palavra
• \`/api/voice/trigger-word/test\` - Testar reconhecimento
• \`/api/voice/trigger-word/suggestions\` - Ver sugestões`, 'ai');
    }

    callContact(phone) {
        // Simular chamada
        this.addMessageToChat(`📞 Simulando chamada para ${phone}...`, 'ai');
        console.log('Simulating call to:', phone);
    }

    voiceCallContact(contactName) {
        // Comando de voz para ligar
        const trigger = this.getTriggerWord();
        this.addMessageToChat(`🎤 Comando de voz: "${trigger}, ligar para ${contactName}"`, 'user');
        setTimeout(() => {
            this.handleVoiceCommand(`ligar para ${contactName}`);
        }, 1000);
    }

    startNewMeeting() {
        this.addMessageToChat('📹 Iniciando nova reunião...', 'ai');
        // Implementar lógica de nova reunião
    }

    viewMeeting(meetingId) {
        this.addMessageToChat(`👁️ Visualizando detalhes da reunião ${meetingId}...`, 'ai');
        // Implementar visualização de reunião
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

            // Configurações do reconhecimento de voz para interação contínua
            this.voiceRecognition.continuous = true;  // Reconhecimento contínuo
            this.voiceRecognition.interimResults = true;  // Resultados parciais
            this.voiceRecognition.lang = 'pt-BR';
            this.voiceRecognition.maxAlternatives = 3;  // Mais alternativas para melhor precisão

            this.voiceRecognition.onstart = () => {
                console.log('Voice recognition started');
                this.updateVoiceStatus(true, '🎤 IAON está ouvindo...');
            };

            this.voiceRecognition.onresult = (event) => {
                const lastResultIndex = event.results.length - 1;
                const result = event.results[lastResultIndex];

                if (result.isFinal) {
                    const transcript = result[0].transcript.trim();
                    const confidence = result[0].confidence;
                    console.log('Voice recognition result:', transcript, 'Confidence:', confidence);

                    // Só processa se tiver confiança mínima
                    if (confidence > 0.3 && transcript.length > 2) {
                        this.handleAdvancedVoiceInput(transcript, confidence);
                    }
                }
            };

            this.voiceRecognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
                let errorMessage = '❌ Erro na voz: ';

                switch (event.error) {
                    case 'no-speech':
                        // Não mostrar erro para ausência de fala, é normal
                        this.restartVoiceRecognition();
                        return;
                    case 'audio-capture':
                        errorMessage += 'Microfone não encontrado';
                        break;
                    case 'not-allowed':
                        errorMessage += 'Permissão de microfone negada';
                        break;
                    case 'network':
                        errorMessage += 'Problema de rede';
                        this.restartVoiceRecognition();
                        return;
                    default:
                        errorMessage += event.error;
                }

                this.updateVoiceStatus(false, errorMessage);
                this.addMessageToChat(errorMessage, 'ai');
            };

            this.voiceRecognition.onend = () => {
                console.log('Voice recognition ended');
                // Reiniciar automaticamente o reconhecimento para manter escuta contínua
                if (this.isVoiceActive) {
                    this.restartVoiceRecognition();
                }
            };

            console.log('Advanced voice recognition setup completed');
        } else {
            console.warn('Speech recognition not supported');
        }
    }

    restartVoiceRecognition() {
        // Reinicia o reconhecimento após um pequeno delay para evitar loops
        setTimeout(() => {
            if (this.isVoiceActive && this.voiceRecognition) {
                try {
                    this.voiceRecognition.start();
                } catch (error) {
                    console.log('Voice recognition restart skipped (already running)');
                }
            }
        }, 1000);
    }

    toggleVoiceRecognition() {
        if (!this.voiceRecognition) {
            this.addMessageToChat('❌ Reconhecimento de voz não suportado neste navegador. Use Chrome, Edge ou Safari.', 'ai');
            return;
        }

        if (this.isVoiceActive) {
            this.voiceRecognition.stop();
            this.isVoiceActive = false;
            this.updateVoiceStatus(false, 'Voz Inativa');
            this.addMessageToChat('🔇 IAON parou de ouvir. Clique no microfone para reativar.', 'ai');
        } else {
            try {
                this.isVoiceActive = true;
                this.voiceRecognition.start();
                this.addMessageToChat(`🎤 IAON está agora em modo de escuta contínua! Pode falar naturalmente comigo, ${this.user?.preferred_name || 'usuário'}. Para comandos específicos, diga "IAON" seguido da instrução.`, 'ai');
                this.addMessageToChat(`💡 <strong>Dica:</strong> Agora posso responder a qualquer coisa que você disser! Experimente dizer "Oi IAON" ou fazer uma pergunta.`, 'ai');
            } catch (error) {
                console.error('Error starting voice recognition:', error);
                this.isVoiceActive = false;
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

    async handleAdvancedVoiceInput(transcript, confidence) {
        console.log('Advanced voice input received:', transcript, 'Confidence:', confidence);

        // Filtrar ruídos e palavras muito curtas
        const cleanTranscript = transcript.trim();
        if (cleanTranscript.length < 3) return;

        // Verificar se é um comando direto ou conversa natural
        const lowerTranscript = cleanTranscript.toLowerCase();

        // Palavras de ativação do IAON
        const activationWords = ['iaon', 'eion', 'aion', 'ia'];
        const isDirectCommand = activationWords.some(word => lowerTranscript.startsWith(word + ' '));

        // Detectar saudações e conversas casuais
        const greetings = ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'ei'];
        const questions = ['como', 'o que', 'onde', 'quando', 'por que', 'qual'];
        const conversationalWords = ['obrigado', 'obrigada', 'valeu', 'legal', 'interessante', 'entendi'];

        const isGreeting = greetings.some(greeting => lowerTranscript.includes(greeting));
        const isQuestion = questions.some(question => lowerTranscript.startsWith(question));
        const isConversational = conversationalWords.some(word => lowerTranscript.includes(word));
        const hasIAONReference = lowerTranscript.includes('iaon') || lowerTranscript.includes('assistente');

        // Mostrar o que foi reconhecido com indicador de confiança
        const confidenceIcon = confidence > 0.8 ? '🎯' : confidence > 0.6 ? '📍' : '💭';
        this.addMessageToChat(`${confidenceIcon} "${cleanTranscript}"`, 'user');

        // Decidir como responder
        if (isDirectCommand) {
            // Comando direto para o IAON
            await this.handleVoiceCommand(cleanTranscript);
        } else if (isGreeting || isQuestion || isConversational || hasIAONReference || confidence > 0.7) {
            // Conversa natural - IAON deve responder
            await this.handleNaturalConversation(cleanTranscript, confidence);
        } else if (confidence > 0.5) {
            // Fala detectada mas não tem certeza se é para o IAON
            await this.handleAmbiguousInput(cleanTranscript, confidence);
        }
        // Se confiança muito baixa, ignora silenciosamente
    }

    async handleNaturalConversation(text, confidence) {
        console.log('Processing natural conversation:', text);

        // Mostrar que está processando
        const typingIndicator = this.showTypingIndicator();

        try {
            // Analisar sentimento e contexto
            const sentimentResponse = await this.analyzeSentiment(text);

            // Gerar resposta contextual baseada no que foi dito
            const response = await this.generateContextualResponse(text, sentimentResponse, confidence);

            // Remover indicador de digitação
            this.removeTypingIndicator(typingIndicator);

            // Mostrar resposta do IAON
            this.addMessageToChat(response, 'ai');

            // Se disponível, também falar a resposta
            this.speakResponse(response);

        } catch (error) {
            console.error('Error in natural conversation:', error);
            this.removeTypingIndicator(typingIndicator);

            // Resposta de fallback
            const fallbackResponses = [
                "🤖 Interessante! Conte-me mais sobre isso.",
                "💭 Entendi. O que mais você gostaria de saber?",
                "🎯 Posso ajudá-lo com algo específico?",
                "✨ Estou aqui para conversar e ajudar no que precisar.",
                "🔍 Tem alguma tarefa que eu possa executar para você?"
            ];

            const randomResponse = fallbackResponses[Math.floor(Math.random() * fallbackResponses.length)];
            this.addMessageToChat(randomResponse, 'ai');
        }
    }

    async handleAmbiguousInput(text, confidence) {
        // Para entradas ambíguas, responder de forma sutil
        const subtleResponses = [
            "🤔 Hmm...",
            "👂 Estou ouvindo...",
            "💡 Posso ajudar?",
            "🎯 Precisa de algo?"
        ];

        // Só responder ocasionalmente para não ser intrusivo
        if (Math.random() < 0.3) {
            const response = subtleResponses[Math.floor(Math.random() * subtleResponses.length)];
            this.addMessageToChat(response, 'ai');
        }
    }

    async analyzeSentiment(text) {
        try {
            const response = await fetch('/api/iaon/analyze-sentiment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error analyzing sentiment:', error);
        }

        // Fallback: análise básica local
        return this.basicSentimentAnalysis(text);
    }

    basicSentimentAnalysis(text) {
        const lowerText = text.toLowerCase();

        const positiveWords = ['bom', 'ótimo', 'legal', 'obrigado', 'feliz', 'perfeito', 'adorei'];
        const negativeWords = ['ruim', 'problema', 'erro', 'chato', 'difícil', 'triste'];

        const positiveCount = positiveWords.filter(word => lowerText.includes(word)).length;
        const negativeCount = negativeWords.filter(word => lowerText.includes(word)).length;

        let sentiment = 'neutral';
        if (positiveCount > negativeCount) sentiment = 'positive';
        else if (negativeCount > positiveCount) sentiment = 'negative';

        return {
            sentiment,
            confidence: 0.6,
            emotions: {
                joy: positiveCount > 0,
                sadness: negativeCount > 0
            }
        };
    }

    async generateContextualResponse(text, sentimentData, confidence) {
        const lowerText = text.toLowerCase();
        const sentiment = sentimentData.sentiment;

        // Respostas baseadas em padrões detectados
        if (lowerText.includes('oi') || lowerText.includes('olá')) {
            const greetings = [
                "👋 Olá! Como posso ajudá-lo hoje?",
                "🌟 Oi! Estou aqui para qualquer coisa que precisar!",
                "😊 Olá! Pronto para uma conversa interessante?"
            ];
            return greetings[Math.floor(Math.random() * greetings.length)];
        }

        if (lowerText.includes('como você está') || lowerText.includes('tudo bem')) {
            return "🤖 Estou funcionando perfeitamente! Todos os meus sistemas estão operacionais. E você, como está?";
        }

        if (lowerText.includes('obrigado') || lowerText.includes('obrigada') || lowerText.includes('valeu')) {
            return "😊 Por nada! Sempre um prazer ajudar. Precisa de mais alguma coisa?";
        }

        if (lowerText.includes('help') || lowerText.includes('ajuda')) {
            return "🆘 Claro! Posso ajudar com agenda, reuniões, sistema médico, finanças, contatos e muito mais. O que você precisa?";
        }

        // Respostas baseadas no sentimento
        if (sentiment === 'positive') {
            const positiveResponses = [
                "😄 Que ótimo! Fico feliz em saber disso!",
                "✨ Excelente! Posso ajudar em mais alguma coisa?",
                "🎉 Fantástico! Conte-me mais!"
            ];
            return positiveResponses[Math.floor(Math.random() * positiveResponses.length)];
        }

        if (sentiment === 'negative') {
            const supportiveResponses = [
                "😔 Entendo sua preocupação. Como posso ajudar a melhorar isso?",
                "🤝 Sinto muito por isso. Estou aqui para ajudar no que for preciso.",
                "💙 Pode contar comigo. Vamos resolver isso juntos!"
            ];
            return supportiveResponses[Math.floor(Math.random() * supportiveResponses.length)];
        }

        // Respostas para perguntas
        if (lowerText.includes('o que você') || lowerText.includes('o que é')) {
            return "🤖 Sou o IAON, seu assistente IA avançado! Posso ajudar com tarefas do dia a dia, organização, saúde, finanças e muito mais. O que gostaria de saber?";
        }

        if (lowerText.includes('que horas') || lowerText.includes('hora')) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('pt-BR');
            return `🕐 Agora são ${timeString}. Posso ajudar com algo relacionado ao tempo ou agenda?`;
        }

        // Resposta contextual padrão
        const contextualResponses = [
            "🤔 Interessante! Pode me contar mais detalhes?",
            "💭 Entendi. Como posso ajudar com isso?",
            "🎯 Posso fazer algo específico para ajudar?",
            "✨ Conte-me mais sobre isso, estou curioso!",
            "🔍 Tem alguma tarefa relacionada que eu possa executar?"
        ];

        return contextualResponses[Math.floor(Math.random() * contextualResponses.length)];
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'ai-bubble chat-bubble p-3 rounded-lg text-white typing-indicator';
        typingDiv.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="text-sm opacity-75">IAON está digitando...</span>
            </div>
        `;

        const chatMessages = document.getElementById('chat-messages');
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return typingDiv;
    }

    removeTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }

    speakResponse(text) {
        // Limpar texto de emojis e caracteres especiais para síntese de voz
        const cleanText = text.replace(/[^\w\s\.,!?]/g, '').trim();

        if ('speechSynthesis' in window && cleanText.length > 0) {
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'pt-BR';
            utterance.rate = 0.9;
            utterance.pitch = 1.1;
            utterance.volume = 0.8;

            // Tentar usar uma voz feminina se disponível
            const voices = speechSynthesis.getVoices();
            const femaleVoice = voices.find(voice =>
                voice.lang.includes('pt') &&
                (voice.name.includes('Female') || voice.name.includes('feminina'))
            );

            if (femaleVoice) {
                utterance.voice = femaleVoice;
            }

            speechSynthesis.speak(utterance);
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
            case 'meeting_management':
                this.showSection('meetings');
                this.addMessageToChat('📹 Ativando sistema de reuniões avançado...', 'ai');
                break;

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

            case 'contact_management':
                this.showSection('contacts');
                this.addMessageToChat('📱 Abrindo agenda de contatos com integração de voz...', 'ai');
                break;

            case 'call_history':
                this.showSection('call_logs');
                this.addMessageToChat('📋 Exibindo histórico de chamadas...', 'ai');
                break;

            case 'app_management':
                this.showSection('apps');
                this.addMessageToChat('📱 Visualizando aplicativos disponíveis...', 'ai');
                break;

            case 'app_launched':
                this.addMessageToChat('✅ Aplicativo foi aberto com sucesso!', 'ai');
                break;

            case 'app_not_found':
                this.addMessageToChat('❌ Aplicativo não encontrado. Tente ser mais específico.', 'ai');
                break;

            case 'app_launch_failed':
                this.addMessageToChat('❌ Erro ao abrir aplicativo. Tente novamente.', 'ai');
                break;

            case 'generate_report':
                this.addMessageToChat('📊 Gerando relatório personalizado... (Em desenvolvimento)', 'ai');
                break;

            case 'show_help':
                this.showHelpWithTriggerWord();
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
        const intelligenceIndicator = document.getElementById('intelligence-indicator');
        const floatingButton = document.getElementById('floating-voice');

        if (indicator) {
            if (active) {
                indicator.className = 'w-3 h-3 rounded-full voice-listening';
            } else {
                indicator.className = 'w-3 h-3 rounded-full bg-red-500';
            }
        }

        if (statusText) {
            statusText.textContent = text;
            statusText.className = active ? 'text-sm text-green-600 font-medium hidden sm:block' : 'text-sm text-gray-600 hidden sm:block';
        }

        if (intelligenceIndicator) {
            intelligenceIndicator.style.display = active ? 'block' : 'none';
        }

        if (floatingButton) {
            if (active) {
                floatingButton.classList.add('listening');
                floatingButton.title = 'IAON está ouvindo... Clique para desativar';
            } else {
                floatingButton.classList.remove('listening');
                floatingButton.title = 'Clique para ativar escuta contínua do IAON';
            }
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
    // ==================== SISTEMA DE REUNIÕES ====================

    async startMeeting() {
        try {
            const title = prompt('Digite o título da reunião:') || 'Reunião IAON';
            const description = prompt('Descrição (opcional):') || '';

            const response = await this.callAPI('/api/meetings/start', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: this.userId,
                    title: title,
                    description: description
                })
            });

            if (response.success) {
                this.currentMeeting = response.meeting;
                this.updateMeetingStatus('active', `📹 Reunião "${title}" iniciada`);
                this.addMessageToChat(`🎉 ${response.message}`, 'ai');

                // Mostrar controles de reunião
                this.showMeetingControls();
            }
        } catch (error) {
            console.error('Error starting meeting:', error);
            this.addMessageToChat('❌ Erro ao iniciar reunião. Tente novamente.', 'ai');
        }
    }

    async addMeetingParticipant() {
        if (!this.currentMeeting) {
            this.addMessageToChat('❌ Nenhuma reunião ativa. Inicie uma reunião primeiro.', 'ai');
            return;
        }

        // Mostrar opções: adicionar conhecido ou novo participante
        const choice = await this.showParticipantSelectionModal();

        if (choice === 'known') {
            // Mostrar lista de participantes conhecidos
            await this.showKnownParticipantsModal();
        } else if (choice === 'new') {
            // Adicionar novo participante
            await this.addNewParticipantToMeeting();
        }
    }

    // Modal para selecionar tipo de participante
    async showParticipantSelectionModal() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
            modal.innerHTML = `
                <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                    <h3 class="text-lg font-semibold mb-4">Adicionar Participante</h3>
                    <p class="text-gray-600 mb-6">Como deseja adicionar o participante?</p>
                    <div class="space-y-3">
                        <button onclick="selectChoice('known')" 
                                class="w-full p-4 text-left border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all">
                            <div class="flex items-center gap-3">
                                <i data-lucide="users" class="w-5 h-5 text-purple-500"></i>
                                <div>
                                    <h4 class="font-medium">Participante Conhecido</h4>
                                    <p class="text-sm text-gray-600">Escolher da lista de participantes salvos</p>
                                </div>
                            </div>
                        </button>
                        <button onclick="selectChoice('new')" 
                                class="w-full p-4 text-left border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all">
                            <div class="flex items-center gap-3">
                                <i data-lucide="user-plus" class="w-5 h-5 text-blue-500"></i>
                                <div>
                                    <h4 class="font-medium">Novo Participante</h4>
                                    <p class="text-sm text-gray-600">Adicionar participante e salvar para futuras reuniões</p>
                                </div>
                            </div>
                        </button>
                    </div>
                    <button onclick="selectChoice('cancel')" 
                            class="w-full mt-4 p-2 text-gray-600 hover:text-gray-800">
                        Cancelar
                    </button>
                </div>
            `;

            document.body.appendChild(modal);

            // Função para selecionar escolha
            window.selectChoice = (choice) => {
                document.body.removeChild(modal);
                delete window.selectChoice;
                resolve(choice);
            };

            // Inicializar ícones
            if (window.lucide) {
                lucide.createIcons();
            }
        });
    }

    // Modal para selecionar participante conhecido
    async showKnownParticipantsModal() {
        try {
            const response = await fetch('/api/known-participants');
            const data = await response.json();

            if (!response.ok) {
                this.addMessageToChat('❌ Erro ao carregar participantes conhecidos.', 'ai');
                return;
            }

            const participants = data.participants;

            if (participants.length === 0) {
                this.addMessageToChat('📋 Nenhum participante conhecido encontrado. Vamos adicionar um novo!', 'ai');
                await this.addNewParticipantToMeeting();
                return;
            }

            return new Promise((resolve) => {
                const modal = document.createElement('div');
                modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
                modal.innerHTML = `
                    <div class="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-96 overflow-hidden">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold">Selecionar Participante Conhecido</h3>
                            <button onclick="closeModal()" class="text-gray-500 hover:text-gray-700">
                                <i data-lucide="x" class="w-5 h-5"></i>
                            </button>
                        </div>
                        <div class="mb-4">
                            <input type="text" id="search-participants" placeholder="Buscar participante..." 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500">
                        </div>
                        <div class="max-h-64 overflow-y-auto space-y-2" id="participants-list-modal">
                            ${participants.map(p => `
                                <div class="p-3 border border-gray-200 rounded-lg hover:bg-purple-50 cursor-pointer participant-item" 
                                     data-participant='${JSON.stringify(p)}' onclick="selectParticipant(${p.id})">
                                    <div class="flex items-center justify-between">
                                        <div>
                                            <h4 class="font-medium">${p.name}</h4>
                                            <p class="text-sm text-gray-600">${p.email || 'Sem email'} • ${p.company || 'Sem empresa'}</p>
                                            <p class="text-xs text-gray-500">${p.meeting_count} reuniões • ${p.is_frequent ? 'Frequente' : 'Ocasional'}</p>
                                        </div>
                                        <div class="text-right">
                                            <span class="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">${p.default_role}</span>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                // Função de busca
                const searchInput = document.getElementById('search-participants');
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value.toLowerCase();
                    const items = document.querySelectorAll('.participant-item');
                    items.forEach(item => {
                        const participant = JSON.parse(item.dataset.participant);
                        const matches = participant.name.toLowerCase().includes(query) ||
                            (participant.email && participant.email.toLowerCase().includes(query)) ||
                            (participant.company && participant.company.toLowerCase().includes(query));
                        item.style.display = matches ? 'block' : 'none';
                    });
                });

                // Funções do modal
                window.closeModal = () => {
                    document.body.removeChild(modal);
                    delete window.closeModal;
                    delete window.selectParticipant;
                    resolve(null);
                };

                window.selectParticipant = async (participantId) => {
                    try {
                        const response = await this.callAPI(`/api/meetings/${this.currentMeeting.id}/add-participant`, {
                            method: 'POST',
                            body: JSON.stringify({
                                known_participant_id: participantId
                            })
                        });

                        if (response.success) {
                            this.meetingParticipants.push(response.participant);
                            this.updateParticipantsList();
                            this.addMessageToChat(`👤 ${response.message}`, 'ai');

                            if (response.is_frequent) {
                                this.addMessageToChat(`⭐ Este é um participante frequente (${response.meeting_count} reuniões)!`, 'ai');
                            }
                        }

                        window.closeModal();
                    } catch (error) {
                        console.error('Error adding known participant:', error);
                        this.addMessageToChat('❌ Erro ao adicionar participante.', 'ai');
                        window.closeModal();
                    }
                };

                // Inicializar ícones
                if (window.lucide) {
                    lucide.createIcons();
                }
            });

        } catch (error) {
            console.error('Error loading known participants:', error);
            this.addMessageToChat('❌ Erro ao carregar participantes conhecidos.', 'ai');
        }
    }

    // Adicionar novo participante à reunião
    async addNewParticipantToMeeting() {
        try {
            const participantName = prompt('Nome do participante:');
            if (!participantName) return;

            const email = prompt('Email (opcional):') || '';
            const company = prompt('Empresa (opcional):') || '';
            const position = prompt('Cargo (opcional):') || '';
            const participantRole = prompt('Função (moderador/participante/apresentador/convidado):') || 'participante';
            const phone = prompt('Telefone (opcional):') || '';

            const response = await this.callAPI(`/api/meetings/${this.currentMeeting.id}/add-participant`, {
                method: 'POST',
                body: JSON.stringify({
                    participant_name: participantName,
                    participant_role: participantRole,
                    email: email,
                    company: company,
                    position: position,
                    phone: phone,
                    voice_sample: '' // Em produção, coletar amostra de voz
                })
            });

            if (response.success) {
                this.meetingParticipants.push(response.participant);
                this.updateParticipantsList();
                this.addMessageToChat(`👤 ${response.message}`, 'ai');

                if (response.known_participant) {
                    this.addMessageToChat(`💾 Participante salvo para futuras reuniões!`, 'ai');
                }
            }
        } catch (error) {
            console.error('Error adding new participant:', error);
            this.addMessageToChat('❌ Erro ao adicionar participante.', 'ai');
        }
    }

    async startMeetingRecording() {
        if (!this.currentMeeting) {
            this.addMessageToChat('❌ Nenhuma reunião ativa. Inicie uma reunião primeiro.', 'ai');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            });

            this.meetingRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.meetingAudioChunks = [];

            this.meetingRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.meetingAudioChunks.push(event.data);
                }
            };

            this.meetingRecorder.onstop = () => {
                const audioBlob = new Blob(this.meetingAudioChunks, { type: 'audio/webm' });
                this.processMeetingAudio(audioBlob);
            };

            // Começar gravação
            this.meetingRecorder.start();
            this.isRecording = true;

            this.updateMeetingStatus('recording', '🔴 Gravando reunião...');
            this.addMessageToChat('🎤 Gravação iniciada! A transcrição será feita automaticamente.', 'ai');

            // Iniciar transcrição em tempo real
            this.startRealTimeTranscription();

            // Atualizar interface
            document.getElementById('start-recording')?.classList.add('hidden');
            document.getElementById('stop-recording')?.classList.remove('hidden');

        } catch (error) {
            console.error('Error starting recording:', error);
            this.addMessageToChat('❌ Erro ao iniciar gravação. Verifique as permissões do microfone.', 'ai');
        }
    }

    stopMeetingRecording() {
        if (this.meetingRecorder && this.isRecording) {
            this.meetingRecorder.stop();
            this.isRecording = false;

            // Parar transcrição em tempo real
            if (this.transcriptionInterval) {
                clearInterval(this.transcriptionInterval);
                this.transcriptionInterval = null;
            }

            this.updateMeetingStatus('active', '⏹️ Gravação finalizada');
            this.addMessageToChat('📹 Gravação finalizada. Processando transcrição...', 'ai');

            // Atualizar interface
            document.getElementById('start-recording')?.classList.remove('hidden');
            document.getElementById('stop-recording')?.classList.add('hidden');
        }
    }

    startRealTimeTranscription() {
        // Simular transcrição em tempo real
        this.transcriptionInterval = setInterval(async () => {
            if (this.isRecording && this.currentMeeting) {
                await this.transcribeCurrentAudio();
            }
        }, 10000); // Transcrever a cada 10 segundos
    }

    async transcribeCurrentAudio() {
        try {
            // Simular dados de áudio para transcrição
            const audioData = this.generateMockAudioData();

            const response = await this.callAPI(`/api/meetings/${this.currentMeeting.id}/transcribe`, {
                method: 'POST',
                body: JSON.stringify({
                    audio_data: audioData,
                    start_time_seconds: Date.now() / 1000,
                    end_time_seconds: (Date.now() / 1000) + 10
                })
            });

            if (response.success) {
                this.displayTranscription(response.transcript);
            }
        } catch (error) {
            console.error('Error transcribing audio:', error);
        }
    }

    displayTranscription(transcript) {
        const transcriptContainer = document.getElementById('transcript-container');
        if (transcriptContainer) {
            const transcriptItem = document.createElement('div');
            transcriptItem.className = 'transcript-item p-3 border-l-4 border-blue-500 bg-gray-50 mb-2';

            const speakerIcon = transcript.speaker_name !== 'Participante Desconhecido' ? '👤' : '❓';
            const confidenceColor = transcript.confidence_score > 0.8 ? 'text-green-600' : 'text-yellow-600';

            transcriptItem.innerHTML = `
                <div class="flex justify-between items-start mb-1">
                    <span class="font-semibold text-blue-700">${speakerIcon} ${transcript.speaker_name}</span>
                    <span class="${confidenceColor} text-xs">Confiança: ${Math.round(transcript.confidence_score * 100)}%</span>
                </div>
                <p class="text-gray-800">${transcript.content}</p>
                <div class="text-xs text-gray-500 mt-1">
                    ${new Date(transcript.timestamp).toLocaleTimeString()}
                    ${transcript.is_action_item ? ' • 🎯 Item de Ação' : ''}
                    ${transcript.is_decision ? ' • ✅ Decisão' : ''}
                </div>
            `;

            transcriptContainer.appendChild(transcriptItem);
            transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
        }
    }

    async generateMeetingAgenda() {
        if (!this.currentMeeting) {
            this.addMessageToChat('❌ Nenhuma reunião ativa.', 'ai');
            return;
        }

        try {
            this.addMessageToChat('📋 Gerando pauta da reunião com IA...', 'ai');

            const response = await this.callAPI(`/api/meetings/${this.currentMeeting.id}/generate-agenda`, {
                method: 'POST'
            });

            if (response.success) {
                this.displayMeetingAgenda(response.agenda);
                this.addMessageToChat(`✅ ${response.message}`, 'ai');
            }
        } catch (error) {
            console.error('Error generating agenda:', error);
            this.addMessageToChat('❌ Erro ao gerar pauta.', 'ai');
        }
    }

    displayMeetingAgenda(agenda) {
        const agendaContainer = document.getElementById('agenda-container');
        if (agendaContainer) {
            agendaContainer.innerHTML = `
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h3 class="text-xl font-bold mb-4 text-gray-800">${agenda.title}</h3>
                    
                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-700 mb-2">📝 Resumo</h4>
                        <p class="text-gray-600">${agenda.summary}</p>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-700 mb-2">🎯 Pontos-Chave</h4>
                        <ul class="list-disc list-inside text-gray-600">
                            ${agenda.key_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-700 mb-2">✅ Itens de Ação</h4>
                        <ul class="list-disc list-inside text-gray-600">
                            ${agenda.action_items.map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-700 mb-2">🏆 Decisões Tomadas</h4>
                        <ul class="list-disc list-inside text-gray-600">
                            ${agenda.decisions_made.map(decision => `<li>${decision}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="mb-4">
                        <h4 class="font-semibold text-gray-700 mb-2">🚀 Próximos Passos</h4>
                        <ul class="list-disc list-inside text-gray-600">
                            ${agenda.next_steps.map(step => `<li>${step}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="text-xs text-gray-400 mt-4">
                        Gerado automaticamente em ${new Date(agenda.generated_at).toLocaleString()}
                    </div>
                </div>
            `;
        }
    }

    async endMeeting() {
        if (!this.currentMeeting) {
            this.addMessageToChat('❌ Nenhuma reunião ativa.', 'ai');
            return;
        }

        if (confirm('🤔 Tem certeza que deseja finalizar a reunião?')) {
            try {
                // Parar gravação se estiver ativa
                if (this.isRecording) {
                    this.stopMeetingRecording();
                }

                const response = await this.callAPI(`/api/meetings/${this.currentMeeting.id}/end`, {
                    method: 'POST'
                });

                if (response.success) {
                    this.currentMeeting = null;
                    this.updateMeetingStatus('ended', '✅ Reunião finalizada');
                    this.addMessageToChat(`🎉 ${response.message}`, 'ai');
                    this.hideMeetingControls();

                    // Mostrar estatísticas
                    const stats = response.statistics;
                    this.addMessageToChat(`📊 **Estatísticas da Reunião:**
• Duração: ${stats.duration_minutes} minutos
• Participantes: ${stats.total_participants}
• Transcrições: ${stats.total_transcripts}
• Qualidade: ${Math.round(stats.quality_score * 100)}%`, 'ai');
                }
            } catch (error) {
                console.error('Error ending meeting:', error);
                this.addMessageToChat('❌ Erro ao finalizar reunião.', 'ai');
            }
        }
    }

    async loadUserMeetings() {
        try {
            const response = await this.callAPI(`/api/meetings/user/${this.userId}`);
            this.displayMeetingsList(response.meetings);
        } catch (error) {
            console.error('Error loading meetings:', error);
            this.addMessageToChat('❌ Erro ao carregar reuniões.', 'ai');
        }
    }

    displayMeetingsList(meetings) {
        const meetingsContainer = document.getElementById('meetings-list');
        if (meetingsContainer) {
            meetingsContainer.innerHTML = meetings.map(meeting => `
                <div class="meeting-item bg-white rounded-lg shadow p-4 mb-3 border-l-4 ${meeting.status === 'completed' ? 'border-green-500' : 'border-blue-500'}">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold text-gray-800">${meeting.title}</h4>
                            <p class="text-sm text-gray-600">${meeting.description || 'Sem descrição'}</p>
                            <div class="text-xs text-gray-500 mt-1">
                                📅 ${new Date(meeting.start_time).toLocaleString()}
                                ${meeting.end_time ? ` - ${new Date(meeting.end_time).toLocaleString()}` : ' (Em andamento)'}
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="inline-block px-2 py-1 text-xs rounded ${meeting.status === 'completed' ? 'bg-green-100 text-green-800' :
                    meeting.status === 'active' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                }">
                                ${meeting.status === 'completed' ? '✅ Finalizada' :
                    meeting.status === 'active' ? '🔴 Ativa' : '⏸️ Pausada'}
                            </span>
                            <div class="text-xs text-gray-500 mt-1">
                                👥 ${meeting.participants_count} participantes
                                📝 ${meeting.transcripts_count} transcrições
                            </div>
                        </div>
                    </div>
                    <div class="mt-3 flex space-x-2">
                        <button onclick="iaon.viewMeetingDetails(${meeting.id})" class="text-xs bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
                            Ver Detalhes
                        </button>
                        ${meeting.agenda_generated ?
                    `<button onclick="iaon.viewMeetingAgenda(${meeting.id})" class="text-xs bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
                                Ver Pauta
                            </button>` : ''
                }
                    </div>
                </div>
            `).join('');
        }
    }

    async viewMeetingDetails(meetingId) {
        try {
            const response = await this.callAPI(`/api/meetings/${meetingId}`);
            this.displayMeetingDetailsModal(response);
        } catch (error) {
            console.error('Error loading meeting details:', error);
            this.addMessageToChat('❌ Erro ao carregar detalhes da reunião.', 'ai');
        }
    }

    showMeetingControls() {
        const meetingControls = document.getElementById('meeting-controls');
        if (meetingControls) {
            meetingControls.classList.remove('hidden');
        }
    }

    hideMeetingControls() {
        const meetingControls = document.getElementById('meeting-controls');
        if (meetingControls) {
            meetingControls.classList.add('hidden');
        }
    }

    updateMeetingStatus(status, message) {
        const statusElement = document.getElementById('meeting-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `meeting-status ${status}`;
        }
    }

    updateParticipantsList() {
        const participantsContainer = document.getElementById('participants-list');
        if (participantsContainer) {
            participantsContainer.innerHTML = this.meetingParticipants.map(participant => `
                <div class="participant-item flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                        <span class="font-medium">${participant.participant_name}</span>
                        <span class="text-sm text-gray-500 ml-2">(${participant.participant_role})</span>
                    </div>
                    <div class="text-xs text-gray-400">
                        ${participant.is_verified ? '✅ Verificado' : '⏳ Pendente'}
                    </div>
                </div>
            `).join('');
        }
    }

    processMeetingAudio(audioBlob) {
        // Processar áudio final da reunião
        console.log('Processing meeting audio blob:', audioBlob);
        // Em produção, enviar para transcrição final
    }

    // ==================== FIM SISTEMA DE REUNIÕES ====================
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

// ==================== SISTEMA DE PARTICIPANTES CONHECIDOS ====================

class ParticipantManager {
    constructor() {
        this.participants = [];
        this.currentFilter = 'all';
        this.editingParticipant = null;
    }

    // Carregar participantes conhecidos
    async loadKnownParticipants() {
        try {
            const response = await fetch('/api/known-participants');
            const data = await response.json();

            if (response.ok) {
                this.participants = data.participants;
                this.renderParticipantsList();
                this.updateParticipantsCount();
            } else {
                console.error('Erro ao carregar participantes:', data.error);
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
        }
    }

    // Renderizar lista de participantes
    renderParticipantsList() {
        const container = document.getElementById('participants-list');
        if (!container) return;

        let filteredParticipants = this.participants;

        // Aplicar filtros
        if (this.currentFilter === 'frequent') {
            filteredParticipants = this.participants.filter(p => p.is_frequent);
        } else if (this.currentFilter === 'recent') {
            const recentDate = new Date();
            recentDate.setDate(recentDate.getDate() - 30);
            filteredParticipants = this.participants.filter(p =>
                p.last_meeting_date && new Date(p.last_meeting_date) > recentDate
            );
        }

        if (filteredParticipants.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-gray-500">
                    <i data-lucide="users" class="w-12 h-12 mx-auto mb-4 text-gray-300"></i>
                    <p>Nenhum participante encontrado</p>
                    <button onclick="showAddParticipantModal()" 
                            class="mt-4 bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600">
                        Adicionar Primeiro Participante
                    </button>
                </div>
            `;
            return;
        }

        const html = filteredParticipants.map(participant => this.renderParticipantCard(participant)).join('');
        container.innerHTML = html;

        // Re-inicializar ícones Lucide
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    // Renderizar card de participante
    renderParticipantCard(participant) {
        const lastMeeting = participant.last_meeting_date ?
            new Date(participant.last_meeting_date).toLocaleDateString('pt-BR') : 'Nunca';

        const frequentBadge = participant.is_frequent ?
            '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Frequente</span>' : '';

        return `
            <div class="p-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                        <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                            <span class="text-purple-600 font-semibold text-lg">${participant.name.charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                                <h4 class="font-semibold text-gray-900">${participant.name}</h4>
                                ${frequentBadge}
                                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">${participant.default_role}</span>
                            </div>
                            <div class="text-sm text-gray-600 space-y-1">
                                ${participant.email ? `<div class="flex items-center gap-1"><i data-lucide="mail" class="w-3 h-3"></i> ${participant.email}</div>` : ''}
                                ${participant.company ? `<div class="flex items-center gap-1"><i data-lucide="building" class="w-3 h-3"></i> ${participant.company}</div>` : ''}
                                <div class="flex items-center gap-4 text-xs text-gray-500 mt-2">
                                    <span class="flex items-center gap-1">
                                        <i data-lucide="calendar" class="w-3 h-3"></i>
                                        ${participant.meeting_count} reuniões
                                    </span>
                                    <span class="flex items-center gap-1">
                                        <i data-lucide="clock" class="w-3 h-3"></i>
                                        Último: ${lastMeeting}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="participantManager.addToMeeting(${participant.id})" 
                                class="bg-green-500 text-white p-2 rounded-lg hover:bg-green-600 transition-colors" 
                                title="Adicionar à Reunião Atual">
                            <i data-lucide="plus" class="w-4 h-4"></i>
                        </button>
                        <button onclick="participantManager.editParticipant(${participant.id})" 
                                class="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 transition-colors" 
                                title="Editar">
                            <i data-lucide="edit" class="w-4 h-4"></i>
                        </button>
                        <button onclick="participantManager.deleteParticipant(${participant.id})" 
                                class="bg-red-500 text-white p-2 rounded-lg hover:bg-red-600 transition-colors" 
                                title="Excluir">
                            <i data-lucide="trash" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Atualizar contador de participantes
    updateParticipantsCount() {
        const countElement = document.getElementById('participants-count');
        if (countElement) {
            const total = this.participants.length;
            const frequent = this.participants.filter(p => p.is_frequent).length;
            countElement.textContent = `${total} participantes cadastrados • ${frequent} frequentes`;
        }
    }

    // Salvar participante
    async saveParticipant(formData) {
        try {
            const url = this.editingParticipant ?
                `/api/known-participants/${this.editingParticipant.id}` :
                '/api/known-participants';

            const method = this.editingParticipant ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                await this.loadKnownParticipants(); // Recarregar lista
                return { success: true, message: data.message };
            } else {
                return { success: false, message: data.error };
            }
        } catch (error) {
            console.error('Erro ao salvar participante:', error);
            return { success: false, message: 'Erro na conexão' };
        }
    }

    // Editar participante
    editParticipant(participantId) {
        this.editingParticipant = this.participants.find(p => p.id === participantId);
        if (this.editingParticipant) {
            showAddParticipantModal(this.editingParticipant);
        }
    }

    // Excluir participante
    async deleteParticipant(participantId) {
        if (!confirm('Tem certeza que deseja excluir este participante?')) {
            return;
        }

        try {
            const response = await fetch(`/api/known-participants/${participantId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                await this.loadKnownParticipants(); // Recarregar lista
                iaon.showMessage('Participante excluído com sucesso', 'success');
            } else {
                iaon.showMessage(data.error, 'error');
            }
        } catch (error) {
            console.error('Erro ao excluir participante:', error);
            iaon.showMessage('Erro na conexão', 'error');
        }
    }

    // Adicionar participante à reunião atual
    async addToMeeting(participantId) {
        if (!iaon.currentMeeting) {
            iaon.showMessage('Nenhuma reunião ativa. Inicie uma reunião primeiro.', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/meetings/${iaon.currentMeeting.id}/add-participant`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    known_participant_id: participantId
                })
            });

            const data = await response.json();

            if (response.ok) {
                iaon.showMessage(data.message, 'success');
                // Atualizar lista de participantes da reunião se necessário
                if (iaon.loadMeetingParticipants) {
                    iaon.loadMeetingParticipants();
                }
            } else {
                iaon.showMessage(data.error, 'error');
            }
        } catch (error) {
            console.error('Erro ao adicionar participante à reunião:', error);
            iaon.showMessage('Erro na conexão', 'error');
        }
    }

    // Buscar participantes
    searchParticipants(query) {
        const searchInput = document.getElementById('participant-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                const filtered = this.participants.filter(p =>
                    p.name.toLowerCase().includes(searchTerm) ||
                    (p.email && p.email.toLowerCase().includes(searchTerm)) ||
                    (p.company && p.company.toLowerCase().includes(searchTerm))
                );

                // Renderizar resultados filtrados
                this.renderFilteredResults(filtered);
            });
        }
    }

    // Renderizar resultados filtrados
    renderFilteredResults(filtered) {
        const container = document.getElementById('participants-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="p-8 text-center text-gray-500">
                    <i data-lucide="search" class="w-12 h-12 mx-auto mb-4 text-gray-300"></i>
                    <p>Nenhum participante encontrado</p>
                </div>
            `;
            return;
        }

        const html = filtered.map(participant => this.renderParticipantCard(participant)).join('');
        container.innerHTML = html;

        // Re-inicializar ícones Lucide
        if (window.lucide) {
            lucide.createIcons();
        }
    }

    // Aplicar filtro
    applyFilter(filter) {
        this.currentFilter = filter;
        this.renderParticipantsList();

        // Atualizar botões de filtro
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-purple-100', 'border-purple-500');
        });

        const activeBtn = document.querySelector(`button[onclick="filterParticipants('${filter}')"]`);
        if (activeBtn) {
            activeBtn.classList.add('active', 'bg-purple-100', 'border-purple-500');
        }
    }

    // Sugerir participantes para reunião
    async suggestParticipants(query) {
        try {
            const response = await fetch('/api/participants/suggest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();

            if (response.ok) {
                return data.suggestions;
            } else {
                console.error('Erro ao buscar sugestões:', data.error);
                return [];
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            return [];
        }
    }
}

// Instância global do gerenciador de participantes
const participantManager = new ParticipantManager();

// Funções globais para interface
function showAddParticipantModal(participant = null) {
    const modal = document.getElementById('participant-modal');
    const title = document.getElementById('modal-title');
    const form = document.getElementById('participant-form');

    if (participant) {
        // Modo edição
        title.textContent = 'Editar Participante';
        document.getElementById('edit-participant-id').value = participant.id;
        document.getElementById('participant-name').value = participant.name || '';
        document.getElementById('participant-email').value = participant.email || '';
        document.getElementById('participant-phone').value = participant.phone || '';
        document.getElementById('participant-company').value = participant.company || '';
        document.getElementById('participant-position').value = participant.position || '';
        document.getElementById('participant-role').value = participant.default_role || 'participante';
        document.getElementById('participant-notes').value = participant.notes || '';
        participantManager.editingParticipant = participant;
    } else {
        // Modo criação
        title.textContent = 'Novo Participante';
        form.reset();
        document.getElementById('edit-participant-id').value = '';
        participantManager.editingParticipant = null;
    }

    modal.classList.remove('hidden');
}

function closeParticipantModal() {
    const modal = document.getElementById('participant-modal');
    modal.classList.add('hidden');
    participantManager.editingParticipant = null;
}

async function saveParticipant(event) {
    event.preventDefault();

    const formData = {
        name: document.getElementById('participant-name').value,
        email: document.getElementById('participant-email').value,
        phone: document.getElementById('participant-phone').value,
        company: document.getElementById('participant-company').value,
        position: document.getElementById('participant-position').value,
        default_role: document.getElementById('participant-role').value,
        notes: document.getElementById('participant-notes').value
    };

    const result = await participantManager.saveParticipant(formData);

    if (result.success) {
        closeParticipantModal();
        iaon.showMessage(result.message, 'success');
    } else {
        iaon.showMessage(result.message, 'error');
    }
}

function filterParticipants(filter) {
    participantManager.applyFilter(filter);
}

// Inicializar sistema de participantes quando a seção for carregada
document.addEventListener('DOMContentLoaded', function () {
    // Carregar participantes quando navegar para a seção
    const navLinks = document.querySelectorAll('[data-section="participants"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            setTimeout(() => {
                participantManager.loadKnownParticipants();
                participantManager.searchParticipants();
            }, 100);
        });
    });
});

// ==================== FUNÇÕES GLOBAIS PARA GERENCIAR PARTICIPANTES ====================

// Variável global para filtro atual
let currentParticipantFilter = 'all';

// Mostrar modal para adicionar participante
function showAddParticipantModal() {
    document.getElementById('modal-title').textContent = 'Novo Participante';
    document.getElementById('edit-participant-id').value = '';
    document.getElementById('participant-form').reset();
    document.getElementById('participant-modal').classList.remove('hidden');
}

// Fechar modal de participante
function closeParticipantModal() {
    document.getElementById('participant-modal').classList.add('hidden');
}

// Editar participante
function editParticipant(participantId) {
    fetch(`/api/known-participants/${participantId}`)
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                document.getElementById('modal-title').textContent = 'Editar Participante';
                document.getElementById('edit-participant-id').value = data.id;
                document.getElementById('participant-name').value = data.name || '';
                document.getElementById('participant-email').value = data.email || '';
                document.getElementById('participant-phone').value = data.phone || '';
                document.getElementById('participant-company').value = data.company || '';
                document.getElementById('participant-position').value = data.position || '';
                document.getElementById('participant-role').value = data.default_role || 'participante';
                document.getElementById('participant-notes').value = data.notes || '';
                document.getElementById('participant-modal').classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Erro ao carregar participante:', error);
            iaon.showMessage('Erro ao carregar dados do participante', 'error');
        });
}

// Salvar participante
function saveParticipant(event) {
    event.preventDefault();

    const participantId = document.getElementById('edit-participant-id').value;
    const isEdit = participantId !== '';

    const data = {
        name: document.getElementById('participant-name').value,
        email: document.getElementById('participant-email').value,
        phone: document.getElementById('participant-phone').value,
        company: document.getElementById('participant-company').value,
        position: document.getElementById('participant-position').value,
        default_role: document.getElementById('participant-role').value,
        notes: document.getElementById('participant-notes').value
    };

    const url = isEdit ? `/api/known-participants/${participantId}` : '/api/known-participants';
    const method = isEdit ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            if (result.participant || result.message) {
                iaon.showMessage(result.message || (isEdit ? 'Participante atualizado!' : 'Participante adicionado!'), 'success');
                closeParticipantModal();
                loadParticipants();
            } else {
                iaon.showMessage(result.error || 'Erro ao salvar participante', 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao salvar participante:', error);
            iaon.showMessage('Erro na conexão', 'error');
        });
}

// Excluir participante
function deleteParticipant(participantId, participantName) {
    if (confirm(`Tem certeza que deseja excluir o participante "${participantName}"?`)) {
        fetch(`/api/known-participants/${participantId}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(result => {
                if (result.message) {
                    iaon.showMessage(result.message, 'success');
                    loadParticipants();
                } else {
                    iaon.showMessage(result.error || 'Erro ao excluir participante', 'error');
                }
            })
            .catch(error => {
                console.error('Erro ao excluir participante:', error);
                iaon.showMessage('Erro na conexão', 'error');
            });
    }
}

// Carregar lista de participantes
function loadParticipants() {
    fetch('/api/known-participants')
        .then(response => response.json())
        .then(data => {
            if (data.participants) {
                displayParticipants(data.participants);
                updateParticipantsCount(data.total);
            } else {
                iaon.showMessage(data.error || 'Erro ao carregar participantes', 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao carregar participantes:', error);
            document.getElementById('participants-list').innerHTML = `
                <div class="p-8 text-center text-red-500">
                    <i data-lucide="alert-circle" class="w-12 h-12 mx-auto mb-4"></i>
                    <p>Erro ao carregar participantes</p>
                </div>
            `;
        });
}

// Exibir participantes na lista
function displayParticipants(participants) {
    const container = document.getElementById('participants-list');

    if (participants.length === 0) {
        container.innerHTML = `
            <div class="p-8 text-center text-gray-500">
                <i data-lucide="users" class="w-12 h-12 mx-auto mb-4 text-gray-300"></i>
                <p class="text-lg font-medium mb-2">Nenhum participante encontrado</p>
                <p class="text-sm">Adicione participantes para começar a usar o sistema de memória inteligente</p>
                <button onclick="showAddParticipantModal()" 
                        class="mt-4 bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors">
                    Adicionar Primeiro Participante
                </button>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Filtrar participantes baseado no filtro atual
    let filteredParticipants = participants;
    if (currentParticipantFilter === 'frequent') {
        filteredParticipants = participants.filter(p => p.is_frequent);
    } else if (currentParticipantFilter === 'recent') {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        filteredParticipants = participants.filter(p =>
            p.last_meeting_date && new Date(p.last_meeting_date) > thirtyDaysAgo
        );
    }

    container.innerHTML = filteredParticipants.map(participant => `
        <div class="p-4 hover:bg-gray-50 transition-colors">
            <div class="flex items-center justify-between">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <h4 class="font-medium text-gray-900">${participant.name}</h4>
                        ${participant.is_frequent ? '<span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Frequente</span>' : ''}
                        <span class="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">${participant.default_role}</span>
                    </div>
                    <div class="text-sm text-gray-600 space-y-1">
                        ${participant.email ? `<div class="flex items-center gap-2"><i data-lucide="mail" class="w-3 h-3"></i>${participant.email}</div>` : ''}
                        ${participant.phone ? `<div class="flex items-center gap-2"><i data-lucide="phone" class="w-3 h-3"></i>${participant.phone}</div>` : ''}
                        ${participant.company ? `<div class="flex items-center gap-2"><i data-lucide="building" class="w-3 h-3"></i>${participant.company}${participant.position ? ` - ${participant.position}` : ''}</div>` : ''}
                        <div class="flex items-center gap-4 mt-2">
                            <span class="flex items-center gap-1">
                                <i data-lucide="calendar" class="w-3 h-3"></i>
                                ${participant.meeting_count} reuniões
                            </span>
                            ${participant.last_meeting_date ? `
                                <span class="flex items-center gap-1">
                                    <i data-lucide="clock" class="w-3 h-3"></i>
                                    ${new Date(participant.last_meeting_date).toLocaleDateString('pt-BR')}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    ${participant.notes ? `<div class="text-sm text-gray-500 mt-2 italic">${participant.notes}</div>` : ''}
                </div>
                <div class="flex items-center gap-2 ml-4">
                    <button onclick="editParticipant(${participant.id})"
                            class="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            title="Editar">
                        <i data-lucide="edit-2" class="w-4 h-4"></i>
                    </button>
                    <button onclick="deleteParticipant(${participant.id}, '${participant.name}')"
                            class="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Excluir">
                        <i data-lucide="trash-2" class="w-4 h-4"></i>
                    </button>
                    ${iaon.currentMeeting ? `
                        <button onclick="addParticipantToCurrentMeeting(${participant.id})"
                                class="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                title="Adicionar à reunião atual">
                            <i data-lucide="plus-circle" class="w-4 h-4"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `).join('');

    // Recrear ícones
    if (window.lucide) {
        lucide.createIcons();
    }
}

// Atualizar contador de participantes
function updateParticipantsCount(total) {
    const countElement = document.getElementById('participants-count');
    if (countElement) {
        countElement.textContent = `${total} participante${total !== 1 ? 's' : ''} cadastrado${total !== 1 ? 's' : ''}`;
    }
}

// Filtrar participantes
function filterParticipants(filter) {
    currentParticipantFilter = filter;

    // Atualizar botões de filtro
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-gray-200', 'border-gray-400');
        btn.classList.add('bg-gray-100', 'border-gray-300');
    });

    const activeBtn = document.querySelector(`[onclick="filterParticipants('${filter}')"]`);
    if (activeBtn) {
        activeBtn.classList.remove('bg-gray-100', 'border-gray-300');
        activeBtn.classList.add('active', 'bg-gray-200', 'border-gray-400');
    }

    // Recarregar lista com filtro
    loadParticipants();
}

// Adicionar participante à reunião atual
function addParticipantToCurrentMeeting(participantId) {
    if (!iaon.currentMeeting) {
        iaon.showMessage('Nenhuma reunião ativa', 'warning');
        return;
    }

    fetch(`/api/meetings/${iaon.currentMeeting.id}/add-participant`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            known_participant_id: participantId
        })
    })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                iaon.meetingParticipants.push(result.participant);
                iaon.updateParticipantsList();
                iaon.showMessage(result.message, 'success');

                if (result.is_frequent) {
                    iaon.showMessage(`⭐ Participante frequente adicionado! (${result.meeting_count} reuniões)`, 'info');
                }
            } else {
                iaon.showMessage(result.error || 'Erro ao adicionar participante', 'error');
            }
        })
        .catch(error => {
            console.error('Erro ao adicionar participante à reunião:', error);
            iaon.showMessage('Erro na conexão', 'error');
        });
}

// Buscar participantes
function searchParticipants() {
    const searchInput = document.getElementById('participant-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const participantItems = document.querySelectorAll('#participants-list > div');

            participantItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? 'block' : 'none';
            });
        });
    }
}

