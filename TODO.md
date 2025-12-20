# TODO - LiberChat

Lista de tarefas pendentes e próximos passos.

---

## 🔥 Prioridade Alta (Próxima Sessão)

### 1. Visualização de Conversa Individual
**Status:** Não iniciado
**Arquivo:** `templates/conversation.html` (novo)

- [ ] Criar template de conversa (`conversation.html`)
- [ ] Header com nome/foto do contato + botão voltar
- [ ] Área de mensagens scrollável
- [ ] Bolhas de mensagem (enviadas à direita, recebidas à esquerda)
- [ ] Campo de input fixo no rodapé
- [ ] Botão de enviar
- [ ] Timestamp em cada mensagem
- [ ] Indicadores de status (enviando, enviado, lido)
- [ ] Integrar função `openChat()` em `chat.html`

### 2. Endpoint de Mensagens Individuais
**Status:** Não iniciado
**Arquivo:** `app.py`

- [ ] Implementar GET `/api/messages?contact_pubkey=xxx`
  - Buscar mensagens de uma conversa específica
  - Ordenar por timestamp (crescente)
  - Limitar a últimas N mensagens (ex: 50)
  - Descriptografar mensagens NIP-04
- [ ] Implementar POST `/api/messages/send`
  - Validar campos (destinatário, conteúdo)
  - Criptografar com NIP-04
  - Salvar no banco local
  - Publicar no Nostr (kind 4)
  - Retornar confirmação

### 3. Busca/Filtragem de Grupos e Contatos
**Status:** Parcial (só chats implementado)
**Arquivo:** `chat.html`

- [ ] Implementar `filterGroups(query)` similar a `filterChats()`
- [ ] Implementar `filterContacts(query)`
- [ ] Atualizar event listener para detectar tab ativa

---

## 📋 Prioridade Média

### 4. Tab de Contatos Funcional
**Status:** UI pronta, backend pendente
**Arquivos:** `app.py`, `chat.html`

- [ ] Implementar GET `/api/contacts`
  - Buscar contatos do usuário (tabela `contacts`)
  - Join com `users` para perfis
  - Retornar lista ordenada alfabeticamente
- [ ] Renderizar lista no frontend
- [ ] Modal "Adicionar Contato"
  - Input: npub ou NIP-05
  - Validação
  - Buscar perfil no Nostr
  - Salvar no banco
- [ ] Abrir conversa ao clicar em contato

### 5. Envio/Recebimento em Tempo Real
**Status:** Não iniciado
**Arquivos:** Novo módulo

**Opção A - WebSocket:**
- [ ] Implementar WebSocket server (Flask-SocketIO)
- [ ] Cliente conecta ao abrir app
- [ ] Emitir evento ao receber mensagem
- [ ] Atualizar UI automaticamente

**Opção B - Polling:**
- [ ] Endpoint GET `/api/messages/poll?since=timestamp`
- [ ] Frontend faz polling a cada 3-5 segundos
- [ ] Atualizar lista de chats e conversa ativa

**Opção C - Nostr Subscription (NIP-01):**
- [ ] Conectar ao relay via WebSocket no frontend
- [ ] Subscribe para kind 4 (DMs) do usuário
- [ ] Processar eventos em tempo real
- [ ] Descriptografar e exibir

### 6. Upload de Mídia
**Status:** Não iniciado
**Integração:** LiberMedia

- [ ] Botão de anexo na conversa
- [ ] Upload para media.libernet.app
- [ ] Retornar URL
- [ ] Enviar mensagem com link
- [ ] Preview de imagens inline
- [ ] Preview de vídeos inline
- [ ] Download de arquivos

---

## 🔧 Prioridade Baixa

### 7. Melhorias de UX

- [ ] Pull-to-refresh nas listas
- [ ] Skeleton loaders durante carregamento
- [ ] Animações de transição entre telas
- [ ] Haptic feedback no mobile
- [ ] Sons de notificação
- [ ] Indicador "digitando..."

### 8. Grupos - Funcionalidades Avançadas

- [ ] Chat em grupo funcional (similar a individual)
- [ ] Mensagens em tempo real
- [ ] Modal de informações do grupo
- [ ] Editar grupo (admin only)
- [ ] Adicionar membros (admin/moderador)
- [ ] Remover membros (admin only)
- [ ] Sair do grupo
- [ ] Permissões por role

### 9. Configurações - Modais Funcionais

- [ ] Modal de Aparência (tema)
- [ ] Modal de Relays
  - Listar relays ativos
  - Adicionar relay customizado
  - Remover relay
  - Testar conexão
- [ ] Modal de Carteira
  - Conectar NWC
  - Exibir saldo
  - Histórico de transações
- [ ] Modal de Publicação de Mídia
  - Escolher servidor de upload
  - Configurar API key (se necessário)
- [ ] Modal de Chave Privada
  - Exibir nsec (com blur)
  - Botão copiar
  - Aviso de segurança destacado

### 10. Lightning Network

- [ ] Integração NWC (Nostr Wallet Connect)
- [ ] Enviar satoshis para contato
- [ ] Receber satoshis
- [ ] Emblemas pagos
  - Escolher emblema
  - Pagar via Lightning
  - Enviar para contato
  - Notificar destinatário
- [ ] Zaps (NIP-57)
  - Botão de zap em mensagens
  - Invoice generation
  - Confirmação de pagamento

---

## 🐛 Bugs Conhecidos

Nenhum bug conhecido no momento.

---

## 📝 Notas para Próxima Sessão

### Contexto
- Lista de chats implementada e funcionando
- Backend retorna conversas ordenadas por última mensagem
- Busca em tempo real nos chats
- Design mobile otimizado (estilo WhatsApp)

### Próximo Passo Lógico
**Implementar visualização de conversa individual** quando usuário clicar em um chat.

### Decisões Técnicas Pendentes
1. **Tempo Real**: Escolher entre WebSocket, Polling ou Nostr direto
2. **Descriptografia**: Onde fazer (backend ou frontend)?
   - Backend: Mais seguro (nsec fica no servidor)
   - Frontend: Mais privado (nsec fica no navegador)
3. **Paginação**: Carregar todas mensagens ou paginar?

### Dicas de Implementação
- Reutilizar componentes do `chat.html` (header, modals)
- Manter consistência visual (cores, tamanhos, espaçamentos)
- Testar sempre no mobile (prioridade)
- Logs detalhados para debug
- Commit frequente

---

## 📊 Progresso Geral

**Funcionalidades Concluídas:** 7/20 (35%)

- ✅ Autenticação Nostr
- ✅ Navegação com tabs
- ✅ Lista de chats
- ✅ Lista de grupos
- ✅ Criar grupos
- ✅ Configurações (UI)
- ✅ PWA básico

**Em Andamento:** 0/20

**Pendentes:** 13/20

---

**Última atualização: 2025-12-09 às 15:30 BRT**
**Próxima sessão: 2025-12-10**
