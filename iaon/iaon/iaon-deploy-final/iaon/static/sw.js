// Service Worker para IAON - Assistente IA Avançado
const CACHE_NAME = 'iaon-v1.0.0';
const STATIC_CACHE = 'iaon-static-v1.0.0';
const DYNAMIC_CACHE = 'iaon-dynamic-v1.0.0';

// Arquivos para cache estático
const STATIC_FILES = [
    '/',
    '/static/index.html',
    '/static/js/main.js',
    '/static/manifest.json',
    '/offline.html'
];

// URLs da API para cache dinâmico
const API_URLS = [
    '/api/health',
    '/api/system-info',
    '/api/ai/chat',
    '/api/voice-biometry/status'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('🔧 IAON Service Worker: Instalando...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('📦 IAON: Cache estático criado');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('✅ IAON: Arquivos estáticos em cache');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('❌ IAON Service Worker: Erro ao instalar', error);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log('🚀 IAON Service Worker: Ativando...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('🗑️ IAON: Removendo cache antigo', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ IAON Service Worker: Ativado');
                return self.clients.claim();
            })
    );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Estratégia para arquivos estáticos
    if (STATIC_FILES.includes(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }
    
    // Estratégia para APIs
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }
    
    // Estratégia para outras requisições
    event.respondWith(staleWhileRevalidate(request));
});

// Estratégia Cache First (para arquivos estáticos)
async function cacheFirst(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        const cache = await caches.open(STATIC_CACHE);
        cache.put(request, networkResponse.clone());
        
        return networkResponse;
    } catch (error) {
        console.error('❌ IAON Cache First falhou:', error);
        return await caches.match('/offline.html');
    }
}

// Estratégia Network First (para APIs)
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache apenas respostas bem-sucedidas
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('🔄 IAON Network First: Tentando cache para', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Retornar resposta offline para APIs
        return new Response(
            JSON.stringify({
                error: 'IAON está offline',
                message: 'Sem conexão com a internet',
                offline: true,
                timestamp: new Date().toISOString()
            }),
            {
                status: 503,
                statusText: 'Service Unavailable',
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
    }
}

// Estratégia Stale While Revalidate
async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(() => cachedResponse);
    
    return cachedResponse || fetchPromise;
}

// Sincronização em background
self.addEventListener('sync', event => {
    console.log('🔄 IAON Service Worker: Sincronização em background', event.tag);
    
    if (event.tag === 'sync-iaon-data') {
        event.waitUntil(syncOfflineData());
    }
    
    if (event.tag === 'sync-voice-commands') {
        event.waitUntil(syncVoiceCommands());
    }
});

// Sincronizar dados offline
async function syncOfflineData() {
    try {
        console.log('🔄 IAON: Sincronizando dados offline...');
        
        // Buscar dados pendentes no IndexedDB
        const offlineData = await getOfflineData();
        
        for (const data of offlineData) {
            try {
                const response = await fetch(data.url, {
                    method: data.method,
                    headers: data.headers,
                    body: data.body
                });
                
                if (response.ok) {
                    await removeOfflineData(data.id);
                    console.log('✅ IAON: Dados sincronizados:', data.id);
                }
            } catch (error) {
                console.error('❌ IAON: Erro ao sincronizar:', error);
            }
        }
    } catch (error) {
        console.error('❌ IAON: Erro na sincronização:', error);
    }
}

// Sincronizar comandos de voz
async function syncVoiceCommands() {
    try {
        console.log('🎤 IAON: Sincronizando comandos de voz...');
        
        const voiceCommands = await getOfflineVoiceCommands();
        
        for (const command of voiceCommands) {
            try {
                const response = await fetch('/api/ai/voice-command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(command)
                });
                
                if (response.ok) {
                    await removeOfflineVoiceCommand(command.id);
                    console.log('✅ IAON: Comando de voz sincronizado:', command.id);
                }
            } catch (error) {
                console.error('❌ IAON: Erro ao sincronizar comando de voz:', error);
            }
        }
    } catch (error) {
        console.error('❌ IAON: Erro na sincronização de comandos de voz:', error);
    }
}

// Notificações push
self.addEventListener('push', event => {
    console.log('📱 IAON Service Worker: Notificação push recebida');
    
    const options = {
        body: 'Você tem uma nova notificação do IAON',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1,
            app: 'IAON'
        },
        actions: [
            {
                action: 'open',
                title: 'Abrir IAON',
                icon: '/static/icons/open.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/close.png'
            }
        ],
        tag: 'iaon-notification',
        renotify: true
    };
    
    if (event.data) {
        const data = event.data.json();
        options.body = data.body || options.body;
        options.title = data.title || 'IAON';
        options.data = { ...options.data, ...data };
    }
    
    event.waitUntil(
        self.registration.showNotification('IAON - Assistente IA', options)
    );
});

// Clique em notificação
self.addEventListener('notificationclick', event => {
    console.log('📱 IAON Service Worker: Clique em notificação');
    
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow('/')
        );
    } else if (event.action === 'close') {
        // Apenas fechar a notificação
    } else {
        // Clique na notificação principal
        event.waitUntil(
            clients.matchAll().then(clientList => {
                if (clientList.length > 0) {
                    return clientList[0].focus();
                }
                return clients.openWindow('/');
            })
        );
    }
});

// Funções auxiliares para IndexedDB
async function getOfflineData() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('IAON_DB', 1);
        
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('offlineData')) {
                db.createObjectStore('offlineData', { keyPath: 'id', autoIncrement: true });
            }
            if (!db.objectStoreNames.contains('voiceCommands')) {
                db.createObjectStore('voiceCommands', { keyPath: 'id', autoIncrement: true });
            }
        };
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['offlineData'], 'readonly');
            const store = transaction.objectStore('offlineData');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                resolve(getAllRequest.result);
            };
            
            getAllRequest.onerror = () => {
                reject(getAllRequest.error);
            };
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

async function removeOfflineData(id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('IAON_DB', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['offlineData'], 'readwrite');
            const store = transaction.objectStore('offlineData');
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => {
                resolve();
            };
            
            deleteRequest.onerror = () => {
                reject(deleteRequest.error);
            };
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

async function getOfflineVoiceCommands() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('IAON_DB', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['voiceCommands'], 'readonly');
            const store = transaction.objectStore('voiceCommands');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                resolve(getAllRequest.result);
            };
            
            getAllRequest.onerror = () => {
                reject(getAllRequest.error);
            };
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

async function removeOfflineVoiceCommand(id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('IAON_DB', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['voiceCommands'], 'readwrite');
            const store = transaction.objectStore('voiceCommands');
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => {
                resolve();
            };
            
            deleteRequest.onerror = () => {
                reject(deleteRequest.error);
            };
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

// Limpeza periódica do cache
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'CLEAN_CACHE') {
        event.waitUntil(cleanOldCache());
    }
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

async function cleanOldCache() {
    const cache = await caches.open(DYNAMIC_CACHE);
    const requests = await cache.keys();
    const now = Date.now();
    const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 dias
    
    for (const request of requests) {
        const response = await cache.match(request);
        const dateHeader = response.headers.get('date');
        
        if (dateHeader) {
            const responseDate = new Date(dateHeader).getTime();
            if (now - responseDate > maxAge) {
                await cache.delete(request);
                console.log('🗑️ IAON: Cache antigo removido:', request.url);
            }
        }
    }
}

// Log de inicialização
console.log(`
🤖 IAON Service Worker Carregado
📱 PWA: Ativo
🔄 Cache: Configurado
🔔 Notificações: Habilitadas
🎤 Comandos de Voz: Suportados
✨ Versão: ${CACHE_NAME}
`);

