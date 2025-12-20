# NIPs Implementados e Necessários no LiberChat

## ✅ NIPs Já Implementados

### NIP-01: Basic protocol flow description
**Status: Implementado**
- Eventos Nostr básicos (kind 0, kind 1)
- Publicação e assinatura de eventos
- Conexão com relays
- Uso: Base de toda comunicação Nostr

### NIP-04: Encrypted Direct Messages
**Status: Implementado**
- Mensagens diretas criptografadas (kind 4)
- Criptografia end-to-end usando NIP-04
- Uso: Chats privados 1-para-1

### NIP-05: Mapping Nostr keys to DNS-based internet identifiers
**Status: Implementado**
- Verificação de identidade via DNS
- Endpoint `/.well-known/nostr.json`
- Sistema de verificação `username@libernet.app`
- Uso: Identificadores amigáveis para usuários

### NIP-19: bech32-encoded entities
**Status: Implementado**
- Codificação/decodificação de npub, nsec
- Conversão de chaves públicas/privadas
- Uso: Formato amigável para compartilhar chaves

## 🔄 NIPs Em Implementação

### NIP-29: Relay-based Groups
**Status: Em implementação**
- Grupos gerenciados por relays
- Sistema de permissões (admin, moderator, member)
- Mensagens de grupo (kind 9, 11, 12)
- Metadados de grupo (kind 39000)
- Uso: Grupos públicos e privados

## 📋 NIPs Necessários para Funcionalidade 100%

### NIP-02: Contact List and Petnames
**Prioridade: Alta**
- Lista de contatos (kind 3)
- Sincronização de contatos entre dispositivos
- Uso: Gerenciar lista de amigos/contatos

### NIP-07: window.nostr capability for web browsers
**Prioridade: Alta**
- Integração com extensões Nostr (Alby, nos2x, etc)
- Login sem inserir nsec diretamente
- Uso: Autenticação segura via extensão

### NIP-10: Conventions for clients' use of e and p tags in text events
**Prioridade: Média**
- Threads e respostas
- Menções em mensagens
- Uso: Conversas encadeadas

### NIP-25: Reactions
**Prioridade: Média**
- Reações a mensagens (kind 7)
- Emojis e curtidas
- Uso: Interações rápidas em mensagens

### NIP-28: Public Chat (deprecado, usar NIP-29)
**Status: Não implementar**
- Substituído por NIP-29

### NIP-46: Nostr Connect
**Prioridade: Média**
- Remote signing
- Login remoto seguro
- Uso: Conectar com outras aplicações

### NIP-47: Wallet Connect
**Prioridade: Alta**
- Conexão com carteiras Lightning (NWC)
- Pagamentos Lightning integrados
- Uso: Enviar/receber satoshis, emblemas pagos

### NIP-57: Lightning Zaps
**Prioridade: Alta**
- Zaps (gorjetas em Bitcoin)
- Integração com Lightning Network
- Uso: Monetização e gratificações

### NIP-58: Badges
**Prioridade: Média**
- Badges/emblemas (kind 30009)
- Sistema de recompensas
- Uso: Emblemas pagos (bronze, prata, ouro, etc)

### NIP-65: Relay List Metadata
**Prioridade: Baixa**
- Lista de relays preferidos do usuário (kind 10002)
- Sincronização entre clientes
- Uso: Melhor descoberta de conteúdo

### NIP-78: Application-specific data
**Prioridade: Baixa**
- Dados específicos da aplicação
- Settings sincronizados
- Uso: Configurações do usuário

### NIP-94: File Metadata
**Prioridade: Média**
- Metadados de arquivos (kind 1063)
- Upload de imagens/vídeos
- Uso: Compartilhar mídia em chats

### NIP-96: HTTP File Storage Integration
**Prioridade: Média**
- Upload de arquivos via HTTP
- Integração com media.libernet.app
- Uso: Hospedagem de imagens de perfil e grupo

## 🎯 Roadmap de Implementação

### Fase 1 - Core (Atual)
- ✅ NIP-01 (Básico)
- ✅ NIP-04 (DMs)
- ✅ NIP-05 (Identidades)
- ✅ NIP-19 (Codificação)
- 🔄 NIP-29 (Grupos)

### Fase 2 - Contatos e Social
- 📋 NIP-02 (Contatos)
- 📋 NIP-07 (Extensões)
- 📋 NIP-10 (Threads)
- 📋 NIP-25 (Reações)

### Fase 3 - Pagamentos e Badges
- 📋 NIP-47 (Wallet Connect)
- 📋 NIP-57 (Zaps)
- 📋 NIP-58 (Badges)

### Fase 4 - Mídia e Extras
- 📋 NIP-94 (File Metadata)
- 📋 NIP-96 (File Storage)
- 📋 NIP-46 (Nostr Connect)
- 📋 NIP-65 (Relay List)
- 📋 NIP-78 (App Data)

## 📊 Progresso Atual

**Implementados:** 4 NIPs (NIP-01, NIP-04, NIP-05, NIP-19)
**Em desenvolvimento:** 1 NIP (NIP-29)
**Necessários para 100%:** ~10 NIPs adicionais
**Progresso:** ~30% das funcionalidades core

## 🔗 Links Úteis

- Especificações oficiais: https://github.com/nostr-protocol/nips
- NIPs em português: https://github.com/nostr-protocol/nips/tree/main/pt
- Ferramentas de teste: https://nostrtool.com
