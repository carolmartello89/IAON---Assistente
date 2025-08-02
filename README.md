# IAON - Aplicação Web Flask

Uma aplicação web moderna construída com Flask, oferecendo funcionalidades de gestão de usuários e interface responsiva.

## 🚀 Características

- **Backend Flask**: API robusta com Flask e SQLAlchemy
- **Banco de Dados**: SQLite para desenvolvimento, facilmente configurável para produção
- **Frontend Responsivo**: Interface moderna com HTML, CSS e JavaScript
- **CORS Configurado**: Permitindo acesso de diferentes origens
- **PWA Ready**: Configurado como Progressive Web App
- **Deploy Automático**: Configurado para Vercel

## 📋 Pré-requisitos

- Python 3.8+
- pip

## 🛠️ Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/carolmartello89/IAON---Assistente.git
cd IAON---Assistente
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python app.py
```

4. Acesse em: `http://localhost:5000`

## 🌐 Deploy no Vercel

Este projeto está configurado para deploy automático no Vercel:

1. Conecte seu repositório GitHub ao Vercel
2. Configure as variáveis de ambiente necessárias
3. Deploy automático a cada push na branch main

### Variáveis de Ambiente

- `SECRET_KEY`: Chave secreta para sessões Flask
- `FLASK_ENV`: Ambiente de execução (production/development)

## 📁 Estrutura do Projeto

```
iaon/
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências Python
├── vercel.json        # Configuração Vercel
├── README.md          # Este arquivo
├── .gitignore         # Arquivos ignorados pelo Git
├── database/          # Diretório do banco de dados
└── static/           # Arquivos estáticos
    ├── index.html    # Página principal
    ├── manifest.json # Manifesto PWA
    ├── sw.js         # Service Worker
    └── js/
        └── main.js   # JavaScript principal
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

Desenvolvido com ❤️ por Caroline M. Costa
