# 💬 LiberChat

> Comunicador Nostr descentralizado com Lightning Network e NFTs

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)

## 🚀 Sobre

LiberChat é um aplicativo de mensagens descentralizado construído sobre o protocolo Nostr, oferecendo:

- ✅ Mensagens privadas criptografadas (NIP-04)
- ⚡ Pagamentos Lightning integrados
- 🎁 Emblemas e NFTs como presentes digitais
- 🔐 Controle total das suas chaves
- 🌐 100% open source e auditável

## 🆕 Últimas Atualizações (2025-12-09)

### Lista de Chats Implementada ✅
- Interface estilo WhatsApp/Telegram
- Conversas ordenadas por última mensagem
- Preview da última mensagem (até 50 caracteres)
- Indicadores de mensagens não lidas
- Timestamp relativo (agora, 5m, 2h, 3d, DD/MM)
- Badge de verificação NIP-05
- Busca em tempo real por nome, npub ou conteúdo

### Melhorias de Interface Mobile
- Bottom navigation fixo com 52px
- Header compacto e otimizado
- Layout edge-to-edge (sem margens desnecessárias)
- Ícones redimensionados para melhor usabilidade
- Safe-area-inset para iOS (notch e home indicator)

### Sistema de Configurações
- Perfil com NIP-05 no topo
- 11 seções organizadas: Geral, Aparência, Relays, Tradução, Carteira, etc.
- Design list-style com ícones Lucide
- Footer com versão e branding

Veja o [CHANGELOG.md](CHANGELOG.md) para histórico completo.

## 📋 Requisitos

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 16
- Redis 7

## 🛠️ Instalação

```bash
# Clone o repositório
cd /mnt/projetos/liberchat

# Configure as variáveis de ambiente
cp .env.example .env
nano .env  # Edite com suas credenciais

# Suba os containers
docker-compose up -d

# Verifique os logs
docker-compose logs -f liberchat
```

## 🌐 Acessar

- **Desenvolvimento:** http://localhost:5052
- **Produção:** https://chat.libernet.app

## 📁 Estrutura do Projeto

```
liberchat/
├── app.py                  # Backend Flask
├── requirements.txt        # Dependências Python
├── docker-compose.yml      # Orquestração Docker
├── Dockerfile             # Imagem Docker
├── .env.example           # Exemplo de variáveis
├── static/
│   ├── css/               # Estilos
│   ├── js/                # Scripts
│   ├── icons/             # Ícones SVG (symlink)
│   ├── images/            # Imagens
│   ├── manifest.json      # PWA Manifest
│   └── sw.js              # Service Worker
├── templates/
│   ├── base.html          # Template base
│   ├── index.html         # Login
│   ├── chat.html          # Interface de chat
│   ├── contacts.html      # Lista de contatos
│   └── settings.html      # Configurações
└── database/
    └── schema.sql         # Schema PostgreSQL
```

## 🔧 Tecnologias

### Backend
- **Flask** - Framework web
- **PostgreSQL** - Banco de dados
- **Redis** - Cache e sessões
- **Gunicorn** - WSGI server

### Frontend
- **Tailwind CSS** - Estilização
- **Vanilla JS** - Interatividade
- **PWA** - Progressive Web App

### Nostr
- **pynostr** - Cliente Python para Nostr
- **NIPs:** 01, 04, 05, 07, 19, 57, 58, 98

### Lightning
- **LNbits** - Pagamentos Lightning
- **NWC** - Nostr Wallet Connect

## 📱 PWA (Progressive Web App)

LiberChat é um PWA completo:

- ✅ Instalável no celular
- ✅ Funciona offline
- ✅ Notificações push
- ✅ Ícone na tela inicial

## 🎨 Design

**Paleta de Cores:**
- Preto (#000000) e Branco (#FFFFFF)
- Variantes de cinza
- Amarelo (#FFC107) para destaques

**Temas:**
- Claro (padrão)
- Escuro
- Automático (segue sistema)

## 🔐 Segurança

- ✅ Mensagens criptografadas end-to-end (NIP-04)
- ✅ Chaves privadas nunca saem do dispositivo
- ✅ HTTPS obrigatório
- ✅ Rate limiting
- ✅ Proteção XSS e SQL Injection
- ✅ CSP (Content Security Policy)

## 📊 Roadmap

### Fase 1 - Core (35% completo)
- [x] Estrutura inicial do projeto
- [x] Autenticação Nostr (NIP-07 + nsec)
- [x] Navegação com tabs (Chats, Grupos, Contatos, Configurações)
- [x] Lista de chats ordenada por última mensagem
- [x] Sistema de grupos (criar, listar, gerenciar)
- [x] Interface de configurações
- [x] Tema claro/escuro/automático
- [x] PWA básico (instalável)
- [ ] Visualização de conversa individual
- [ ] Envio/Recebimento de mensagens (NIP-04)
- [ ] Lista de contatos funcional
- [ ] Notificações em tempo real

### Fase 2 - Social
- [x] Criar e gerenciar grupos
- [ ] Chat em grupo funcional
- [ ] Upload de mídia (integração LiberMedia)
- [ ] Perfis de usuário completos
- [ ] NIP-05 @libernet.app (backend pronto)
- [ ] Busca global de usuários

### Fase 3 - Lightning
- [ ] Integração NWC (Nostr Wallet Connect)
- [ ] Enviar/receber satoshis
- [ ] Emblemas pagos
- [ ] Zaps (NIP-57)
- [ ] Carteira integrada

### Fase 4 - Avançado
- [ ] Sistema de NFTs (NIP-58)
- [ ] Chamadas de voz/vídeo
- [ ] Stories (NIP-71)
- [ ] Marketplace
- [ ] Aplicativo nativo (iOS/Android)

## 🤝 Integrações

- **LiberMedia** - Upload de mídia em chats
- **Sofia** - Chat com IA integrado
- **relay.libernet.app** - Relay Nostr principal
- **NIP-05** - Verificação @libernet.app

## 👨‍💻 Desenvolvimento

```bash
# Instalar dependências localmente
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Rodar em modo desenvolvimento
export FLASK_ENV=development
export DEBUG=True
python app.py
```

## 📝 Licença

MIT License - Veja LICENSE para detalhes

## 📞 Contato

- **Desenvolvedor:** Barak (Luciano)
- **Email:** luciano@libernet.app
- **Nostr:** luciano.barak@libernet.app
- **Site:** https://libernet.app

---

**🤖 Desenvolvido com Claude Code**
**⚡ Powered by Nostr & Lightning**
