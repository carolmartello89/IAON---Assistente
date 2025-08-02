# 🎫 Sistema de Cupons Exclusivos IAON

## 🔒 **CARACTERÍSTICAS PRINCIPAIS**

### ✅ **Uso Único Total**
- Cada cupom só pode ser usado **UMA VEZ**
- Após o uso, fica **permanentemente inválido**
- Nenhum outro usuário pode usar o mesmo código

### ✅ **Controle Exclusivo de Usuários**
- Cupons são criados para **usuários específicos**
- Só o usuário autorizado pode usar
- Validação por **user_id** ou **email**

### ✅ **Controle Total do Administrador**
- Apenas você pode criar cupons exclusivos
- Acompanhar quem usou e quando
- Descontos de **20% até 100%** conforme sua escolha

---

## 🎯 **COMO CRIAR CUPONS EXCLUSIVOS**

### 1. **Endpoint para Criação**
```bash
POST /api/coupons/create-exclusive
```

### 2. **Exemplo de Criação - Desconto 50%**
```json
{
  "target_user_email": "cliente@email.com",
  "discount_value": 50,
  "admin_password": "IAON_ADMIN_2025",
  "name": "Desconto Especial Cliente VIP",
  "description": "Desconto exclusivo de 50% - uso único",
  "valid_until": "2025-12-31T23:59:59",
  "applicable_plans": [2, 3],
  "admin_notes": "Cliente especial - desconto promocional"
}
```

### 3. **Exemplo de Criação - Desconto 100% (Grátis)**
```json
{
  "target_user_id": 123,
  "discount_value": 100,
  "admin_password": "IAON_ADMIN_2025",
  "name": "Plano Gratuito - Usuário Premium",
  "description": "Primeiro mês totalmente gratuito",
  "code": "PREMIUM_FREE_2025",
  "billing_cycles": "monthly"
}
```

---

## 📱 **RESPOSTA DO SISTEMA**

### **Cupom Criado com Sucesso**
```json
{
  "success": true,
  "coupon": {
    "code": "EXCLUSIVE_CLIENTE_456",
    "discount_value": 50,
    "is_single_use": true,
    "exclusive_user_email": "cliente@email.com"
  },
  "sharing_info": {
    "message_template": "🎉 CUPOM EXCLUSIVO IAON - 50% DE DESCONTO! 🎉\n\nCódigo: EXCLUSIVE_CLIENTE_456\nDesconto: 50%\nVálido até: 31/12/2025\n🔒 Uso único: Este cupom só pode ser usado UMA VEZ!",
    "whatsapp_link": "https://wa.me/?text=🎉%20CUPOM%20EXCLUSIVO...",
    "email_subject": "🎁 Seu cupom exclusivo IAON de 50% chegou!"
  }
}
```

---

## 🔐 **SEGURANÇA E VALIDAÇÃO**

### **Verificações Automáticas**
1. ✅ **Usuário Autorizado**: Só quem foi selecionado pode usar
2. ✅ **Uso Único**: Impossível usar duas vezes
3. ✅ **Validade**: Respeitada a data de expiração
4. ✅ **Senha Admin**: Proteção contra criação não autorizada

### **Códigos de Erro**
- `COUPON_NOT_FOUND`: Cupom não existe
- `COUPON_ALREADY_USED`: Já foi utilizado
- `COUPON_NOT_AUTHORIZED`: Usuário não autorizado
- `COUPON_NOT_APPLICABLE`: Não se aplica ao plano

---

## 📊 **MONITORAMENTO E CONTROLE**

### **Ver Seus Cupons Exclusivos**
```bash
GET /api/coupons/my-exclusive?admin_password=IAON_ADMIN_2025
```

### **Resposta de Monitoramento**
```json
{
  "exclusive_coupons": [
    {
      "coupon": {
        "code": "EXCLUSIVE_CLIENTE_456",
        "discount_value": 50
      },
      "target_user": {
        "name": "João Silva",
        "email": "joao@email.com"
      },
      "status": {
        "is_used": false,
        "can_still_be_used": true,
        "used_by": null,
        "used_at": null
      }
    }
  ],
  "summary": {
    "total_created": 10,
    "total_used": 3,
    "total_available": 7
  }
}
```

---

## 🎮 **EXEMPLOS PRÁTICOS**

### **Cenário 1: Cliente VIP - 70% Desconto**
```bash
curl -X POST http://localhost:5000/api/coupons/create-exclusive \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_email": "clientevip@empresa.com",
    "discount_value": 70,
    "admin_password": "IAON_ADMIN_2025",
    "name": "Desconto VIP Especial",
    "valid_until": "2025-09-30T23:59:59"
  }'
```

### **Cenário 2: Teste Gratuito - 100% Desconto**
```bash
curl -X POST http://localhost:5000/api/coupons/create-exclusive \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_email": "beta@tester.com",
    "discount_value": 100,
    "admin_password": "IAON_ADMIN_2025",
    "name": "Beta Tester - Gratuito",
    "billing_cycles": "monthly",
    "code": "BETA_FREE_2025"
  }'
```

### **Cenário 3: Desconto Corporativo - 40%**
```bash
curl -X POST http://localhost:5000/api/coupons/create-exclusive \
  -H "Content-Type: application/json" \
  -d '{
    "target_user_id": 456,
    "discount_value": 40,
    "admin_password": "IAON_ADMIN_2025",
    "applicable_plans": [3, 4],
    "admin_notes": "Parceria corporativa"
  }'
```

---

## ✉️ **ENVIANDO CUPONS PARA CLIENTES**

### **Mensagem WhatsApp (Automática)**
```
🎉 CUPOM EXCLUSIVO IAON - 50% DE DESCONTO! 🎉

Olá João Silva!

Você recebeu um cupom exclusivo de desconto:

📧 Código: EXCLUSIVE_JOAO_789
💰 Desconto: 50%
⏰ Válido até: 31/12/2025
🔒 Uso único: Este cupom só pode ser usado UMA VEZ e é exclusivo para você!

Para usar:
1. Faça seu cadastro no IAON
2. Escolha seu plano
3. Digite o código: EXCLUSIVE_JOAO_789
4. Aproveite o desconto!

Atenção: Este cupom é pessoal e intransferível. Após o uso, não poderá ser usado novamente.

Baixe o IAON e transforme suas reuniões! 🚀
```

### **Email (Template Pronto)**
- **Assunto**: 🎁 Seu cupom exclusivo IAON de 50% chegou!
- **Corpo**: Mensagem personalizada com código e instruções

---

## 🚨 **IMPORTANTE - CONFIGURAÇÕES DE SEGURANÇA**

### **Senha de Admin**
- **Senha atual**: `IAON_ADMIN_2025`
- **Recomendação**: Altere para uma senha pessoal forte
- **Local para alterar**: Linha ~1745 do arquivo `app.py`

### **Alterar Senha (Exemplo)**
```python
# Altere esta linha no código:
if admin_password != 'SUA_SENHA_SUPER_SECRETA_AQUI':
```

---

## 📈 **ESTATÍSTICAS DE USO**

### **Métricas Coletadas**
- Total de cupons exclusivos criados
- Quantos foram utilizados
- Quantos ainda estão disponíveis
- Valor total de descontos concedidos
- Usuários que mais receberam cupons

### **Relatório Automático**
```json
{
  "period": "últimos_30_dias",
  "exclusive_coupons": {
    "created": 25,
    "used": 18,
    "available": 7,
    "total_discount_given": "R$ 2.450,00"
  },
  "top_discount_values": [100, 70, 50, 30, 20],
  "conversion_rate": "72% dos cupons foram utilizados"
}
```

---

## 🎯 **VANTAGENS DO SISTEMA**

### ✅ **Para Você (Administrador)**
- **Controle Total**: Você decide quem recebe e quanto de desconto
- **Uso Único**: Impossível fraude ou uso múltiplo
- **Rastreamento**: Sabe exatamente quem usou quando
- **Flexibilidade**: Descontos de 20% a 100%

### ✅ **Para os Clientes**
- **Exclusividade**: Cupom pessoal e intransferível
- **Simplicidade**: Código fácil de usar
- **Transparência**: Sabem que é uso único
- **Valor Percebido**: Sentem-se especiais e únicos

### ✅ **Para o Negócio**
- **Conversão**: Cupons exclusivos têm alta taxa de conversão
- **Controle de Custos**: Você define exatamente o investimento
- **Relacionamento**: Fortalece vínculo com clientes VIP
- **Rastreabilidade**: Métricas precisas de ROI

---

🎉 **Sistema de Cupons Exclusivos IAON - 100% Operacional!** 🎉

*Agora você tem controle total sobre descontos exclusivos, garantindo que apenas pessoas selecionadas por você tenham acesso aos cupons, e cada um só pode ser usado uma única vez!*
