#!/bin/bash
# Script de deploy para Railway

echo "🚀 Preparando deploy para Railway..."

# Instalar dependências
pip install -r requirements.txt

# Teste local
echo "🧪 Testando aplicação..."
python app.py &
APP_PID=$!
sleep 5

# Verificar se está rodando
if curl -f http://localhost:5000/health; then
    echo "✅ Aplicação funcionando localmente"
    kill $APP_PID
else
    echo "❌ Erro na aplicação local"
    kill $APP_PID
    exit 1
fi

# Deploy Railway
echo "🚂 Fazendo deploy no Railway..."
railway up

echo "✅ Deploy concluído!"
echo "🌐 Acesse: https://sua-app.railway.app"
