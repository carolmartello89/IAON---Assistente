import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string

# Sistema de Planos de Assinatura para IAON
class SubscriptionManager:
    def __init__(self):
        self.plans = {
            'free': {
                'name': 'Gratuito',
                'price': 0,
                'currency': 'BRL',
                'billing': 'monthly',
                'limits': {
                    'meetings_per_month': 3,
                    'participants_per_meeting': 3,
                    'storage_gb': 0.1,
                    'ai_reports': False,
                    'voice_biometry': False
                },
                'features': [
                    '3 reuniões por mês',
                    'Até 3 participantes',
                    'Transcrição básica',
                    'Suporte por email'
                ]
            },
            'starter': {
                'name': 'Starter',
                'price': 29.90,
                'currency': 'BRL',
                'billing': 'monthly',
                'limits': {
                    'meetings_per_month': 20,
                    'participants_per_meeting': 10,
                    'storage_gb': 2,
                    'ai_reports': True,
                    'voice_biometry': True
                },
                'features': [
                    '20 reuniões por mês',
                    'Até 10 participantes',
                    'Relatórios com IA',
                    'Biometria de voz',
                    'Suporte prioritário'
                ]
            },
            'professional': {
                'name': 'Profissional',
                'price': 79.90,
                'currency': 'BRL',
                'billing': 'monthly',
                'limits': {
                    'meetings_per_month': 100,
                    'participants_per_meeting': 25,
                    'storage_gb': 10,
                    'ai_reports': True,
                    'voice_biometry': True,
                    'advanced_analytics': True
                },
                'features': [
                    '100 reuniões por mês',
                    'Até 25 participantes',
                    'Analytics avançados',
                    'Integrações via API',
                    'Coaching incluso (2h/mês)',
                    'Suporte 24/7'
                ]
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': 299.90,
                'currency': 'BRL',
                'billing': 'monthly',
                'limits': {
                    'meetings_per_month': -1,  # Ilimitado
                    'participants_per_meeting': -1,
                    'storage_gb': 100,
                    'ai_reports': True,
                    'voice_biometry': True,
                    'advanced_analytics': True,
                    'custom_branding': True,
                    'white_label': True
                },
                'features': [
                    'Reuniões ilimitadas',
                    'Participantes ilimitados',
                    'White label',
                    'Branding personalizado',
                    'Coaching dedicado (10h/mês)',
                    'SLA 99.9%',
                    'Suporte dedicado'
                ]
            }
        }
    
    def get_plan_details(self, plan_id):
        """Retorna detalhes de um plano específico"""
        return self.plans.get(plan_id)
    
    def get_all_plans(self):
        """Retorna todos os planos disponíveis"""
        return self.plans
    
    def check_usage_limits(self, user_subscription, action_type):
        """Verifica se usuário pode executar determinada ação"""
        plan = self.get_plan_details(user_subscription.get('plan_id', 'free'))
        if not plan:
            return False, "Plano não encontrado"
        
        limits = plan['limits']
        usage = user_subscription.get('usage', {})
        
        # Verificar limite de reuniões
        if action_type == 'create_meeting':
            if limits['meetings_per_month'] != -1:  # -1 = ilimitado
                if usage.get('meetings_this_month', 0) >= limits['meetings_per_month']:
                    return False, f"Limite de {limits['meetings_per_month']} reuniões/mês atingido"
        
        # Verificar limite de participantes
        elif action_type == 'add_participant':
            participant_count = usage.get('current_meeting_participants', 0)
            if limits['participants_per_meeting'] != -1:
                if participant_count >= limits['participants_per_meeting']:
                    return False, f"Limite de {limits['participants_per_meeting']} participantes atingido"
        
        # Verificar recursos premium
        elif action_type == 'generate_ai_report':
            if not limits.get('ai_reports', False):
                return False, "Relatórios IA disponíveis apenas em planos pagos"
        
        elif action_type == 'voice_biometry':
            if not limits.get('voice_biometry', False):
                return False, "Biometria de voz disponível apenas em planos pagos"
        
        return True, "OK"
    
    def calculate_upgrade_benefit(self, current_plan, target_plan):
        """Calcula benefícios do upgrade"""
        current = self.get_plan_details(current_plan)
        target = self.get_plan_details(target_plan)
        
        if not current or not target:
            return None
        
        benefits = {
            'price_difference': target['price'] - current['price'],
            'additional_meetings': target['limits']['meetings_per_month'] - current['limits']['meetings_per_month'],
            'additional_participants': target['limits']['participants_per_meeting'] - current['limits']['participants_per_meeting'],
            'new_features': []
        }
        
        # Identificar novos recursos
        for feature in target['features']:
            if feature not in current['features']:
                benefits['new_features'].append(feature)
        
        return benefits

# Landing Page para Vendas
LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IAON - Assistente IA para Reuniões</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="fas fa-robot text-3xl text-blue-600 mr-3"></i>
                    <h1 class="text-2xl font-bold text-gray-800">IAON</h1>
                </div>
                <nav class="hidden md:flex space-x-6">
                    <a href="#features" class="text-gray-600 hover:text-blue-600">Recursos</a>
                    <a href="#pricing" class="text-gray-600 hover:text-blue-600">Preços</a>
                    <a href="#demo" class="text-gray-600 hover:text-blue-600">Demo</a>
                    <a href="#contact" class="text-gray-600 hover:text-blue-600">Contato</a>
                </nav>
                <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                    Teste Grátis
                </button>
            </div>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
        <div class="container mx-auto px-6 text-center">
            <h2 class="text-5xl font-bold mb-6">
                Transforme suas Reuniões com IA
            </h2>
            <p class="text-xl mb-8 max-w-3xl mx-auto">
                O IAON usa inteligência artificial avançada para transcrever, analisar e gerar insights 
                poderosos de suas reuniões. Aumente a produtividade da sua equipe em 300%.
            </p>
            <div class="flex flex-col sm:flex-row gap-4 justify-center">
                <button class="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100">
                    <i class="fas fa-play mr-2"></i>Assistir Demo
                </button>
                <button class="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600">
                    Teste 30 Dias Grátis
                </button>
            </div>
        </div>
    </section>

    <!-- Features -->
    <section id="features" class="py-20">
        <div class="container mx-auto px-6">
            <h3 class="text-3xl font-bold text-center mb-12">Recursos Poderosos</h3>
            <div class="grid md:grid-cols-3 gap-8">
                <div class="text-center p-6 bg-white rounded-lg shadow-lg">
                    <i class="fas fa-microphone text-4xl text-blue-600 mb-4"></i>
                    <h4 class="text-xl font-semibold mb-3">Transcrição Inteligente</h4>
                    <p class="text-gray-600">Reconhecimento de voz avançado que identifica cada participante automaticamente.</p>
                </div>
                <div class="text-center p-6 bg-white rounded-lg shadow-lg">
                    <i class="fas fa-brain text-4xl text-blue-600 mb-4"></i>
                    <h4 class="text-xl font-semibold mb-3">Análise com IA</h4>
                    <p class="text-gray-600">Gera insights, ações e decisões automaticamente de cada reunião.</p>
                </div>
                <div class="text-center p-6 bg-white rounded-lg shadow-lg">
                    <i class="fas fa-users text-4xl text-blue-600 mb-4"></i>
                    <h4 class="text-xl font-semibold mb-3">Gestão de Participantes</h4>
                    <p class="text-gray-600">Memória inteligente de participantes com biometria de voz.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="py-20 bg-gray-100">
        <div class="container mx-auto px-6">
            <h3 class="text-3xl font-bold text-center mb-12">Escolha seu Plano</h3>
            <div class="grid md:grid-cols-4 gap-6">
                <!-- Plano Gratuito -->
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h4 class="text-xl font-semibold mb-3">Gratuito</h4>
                    <div class="text-3xl font-bold mb-4">R$ 0<span class="text-sm text-gray-500">/mês</span></div>
                    <ul class="space-y-2 mb-6">
                        <li><i class="fas fa-check text-green-500 mr-2"></i>3 reuniões/mês</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Até 3 participantes</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Transcrição básica</li>
                        <li><i class="fas fa-times text-red-500 mr-2"></i>Sem relatórios IA</li>
                    </ul>
                    <button class="w-full bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700">
                        Começar Grátis
                    </button>
                </div>

                <!-- Plano Starter -->
                <div class="bg-white rounded-lg shadow-lg p-6 border-2 border-blue-500">
                    <div class="bg-blue-500 text-white text-xs px-2 py-1 rounded-full inline-block mb-3">POPULAR</div>
                    <h4 class="text-xl font-semibold mb-3">Starter</h4>
                    <div class="text-3xl font-bold mb-4">R$ 29,90<span class="text-sm text-gray-500">/mês</span></div>
                    <ul class="space-y-2 mb-6">
                        <li><i class="fas fa-check text-green-500 mr-2"></i>20 reuniões/mês</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Até 10 participantes</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Relatórios IA</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Biometria de voz</li>
                    </ul>
                    <button class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                        Teste 30 Dias
                    </button>
                </div>

                <!-- Plano Professional -->
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h4 class="text-xl font-semibold mb-3">Profissional</h4>
                    <div class="text-3xl font-bold mb-4">R$ 79,90<span class="text-sm text-gray-500">/mês</span></div>
                    <ul class="space-y-2 mb-6">
                        <li><i class="fas fa-check text-green-500 mr-2"></i>100 reuniões/mês</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Até 25 participantes</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Analytics avançados</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Coaching 2h/mês</li>
                    </ul>
                    <button class="w-full bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700">
                        Começar Agora
                    </button>
                </div>

                <!-- Plano Enterprise -->
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h4 class="text-xl font-semibold mb-3">Enterprise</h4>
                    <div class="text-3xl font-bold mb-4">R$ 299,90<span class="text-sm text-gray-500">/mês</span></div>
                    <ul class="space-y-2 mb-6">
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Reuniões ilimitadas</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Participantes ilimitados</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>White label</li>
                        <li><i class="fas fa-check text-green-500 mr-2"></i>Coaching 10h/mês</li>
                    </ul>
                    <button class="w-full bg-gold-600 text-white py-2 rounded-lg hover:bg-gold-700">
                        Falar com Vendas
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- CTA Section -->
    <section class="bg-blue-600 text-white py-16">
        <div class="container mx-auto px-6 text-center">
            <h3 class="text-3xl font-bold mb-4">Pronto para Revolucionar suas Reuniões?</h3>
            <p class="text-xl mb-8">Junte-se a mais de 1.000 empresas que já usam IAON</p>
            <button class="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100">
                Começar Teste Gratuito de 30 Dias
            </button>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-800 text-white py-12">
        <div class="container mx-auto px-6">
            <div class="grid md:grid-cols-4 gap-8">
                <div>
                    <h5 class="font-semibold mb-4">IAON</h5>
                    <p class="text-gray-400">O futuro das reuniões inteligentes com IA.</p>
                </div>
                <div>
                    <h5 class="font-semibold mb-4">Produto</h5>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">Recursos</a></li>
                        <li><a href="#" class="hover:text-white">Preços</a></li>
                        <li><a href="#" class="hover:text-white">API</a></li>
                    </ul>
                </div>
                <div>
                    <h5 class="font-semibold mb-4">Empresa</h5>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">Sobre</a></li>
                        <li><a href="#" class="hover:text-white">Blog</a></li>
                        <li><a href="#" class="hover:text-white">Carreiras</a></li>
                    </ul>
                </div>
                <div>
                    <h5 class="font-semibold mb-4">Suporte</h5>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#" class="hover:text-white">Ajuda</a></li>
                        <li><a href="#" class="hover:text-white">Contato</a></li>
                        <li><a href="#" class="hover:text-white">Status</a></li>
                    </ul>
                </div>
            </div>
            <div class="border-t border-gray-700 pt-8 mt-8 text-center text-gray-400">
                <p>&copy; 2025 IAON. Todos os direitos reservados.</p>
            </div>
        </div>
    </footer>
</body>
</html>
"""

def create_subscription_routes(app, db):
    """Adiciona rotas de assinatura ao Flask app"""
    
    subscription_manager = SubscriptionManager()
    
    @app.route('/landing')
    def landing_page():
        """Landing page para vendas"""
        return LANDING_PAGE_HTML
    
    @app.route('/api/plans')
    def get_plans():
        """API para listar todos os planos"""
        return jsonify({
            'success': True,
            'plans': subscription_manager.get_all_plans()
        })
    
    @app.route('/api/plans/<plan_id>')
    def get_plan_details(plan_id):
        """API para detalhes de um plano específico"""
        plan = subscription_manager.get_plan_details(plan_id)
        if plan:
            return jsonify({
                'success': True,
                'plan': plan
            })
        return jsonify({
            'success': False,
            'error': 'Plano não encontrado'
        }), 404
    
    @app.route('/api/subscription/check-limit', methods=['POST'])
    def check_usage_limit():
        """API para verificar limites de uso"""
        data = request.get_json()
        user_subscription = data.get('user_subscription', {})
        action_type = data.get('action_type')
        
        can_proceed, message = subscription_manager.check_usage_limits(
            user_subscription, action_type
        )
        
        return jsonify({
            'success': True,
            'can_proceed': can_proceed,
            'message': message
        })
    
    @app.route('/api/subscription/upgrade-benefits', methods=['POST'])
    def get_upgrade_benefits():
        """API para calcular benefícios do upgrade"""
        data = request.get_json()
        current_plan = data.get('current_plan')
        target_plan = data.get('target_plan')
        
        benefits = subscription_manager.calculate_upgrade_benefit(current_plan, target_plan)
        
        return jsonify({
            'success': True,
            'benefits': benefits
        })

if __name__ == '__main__':
    # Exemplo de uso
    manager = SubscriptionManager()
    
    # Simular verificação de limite
    user_sub = {
        'plan_id': 'free',
        'usage': {
            'meetings_this_month': 2,
            'current_meeting_participants': 3
        }
    }
    
    can_create, msg = manager.check_usage_limits(user_sub, 'create_meeting')
    print(f"Pode criar reunião: {can_create} - {msg}")
    
    # Calcular benefícios do upgrade
    benefits = manager.calculate_upgrade_benefit('free', 'starter')
    print(f"Benefícios do upgrade: {benefits}")
