#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime

class CostCalculator:
    """Calculadora de Custos do IAON"""
    
    def __init__(self):
        self.platforms = {
            'railway': {
                'name': 'Railway',
                'free_hours': 500,
                'paid_monthly': 25,  # R$ 25/mês
                'database_included': True,
                'ssl_included': True,
                'recommended': True
            },
            'render': {
                'name': 'Render',
                'free_hours': 750,
                'paid_monthly': 35,  # R$ 35/mês
                'database_included': True,
                'ssl_included': True,
                'recommended': False
            },
            'heroku': {
                'name': 'Heroku',
                'free_hours': 550,
                'paid_monthly': 35,  # R$ 35/mês base
                'database_cost': 45,  # R$ 45/mês PostgreSQL
                'ssl_included': True,
                'recommended': False
            },
            'vercel': {
                'name': 'Vercel',
                'free_bandwidth': '100GB',
                'paid_monthly': 100,  # R$ 100/mês
                'database_included': False,
                'ssl_included': True,
                'recommended': False,
                'note': 'Problemático para Flask'
            }
        }
        
        self.pricing_plans = {
            'free': 0,
            'starter': 29.90,
            'professional': 79.90,
            'enterprise': 299.90
        }
    
    def calculate_infrastructure_cost(self, users_total, platform='railway'):
        """Calcula custo de infraestrutura baseado no número de usuários"""
        
        if users_total <= 100:
            # Pode usar plano gratuito
            if platform == 'railway':
                return 0  # 500h gratuitas suficientes
            elif platform == 'render':
                return 0  # 750h gratuitas suficientes
            else:
                return self.platforms[platform]['paid_monthly']
        
        elif users_total <= 1000:
            # Precisa do plano pago básico
            base_cost = self.platforms[platform]['paid_monthly']
            if platform == 'heroku':
                base_cost += self.platforms[platform]['database_cost']
            return base_cost
        
        else:
            # Precisa de recursos premium
            base_cost = self.platforms[platform]['paid_monthly']
            if platform == 'heroku':
                base_cost += self.platforms[platform]['database_cost']
            
            # Custos adicionais para alta escala
            scaling_cost = min(users_total / 1000 * 50, 500)  # Máximo R$ 500 extra
            return base_cost + scaling_cost
    
    def calculate_operational_costs(self, users_total, revenue_monthly):
        """Calcula custos operacionais baseado na escala"""
        
        costs = {
            'infrastructure': 0,
            'email_marketing': 0,
            'analytics': 0,
            'payment_fees': 0,
            'support': 0,
            'marketing': 0,
            'total': 0
        }
        
        # Email marketing
        if users_total <= 100:
            costs['email_marketing'] = 0  # SendGrid gratuito
        elif users_total <= 1000:
            costs['email_marketing'] = 50
        else:
            costs['email_marketing'] = 200
        
        # Analytics e monitoring
        if users_total <= 100:
            costs['analytics'] = 0  # Google Analytics gratuito
        elif users_total <= 1000:
            costs['analytics'] = 100
        else:
            costs['analytics'] = 500
        
        # Taxas de pagamento (média 3.5%)
        costs['payment_fees'] = revenue_monthly * 0.035
        
        # Suporte
        if users_total <= 100:
            costs['support'] = 0  # Você mesmo
        elif users_total <= 1000:
            costs['support'] = 500  # Part-time
        else:
            costs['support'] = 2000  # Full-time
        
        # Marketing
        if revenue_monthly > 5000:
            costs['marketing'] = revenue_monthly * 0.2  # 20% da receita
        elif revenue_monthly > 1000:
            costs['marketing'] = revenue_monthly * 0.1  # 10% da receita
        else:
            costs['marketing'] = 0
        
        costs['total'] = sum(costs.values())
        return costs
    
    def calculate_scenario(self, users_free, users_starter, users_pro, users_enterprise, platform='railway'):
        """Calcula um cenário completo"""
        
        # Cálculos básicos
        users_total = users_free + users_starter + users_pro + users_enterprise
        users_paid = users_starter + users_pro + users_enterprise
        
        # Receita
        revenue = (
            users_starter * self.pricing_plans['starter'] +
            users_pro * self.pricing_plans['professional'] +
            users_enterprise * self.pricing_plans['enterprise']
        )
        
        # Custos de infraestrutura
        infrastructure_cost = self.calculate_infrastructure_cost(users_total, platform)
        
        # Custos operacionais
        operational_costs = self.calculate_operational_costs(users_total, revenue)
        operational_costs['infrastructure'] = infrastructure_cost
        
        total_costs = operational_costs['total'] + infrastructure_cost
        profit = revenue - total_costs
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        # Métricas
        conversion_rate = (users_paid / users_total * 100) if users_total > 0 else 0
        arpu = revenue / users_paid if users_paid > 0 else 0
        
        return {
            'users': {
                'total': users_total,
                'free': users_free,
                'paid': users_paid,
                'conversion_rate': conversion_rate
            },
            'revenue': {
                'monthly': revenue,
                'yearly': revenue * 12,
                'arpu': arpu
            },
            'costs': operational_costs,
            'profit': {
                'monthly': profit,
                'yearly': profit * 12,
                'margin': margin
            },
            'platform': self.platforms[platform]['name']
        }
    
    def print_scenario_report(self, scenario):
        """Imprime relatório formatado do cenário"""
        
        print("\n" + "="*60)
        print(f"📊 RELATÓRIO DE CENÁRIO - {scenario['platform']}")
        print("="*60)
        
        # Usuários
        print(f"\n👥 USUÁRIOS:")
        print(f"  Total: {scenario['users']['total']:,}")
        print(f"  Gratuitos: {scenario['users']['free']:,}")
        print(f"  Pagantes: {scenario['users']['paid']:,}")
        print(f"  Taxa de Conversão: {scenario['users']['conversion_rate']:.1f}%")
        
        # Receita
        print(f"\n💰 RECEITA:")
        print(f"  Mensal: R$ {scenario['revenue']['monthly']:,.2f}")
        print(f"  Anual: R$ {scenario['revenue']['yearly']:,.2f}")
        print(f"  ARPU: R$ {scenario['revenue']['arpu']:.2f}")
        
        # Custos
        print(f"\n💸 CUSTOS MENSAIS:")
        print(f"  Infraestrutura: R$ {scenario['costs']['infrastructure']:,.2f}")
        print(f"  Email Marketing: R$ {scenario['costs']['email_marketing']:,.2f}")
        print(f"  Analytics: R$ {scenario['costs']['analytics']:,.2f}")
        print(f"  Taxas Pagamento: R$ {scenario['costs']['payment_fees']:,.2f}")
        print(f"  Suporte: R$ {scenario['costs']['support']:,.2f}")
        print(f"  Marketing: R$ {scenario['costs']['marketing']:,.2f}")
        print(f"  TOTAL: R$ {scenario['costs']['total']:,.2f}")
        
        # Lucro
        print(f"\n🎯 LUCRO:")
        print(f"  Mensal: R$ {scenario['profit']['monthly']:,.2f}")
        print(f"  Anual: R$ {scenario['profit']['yearly']:,.2f}")
        print(f"  Margem: {scenario['profit']['margin']:.1f}%")
        
        # Status
        if scenario['profit']['margin'] > 80:
            status = "🟢 EXCELENTE"
        elif scenario['profit']['margin'] > 60:
            status = "🟡 BOM"
        elif scenario['profit']['margin'] > 40:
            status = "🟠 RAZOÁVEL"
        else:
            status = "🔴 ATENÇÃO"
        
        print(f"\n📈 STATUS: {status}")

def main():
    """Função principal com exemplos"""
    
    calc = CostCalculator()
    
    print("🚀 CALCULADORA DE CUSTOS IAON")
    print("Análise comparativa de diferentes cenários\n")
    
    # Cenário 1: Início (MVP)
    print("📋 CENÁRIO 1: MVP/VALIDAÇÃO")
    scenario1 = calc.calculate_scenario(
        users_free=30,
        users_starter=15,
        users_pro=3,
        users_enterprise=0,
        platform='railway'
    )
    calc.print_scenario_report(scenario1)
    
    # Cenário 2: Crescimento
    print("\n📋 CENÁRIO 2: CRESCIMENTO")
    scenario2 = calc.calculate_scenario(
        users_free=150,
        users_starter=80,
        users_pro=25,
        users_enterprise=5,
        platform='railway'
    )
    calc.print_scenario_report(scenario2)
    
    # Cenário 3: Scale
    print("\n📋 CENÁRIO 3: ESCALA")
    scenario3 = calc.calculate_scenario(
        users_free=800,
        users_starter=400,
        users_pro=150,
        users_enterprise=30,
        platform='railway'
    )
    calc.print_scenario_report(scenario3)
    
    # Comparação de plataformas
    print("\n" + "="*60)
    print("🏗️ COMPARAÇÃO DE PLATAFORMAS")
    print("="*60)
    
    platforms = ['railway', 'render', 'heroku', 'vercel']
    test_scenario = calc.calculate_scenario(150, 80, 25, 5, 'railway')
    
    print(f"\nPara {test_scenario['users']['total']} usuários:")
    
    for platform in platforms:
        infra_cost = calc.calculate_infrastructure_cost(test_scenario['users']['total'], platform)
        recommended = "⭐ RECOMENDADO" if calc.platforms[platform].get('recommended') else ""
        print(f"  {calc.platforms[platform]['name']:10} R$ {infra_cost:6.2f}/mês {recommended}")
    
    print("\n💡 DICA: Railway oferece o melhor custo-benefício!")
    print("🎯 Comece GRÁTIS e escale conforme cresce!")

if __name__ == "__main__":
    main()
