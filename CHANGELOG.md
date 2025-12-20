# Changelog - LiberChat

Registro de todas as alterações importantes do projeto.

---

## [2025-12-09] - Implementação da Lista de Chats e Melhorias na Interface

### Adicionado

#### Backend
- **Endpoint `/api/chats/list`** (`app.py:205-303`)
  - Lista todas as conversas do usuário ordenadas por última mensagem
  - Utiliza query SQL otimizada com CTEs (Common Table Expressions)
  - Retorna dados do contato: nome, foto, NIP-05, npub
  - Inclui preview da última mensagem (limitado a 50 caracteres)
  - Indica se a mensagem foi enviada ou recebida
  - Marca mensagens não lidas (campo `read_at`)
  - Join com tabela `users` para informações do perfil
  - Tratamento de erros com logging detalhado

#### Frontend - Interface de Lista de Chats
- **Função `loadChats()`** (`chat.html:668-701`)
  - Carrega conversas via API
  - Armazena em cache global para filtros
  - Renderiza lista vazia caso não haja conversas

- **Função `renderChatsList()`** (`chat.html:797-879`)
  - Renderiza lista de chats estilo WhatsApp/Telegram
  - Layout sem espaçamento entre itens (borda inferior única)
  - Avatar circular (foto ou inicial do nome em gradiente amarelo)
  - Nome do contato com badge NIP-05 verificado
  - Preview da mensagem com prefixo "Você: " se enviada
  - Timestamp relativo:
    - "agora" (< 1 min)
    - "Xm" (minutos)
    - "Xh" (horas)
    - "Xd" (dias < 7)
    - "DD/MM" (> 7 dias)
  - Indicador visual amarelo para não lidas
  - Negrito em nome e mensagem não lidas
  - Hover effect para feedback visual

- **Função `filterChats()`** (`chat.html:775-795`)
  - Busca em tempo real no campo superior
  - Filtra por: nome, npub, NIP-05, conteúdo da mensagem
  - Case-insensitive
  - Atualiza UI dinamicamente
  - Estado vazio personalizado para "sem resultados"

- **Event Listener de Busca** (`chat.html:892-900`)
  - Input event no `#searchInput`
  - Detecta tab ativa (chats, grupos, contatos)
  - Aplica filtro correspondente

#### Ajustes de Layout
- **Container da lista de chats** (`chat.html:37`)
  - Removido padding (p-4) para layout edge-to-edge
  - Cada item ocupa largura total com bordas internas

### Modificado

#### Service Worker
- Atualizado para v13.0.0 (`static/sw.js:2,4`)
- Cache name: `liberchat-v13`
- Força atualização no PWA mobile

#### Container Docker
- Reiniciado para aplicar mudanças
- Logs confirmam inicialização correta
- Gunicorn rodando com 2 workers

### Técnico

**Arquivos Modificados:**
- `app.py` - Novo endpoint de lista de chats
- `templates/chat.html` - Interface e funções JavaScript
- `static/sw.js` - Bump de versão

**Performance:**
- Query SQL otimizada com CTEs
- Cache local de chats para filtros instantâneos
- Rerender apenas quando necessário

**UX/UI:**
- Design mobile-first estilo WhatsApp
- Feedback visual claro (hover, unread indicators)
- Busca em tempo real sem lag
- Timestamps humanizados

**Estado Atual:**
- ✅ Backend: Endpoint funcional
- ✅ Frontend: Interface completa
- ✅ Busca: Funcionando
- ✅ Mobile: Layout otimizado
- ⏳ Chat view: Placeholder (próxima implementação)

---

## [2025-12-08] - Configurações e Navegação

### Adicionado

#### Navegação Inferior (Bottom Navigation)
- 4 abas: Chats, Grupos, Contatos, Configurações
- Fixed positioning com safe-area-inset para iOS
- Altura: 52px (otimizada para mobile)
- Ícones Lucide 20x20px
- Labels em fonte pequena (9px)
- Active state com borda amarela superior

#### Tab de Configurações
- **Perfil com NIP-05** no topo
  - Avatar circular
  - Display name
  - Badge de verificação (se NIP-05 ativo)
  - Botão "Configurar NIP-05"

- **Menu de Configurações** (11 seções):
  1. **Geral** - Configurações gerais
  2. **Aparência** - Tema claro/escuro/sistema
  3. **Relays** - Gerenciar relays Nostr (padrão: relay.libernet.app)
  4. **Tradução** - Idiomas (em andamento)
  5. **Carteira Lightning** - Recomendações NWC (Alby, WoS, BlueWallet, etc.)
  6. **Publicação de Mídia** - Upload (padrão: media.libernet.app)
  7. **Pacotes de Emoji** - Futuro
  8. **Copiar Chave Privada** - Com aviso de segurança
  9. **Sistema** - Link para libernet.app
  10. **Ajuda** - FAQ e Sofia IA
  11. **Apoie** - Lightning address e doações

- **Footer** - Versão: "LiberChat v1.0.0 • Nostr Protocol • Libernet Network"

#### Header Superior
- Campo de busca responsivo
- Botão + compacto (padding 1.5, ícone 4x4)
- Placeholder dinâmico por tab
- Safe-area-inset para notch iOS

#### Sistema de Grupos
- **Schema de banco** (`database/schema.sql:117-160`)
  - Tabela `groups` (metadados)
  - Tabela `group_members` (membros e roles)
  - Tabela `group_messages` (cache local)
  - Índices otimizados

- **Backend** (`app.py:243-408`)
  - POST `/api/groups/create` - Criar grupo
  - GET `/api/groups/list` - Listar grupos
  - PUT `/api/groups/:id/update` - Editar grupo
  - POST `/api/groups/:id/members` - Adicionar membro
  - DELETE `/api/groups/:id/members/:pubkey` - Remover membro

- **NIP-29 Integration** (`app.py:410-470`)
  - Função `publicar_grupo_nostr()` - Publica metadados
  - Kind 39000 (Group Metadata)
  - Tags: d (group_id), name, about, picture, public/private
  - Atualmente em modo logging (estrutura pronta)

- **Frontend**
  - Modal de criar grupo
  - Campos: nome, descrição, imagem, privacidade
  - Preview de imagem
  - Lista de grupos com badges (Admin, Privado)
  - Contador de membros

#### Ícones Lucide Adicionados
- `chevron-right.svg` - Navegação
- `radio.svg` - Relays
- `globe.svg` - Sistema/Tradução
- `wallet.svg` - Carteira
- `upload.svg` - Upload
- `smile.svg` - Emoji
- `external-link.svg` - Links externos
- `help-circle.svg` - Ajuda
- `heart.svg` - Apoiar

### Modificado

#### UI/UX Mobile
- **Bottom bar**: Altura reduzida para 52px (era ~60px)
- **Top header**: Padding reduzido py-2 (era p-4)
- **Ícones**: Tamanho 4x4 no header, 5x5 no nav (eram 6x6)
- **Botão +**: padding 1.5 (era p-2)
- Removido card de perfil da tab Chats (só em Settings)

#### Layout
- Container principal com `padding-bottom: calc(52px + env(safe-area-inset-bottom))`
- Tabs com overflow-y-auto individual
- HTML/body com `position: fixed` para evitar scroll duplo
- `-webkit-overflow-scrolling: touch` para iOS

### Documentação

#### NIPS.md
- Listagem de todos os NIPs necessários
- Status de implementação (5/15)
- Roadmap em 4 fases
- Priorização: Core > Social > Avançado

---

## [2025-12-08] - Setup Inicial

### Adicionado

#### Infraestrutura
- Docker Compose com PostgreSQL 16 e Redis 7
- Dockerfile multi-stage
- Gunicorn como WSGI server
- Variáveis de ambiente (.env)

#### Autenticação
- Login com nsec ou NIP-07
- Sessão Flask com cookies seguros
- Geração de npub a partir de nsec
- Verificação de chaves Nostr

#### PWA
- Service Worker (sw.js)
- Manifest.json
- Ícones 192x192 e 512x512
- Cache strategy: Network First

#### Database
- Schema completo (`schema.sql`)
- Tabelas: users, contacts, messages, badges, nfts, groups
- Índices otimizados
- NIP-05 verification table

#### Tema
- Sistema de dark/light mode
- Toggle em Settings
- Persistência em localStorage
- Classes Tailwind dinâmicas

#### NIP-05
- Backend: `/api/nip05/request`
- Validação de username (regex)
- Domínio: libernet.app
- Status: `/api/nip05/status`
- Página de configuração: `/settings`

#### Iconografia
- Symlink para /opt/libernet/icons
- Biblioteca Lucide Icons v0.294.0
- SVG otimizados
- Dark mode com CSS invert

---

## Próximas Implementações

### Alta Prioridade
1. **Visualização de Conversas**
   - Tela de chat individual
   - Histórico de mensagens
   - Campo de input com envio
   - Criptografia NIP-04

2. **Envio/Recebimento de Mensagens**
   - WebSocket ou polling
   - Notificações em tempo real
   - Upload de mídia (integração LiberMedia)
   - Emojis e reações

3. **Lista de Contatos**
   - Tab "Contatos" funcional
   - Adicionar por npub/nip05
   - Buscar na rede Nostr
   - Perfis com foto e bio

### Média Prioridade
4. **Grupos Completos**
   - Chat em grupo funcional
   - Mensagens em tempo real
   - Administração (adicionar/remover)
   - NIP-29 completo

5. **Lightning Network**
   - NWC (Nostr Wallet Connect)
   - Enviar/receber satoshis
   - Emblemas pagos
   - Zaps (NIP-57)

### Baixa Prioridade
6. **NFTs e Emblemas**
   - Marketplace de NFTs
   - Criar/enviar emblemas
   - Galeria de coleções
   - NIP-58 completo

7. **Recursos Avançados**
   - Chamadas de voz/vídeo
   - Stories (NIP-71)
   - Comunidades (NIP-72)
   - Marketplace integrado

---

## Notas de Desenvolvimento

### Arquitetura
- **Backend**: Flask + PostgreSQL + Redis
- **Frontend**: Vanilla JS + Tailwind CSS
- **Protocol**: Nostr (nostr-sdk Python)
- **Deployment**: Docker + Gunicorn + Cloudflare

### Boas Práticas
- Commits atômicos
- Logs detalhados em desenvolvimento
- Tratamento de erros abrangente
- Queries SQL otimizadas
- Mobile-first design
- Acessibilidade (a11y)

### Testes
- Teste manual em mobile (iOS/Android)
- Verificar PWA installability
- Testar dark mode
- Validar NIP-05
- Checar performance de queries

---

**Desenvolvido com Claude Code**
**Atualizado em: 2025-12-09**
