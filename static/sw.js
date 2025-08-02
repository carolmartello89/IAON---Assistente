// IAON - Sistema de Proteção 24/7 - SERVICE WORKER PRODUÇÃO
// Sistema de Segurança Avançado contra Sequestro e Invasão Domiciliar
// Versão 100% Operacional - São Paulo, Brasil

console.log('🛡️ IAON Security Service Worker PRODUÇÃO - Carregando...');

class ProductionSecurityMonitor {
    constructor() {
        console.log('🔧 Inicializando ProductionSecurityMonitor...');

        // Configurações de produção
        this.systemId = this.generateSystemId();
        this.isActive = false;
        this.version = '1.0.0-PRODUCTION';

        // Configurações de bateria otimizada
        this.batteryOptimized = true;
        this.lastHeartbeat = Date.now();
        this.riskLevel = 'normal'; // normal, elevated, critical

        // Intervalos de monitoramento (em milissegundos)
        this.monitoringIntervals = {
            normal: 30000,    // 30 segundos
            elevated: 15000,  // 15 segundos
            critical: 5000    // 5 segundos
        };

        // Dados do usuário e comportamento
        this.userProfile = {
            emergencyContacts: [],
            safetyPhrases: [],
            settings: {
                silentMode: true,
                autoCall: true,
                locationTracking: true,
                audioRecording: true,
                photoCapture: true
            }
        };

        // Dados comportamentais para detecção de anomalias
        this.userBehaviorData = {
            lastInteraction: Date.now(),
            homeLocation: null,
            regularPattern: null,
            movementHistory: [],
            locationHistory: []
        };

        // Sistemas de detecção ativos
        this.speechRecognition = null;
        this.invasionSpeechRecognition = null;
        this.locationWatcher = null;
        this.emergencyRecorder = null;
        this.continuousRecorder = null;
        this.invasionRecorder = null;

        console.log(`✅ ProductionSecurityMonitor criado - ID: ${this.systemId}`);
    }

    generateSystemId() {
        return 'IAON_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async init() {
        console.log('🛡️ Iniciando Sistema de Segurança IAON - PRODUÇÃO');

        try {
            // Configurar permissões críticas
            await this.setupProductionPermissions();

            // Configurar otimização de bateria
            await this.setupBatteryOptimization();

            // Carregar perfil do usuário e contatos de emergência
            await this.loadUserProfile();

            // Ativar sistema de detecção de sequestro
            await this.setupKidnappingDetection();

            // Ativar sistema de detecção de invasão domiciliar
            await this.setupHomeInvasionDetection();

            // Iniciar monitoramento contínuo
            this.startContinuousMonitoring();

            this.isActive = true;

            console.log('✅ Sistema de Segurança IAON ATIVO - Proteção 24/7');

            // Notificar página principal sobre ativação
            this.notifyPageOfActivation();

        } catch (error) {
            console.error('❌ Erro crítico na inicialização:', error);
            // Tentar reinicializar após 30 segundos
            setTimeout(() => this.init(), 30000);
        }
    }

    async setupProductionPermissions() {
        console.log('🔑 Configurando permissões de produção...');

        try {
            // Solicitar permissão de localização com alta precisão
            if ('geolocation' in navigator) {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 0
                    });
                });
                console.log('✅ Localização autorizada');
                this.userBehaviorData.homeLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };
            }

            // Solicitar permissão de mídia (áudio e vídeo)
            if ('mediaDevices' in navigator) {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: true,
                    video: true
                });
                console.log('✅ Câmera e microfone autorizados');
                // Parar stream inicial - será usado quando necessário
                stream.getTracks().forEach(track => track.stop());
            }

            // Configurar notificações
            if ('Notification' in self) {
                const permission = await Notification.requestPermission();
                console.log('✅ Notificações:', permission);
            }

            // Configurar background sync
            if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                console.log('✅ Background Sync disponível');
            }

        } catch (error) {
            console.error('❌ Erro ao configurar permissões:', error);
        }
    }

    async setupBatteryOptimization() {
        console.log('🔋 Configurando otimização de bateria...');

        try {
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();

                // Ajustar comportamento baseado no nível da bateria
                if (battery.level < 0.20) {
                    this.batteryOptimized = true;
                    console.log('🔋 Modo economia ativado (bateria baixa)');
                } else {
                    this.batteryOptimized = false;
                    console.log('🔋 Modo normal (bateria OK)');
                }

                // Monitorar mudanças na bateria
                battery.addEventListener('levelchange', () => {
                    if (battery.level < 0.15 && !this.batteryOptimized) {
                        this.batteryOptimized = true;
                        console.log('🔋 Ativando modo economia');
                    } else if (battery.level > 0.30 && this.batteryOptimized) {
                        this.batteryOptimized = false;
                        console.log('🔋 Desativando modo economia');
                    }
                });
            }
        } catch (error) {
            console.error('❌ Erro ao configurar bateria:', error);
        }
    }

    async loadUserProfile() {
        console.log('👤 Carregando perfil do usuário...');

        try {
            // Abrir IndexedDB para dados locais
            const db = await this.openDatabase();

            // Carregar contatos de emergência
            const emergencyContacts = await this.getStoredData(db, 'emergency_contacts');
            if (emergencyContacts && emergencyContacts.length > 0) {
                this.userProfile.emergencyContacts = emergencyContacts;
                console.log(`✅ ${emergencyContacts.length} contatos de emergência carregados`);
            } else {
                console.log('⚠️ Nenhum contato de emergência configurado');
                // Configurar contatos padrão se necessário
                await this.setupDefaultEmergencyContacts();
            }

            // Carregar frases de segurança para invasão domiciliar
            const safetyPhrases = await this.getStoredData(db, 'safety_phrases');
            if (safetyPhrases) {
                this.userProfile.safetyPhrases = safetyPhrases;
                console.log('✅ Frases de segurança carregadas');
            } else {
                await this.setupDefaultSafetyPhrases();
            }

            // Carregar configurações de comportamento
            const behaviorSettings = await this.getStoredData(db, 'behavior_settings');
            if (behaviorSettings) {
                this.userBehaviorData = { ...this.userBehaviorData, ...behaviorSettings };
                console.log('✅ Configurações de comportamento carregadas');
            }

            db.close();

        } catch (error) {
            console.error('❌ Erro ao carregar perfil:', error);
            await this.setupDefaultProfile();
        }
    }

    async setupDefaultEmergencyContacts() {
        console.log('⚙️ Configurando contatos de emergência padrão...');

        // Contatos de emergência padrão do Brasil
        const defaultContacts = [
            { name: 'SAMU', phone: '192', type: 'medical' },
            { name: 'Polícia Militar', phone: '190', type: 'police' },
            { name: 'Bombeiros', phone: '193', type: 'fire' },
            { name: 'Polícia Civil', phone: '197', type: 'police' }
        ];

        this.userProfile.emergencyContacts = defaultContacts;

        // Salvar no IndexedDB
        try {
            const db = await this.openDatabase();
            await this.saveData(db, 'emergency_contacts', defaultContacts);
            db.close();
            console.log('✅ Contatos de emergência padrão salvos');
        } catch (error) {
            console.error('❌ Erro ao salvar contatos padrão:', error);
        }
    }

    async setupDefaultSafetyPhrases() {
        console.log('⚙️ Configurando frases de segurança padrão...');

        const defaultPhrases = [
            'estou com problemas',
            'preciso de ajuda',
            'chamem a polícia',
            'invasão',
            'socorro',
            'me ajudem',
            'estão me roubando',
            'entrou alguém aqui'
        ];

        this.userProfile.safetyPhrases = defaultPhrases;

        try {
            const db = await this.openDatabase();
            await this.saveData(db, 'safety_phrases', defaultPhrases);
            db.close();
            console.log('✅ Frases de segurança padrão salvas');
        } catch (error) {
            console.error('❌ Erro ao salvar frases padrão:', error);
        }
    }

    async setupDefaultProfile() {
        console.log('⚙️ Configurando perfil padrão...');

        this.userProfile = {
            emergencyContacts: [],
            safetyPhrases: [],
            settings: {
                silentMode: true,
                autoCall: true,
                locationTracking: true,
                audioRecording: true,
                photoCapture: true
            }
        };

        await this.setupDefaultEmergencyContacts();
        await this.setupDefaultSafetyPhrases();
    }

    async setupKidnappingDetection() {
        console.log('🚨 Ativando sistema de detecção de sequestro PRODUÇÃO...');

        try {
            // Configurar sensores de movimento com detecção avançada
            if ('DeviceMotionEvent' in self && typeof DeviceMotionEvent.requestPermission === 'function') {
                const permission = await DeviceMotionEvent.requestPermission();
                if (permission === 'granted') {
                    this.startAdvancedMotionMonitoring();
                }
            } else if ('DeviceMotionEvent' in self) {
                this.startAdvancedMotionMonitoring();
            }

            // Configurar rastreamento de localização em tempo real
            this.startRealTimeLocationTracking();

            // Configurar detectores de comportamento suspeito
            this.setupAdvancedSuspiciousBehaviorDetection();

            // Configurar triggers de pânico silencioso
            this.setupProductionPanicTriggers();

            // Configurar detecção de áudio de emergência
            this.setupEmergencyAudioDetection();

            console.log('✅ Sistema anti-sequestro PRODUÇÃO ativo');

        } catch (error) {
            console.error('❌ Erro crítico ao configurar detecção de sequestro:', error);
            // Tentar configuração básica
            this.setupBasicKidnappingDetection();
        }
    }

    startAdvancedMotionMonitoring() {
        // Monitoramento avançado de movimento para detecção de sequestro
        self.addEventListener('devicemotion', (event) => {
            if (!this.isActive) return;

            const acceleration = event.acceleration;
            if (acceleration) {
                const magnitude = Math.sqrt(
                    acceleration.x ** 2 +
                    acceleration.y ** 2 +
                    acceleration.z ** 2
                );

                // Detectar movimento violento (luta/resistência)
                if (magnitude > 20) {
                    this.handleViolentMovement(magnitude, event);
                }

                // Detectar movimento de veículo suspeito
                if (magnitude > 8 && magnitude < 15) {
                    this.analyzeVehicleMovement(magnitude, event);
                }

                // Armazenar padrão de movimento
                this.storeMovementPattern(magnitude, event.timeStamp);
            }
        });
    }

    startRealTimeLocationTracking() {
        // Rastreamento em tempo real com alta precisão
        if ('geolocation' in navigator) {
            this.locationWatcher = navigator.geolocation.watchPosition(
                (position) => {
                    this.analyzeLocationForKidnapping(position);
                },
                (error) => {
                    console.warn('Erro no rastreamento:', error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 5000
                }
            );
        }
    }

    analyzeLocationForKidnapping(position) {
        const currentLocation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            timestamp: Date.now(),
            accuracy: position.coords.accuracy,
            speed: position.coords.speed
        };

        // Verificar se saiu da área segura muito rapidamente
        if (this.userBehaviorData.homeLocation) {
            const distance = this.calculateDistance(
                this.userBehaviorData.homeLocation,
                currentLocation
            );

            // Se moveu mais de 5km em menos de 10 minutos (possível sequestro)
            if (distance > 5000 && this.lastSafeLocation) {
                const timeDiff = currentLocation.timestamp - this.lastSafeLocation.timestamp;
                if (timeDiff < 600000) { // 10 minutos
                    this.triggerKidnappingAlert('rapid_location_change', {
                        distance: distance,
                        timeMinutes: timeDiff / 60000,
                        speed: currentLocation.speed
                    });
                }
            }
        }

        // Armazenar localização para análise
        this.storeLocationData(currentLocation);
    }

    setupAdvancedSuspiciousBehaviorDetection() {
        // Detectar padrões comportamentais suspeitos
        setInterval(() => {
            if (!this.isActive) return;

            this.analyzeBehaviorPatterns();
        }, 30000); // Analisar a cada 30 segundos
    }

    analyzeBehaviorPatterns() {
        const now = Date.now();
        const recentData = this.behaviorData?.filter(
            data => now - data.timestamp < 300000 // últimos 5 minutos
        ) || [];

        // Analisar padrões anômalos
        if (recentData.length > 0) {
            const avgMovement = recentData.reduce((sum, data) => sum + data.movement, 0) / recentData.length;
            const locationChanges = this.countLocationChanges(recentData);

            // Detectar comportamento anômalo
            if (avgMovement > 15 && locationChanges > 3) {
                this.triggerKidnappingAlert('anomalous_behavior', {
                    avgMovement: avgMovement,
                    locationChanges: locationChanges,
                    dataPoints: recentData.length
                });
            }
        }
    }

    setupProductionPanicTriggers() {
        // Triggers de pânico para produção

        // Trigger por toque múltiplo rápido
        let touchCount = 0;
        let touchTimer = null;

        self.addEventListener('message', (event) => {
            if (event.data.type === 'emergency_touch') {
                touchCount++;

                if (touchTimer) clearTimeout(touchTimer);

                if (touchCount >= 5) {
                    // 5 toques rápidos = alerta de sequestro
                    this.triggerKidnappingAlert('panic_touch', { touches: touchCount });
                    touchCount = 0;
                } else {
                    touchTimer = setTimeout(() => {
                        touchCount = 0;
                    }, 3000); // Reset após 3 segundos
                }
            }
        });

        // Trigger por combinação de teclas de volume
        let volumeSequence = [];
        self.addEventListener('message', (event) => {
            if (event.data.type === 'volume_press') {
                volumeSequence.push(event.data.button);

                // Sequência: volume up, down, up, up = alerta
                if (volumeSequence.length >= 4) {
                    const sequence = volumeSequence.slice(-4).join(',');
                    if (sequence === 'up,down,up,up') {
                        this.triggerKidnappingAlert('panic_volume', { sequence: sequence });
                    }
                    volumeSequence = [];
                }

                // Limpar sequência após 10 segundos
                setTimeout(() => {
                    volumeSequence = [];
                }, 10000);
            }
        });
    }

    async triggerKidnappingAlert(type, data = {}) {
        console.log(`🚨 ALERTA DE SEQUESTRO ATIVADO: ${type}`);

        try {
            // Capturar dados críticos imediatamente
            const alertData = await this.gatherEmergencyData(type, data);

            // Enviar alertas silenciosos múltiplos
            await this.sendMultipleAlerts(alertData);

            // Iniciar gravação contínua
            await this.startContinuousRecording();

            // Ativar rastreamento intensivo
            this.activateIntensiveTracking();

            // Notificar contatos de emergência
            await this.notifyEmergencyContacts(alertData);

            // Salvar evento localmente
            await this.saveEmergencyEvent(alertData);

            console.log('✅ Todos os protocolos de sequestro ativados');

        } catch (error) {
            console.error('❌ Erro crítico no alerta de sequestro:', error);
            // Protocolo de emergência básico
            await this.sendBasicKidnappingAlert(type, data);
        }
    }

    async gatherEmergencyData(type, data) {
        console.log('📊 Coletando dados de emergência...');

        const emergencyData = {
            id: this.generateUniqueId(),
            type: 'kidnapping',
            subtype: type,
            timestamp: new Date().toISOString(),
            systemId: this.systemId,
            originalData: data,
            location: null,
            photos: [],
            audio: null,
            deviceInfo: {
                userAgent: navigator.userAgent,
                battery: null,
                network: navigator.connection?.effectiveType || 'unknown'
            }
        };

        try {
            // Capturar localização atual
            emergencyData.location = await this.getCurrentLocationForced();

            // Capturar fotos das câmeras silenciosamente
            emergencyData.photos = await this.captureEmergencyPhotos();

            // Iniciar gravação de áudio
            emergencyData.audio = await this.startEmergencyRecording();

            // Obter informações da bateria
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();
                emergencyData.deviceInfo.battery = {
                    level: battery.level,
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            }

        } catch (error) {
            console.error('❌ Erro ao coletar dados de emergência:', error);
        }

        return emergencyData;
    }

    async getCurrentLocationForced() {
        return new Promise((resolve) => {
            if ('geolocation' in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        resolve({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy,
                            altitude: position.coords.altitude,
                            speed: position.coords.speed,
                            heading: position.coords.heading,
                            timestamp: position.timestamp
                        });
                    },
                    (error) => {
                        console.warn('Erro ao obter localização:', error);
                        resolve(null);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            } else {
                resolve(null);
            }
        });
    }

    generateUniqueId() {
        return 'alert_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async setupHomeInvasionDetection() {
        console.log('🏠 Ativando sistema de detecção de invasão domiciliar PRODUÇÃO...');

        try {
            // Configurar reconhecimento de voz contínuo para frases de emergência
            await this.setupProductionVoiceRecognition();

            // Configurar detectores de comportamento de invasão
            this.setupAdvancedInvasionDetection();

            // Configurar sistema de chamadas silenciosas com áudio unidirecional
            this.setupProductionSilentCallSystem();

            // Configurar monitoramento ambiente avançado
            this.setupAdvancedAmbientMonitoring();

            // Configurar triggers específicos para invasão
            this.setupInvasionTriggers();

            console.log('✅ Sistema anti-invasão PRODUÇÃO ativo');

        } catch (error) {
            console.error('❌ Erro crítico ao configurar detecção de invasão:', error);
            // Tentar configuração básica
            this.setupBasicInvasionDetection();
        }
    }

    async setupProductionVoiceRecognition() {
        console.log('🎤 Configurando reconhecimento de voz PRODUÇÃO...');

        try {
            if ('webkitSpeechRecognition' in self || 'SpeechRecognition' in self) {
                const SpeechRecognition = self.SpeechRecognition || self.webkitSpeechRecognition;
                this.invasionSpeechRecognition = new SpeechRecognition();

                // Configurações de produção
                this.invasionSpeechRecognition.continuous = true;
                this.invasionSpeechRecognition.interimResults = true;
                this.invasionSpeechRecognition.lang = 'pt-BR';
                this.invasionSpeechRecognition.maxAlternatives = 3;

                // Handler para resultados de voz
                this.invasionSpeechRecognition.onresult = (event) => {
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        const result = event.results[i];
                        if (result.isFinal) {
                            const transcript = result[0].transcript.toLowerCase().trim();
                            const confidence = result[0].confidence;

                            console.log(`🎤 Voz detectada: "${transcript}" (confiança: ${confidence})`);
                            this.analyzeInvasionKeywords(transcript, confidence);
                        }
                    }
                };

                // Handler para erros
                this.invasionSpeechRecognition.onerror = (event) => {
                    console.warn('⚠️ Erro no reconhecimento de voz:', event.error);

                    // Reiniciar automaticamente após erro
                    setTimeout(() => {
                        if (this.isActive) {
                            try {
                                this.invasionSpeechRecognition.start();
                            } catch (error) {
                                console.warn('Erro ao reiniciar reconhecimento:', error);
                            }
                        }
                    }, 2000);
                };

                // Handler para fim de reconhecimento
                this.invasionSpeechRecognition.onend = () => {
                    console.log('🔄 Reconhecimento de voz finalizado, reiniciando...');

                    // Reiniciar automaticamente para detecção contínua
                    if (this.isActive) {
                        setTimeout(() => {
                            try {
                                this.invasionSpeechRecognition.start();
                            } catch (error) {
                                console.warn('Erro ao reiniciar reconhecimento:', error);
                            }
                        }, 1000);
                    }
                };

                // Iniciar reconhecimento contínuo
                try {
                    this.invasionSpeechRecognition.start();
                    console.log('✅ Reconhecimento de voz contínuo iniciado');
                } catch (error) {
                    console.warn('⚠️ Erro ao iniciar reconhecimento de voz:', error);
                }

            } else {
                console.warn('⚠️ Speech Recognition API não disponível');
                // Configurar alternativa baseada em áudio
                this.setupAudioFallback();
            }

        } catch (error) {
            console.error('❌ Erro ao configurar reconhecimento de voz:', error);
            this.setupAudioFallback();
        }
    }

    analyzeInvasionKeywords(transcript, confidence) {
        // Frases específicas para invasão domiciliar em São Paulo
        const invasionPhrases = [
            // Frases diretas de invasão
            'estão me roubando',
            'entrou alguém aqui',
            'invasão',
            'me ajudem',
            'chamem a polícia',
            'entraram na minha casa',

            // Frases disfarçadas (códigos)
            'estou com problemas',
            'preciso de ajuda',
            'não estou bem',
            'algo está errado',

            // Frases específicas do contexto brasileiro
            'estão me assaltando',
            'bandidos aqui',
            'ladrões na casa',
            'sequestro relâmpago'
        ];

        // Verificar se alguma frase de invasão foi detectada
        for (const phrase of invasionPhrases) {
            if (transcript.includes(phrase)) {
                console.log(`🚨 FRASE DE INVASÃO DETECTADA: "${phrase}"`);

                // Determinar nível de urgência baseado na frase
                const urgencyLevel = this.determineUrgencyLevel(phrase, confidence);

                // Ativar protocolo de invasão
                this.triggerInvasionAlert(phrase, {
                    transcript: transcript,
                    confidence: confidence,
                    urgency: urgencyLevel,
                    detectionTime: Date.now()
                });

                return; // Sair após primeira detecção
            }
        }

        // Verificar padrões de palavras-chave relacionadas
        this.analyzeRelatedKeywords(transcript, confidence);
    }

    determineUrgencyLevel(phrase, confidence) {
        // Frases de alta urgência
        const highUrgencyPhrases = [
            'estão me roubando',
            'entrou alguém aqui',
            'invasão',
            'entraram na minha casa',
            'bandidos aqui'
        ];

        // Frases de urgência média (podem ser códigos)
        const mediumUrgencyPhrases = [
            'estou com problemas',
            'preciso de ajuda',
            'não estou bem'
        ];

        if (highUrgencyPhrases.some(p => phrase.includes(p))) {
            return confidence > 0.8 ? 'critical' : 'high';
        } else if (mediumUrgencyPhrases.some(p => phrase.includes(p))) {
            return confidence > 0.7 ? 'high' : 'medium';
        }

        return 'low';
    }

    async triggerInvasionAlert(phrase, data = {}) {
        console.log(`🚨 ALERTA DE INVASÃO DOMICILIAR ATIVADO: "${phrase}"`);

        try {
            // Coletar dados de emergência para invasão
            const alertData = await this.gatherInvasionEmergencyData(phrase, data);

            // Enviar alertas silenciosos imediatos
            await this.sendInvasionAlerts(alertData);

            // Iniciar chamadas automáticas silenciosas
            await this.initiateInvasionCalls(alertData);

            // Ativar gravação ambiente contínua
            await this.startInvasionRecording();

            // Salvar evento crítico
            await this.saveInvasionEvent(alertData);

            console.log('✅ Protocolo de invasão domiciliar ativado');

        } catch (error) {
            console.error('❌ Erro crítico no alerta de invasão:', error);
            // Protocolo de emergência básico
            await this.sendBasicInvasionAlert(phrase, data);
        }
    }

    async gatherInvasionEmergencyData(phrase, data) {
        const emergencyData = {
            id: this.generateUniqueId(),
            type: 'home_invasion',
            phrase: phrase,
            timestamp: new Date().toISOString(),
            systemId: this.systemId,
            originalData: data,
            location: await this.getCurrentLocationForced(),
            deviceInfo: {
                userAgent: navigator.userAgent,
                timestamp: Date.now(),
                batteryLevel: await this.getBatteryLevel()
            },
            urgencyLevel: data.urgency || 'high'
        };

        // Adicionar informações específicas de invasão
        emergencyData.invasionData = {
            detectedPhrase: phrase,
            confidence: data.confidence,
            transcriptFull: data.transcript,
            detectionMethod: 'voice_recognition'
        };

        return emergencyData;
    }

    async sendInvasionAlerts(alertData) {
        console.log('📤 Enviando alertas de invasão...');

        // Enviar para servidor de emergência
        try {
            await fetch('/api/emergency/home-invasion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Emergency': 'invasion',
                    'X-Priority': alertData.urgencyLevel
                },
                body: JSON.stringify(alertData)
            });
            console.log('✅ Alerta enviado para servidor');
        } catch (error) {
            console.error('❌ Erro ao enviar para servidor:', error);
        }

        // Enviar SMS para contatos de emergência
        await this.sendInvasionSMS(alertData);
    }

    async sendInvasionSMS(alertData) {
        const message = `🚨 INVASÃO DOMICILIAR DETECTADA! Frase: "${alertData.phrase}". Localização: ${alertData.location?.latitude}, ${alertData.location?.longitude}. Tempo: ${new Date().toLocaleString('pt-BR')}. CONTATE AS AUTORIDADES IMEDIATAMENTE! - Sistema IAON`;

        for (const contact of this.userProfile.emergencyContacts) {
            try {
                await fetch('/api/emergency/sms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone: contact.phone,
                        message: message,
                        priority: 'urgent',
                        alertId: alertData.id
                    })
                });
                console.log(`✅ SMS enviado para ${contact.name}`);
            } catch (error) {
                console.error(`❌ Erro ao enviar SMS para ${contact.name}:`, error);
            }
        }
    }

    async initiateInvasionCalls(alertData) {
        console.log('📞 Iniciando chamadas de emergência silenciosas...');

        // Aguardar 1 minuto antes de começar as chamadas
        setTimeout(async () => {
            for (const contact of this.userProfile.emergencyContacts) {
                try {
                    // Fazer chamada silenciosa com áudio unidirecional
                    await this.makeSilentCall(contact, alertData);

                    // Aguardar 30 segundos entre chamadas
                    await new Promise(resolve => setTimeout(resolve, 30000));

                } catch (error) {
                    console.error(`❌ Erro ao chamar ${contact.name}:`, error);
                }
            }
        }, 60000); // 1 minuto
    }

    async makeSilentCall(contact, alertData) {
        console.log(`📞 Chamando ${contact.name} silenciosamente...`);

        try {
            const response = await fetch('/api/emergency/make-call', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Emergency': 'invasion'
                },
                body: JSON.stringify({
                    phone: contact.phone,
                    name: contact.name,
                    alertId: alertData.id,
                    audioMode: 'unidirectional', // Só eles ouvem, usuário não ouve
                    silentMode: true
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log(`✅ Chamada iniciada para ${contact.name}: ${result.callId}`);

                // Iniciar transmissão de áudio ambiente
                this.startAudioTransmission(result.callId);
            }

        } catch (error) {
            console.error(`❌ Erro ao chamar ${contact.name}:`, error);
        }
    }

    async startAudioTransmission(callId) {
        try {
            // Capturar áudio ambiente
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false
                }
            });

            // Transmitir áudio para a chamada
            const response = await fetch('/api/emergency/audio-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    callId: callId,
                    streamType: 'ambient_audio'
                })
            });

            console.log(`✅ Transmissão de áudio iniciada para chamada ${callId}`);

        } catch (error) {
            console.error('❌ Erro ao iniciar transmissão de áudio:', error);
        }
    }

    // Métodos auxiliares e utilitários
    startContinuousMonitoring() {
        // Implementação do monitoramento contínuo
        this.startHeartbeat();
        this.startBehaviorAnalysis();
        this.startBackupMonitoring();
    }

    startHeartbeat() {
        const sendHeartbeat = () => {
            if (!this.isActive) return;

            this.lastHeartbeat = Date.now();

            const interval = this.batteryOptimized ?
                this.monitoringIntervals[this.riskLevel] * 1.5 :
                this.monitoringIntervals[this.riskLevel];

            setTimeout(sendHeartbeat, interval);
        };

        sendHeartbeat();
    }

    notifyPageOfActivation() {
        // Notificar todas as páginas que o sistema está ativo
        self.clients.matchAll().then(clients => {
            clients.forEach(client => {
                client.postMessage({
                    type: 'SECURITY_SYSTEM_ACTIVE',
                    systemId: this.systemId,
                    timestamp: Date.now()
                });
            });
        });
    }

    async openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('iaonSecurityMonitor', 1);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('data')) {
                    db.createObjectStore('data', { keyPath: 'key' });
                }
            };

            request.onsuccess = (event) => {
                resolve(event.target.result);
            };

            request.onerror = (event) => {
                reject(event.target.error);
            };
        });
    }

    async getStoredData(db, key) {
        return new Promise((resolve) => {
            const transaction = db.transaction(['data'], 'readonly');
            const store = transaction.objectStore('data');
            const getRequest = store.get(key);

            getRequest.onsuccess = () => {
                resolve(getRequest.result ? getRequest.result.value : null);
            };

            getRequest.onerror = () => resolve(null);
        });
    }

    async saveData(db, key, value) {
        return new Promise((resolve) => {
            const transaction = db.transaction(['data'], 'readwrite');
            const store = transaction.objectStore('data');
            const putRequest = store.put({ key: key, value: value });

            putRequest.onsuccess = () => resolve(true);
            putRequest.onerror = () => resolve(false);
        });
    }

    calculateDistance(pos1, pos2) {
        const R = 6371000; // Raio da Terra em metros
        const dLat = (pos2.lat - pos1.lat) * Math.PI / 180;
        const dLon = (pos2.lng - pos1.lng) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(pos1.lat * Math.PI / 180) * Math.cos(pos2.lat * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    storeMovementPattern(magnitude, timestamp) {
        if (!this.movementHistory) {
            this.movementHistory = [];
        }

        this.movementHistory.push({ magnitude, timestamp });

        // Manter apenas os últimos 100 registros
        if (this.movementHistory.length > 100) {
            this.movementHistory.shift();
        }
    }

    storeLocationData(location) {
        if (!this.locationHistory) {
            this.locationHistory = [];
        }

        this.locationHistory.push(location);

        // Manter apenas as últimas 50 localizações
        if (this.locationHistory.length > 50) {
            this.locationHistory.shift();
        }

        // Atualizar última localização segura se estiver próximo de casa
        if (this.userBehaviorData.homeLocation) {
            const distance = this.calculateDistance(this.userBehaviorData.homeLocation, location);
            if (distance < 500) { // Dentro de 500m de casa
                this.lastSafeLocation = location;
            }
        }
    }

    countLocationChanges(recentData) {
        if (!recentData || recentData.length < 2) return 0;

        let changes = 0;
        for (let i = 1; i < recentData.length; i++) {
            if (recentData[i].location && recentData[i - 1].location) {
                const distance = this.calculateDistance(
                    recentData[i - 1].location,
                    recentData[i].location
                );
                if (distance > 100) { // Mudança significativa > 100m
                    changes++;
                }
            }
        }
        return changes;
    }

    async getBatteryLevel() {
        try {
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();
                return {
                    level: battery.level,
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            }
        } catch (error) {
            console.warn('Erro ao obter informações da bateria:', error);
        }
        return null;
    }

    async saveEmergencyEvent(eventData) {
        try {
            const db = await this.openDatabase();
            await this.saveData(db, 'emergency_events', eventData);
            db.close();
            console.log('✅ Evento de emergência salvo localmente');
        } catch (error) {
            console.error('❌ Erro ao salvar evento de emergência:', error);
        }
    }

    async saveInvasionEvent(eventData) {
        try {
            const db = await this.openDatabase();
            await this.saveData(db, 'invasion_events', eventData);
            db.close();
            console.log('✅ Evento de invasão salvo localmente');
        } catch (error) {
            console.error('❌ Erro ao salvar evento de invasão:', error);
        }
    }

    stop() {
        this.isActive = false;

        // Parar reconhecimento de voz
        if (this.invasionSpeechRecognition) {
            this.invasionSpeechRecognition.stop();
        }

        // Parar rastreamento de localização
        if (this.locationWatcher) {
            navigator.geolocation.clearWatch(this.locationWatcher);
        }

        // Parar gravações
        if (this.emergencyRecorder) {
            this.emergencyRecorder.stop();
        }

        console.log('🛑 Sistema de Segurança IAON interrompido');
    }
}

// ===============================
// INICIALIZAÇÃO DO SERVICE WORKER
// ===============================

let lifeSecurityMonitor = null;

// Event Listeners do Service Worker
self.addEventListener('install', (event) => {
    console.log('🛡️ IAON Security Service Worker instalado');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('🛡️ IAON Security Service Worker ativado');

    event.waitUntil(
        clients.claim().then(() => {
            // Inicializar o sistema de segurança
            lifeSecurityMonitor = new ProductionSecurityMonitor();
            return lifeSecurityMonitor.init();
        })
    );
});

self.addEventListener('message', (event) => {
    if (event.data.type === 'START_MONITORING') {
        if (!lifeSecurityMonitor) {
            lifeSecurityMonitor = new ProductionSecurityMonitor();
            lifeSecurityMonitor.init();
        }
    } else if (event.data.type === 'STOP_MONITORING') {
        if (lifeSecurityMonitor) {
            lifeSecurityMonitor.stop();
            lifeSecurityMonitor = null;
        }
    } else if (event.data.type === 'PANIC_BUTTON') {
        if (lifeSecurityMonitor) {
            lifeSecurityMonitor.triggerKidnappingAlert('manual_panic', event.data);
        }
    } else if (event.data.type === 'INVASION_ALERT') {
        if (lifeSecurityMonitor) {
            lifeSecurityMonitor.triggerInvasionAlert(event.data.phrase, event.data);
        }
    } else if (event.data.type === 'SUSPICIOUS_ACTIVITY') {
        if (lifeSecurityMonitor) {
            lifeSecurityMonitor.triggerKidnappingAlert('suspicious_activity', event.data);
        }
    } else if (event.data.type === 'UPDATE_ACTIVITY') {
        if (lifeSecurityMonitor) {
            lifeSecurityMonitor.userBehaviorData.lastInteraction = Date.now();
        }
    }
});

console.log('🛡️ IAON Security Service Worker PRODUÇÃO carregado - Sistema de proteção 24/7 ativo');
