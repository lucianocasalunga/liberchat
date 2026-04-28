<div align="center">

> ⚠️ **PROJETO DESCONTINUADO** — O LiberChat foi substituído pelo mensageiro integrado ao [LiberMedia](https://media.libernet.app). Este repositório é mantido apenas como referência histórica.

# 💬 LiberChat

**Cliente de Chat Nostr Descentralizado**
*Conversas privadas, seguras e livres*

[![Status](https://img.shields.io/badge/status-descontinuado-inactive?style=for-the-badge)](https://media.libernet.app)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Nostr](https://img.shields.io/badge/nostr-100%25-8B5CF6?style=for-the-badge&logo=nostr&logoColor=white)](https://nostr.com)
[![PWA](https://img.shields.io/badge/PWA-enabled-5A0FC8?style=for-the-badge)](https://chat.libernet.app)

[🌐 Demo ao Vivo](https://chat.libernet.app) • [📖 Docs](https://github.com/lucianocasalunga/liberchat/wiki) • [🐛 Issues](https://github.com/lucianocasalunga/liberchat/issues)

</div>

---

## 🌟 Visão Geral

**LiberChat** é um cliente de chat nativo do Nostr que oferece uma experiência moderna e intuitiva para comunicação descentralizada.

### Por Que LiberChat?

- 🔐 **Privacidade Total**: Suas conversas, suas chaves, seu controle
- 💬 **DMs Encriptadas**: NIP-04 para mensagens privadas seguras
- 👥 **Grupos Públicos**: Canais comunitários abertos
- ⚡ **Lightning Ready**: Integração nativa com pagamentos
- 📱 **PWA**: Instale como app no celular
- 🌍 **Multilíngue**: pt-BR, en-US, es-ES

---

## ✨ Funcionalidades

<table>
<tr>
<td width="50%">

### 💬 Chat Completo

- DMs encriptadas (NIP-04)
- Grupos públicos
- Canais comunitários
- Reactions e emojis
- Upload de mídia
- Mensagens em tempo real

</td>
<td width="50%">

### 🔑 Autenticação Nostr

- Login NIP-07 (extensões)
- Login com nsec
- Gestão de perfil
- Avatar e metadata
- Verificação NIP-05
- Multi-relay support

</td>
</tr>
<tr>
<td width="50%">

### 📱 Interface Moderna

- Design responsivo
- Dark/Light mode
- Temas customizáveis
- Wallpapers personalizados
- 100+ ícones SVG
- PWA instalável

</td>
<td width="50%">

### ⚡ Recursos Avançados

- Notificações push
- Busca de mensagens
- Filtros de conteúdo
- Backup de conversas
- Export/Import data
- Gestão de relays

</td>
</tr>
</table>

---

## 🛠️ Stack Tecnológico

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

- Python 3.12 + Flask
- PostgreSQL (mensagens e usuários)
- nostr-sdk (Python bindings)
- WebSockets (real-time)
- Docker + Compose

### Frontend
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-5A0FC8?style=flat&logo=pwa&logoColor=white)

- Vanilla JavaScript
- Modern CSS (Grid/Flexbox)
- Service Workers
- i18n (3 idiomas)
- Responsive design

---

## 🚀 Instalação

### Usando Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/lucianocasalunga/liberchat.git
cd liberchat

# Configure o ambiente
cp .env.example .env
nano .env

# Inicie com Docker
docker-compose up -d

# Acesse
open http://localhost:5052
```

### Instalação Manual

```bash
# Clone e entre
git clone https://github.com/lucianocasalunga/liberchat.git
cd liberchat

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Execute
python app.py
```

---

## 📚 NIPs Implementados

| NIP | Descrição | Status |
|-----|-----------|--------|
| [NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md) | Protocolo base | ✅ |
| [NIP-04](https://github.com/nostr-protocol/nips/blob/master/04.md) | Mensagens encriptadas | ✅ |
| [NIP-05](https://github.com/nostr-protocol/nips/blob/master/05.md) | Verificação de identidade | ✅ |
| [NIP-07](https://github.com/nostr-protocol/nips/blob/master/07.md) | Extensões de navegador | ✅ |
| [NIP-10](https://github.com/nostr-protocol/nips/blob/master/10.md) | Marcação de eventos | ✅ |
| [NIP-25](https://github.com/nostr-protocol/nips/blob/master/25.md) | Reactions | ✅ |
| [NIP-28](https://github.com/nostr-protocol/nips/blob/master/28.md) | Canais públicos | 🚧 |

---

## 🗺️ Roadmap

### ✅ Concluído (2024-2025)
- [x] Sistema de chat completo
- [x] DMs encriptadas (NIP-04)
- [x] Interface PWA responsiva
- [x] Sistema de temas e wallpapers
- [x] i18n (3 idiomas)
- [x] Gestão de contatos

### 🚧 Em Desenvolvimento (Q1 2025)
- [ ] Grupos privados (NIP-28)
- [ ] Calls de voz/vídeo
- [ ] Stickers customizados
- [ ] Bots integrados
- [ ] Marketplace de temas

### 🔮 Futuro (Q2-Q3 2025)
- [ ] Mobile app nativo
- [ ] Desktop app (Electron)
- [ ] E2E encryption extra
- [ ] Stories (NIP-XX)
- [ ] Communities (NIP-XX)

---

## 🤝 Contribuindo

Contribuições são bem-vindas!

```bash
# Fork o projeto
git checkout -b feature/MinhaFeature
git commit -m 'feat: Adiciona MinhaFeature'
git push origin feature/MinhaFeature
# Abra um Pull Request
```

---

## 📄 Licença

MIT License - Copyright (c) 2025 Luciano Casalunga

Veja [LICENSE](LICENSE) para detalhes.

---

## 👤 Autor

**Luciano Casalunga** (Barak)

- 🌐 [libernet.app](https://libernet.app)
- 💜 Nostr: [npub1nvcezhw3gze5waxtvrzzls8qzhvqpn087hj0s2jl948zr4egq0jqhm3mrr](https://njump.me/npub1nvcezhw3gze5waxtvrzzls8qzhvqpn087hj0s2jl948zr4egq0jqhm3mrr)
- 🐦 [@LucianoBarak](https://twitter.com/LucianoBarak)

---

<div align="center">

**LiberChat** - Conversas livres para pessoas livres 💜

*Parte do ecossistema LiberNet*

[![LiberNet](https://img.shields.io/badge/LiberNet-Ecosystem-8B5CF6?style=for-the-badge)](https://libernet.app)

</div>
