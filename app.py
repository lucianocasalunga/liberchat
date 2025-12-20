#!/usr/bin/env python3
"""
LiberChat - Comunicador Nostr Descentralizado
Desenvolvido por: LiberNet
Data: 2025-12-08
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
from datetime import datetime, timedelta
from functools import wraps
import nostr_utils
from nostr_sdk import Client, Filter, Kind, Nip19
import asyncio
import payment_integration

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')

# Configurar sessões para funcionar via HTTPS/Proxy
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS via Caddy
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Necessário para Safari/Chrome modernos
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit para uploads

# CORS com suporte a credenciais (cookies/session)
CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": ["https://chat.libernet.app", "http://localhost:5052"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Configurações
DEBUG = os.getenv('DEBUG', 'False') == 'True'
PORT = int(os.getenv('PORT', 5052))

# Database connection
def get_db_connection():
    """Conecta ao PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME', 'liberchat'),
        user=os.getenv('DB_USER', 'liberchat'),
        password=os.getenv('DB_PASSWORD', ''),
        cursor_factory=RealDictCursor
    )

# Redis connection
def get_redis_connection():
    """Conecta ao Redis"""
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True
    )


# ==================== AUTH DECORATORS ====================

def login_required(f):
    """Decorator para rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'pubkey' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROTAS ====================

@app.route('/')
def index():
    """Página inicial / Login"""
    return render_template('index.html')

@app.route('/chat')
@login_required
def chat():
    """Interface de chat"""
    return render_template('chat.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/dm/<contact_pubkey>')
@login_required
def dm_chat(contact_pubkey):
    """Interface de mensagens diretas (DM)"""
    print(f'[DM] Abrindo DM com pubkey: {contact_pubkey}')

    # Buscar informações do contato via Nostr
    from nostr_sdk import PublicKey

    try:
        # Converter pubkey para npub
        print(f'[DM] Convertendo pubkey para npub...')
        contact_pk = PublicKey.from_hex(contact_pubkey)
        contact_npub = contact_pk.to_bech32()
        print(f'[DM] npub gerado: {contact_npub}')

        # Buscar perfil do contato
        print(f'[DM] Buscando perfil do contato...')
        perfil = buscar_perfil_nostr(contact_npub)
        print(f'[DM] Perfil encontrado: {perfil}')

        # Se não encontrar perfil, usar dados básicos
        if not perfil:
            print(f'[DM] Perfil não encontrado, usando dados básicos')
            perfil = {}

        contact = {
            'pubkey': contact_pubkey,
            'npub': contact_npub,
            'name': perfil.get('name', 'Usuário'),
            'display_name': perfil.get('display_name') or perfil.get('name', 'Usuário'),
            'picture': perfil.get('picture'),
            'nip05': perfil.get('nip05'),
            'about': perfil.get('about')
        }

        # Salvar/atualizar perfil do contato na tabela users
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO users (pubkey, npub, display_name, picture_url, nip05, about, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (pubkey)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    picture_url = EXCLUDED.picture_url,
                    nip05 = EXCLUDED.nip05,
                    about = EXCLUDED.about,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                contact_pubkey,
                contact_npub,
                contact['display_name'],
                contact['picture'],
                contact['nip05'],
                contact['about']
            ))

            # Adicionar automaticamente à lista de contatos do usuário
            user_id = session.get('user_id')
            if user_id:
                cur.execute("""
                    INSERT INTO contacts (user_id, contact_pubkey)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, contact_pubkey) DO NOTHING
                """, (user_id, contact_pubkey))
                print(f'[DM] Contato adicionado à lista do usuário')

            conn.commit()
            cur.close()
            conn.close()
            print(f'[DM] Perfil do contato salvo/atualizado na tabela users')
        except Exception as e:
            print(f'[DM] Erro ao salvar perfil do contato: {e}')
            # Não interromper o fluxo por erro ao salvar perfil

        print(f'[DM] Renderizando template com contact: {contact}')

        return render_template('dm_chat.html',
                             pubkey=session.get('pubkey'),
                             npub=session.get('npub'),
                             contact=contact)
    except Exception as e:
        print(f'[DM] Erro ao carregar contato: {e}')
        import traceback
        traceback.print_exc()
        return f"Erro ao carregar contato: {str(e)}", 500

@app.route('/api/dm/save', methods=['POST'])
@login_required
def save_dm():
    """Salvar mensagem DM no banco de dados local"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        recipient_pubkey = data.get('recipient_pubkey')
        encrypted_content = data.get('encrypted_content')
        decrypted_content = data.get('decrypted_content')
        created_at = data.get('created_at')

        if not all([event_id, recipient_pubkey, encrypted_content, decrypted_content, created_at]):
            return jsonify({'status': 'error', 'error': 'Campos obrigatórios faltando'}), 400

        sender_pubkey = session.get('pubkey')

        print(f'[DM] Salvando mensagem no banco de dados')
        print(f'[DM] Event ID: {event_id}')
        print(f'[DM] De: {sender_pubkey[:16]}... Para: {recipient_pubkey[:16]}...')

        conn = get_db_connection()
        cur = conn.cursor()

        # Salvar mensagem
        cur.execute("""
            INSERT INTO messages (event_id, sender_pubkey, recipient_pubkey, content, decrypted_content, created_at)
            VALUES (%s, %s, %s, %s, %s, to_timestamp(%s))
            ON CONFLICT (event_id) DO NOTHING
        """, (event_id, sender_pubkey, recipient_pubkey, encrypted_content, decrypted_content, created_at))

        conn.commit()
        cur.close()
        conn.close()

        print(f'[DM] Mensagem salva com sucesso!')

        return jsonify({
            'status': 'ok',
            'message': 'Mensagem salva'
        })

    except Exception as e:
        print(f'[DM] Erro ao salvar mensagem: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/group/<int:group_id>')
@login_required
def group_chat(group_id):
    """Interface de chat do grupo"""
    # Verificar se o grupo existe e se o usuário é membro
    conn = get_db_connection()
    cur = conn.cursor()

    pubkey = session.get('pubkey')

    # Buscar informações do grupo
    cur.execute("""
        SELECT g.*,
               EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_pubkey = %s) as is_member,
               (g.admin_pubkey = %s) as is_admin
        FROM groups g
        WHERE g.id = %s
    """, (pubkey, pubkey, group_id))

    group = cur.fetchone()
    cur.close()
    conn.close()

    if not group:
        return "Grupo não encontrado", 404

    # Se o grupo é privado e o usuário não é membro, negar acesso
    if group['private'] and not group['is_member']:
        return "Você não tem permissão para acessar este grupo", 403

    return render_template('group_chat.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'),
                         group=group)

@app.route('/contacts')
@login_required
def contacts():
    """Lista de contatos"""
    return render_template('contacts.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/settings')
@login_required
def settings():
    """Configurações"""
    return render_template('settings.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/security')
@login_required
def security():
    """Página de Segurança"""
    return render_template('security.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/general')
@login_required
def settings_general():
    """Configurações Gerais"""
    return render_template('general.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/appearance')
@login_required
def settings_appearance():
    """Configurações de Aparência"""
    return render_template('appearance.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/notifications')
@login_required
def settings_notifications():
    """Configurações de Notificações"""
    return render_template('notifications.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/relays')
@login_required
def settings_relays():
    """Configurações de Relays"""
    return render_template('relays.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/translation')
@login_required
def settings_translation():
    """Configurações de Tradução"""
    return render_template('translation.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


@app.route('/settings/wallet')
@login_required
def settings_wallet():
    """Configurações de Carteira Lightning"""
    return render_template('wallet.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/settings/emojis')
@login_required
def settings_emojis():
    """Configurações de Emojis"""
    return render_template('emojis.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/projects')
@login_required
def projects():
    """Página de Projetos Liber"""
    return render_template('projects.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/help')
@login_required
def help_page():
    """Página de Ajuda"""
    return render_template('help.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/donate')
@login_required
def donate():
    """Página de Doações"""
    return render_template('donate.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))

@app.route('/edit-profile')
@login_required
def edit_profile():
    """Página de Edição de Perfil"""
    return render_template('edit_profile.html',
                         pubkey=session.get('pubkey'),
                         npub=session.get('npub'))


# ==================== API ENDPOINTS ====================

@app.route('/api/auth/nostr', methods=['POST'])
def auth_nostr():
    """Autenticação via Nostr (NIP-07 ou nsec)"""
    data = request.json

    if not data:
        return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400

    pubkey_hex = None

    # Autenticação via pubkey (NIP-07 - extensão)
    if 'pubkey' in data:
        pubkey_hex = data['pubkey']

        # Validar formato hex (64 caracteres)
        if not pubkey_hex or len(pubkey_hex) != 64:
            return jsonify({'success': False, 'error': 'Pubkey inválida'}), 400

    # Autenticação via nsec (chave privada)
    elif 'nsec' in data:
        nsec = data['nsec']

        # Validar nsec
        if not nostr_utils.validate_nsec(nsec):
            return jsonify({'success': False, 'error': 'nsec inválido'}), 400

        # Converter nsec para hex
        private_key_hex = nostr_utils.nsec_to_hex(nsec)
        if not private_key_hex:
            return jsonify({'success': False, 'error': 'Erro ao processar nsec'}), 500

        # Derivar chave pública
        pubkey_hex = nostr_utils.get_public_key_from_private(private_key_hex)
        if not pubkey_hex:
            return jsonify({'success': False, 'error': 'Erro ao derivar chave pública'}), 500

    else:
        return jsonify({'success': False, 'error': 'pubkey ou nsec requerido'}), 400

    # Salvar na sessão
    session.permanent = True  # Tornar sessão persistente
    session['pubkey'] = pubkey_hex
    session['npub'] = nostr_utils.hex_to_npub(pubkey_hex)
    session['logged_in'] = True

    # Salvar no Redis (cache de usuários online)
    try:
        r = get_redis_connection()
        user_data = {
            'pubkey': pubkey_hex,
            'npub': session['npub'],
            'last_seen': datetime.now().isoformat()
        }
        r.setex(f'user:{pubkey_hex}', 3600, json.dumps(user_data))  # 1 hora
    except Exception as e:
        print(f'Erro ao salvar no Redis: {e}')

    # Salvar/atualizar perfil no PostgreSQL
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Inserir ou atualizar usuário
        cur.execute("""
            INSERT INTO users (pubkey, npub, last_seen)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (pubkey)
            DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (pubkey_hex, session['npub']))

        user_id = cur.fetchone()['id']
        session['user_id'] = user_id

        conn.commit()
        print(f'Usuário {session["npub"]} salvo no banco (ID: {user_id})')

    except Exception as e:
        print(f'Erro ao salvar usuário no PostgreSQL: {e}')
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return jsonify({
        'success': True,
        'pubkey': pubkey_hex,
        'npub': session['npub']
    })

@app.route('/api/chats/unified', methods=['GET'])
@login_required
def list_unified_chats():
    """Listar conversas DM e grupos unificados, ordenados por última atividade"""
    conn = None
    cur = None
    try:
        user_pubkey = session.get('pubkey')
        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar DMs com última mensagem
        cur.execute("""
            WITH RankedMessages AS (
                SELECT
                    CASE
                        WHEN sender_pubkey = %s THEN recipient_pubkey
                        ELSE sender_pubkey
                    END as contact_pubkey,
                    decrypted_content,
                    sender_pubkey,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY CASE
                            WHEN sender_pubkey = %s THEN recipient_pubkey
                            ELSE sender_pubkey
                        END
                        ORDER BY created_at DESC
                    ) as rn
                FROM messages
                WHERE sender_pubkey = %s OR recipient_pubkey = %s
            )
            SELECT
                'dm' as type,
                rm.contact_pubkey as id,
                rm.contact_pubkey,
                u.display_name as name,
                u.picture_url,
                u.nip05,
                rm.decrypted_content as last_message,
                rm.sender_pubkey as last_sender,
                rm.created_at as last_message_time,
                NULL::boolean as is_group,
                NULL::integer as member_count,
                NULL::boolean as is_admin,
                NULL::boolean as private
            FROM RankedMessages rm
            LEFT JOIN users u ON u.pubkey = rm.contact_pubkey
            WHERE rm.rn = 1
        """, (user_pubkey, user_pubkey, user_pubkey, user_pubkey))

        dms = cur.fetchall()

        # Buscar grupos com última mensagem
        cur.execute("""
            SELECT
                'group' as type,
                g.id::text as id,
                NULL as contact_pubkey,
                g.name,
                g.picture_url,
                NULL as nip05,
                (SELECT content FROM group_messages WHERE group_id = g.id ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT sender_pubkey FROM group_messages WHERE group_id = g.id ORDER BY created_at DESC LIMIT 1) as last_sender,
                (SELECT MAX(created_at) FROM group_messages WHERE group_id = g.id) as last_message_time,
                true as is_group,
                (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
                (g.admin_pubkey = %s) as is_admin,
                g.private
            FROM groups g
            INNER JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_pubkey = %s
        """, (user_pubkey, user_pubkey))

        groups = cur.fetchall()

        # Combinar e ordenar por última mensagem
        all_chats = []

        # Processar DMs
        from nostr_sdk import PublicKey
        for dm in dms:
            try:
                contact_pk = PublicKey.from_hex(dm['contact_pubkey'])
                contact_npub = contact_pk.to_bech32()
            except:
                contact_npub = dm['contact_pubkey'][:12] + '...'

            is_sent = dm['last_sender'] == user_pubkey
            last_msg = dm['last_message'] or ''

            all_chats.append({
                'type': 'dm',
                'id': dm['contact_pubkey'],
                'pubkey': dm['contact_pubkey'],
                'npub': contact_npub,
                'name': dm['name'] or f"{dm['contact_pubkey'][:8]}...",
                'picture': dm['picture_url'],
                'nip05': dm['nip05'],
                'last_message': last_msg[:50] + '...' if len(last_msg) > 50 else last_msg,
                'last_message_time': dm['last_message_time'].isoformat() if dm['last_message_time'] else '',
                'timestamp': dm['last_message_time'].timestamp() if dm['last_message_time'] else 0,
                'is_sent': is_sent,
                'is_group': False
            })

        # Processar grupos
        for group in groups:
            last_msg = group['last_message'] or ''
            member_text = f"{group['member_count']} {'membro' if group['member_count'] == 1 else 'membros'}"

            all_chats.append({
                'type': 'group',
                'id': group['id'],
                'group_id': int(group['id']),
                'name': group['name'],
                'picture': group['picture_url'],
                'last_message': last_msg[:50] + '...' if len(last_msg) > 50 else last_msg,
                'last_message_time': group['last_message_time'].isoformat() if group['last_message_time'] else '',
                'timestamp': group['last_message_time'].timestamp() if group['last_message_time'] else 0,
                'is_group': True,
                'member_count': group['member_count'],
                'member_text': member_text,
                'is_admin': group['is_admin'],
                'private': group['private']
            })

        # Ordenar por timestamp (mais recente primeiro)
        all_chats.sort(key=lambda x: x['timestamp'], reverse=True)

        # Remover timestamp do resultado final
        for chat in all_chats:
            del chat['timestamp']

        print(f'[UNIFIED] Retornando {len(all_chats)} conversas ({len(dms)} DMs + {len(groups)} grupos)')

        return jsonify({
            'status': 'ok',
            'chats': all_chats
        })

    except Exception as e:
        print(f'Erro ao listar chats unificados: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/chats/list', methods=['GET'])
@login_required
def list_chats():
    """Listar conversas do usuário ordenadas por última mensagem"""
    try:
        user_pubkey = session.get('pubkey')

        print(f'[CHATS] Sessão completa: {dict(session)}')
        print(f'[CHATS] user_pubkey da sessão: {user_pubkey}')

        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar todas as conversas com a última mensagem de cada uma
        cur.execute("""
            WITH LastMessages AS (
                SELECT
                    CASE
                        WHEN sender_pubkey = %s THEN recipient_pubkey
                        ELSE sender_pubkey
                    END as contact_pubkey,
                    MAX(created_at) as last_message_time
                FROM messages
                WHERE sender_pubkey = %s OR recipient_pubkey = %s
                GROUP BY contact_pubkey
            ),
            ContactDetails AS (
                SELECT
                    lm.contact_pubkey,
                    lm.last_message_time,
                    u.display_name,
                    u.picture_url,
                    u.nip05,
                    m.content,
                    m.decrypted_content,
                    m.sender_pubkey,
                    m.read_at
                FROM LastMessages lm
                LEFT JOIN users u ON u.pubkey = lm.contact_pubkey
                LEFT JOIN messages m ON (
                    (m.sender_pubkey = %s AND m.recipient_pubkey = lm.contact_pubkey) OR
                    (m.recipient_pubkey = %s AND m.sender_pubkey = lm.contact_pubkey)
                ) AND m.created_at = lm.last_message_time
            )
            SELECT
                contact_pubkey,
                display_name,
                picture_url,
                nip05,
                COALESCE(decrypted_content, content) as last_message,
                sender_pubkey,
                last_message_time,
                read_at
            FROM ContactDetails
            ORDER BY last_message_time DESC
        """, (user_pubkey, user_pubkey, user_pubkey, user_pubkey, user_pubkey))

        chats = []
        for row in cur.fetchall():
            # Determinar se a mensagem foi enviada ou recebida
            is_sent = row['sender_pubkey'] == user_pubkey

            # Verificar se há mensagens não lidas (apenas mensagens recebidas)
            unread = not is_sent and row['read_at'] is None

            # Criar npub do contato
            from nostr_sdk import PublicKey
            try:
                contact_pk = PublicKey.from_hex(row['contact_pubkey'])
                contact_npub = contact_pk.to_bech32()
            except:
                contact_npub = row['contact_pubkey'][:12] + '...'

            chat = {
                'pubkey': row['contact_pubkey'],
                'npub': contact_npub,
                'name': row['display_name'] or f"{row['contact_pubkey'][:8]}...",
                'picture': row['picture_url'],
                'nip05': row['nip05'],
                'last_message': row['last_message'][:50] + '...' if row['last_message'] and len(row['last_message']) > 50 else (row['last_message'] or ''),
                'last_message_time': row['last_message_time'].isoformat() if row['last_message_time'] else '',
                'is_sent': is_sent,
                'unread': unread
            }
            chats.append(chat)

        cur.close()
        conn.close()

        print(f'[CHATS] Retornando {len(chats)} conversas')

        return jsonify({
            'status': 'ok',
            'chats': chats
        })

    except Exception as e:
        print(f'Erro ao listar chats: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Buscar mensagens de um chat"""
    try:
        contact_pubkey = request.args.get('contact_pubkey')

        if not contact_pubkey:
            return jsonify({'status': 'error', 'error': 'contact_pubkey obrigatório'}), 400

        my_pubkey = session.get('pubkey')

        if not my_pubkey:
            return jsonify({'status': 'error', 'error': 'Usuário não autenticado'}), 401

        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar mensagens entre os dois usuários (ambas as direções)
        cur.execute("""
            SELECT
                event_id,
                sender_pubkey,
                recipient_pubkey,
                content as encrypted_content,
                decrypted_content,
                created_at,
                read_at
            FROM messages
            WHERE
                (sender_pubkey = %s AND recipient_pubkey = %s)
                OR
                (sender_pubkey = %s AND recipient_pubkey = %s)
            ORDER BY created_at ASC
        """, (my_pubkey, contact_pubkey, contact_pubkey, my_pubkey))

        messages = []
        for row in cur.fetchall():
            messages.append({
                'event_id': row['event_id'],
                'sender_pubkey': row['sender_pubkey'],
                'recipient_pubkey': row['recipient_pubkey'],
                'encrypted_content': row['encrypted_content'],
                'decrypted_content': row['decrypted_content'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'read_at': row['read_at'].isoformat() if row['read_at'] else None,
                'is_mine': row['sender_pubkey'] == my_pubkey
            })

        cur.close()
        conn.close()

        print(f'[MESSAGES] Retornando {len(messages)} mensagens entre {my_pubkey[:8]}... e {contact_pubkey[:8]}...')

        return jsonify({'status': 'ok', 'messages': messages})

    except Exception as e:
        print(f'[MESSAGES] Erro ao buscar mensagens: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Enviar mensagem (NIP-04)"""
    data = request.json
    # TODO: Implementar envio de mensagem
    return jsonify({'success': True, 'message': 'Mensagem enviada'})

@app.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    """Listar contatos do usuário"""
    try:
        user_id = session.get('user_id')

        print(f'[CONTACTS GET] Sessão completa: {dict(session)}')
        print(f'[CONTACTS GET] user_id da sessão: {user_id}')

        if not user_id:
            print(f'[CONTACTS GET] ERRO: user_id é None!')
            return jsonify({'status': 'error', 'error': 'Sessão inválida', 'contacts': []}), 401

        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar contatos do usuário com informações do perfil
        cur.execute("""
            SELECT
                c.contact_pubkey,
                u.npub,
                u.display_name,
                u.picture_url,
                u.nip05,
                c.added_at
            FROM contacts c
            LEFT JOIN users u ON u.pubkey = c.contact_pubkey
            WHERE c.user_id = %s
            ORDER BY c.added_at DESC
        """, (user_id,))

        contacts = []
        for row in cur.fetchall():
            from nostr_sdk import PublicKey

            # Converter pubkey para npub se não tiver
            npub = row['npub']
            if not npub:
                try:
                    pk = PublicKey.from_hex(row['contact_pubkey'])
                    npub = pk.to_bech32()
                except:
                    npub = row['contact_pubkey'][:12] + '...'

            contacts.append({
                'pubkey': row['contact_pubkey'],
                'npub': npub,
                'name': row['display_name'] or f"{row['contact_pubkey'][:8]}...",
                'picture': row['picture_url'],
                'nip05': row['nip05'],
                'added_at': row['added_at'].isoformat() if row['added_at'] else None
            })

        cur.close()
        conn.close()

        print(f'[CONTACTS GET] Retornando {len(contacts)} contatos')

        return jsonify({'status': 'ok', 'contacts': contacts})

    except Exception as e:
        print(f'[CONTACTS] Erro ao listar contatos: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/contacts/add', methods=['POST'])
@login_required
def add_contact():
    """Adicionar contato"""
    try:
        data = request.get_json()
        contact_pubkey = data.get('pubkey')

        if not contact_pubkey:
            return jsonify({'status': 'error', 'error': 'pubkey obrigatório'}), 400

        user_id = session.get('user_id')

        print(f'[CONTACTS] Sessão completa: {dict(session)}')
        print(f'[CONTACTS] user_id da sessão: {user_id}')

        if not user_id:
            return jsonify({'status': 'error', 'error': 'Sessão inválida. Faça login novamente.'}), 401

        # Primeiro, buscar perfil Nostr do contato e salvar na tabela users
        from nostr_sdk import PublicKey

        try:
            contact_pk = PublicKey.from_hex(contact_pubkey)
            contact_npub = contact_pk.to_bech32()
            print(f'[CONTACTS] Buscando perfil Nostr para {contact_npub}...')

            # Buscar perfil
            perfil = buscar_perfil_nostr(contact_npub)

            conn = get_db_connection()
            cur = conn.cursor()

            # Salvar/atualizar perfil na tabela users
            if perfil:
                print(f'[CONTACTS] Perfil encontrado: {perfil.get("display_name") or perfil.get("name")}')
                cur.execute("""
                    INSERT INTO users (pubkey, npub, display_name, picture_url, nip05, about, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (pubkey)
                    DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        picture_url = EXCLUDED.picture_url,
                        nip05 = EXCLUDED.nip05,
                        about = EXCLUDED.about,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    contact_pubkey,
                    contact_npub,
                    perfil.get('display_name') or perfil.get('name'),
                    perfil.get('picture'),
                    perfil.get('nip05'),
                    perfil.get('about')
                ))
            else:
                # Se não encontrou perfil, criar registro básico
                print(f'[CONTACTS] Perfil não encontrado, criando registro básico')
                cur.execute("""
                    INSERT INTO users (pubkey, npub, last_seen)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (pubkey) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                """, (contact_pubkey, contact_npub))

            # Adicionar contato (ON CONFLICT ignora se já existe)
            cur.execute("""
                INSERT INTO contacts (user_id, contact_pubkey)
                VALUES (%s, %s)
                ON CONFLICT (user_id, contact_pubkey) DO NOTHING
            """, (user_id, contact_pubkey))

            conn.commit()
            cur.close()
            conn.close()

            print(f'[CONTACTS] Contato adicionado: {contact_pubkey[:16]}...')

            return jsonify({'status': 'ok', 'message': 'Contato adicionado'})

        except Exception as e:
            print(f'[CONTACTS] Erro ao processar contato: {e}')
            # Se der erro na busca de perfil, ainda adiciona aos contatos
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO contacts (user_id, contact_pubkey)
                VALUES (%s, %s)
                ON CONFLICT (user_id, contact_pubkey) DO NOTHING
            """, (user_id, contact_pubkey))

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({'status': 'ok', 'message': 'Contato adicionado (sem perfil)'})

    except Exception as e:
        print(f'[CONTACTS] Erro ao adicionar contato: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/contacts/<contact_pubkey>/refresh', methods=['POST'])
@login_required
def refresh_contact_profile(contact_pubkey):
    """Atualizar perfil de um contato buscando no Nostr"""
    try:
        from nostr_sdk import PublicKey

        # Converter pubkey para npub
        contact_pk = PublicKey.from_hex(contact_pubkey)
        contact_npub = contact_pk.to_bech32()

        print(f'[CONTACTS] Atualizando perfil de {contact_npub}...')

        # Buscar perfil
        perfil = buscar_perfil_nostr(contact_npub)

        conn = get_db_connection()
        cur = conn.cursor()

        if perfil:
            print(f'[CONTACTS] Perfil encontrado: {perfil.get("display_name") or perfil.get("name")}')
            cur.execute("""
                INSERT INTO users (pubkey, npub, display_name, picture_url, nip05, about, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (pubkey)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    picture_url = EXCLUDED.picture_url,
                    nip05 = EXCLUDED.nip05,
                    about = EXCLUDED.about,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                contact_pubkey,
                contact_npub,
                perfil.get('display_name') or perfil.get('name'),
                perfil.get('picture'),
                perfil.get('nip05'),
                perfil.get('about')
            ))
            conn.commit()
            cur.close()
            conn.close()

            return jsonify({
                'status': 'ok',
                'message': 'Perfil atualizado',
                'perfil': perfil
            })
        else:
            cur.close()
            conn.close()
            return jsonify({'status': 'error', 'error': 'Perfil não encontrado'}), 404

    except Exception as e:
        print(f'[CONTACTS] Erro ao atualizar perfil: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/contacts/<contact_pubkey>', methods=['DELETE'])
@login_required
def delete_contact(contact_pubkey):
    """Remover contato"""
    try:
        user_id = session.get('user_id')

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM contacts
            WHERE user_id = %s AND contact_pubkey = %s
        """, (user_id, contact_pubkey))

        conn.commit()
        cur.close()
        conn.close()

        print(f'[CONTACTS] Contato removido: {contact_pubkey[:16]}...')

        return jsonify({'status': 'ok', 'message': 'Contato removido'})

    except Exception as e:
        print(f'[CONTACTS] Erro ao remover contato: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout - limpar sessão"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/profile', methods=['GET', 'POST'])
def profile():
    """Obter ou atualizar perfil do usuário"""
    if request.method == 'GET':
        # TODO: Retornar perfil
        return jsonify({'profile': {}})
    else:
        # TODO: Atualizar perfil
        return jsonify({'success': True})


# ==================== GROUPS ENDPOINTS ====================

@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    """Criar novo grupo"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        picture_url = data.get('picture_url', '').strip()
        private = data.get('private', False)

        if not name or len(name) < 3:
            return jsonify({'status': 'error', 'error': 'Nome deve ter no mínimo 3 caracteres'}), 400

        # Gerar ID único para o grupo (usando hash do nome + timestamp)
        import hashlib
        import time
        group_id_raw = f"{name}{session['pubkey']}{time.time()}"
        group_id = hashlib.sha256(group_id_raw.encode()).hexdigest()[:32]

        conn = get_db_connection()
        cur = conn.cursor()

        # Criar grupo
        cur.execute("""
            INSERT INTO groups (group_id, name, description, picture_url, admin_pubkey, private)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (group_id, name, description, picture_url, session['pubkey'], private))

        new_group_id = cur.fetchone()['id']

        # Adicionar criador como admin
        cur.execute("""
            INSERT INTO group_members (group_id, user_pubkey, role)
            VALUES (%s, %s, 'admin')
        """, (new_group_id, session['pubkey']))

        conn.commit()

        print(f'Grupo criado: {name} (ID: {new_group_id})')

        # Publicar grupo no Nostr (NIP-29)
        try:
            publicar_grupo_nostr(group_id, name, description or '', picture_url or '', session['pubkey'], private)
        except Exception as e:
            print(f'Aviso: Erro ao publicar grupo no Nostr: {e}')
            # Não falhar se der erro no Nostr, o grupo já foi criado localmente

        return jsonify({
            'status': 'ok',
            'group': {
                'id': new_group_id,
                'group_id': group_id,
                'name': name,
                'description': description,
                'picture_url': picture_url,
                'private': private
            }
        })

    except Exception as e:
        print(f'Erro ao criar grupo: {e}')
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/groups/list', methods=['GET'])
@login_required
def list_groups():
    """Listar grupos do usuário"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar grupos onde o usuário é membro
        cur.execute("""
            SELECT
                g.id,
                g.group_id,
                g.name,
                g.description,
                g.picture_url,
                g.admin_pubkey,
                g.private,
                g.created_at,
                gm.role,
                (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count,
                (SELECT MAX(created_at) FROM group_messages WHERE group_id = g.id) as last_message_at
            FROM groups g
            INNER JOIN group_members gm ON g.id = gm.group_id
            WHERE gm.user_pubkey = %s
            ORDER BY last_message_at DESC NULLS LAST, g.created_at DESC
        """, (session['pubkey'],))

        groups = cur.fetchall()

        groups_list = []
        for group in groups:
            groups_list.append({
                'id': group['id'],
                'group_id': group['group_id'],
                'name': group['name'],
                'description': group['description'],
                'picture_url': group['picture_url'],
                'admin_pubkey': group['admin_pubkey'],
                'private': group['private'],
                'created_at': group['created_at'].isoformat() if group['created_at'] else None,
                'role': group['role'],
                'member_count': group['member_count'],
                'last_message_at': group['last_message_at'].isoformat() if group['last_message_at'] else None,
                'is_admin': group['admin_pubkey'] == session['pubkey']
            })

        return jsonify({'status': 'ok', 'groups': groups_list})

    except Exception as e:
        print(f'Erro ao listar grupos: {e}')
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/groups/<int:group_id>/update', methods=['PUT'])
@login_required
def update_group(group_id):
    """Atualizar grupo (nome, descrição, imagem)"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se é admin do grupo
        cur.execute("""
            SELECT admin_pubkey FROM groups WHERE id = %s
        """, (group_id,))

        group = cur.fetchone()
        if not group:
            return jsonify({'status': 'error', 'error': 'Grupo não encontrado'}), 404

        if group['admin_pubkey'] != session['pubkey']:
            return jsonify({'status': 'error', 'error': 'Apenas o admin pode editar o grupo'}), 403

        # Atualizar campos
        updates = []
        params = []

        if 'name' in data:
            updates.append('name = %s')
            params.append(data['name'].strip())

        if 'description' in data:
            updates.append('description = %s')
            params.append(data['description'].strip())

        if 'picture_url' in data:
            updates.append('picture_url = %s')
            params.append(data['picture_url'].strip())

        if not updates:
            return jsonify({'status': 'error', 'error': 'Nenhum campo para atualizar'}), 400

        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(group_id)

        query = f"UPDATE groups SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        conn.commit()

        print(f'Grupo {group_id} atualizado')

        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f'Erro ao atualizar grupo: {e}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/groups/<int:group_id>/members', methods=['GET'])
@login_required
def get_group_members(group_id):
    """Listar membros do grupo"""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se usuário é membro
        cur.execute("""
            SELECT 1 FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, session['pubkey']))

        if not cur.fetchone():
            return jsonify({'status': 'error', 'error': 'Você não é membro deste grupo'}), 403

        # Buscar membros
        cur.execute("""
            SELECT
                gm.user_pubkey,
                gm.role,
                gm.joined_at,
                u.display_name,
                u.nip05,
                u.picture_url
            FROM group_members gm
            LEFT JOIN users u ON gm.user_pubkey = u.pubkey
            WHERE gm.group_id = %s
            ORDER BY
                CASE gm.role
                    WHEN 'admin' THEN 1
                    WHEN 'moderator' THEN 2
                    ELSE 3
                END,
                gm.joined_at ASC
        """, (group_id,))

        members = cur.fetchall()

        members_list = []
        for member in members:
            pubkey = member['user_pubkey']
            name = member['display_name']
            nip05 = member['nip05']
            picture = member['picture_url']

            # Se não tem informações, tentar buscar do Nostr
            if not name or not picture:
                try:
                    # Converter pubkey para npub
                    from nostr_sdk import PublicKey
                    pk = PublicKey.from_hex(pubkey)
                    npub = pk.to_bech32()

                    # Buscar perfil do Nostr
                    profile_data = buscar_perfil_nostr(npub)

                    if profile_data:
                        if not name and profile_data.get('name'):
                            name = profile_data.get('name')
                        if not picture and profile_data.get('picture'):
                            picture = profile_data.get('picture')
                        if not nip05 and profile_data.get('nip05'):
                            nip05 = profile_data.get('nip05')

                        # Atualizar ou criar registro no users
                        cur.execute("""
                            INSERT INTO users (npub, pubkey, display_name, nip05, picture_url)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (pubkey) DO UPDATE SET
                                display_name = COALESCE(EXCLUDED.display_name, users.display_name),
                                nip05 = COALESCE(EXCLUDED.nip05, users.nip05),
                                picture_url = COALESCE(EXCLUDED.picture_url, users.picture_url),
                                updated_at = NOW()
                        """, (npub, pubkey, name, nip05, picture))
                        conn.commit()

                        print(f'[GROUP] Perfil atualizado para {pubkey[:8]}...: {name}')
                except Exception as e:
                    print(f'[GROUP] Erro ao buscar perfil do Nostr para {pubkey[:8]}...: {e}')

            members_list.append({
                'pubkey': pubkey,
                'role': member['role'],
                'joined_at': member['joined_at'].isoformat() if member['joined_at'] else None,
                'name': name or 'Usuário',
                'nip05': nip05,
                'picture': picture,
                'is_admin': member['role'] == 'admin'
            })

        return jsonify({'status': 'ok', 'members': members_list})

    except Exception as e:
        print(f'Erro ao listar membros: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/groups/<int:group_id>/members/add', methods=['POST'])
@login_required
def add_group_member(group_id):
    """Adicionar membro ao grupo"""
    try:
        data = request.get_json()
        member_pubkey = data.get('pubkey', '').strip()

        if not member_pubkey:
            return jsonify({'status': 'error', 'error': 'pubkey obrigatório'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se é admin ou moderador
        cur.execute("""
            SELECT role FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, session['pubkey']))

        member = cur.fetchone()
        if not member or member['role'] not in ['admin', 'moderator']:
            return jsonify({'status': 'error', 'error': 'Apenas admins e moderadores podem adicionar membros'}), 403

        # Adicionar membro
        try:
            cur.execute("""
                INSERT INTO group_members (group_id, user_pubkey, role)
                VALUES (%s, %s, 'member')
            """, (group_id, member_pubkey))
            conn.commit()

            print(f'Membro {member_pubkey} adicionado ao grupo {group_id}')

            # Publicar no Nostr (NIP-29)
            try:
                adicionar_membro_grupo_nostr(str(group_id), member_pubkey, 'member')
            except Exception as e:
                print(f'Aviso: Erro ao publicar no Nostr: {e}')

            return jsonify({'status': 'ok'})
        except Exception as e:
            if 'unique' in str(e).lower():
                return jsonify({'status': 'error', 'error': 'Usuário já é membro do grupo'}), 400
            raise

    except Exception as e:
        print(f'Erro ao adicionar membro: {e}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/groups/<int:group_id>/messages', methods=['GET'])
@login_required
def get_group_messages(group_id):
    """Buscar mensagens do grupo"""
    conn = None
    cur = None
    try:
        limit = request.args.get('limit', 50, type=int)
        before_id = request.args.get('before', None, type=int)

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se usuário é membro do grupo
        cur.execute("""
            SELECT 1 FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, session['pubkey']))

        if not cur.fetchone():
            return jsonify({'status': 'error', 'error': 'Você não é membro deste grupo'}), 403

        # Buscar mensagens
        if before_id:
            cur.execute("""
                SELECT gm.id, gm.event_id, gm.sender_pubkey, gm.content, gm.created_at,
                       u.display_name as sender_name, u.picture_url as sender_picture
                FROM group_messages gm
                LEFT JOIN users u ON u.pubkey = gm.sender_pubkey
                WHERE gm.group_id = %s AND gm.id < %s
                ORDER BY gm.created_at DESC
                LIMIT %s
            """, (group_id, before_id, limit))
        else:
            cur.execute("""
                SELECT gm.id, gm.event_id, gm.sender_pubkey, gm.content, gm.created_at,
                       u.display_name as sender_name, u.picture_url as sender_picture
                FROM group_messages gm
                LEFT JOIN users u ON u.pubkey = gm.sender_pubkey
                WHERE gm.group_id = %s
                ORDER BY gm.created_at DESC
                LIMIT %s
            """, (group_id, limit))

        messages = cur.fetchall()

        # Formatar mensagens
        result = []
        for msg in reversed(messages):
            result.append({
                'id': msg['id'],
                'event_id': msg['event_id'],
                'sender_pubkey': msg['sender_pubkey'],
                'sender_name': msg['sender_name'] or 'Usuário',
                'sender_picture': msg['sender_picture'],
                'content': msg['content'],
                'created_at': msg['created_at'].isoformat() if msg['created_at'] else None,
                'is_mine': msg['sender_pubkey'] == session['pubkey']
            })

        return jsonify({'status': 'ok', 'messages': result})

    except Exception as e:
        print(f'Erro ao buscar mensagens do grupo: {e}')
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/groups/<int:group_id>/messages/send', methods=['POST'])
@login_required
def send_group_message(group_id):
    """Enviar mensagem para o grupo"""
    conn = None
    cur = None
    try:
        data = request.get_json()
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'status': 'error', 'error': 'Mensagem vazia'}), 400

        if len(content) > 10000:
            return jsonify({'status': 'error', 'error': 'Mensagem muito longa (máx 10000 caracteres)'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se é membro do grupo
        cur.execute("""
            SELECT 1 FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, session['pubkey']))

        if not cur.fetchone():
            return jsonify({'status': 'error', 'error': 'Você não é membro deste grupo'}), 403

        # Gerar event_id único (simplificado)
        import hashlib
        import time
        event_data = f"{group_id}{session['pubkey']}{content}{time.time()}"
        event_id = hashlib.sha256(event_data.encode()).hexdigest()

        # Inserir mensagem
        cur.execute("""
            INSERT INTO group_messages (event_id, group_id, sender_pubkey, content, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id, created_at
        """, (event_id, group_id, session['pubkey'], content))

        result = cur.fetchone()
        conn.commit()

        message_id = result['id']
        created_at = result['created_at']

        print(f'Mensagem enviada ao grupo {group_id} por {session["pubkey"][:8]}...')

        # Publicar no Nostr (opcional, não-bloqueante)
        try:
            publicar_mensagem_grupo_nostr(str(group_id), content, session['pubkey'])
        except Exception as e:
            print(f'Aviso: Erro ao publicar mensagem no Nostr: {e}')

        return jsonify({
            'status': 'ok',
            'message': {
                'id': message_id,
                'event_id': event_id,
                'content': content,
                'created_at': created_at.isoformat()
            }
        })

    except Exception as e:
        print(f'Erro ao enviar mensagem: {e}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/groups/<int:group_id>/members/remove', methods=['DELETE'])
@login_required
def remove_group_member(group_id):
    """Remover membro do grupo"""
    conn = None
    cur = None
    try:
        data = request.get_json()
        member_pubkey = data.get('pubkey', '').strip()

        if not member_pubkey:
            return jsonify({'status': 'error', 'error': 'pubkey obrigatório'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se é admin ou moderador
        cur.execute("""
            SELECT role FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, session['pubkey']))

        member = cur.fetchone()
        if not member or member['role'] not in ['admin', 'moderator']:
            return jsonify({'status': 'error', 'error': 'Apenas admins e moderadores podem remover membros'}), 403

        # Não permitir remover o próprio admin
        if member_pubkey == session['pubkey']:
            return jsonify({'status': 'error', 'error': 'Você não pode se remover do grupo'}), 400

        # Verificar se o membro a ser removido é admin
        cur.execute("""
            SELECT role FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, member_pubkey))

        target_member = cur.fetchone()
        if target_member and target_member['role'] == 'admin':
            return jsonify({'status': 'error', 'error': 'Não é possível remover outro admin'}), 403

        # Remover membro
        cur.execute("""
            DELETE FROM group_members
            WHERE group_id = %s AND user_pubkey = %s
        """, (group_id, member_pubkey))

        conn.commit()

        if cur.rowcount == 0:
            return jsonify({'status': 'error', 'error': 'Membro não encontrado no grupo'}), 404

        print(f'Membro {member_pubkey} removido do grupo {group_id}')

        # TODO: Publicar remoção no Nostr (NIP-29)

        return jsonify({'status': 'ok'})

    except Exception as e:
        print(f'Erro ao remover membro: {e}')
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ==================== NIP-05 ENDPOINTS ====================

@app.route('/.well-known/nostr.json', methods=['GET'])
def nostr_json():
    """NIP-05: Retorna mapeamento de usernames para pubkeys"""
    name = request.args.get('name')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if name:
            # Buscar username específico
            cur.execute("""
                SELECT username, pubkey
                FROM nip05_verifications
                WHERE username = %s AND verified = TRUE
            """, (name,))
            result = cur.fetchone()

            if result:
                return jsonify({
                    'names': {
                        result['username']: result['pubkey']
                    }
                })
            else:
                return jsonify({'names': {}}), 404
        else:
            # Retornar todos os verificados
            cur.execute("""
                SELECT username, pubkey
                FROM nip05_verifications
                WHERE verified = TRUE
                ORDER BY username
            """)
            results = cur.fetchall()

            names = {r['username']: r['pubkey'] for r in results}

            return jsonify({'names': names})

    except Exception as e:
        print(f'Erro no NIP-05: {e}')
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/nip05/check', methods=['GET'])
def nip05_check():
    """Verificar se um username está disponível"""
    username = request.args.get('username', '').lower().strip()

    if not username:
        return jsonify({'error': 'Username requerido'}), 400

    # Validar formato (apenas letras minúsculas, números, hífen e underscore)
    import re
    if not re.match(r'^[a-z0-9_-]{3,50}$', username):
        return jsonify({
            'available': False,
            'error': 'Username inválido. Use apenas letras minúsculas, números, hífen e underscore (3-50 caracteres)'
        }), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id FROM nip05_verifications
            WHERE username = %s
        """, (username,))

        exists = cur.fetchone() is not None

        return jsonify({
            'available': not exists,
            'username': username
        })

    except Exception as e:
        print(f'Erro ao verificar NIP-05: {e}')
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/nip05/request', methods=['POST'])
@login_required
def nip05_request():
    """Solicitar verificação NIP-05"""
    data = request.json
    username = data.get('username', '').lower().strip()

    if not username:
        return jsonify({'error': 'Username requerido'}), 400

    # Validar formato
    import re
    if not re.match(r'^[a-z0-9_-]{3,50}$', username):
        return jsonify({
            'error': 'Username inválido. Use apenas letras minúsculas, números, hífen e underscore (3-50 caracteres)'
        }), 400

    pubkey = session.get('pubkey')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar se username já existe
        cur.execute("""
            SELECT id FROM nip05_verifications
            WHERE username = %s
        """, (username,))

        if cur.fetchone():
            return jsonify({'error': 'Username já está em uso'}), 409

        # Verificar se usuário já tem verificação
        cur.execute("""
            SELECT id FROM nip05_verifications
            WHERE pubkey = %s
        """, (pubkey,))

        if cur.fetchone():
            return jsonify({'error': 'Você já possui uma verificação NIP-05'}), 409

        # Criar ou obter user_id
        cur.execute("""
            INSERT INTO users (pubkey, npub)
            VALUES (%s, %s)
            ON CONFLICT (pubkey) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (pubkey, session.get('npub')))

        user_id = cur.fetchone()['id']

        # Criar solicitação (já verificada automaticamente por enquanto)
        cur.execute("""
            INSERT INTO nip05_verifications (user_id, pubkey, username, verified, verified_at)
            VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
            RETURNING id, username, domain
        """, (user_id, pubkey, username))

        result = cur.fetchone()
        conn.commit()

        # Atualizar campo nip05 na tabela users
        nip05_identifier = f"{result['username']}@{result['domain']}"
        cur.execute("""
            UPDATE users
            SET nip05 = %s
            WHERE id = %s
        """, (nip05_identifier, user_id))
        conn.commit()

        return jsonify({
            'success': True,
            'username': result['username'],
            'domain': result['domain'],
            'nip05': nip05_identifier
        })

    except Exception as e:
        print(f'Erro ao criar NIP-05: {e}')
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/nip05/status', methods=['GET'])
@login_required
def nip05_status():
    """Verificar status da verificação NIP-05 do usuário"""
    pubkey = session.get('pubkey')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT username, domain, verified, verified_at
            FROM nip05_verifications
            WHERE pubkey = %s
        """, (pubkey,))

        result = cur.fetchone()

        if result:
            return jsonify({
                'has_nip05': True,
                'username': result['username'],
                'domain': result['domain'],
                'verified': result['verified'],
                'nip05': f"{result['username']}@{result['domain']}",
                'verified_at': result['verified_at'].isoformat() if result['verified_at'] else None
            })
        else:
            return jsonify({
                'has_nip05': False
            })

    except Exception as e:
        print(f'Erro ao verificar status NIP-05: {e}')
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ==================== DONATION ENDPOINTS ====================

@app.route('/api/donate/create-invoice', methods=['POST'])
@login_required
def create_donation_invoice():
    """Criar invoice Lightning para doação"""
    try:
        data = request.get_json()
        amount_key = data.get('amount_key')  # '5k', '10k', etc
        amount_sats = data.get('amount_sats')  # Ou valor livre

        if amount_key:
            # Valor pré-definido
            invoice_data = payment_integration.create_donation_invoice(amount_key)
        elif amount_sats:
            # Valor livre
            invoice_data = payment_integration.create_custom_donation_invoice(int(amount_sats))
        else:
            return jsonify({'status': 'error', 'error': 'amount_key ou amount_sats requerido'}), 400

        if not invoice_data:
            return jsonify({'status': 'error', 'error': 'Erro ao criar invoice'}), 500

        # Salvar invoice no banco para tracking
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            amount = payment_integration.DONATION_AMOUNTS.get(amount_key, amount_sats)

            cur.execute("""
                INSERT INTO donations (
                    user_pubkey,
                    amount_sats,
                    payment_hash,
                    bolt11,
                    status
                )
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
            """, (
                session.get('pubkey'),
                amount,
                invoice_data['payment_hash'],
                invoice_data['bolt11']
            ))

            donation_id = cur.fetchone()['id']
            conn.commit()

            print(f'[DONATION] Invoice criado - ID: {donation_id}, Amount: {amount} sats')

        except Exception as e:
            print(f'[DONATION] Erro ao salvar no banco: {e}')
            # Não falhar se der erro no banco, invoice já foi criado
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        return jsonify({
            'status': 'ok',
            'invoice': invoice_data
        })

    except Exception as e:
        print(f'[DONATION] Erro ao criar invoice: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/donate/check-payment/<charge_id>', methods=['GET'])
@login_required
def check_donation_payment(charge_id):
    """Verificar se pagamento foi realizado"""
    try:
        payment_status = payment_integration.opennode.check_invoice(charge_id)

        if not payment_status:
            return jsonify({'status': 'error', 'error': 'Erro ao verificar pagamento'}), 500

        # Se pago, atualizar no banco
        if payment_status['paid']:
            try:
                conn = get_db_connection()
                cur = conn.cursor()

                cur.execute("""
                    UPDATE donations
                    SET status = 'paid',
                        paid_at = CURRENT_TIMESTAMP
                    WHERE payment_hash = %s
                    RETURNING user_pubkey, amount_sats
                """, (charge_id,))

                result = cur.fetchone()
                conn.commit()

                if result:
                    print(f'[DONATION] ✅ Pagamento confirmado - {result["amount_sats"]} sats de {result["user_pubkey"][:16]}...')

            except Exception as e:
                print(f'[DONATION] Erro ao atualizar status: {e}')
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

        return jsonify({
            'status': 'ok',
            'paid': payment_status['paid'],
            'payment_status': payment_status['status']
        })

    except Exception as e:
        print(f'[DONATION] Erro ao verificar pagamento: {e}')
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/donate/hall-of-fame', methods=['GET'])
def get_hall_of_fame():
    """Listar maiores doadores"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Buscar top 10 doadores (agregado por pubkey)
        cur.execute("""
            SELECT
                d.user_pubkey,
                u.display_name,
                u.nip05,
                u.picture_url,
                SUM(d.amount_sats) as total_donated,
                MIN(d.created_at) as first_donation,
                COUNT(d.id) as donation_count
            FROM donations d
            LEFT JOIN users u ON u.pubkey = d.user_pubkey
            WHERE d.status = 'paid'
            GROUP BY d.user_pubkey, u.display_name, u.nip05, u.picture_url
            ORDER BY total_donated DESC
            LIMIT 10
        """)

        donors = cur.fetchall()

        donors_list = []
        for idx, donor in enumerate(donors, 1):
            # Formatar npub
            try:
                from nostr_sdk import PublicKey
                pk = PublicKey.from_hex(donor['user_pubkey'])
                npub = pk.to_bech32()
            except:
                npub = donor['user_pubkey'][:12] + '...'

            donors_list.append({
                'rank': idx,
                'pubkey': donor['user_pubkey'],
                'npub': npub,
                'name': donor['display_name'] or 'Anônimo',
                'nip05': donor['nip05'],
                'picture': donor['picture_url'],
                'total_donated': donor['total_donated'],
                'first_donation': donor['first_donation'].isoformat() if donor['first_donation'] else None,
                'donation_count': donor['donation_count']
            })

        return jsonify({
            'status': 'ok',
            'donors': donors_list
        })

    except Exception as e:
        print(f'[DONATION] Erro ao buscar hall da fama: {e}')
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/webhook/opennode', methods=['POST'])
def opennode_webhook():
    """Webhook para receber notificações de pagamento do OpenNode"""
    try:
        data = request.get_json()
        print(f'[OPENNODE WEBHOOK] Recebido: {data}')

        # OpenNode envia: {id, status, amount, etc}
        charge_id = data.get('id')
        status = data.get('status')

        if status == 'paid':
            # Atualizar no banco
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE donations
                SET status = 'paid',
                    paid_at = CURRENT_TIMESTAMP
                WHERE payment_hash = %s
                RETURNING user_pubkey, amount_sats
            """, (charge_id,))

            result = cur.fetchone()
            conn.commit()

            if result:
                print(f'[WEBHOOK] ✅ Doação confirmada via webhook - {result["amount_sats"]} sats')

            cur.close()
            conn.close()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        print(f'[WEBHOOK] Erro: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error'}), 500


# ==================== NOSTR PROFILE ====================

async def buscar_perfil_nostr_async(npub: str):
    """Busca perfil (kind 0) de um npub nos relays"""
    try:
        decoded = Nip19.from_bech32(npub)
        pubkey = decoded.as_enum().npub

        client = Client()
        await client.add_relay("wss://relay.damus.io")
        await client.add_relay("wss://nos.lol")
        await client.add_relay("wss://relay.nostr.band")

        await client.connect()

        filter_obj = Filter().kind(Kind(0)).author(pubkey).limit(1)
        events = await client.fetch_events([filter_obj], timeout=timedelta(seconds=10))

        if not events.is_empty():
            event = events.first()
            content = json.loads(event.content())

            return {
                "name": content.get("name", ""),
                "display_name": content.get("display_name", ""),
                "picture": content.get("picture", ""),
                "about": content.get("about", ""),
                "banner": content.get("banner", ""),
                "website": content.get("website", ""),
                "nip05": content.get("nip05", ""),
                "lud16": content.get("lud16", "")
            }

        return None
    except Exception as e:
        print(f'Erro ao buscar perfil: {e}')
        return None
    finally:
        try:
            await client.disconnect()
        except:
            pass

def buscar_perfil_nostr(npub: str):
    """Wrapper síncrono para buscar perfil"""
    return asyncio.run(buscar_perfil_nostr_async(npub))


# ==================== NIP-29: GROUPS ====================

async def publicar_grupo_nostr_async(group_id: str, name: str, description: str, picture_url: str, admin_pubkey: str, private: bool):
    """Publica metadados de grupo no Nostr (NIP-29 kind 39000)"""
    try:
        from nostr_sdk import Keys, EventBuilder, Tag

        # TODO: Usar as chaves do admin do grupo
        # Por enquanto, apenas logamos que seria publicado
        print(f'[NIP-29] Publicaria grupo no Nostr:')
        print(f'  - ID: {group_id}')
        print(f'  - Nome: {name}')
        print(f'  - Admin: {admin_pubkey}')
        print(f'  - Privado: {private}')

        # Estrutura do evento NIP-29:
        # kind: 39000 (Group Metadata)
        # tags:
        #   - ["d", group_id] - identificador único do grupo
        #   - ["name", name] - nome do grupo
        #   - ["about", description] - descrição
        #   - ["picture", picture_url] - imagem
        #   - ["public"] ou ["private"] - tipo de grupo

        return True
    except Exception as e:
        print(f'[NIP-29] Erro ao publicar grupo: {e}')
        return False

async def publicar_mensagem_grupo_nostr_async(group_id: str, content: str, sender_pubkey: str):
    """Publica mensagem de grupo no Nostr (NIP-29 kind 9)"""
    try:
        print(f'[NIP-29] Publicaria mensagem no grupo {group_id}')
        print(f'  - De: {sender_pubkey}')
        print(f'  - Conteúdo: {content[:50]}...')

        # Estrutura do evento NIP-29:
        # kind: 9 (Group Chat Message)
        # tags:
        #   - ["h", group_id] - identificador do grupo
        # content: mensagem em texto claro (grupos públicos) ou criptografada (grupos privados)

        return True
    except Exception as e:
        print(f'[NIP-29] Erro ao publicar mensagem: {e}')
        return False

async def adicionar_membro_grupo_nostr_async(group_id: str, member_pubkey: str, role: str):
    """Adiciona membro ao grupo no Nostr (NIP-29 kind 9000)"""
    try:
        print(f'[NIP-29] Adicionaria membro ao grupo {group_id}')
        print(f'  - Membro: {member_pubkey}')
        print(f'  - Role: {role}')

        # Estrutura do evento NIP-29:
        # kind: 9000 (Group Admin - Add User)
        # tags:
        #   - ["h", group_id]
        #   - ["p", member_pubkey]
        #   - ["role", role] - admin, moderator, ou member

        return True
    except Exception as e:
        print(f'[NIP-29] Erro ao adicionar membro: {e}')
        return False

def publicar_grupo_nostr(group_id: str, name: str, description: str, picture_url: str, admin_pubkey: str, private: bool):
    """Wrapper síncrono para publicar grupo"""
    return asyncio.run(publicar_grupo_nostr_async(group_id, name, description, picture_url, admin_pubkey, private))

def publicar_mensagem_grupo_nostr(group_id: str, content: str, sender_pubkey: str):
    """Wrapper síncrono para publicar mensagem"""
    return asyncio.run(publicar_mensagem_grupo_nostr_async(group_id, content, sender_pubkey))

def adicionar_membro_grupo_nostr(group_id: str, member_pubkey: str, role: str):
    """Wrapper síncrono para adicionar membro"""
    return asyncio.run(adicionar_membro_grupo_nostr_async(group_id, member_pubkey, role))


@app.route('/api/user/badge', methods=['GET'])
def get_user_badge():
    """Retorna o badge/selo do usuário"""
    pubkey = request.args.get('pubkey')

    if not pubkey:
        return jsonify({'status': 'error', 'error': 'pubkey requerido'}), 400

    try:
        # Pubkeys de administradores
        admin_pubkeys = [
            '9fbd8e0100663ed095590c14b5ba1ebb32704b7b4718dfac9f4e7f5b2c7b1c9a',  # Barak
            # Adicionar pubkey da Sofia se necessário
        ]

        # Verificar se é admin
        if pubkey in admin_pubkeys:
            return jsonify({'status': 'ok', 'badge': 'admin'})

        # Verificar se tem doações (badge pago)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT SUM(amount_sats) as total
            FROM donations
            WHERE user_pubkey = %s AND status = 'paid'
        """, (pubkey,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result['total'] and result['total'] >= 1000:
            return jsonify({'status': 'ok', 'badge': 'paid'})

        # Badge padrão
        return jsonify({'status': 'ok', 'badge': 'free'})

    except Exception as e:
        print(f'[BADGE] Erro ao verificar badge: {e}')
        return jsonify({'status': 'ok', 'badge': 'free'})


@app.route('/api/nostr/profile', methods=['POST'])
def api_nostr_profile():
    """API para buscar perfil Nostr (kind 0)"""
    try:
        data = request.get_json()
        npub = data.get('npub')
        pubkey_hex = data.get('pubkey')

        # Se foi fornecida a pubkey (hex), converter para npub
        if pubkey_hex and not npub:
            try:
                from nostr_sdk import PublicKey
                contact_pk = PublicKey.from_hex(pubkey_hex)
                npub = contact_pk.to_bech32()
                print(f'[DEBUG] Convertido pubkey {pubkey_hex} para npub: {npub}')
            except Exception as e:
                print(f'[DEBUG] Erro ao converter pubkey: {e}')
                return jsonify({'status': 'error', 'error': 'pubkey inválida'}), 400

        print(f'[DEBUG] Buscando perfil para npub: {npub}')

        if not npub:
            return jsonify({'status': 'error', 'error': 'npub ou pubkey obrigatório'}), 400

        # Se não temos pubkey_hex, extrair do npub
        if not pubkey_hex:
            try:
                from nostr_sdk import PublicKey
                decoded = Nip19.from_bech32(npub)
                pubkey_obj = decoded.as_enum().npub
                pubkey_hex = pubkey_obj.to_hex()
                print(f'[DEBUG] Extraída pubkey do npub: {pubkey_hex}')
            except Exception as e:
                print(f'[DEBUG] Erro ao extrair pubkey do npub: {e}')
                return jsonify({'status': 'error', 'error': 'npub inválido'}), 400

        perfil = buscar_perfil_nostr(npub)

        print(f'[DEBUG] Perfil encontrado: {perfil}')

        if perfil:
            # Sempre retornar a pubkey
            response_data = {
                'status': 'ok',
                'perfil': perfil,
                'pubkey': pubkey_hex
            }
            return jsonify(response_data)
        else:
            return jsonify({'status': 'error', 'error': 'Perfil não encontrado'}), 404

    except Exception as e:
        print(f'[ERROR] Erro ao buscar perfil: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== UPLOAD DE ARQUIVOS ====================

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload de arquivo para servidor de mídia configurado"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'error': 'Arquivo inválido'}), 400

        # Pegar npub do usuário logado
        user_pubkey = session.get('pubkey')
        from nostr_sdk import PublicKey
        try:
            pk = PublicKey.from_hex(user_pubkey)
            npub = pk.to_bech32()
        except:
            return jsonify({'status': 'error', 'error': 'Usuário não autenticado'}), 401

        # Ler servidor configurado do request
        media_server = request.form.get('server_url', 'https://media.libernet.app')
        server_protocol = request.form.get('server_protocol', 'nip96')

        print(f'[UPLOAD] Servidor: {media_server} | Protocolo: {server_protocol}')

        # Preparar upload baseado no protocolo
        import requests

        # Resetar stream do arquivo para poder reler
        file.stream.seek(0)

        if server_protocol == 'libermedia':
            # LiberMedia - endpoint customizado
            files = {'file': (file.filename, file.stream, file.content_type)}
            data = {'npub': npub, 'pasta': 'LiberChat'}
            upload_endpoint = f'{media_server}/api/upload'

            response = requests.post(upload_endpoint, files=files, data=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'ok':
                    arquivo = result.get('arquivo', {})
                    arquivo_id = arquivo.get('id')

                    # LiberMedia usa /f/{id} que redireciona para arquivo com extensão correta
                    file_url = f"{media_server}/f/{arquivo_id}"

                    return jsonify({
                        'status': 'ok',
                        'url': file_url,
                        'filename': arquivo.get('nome', file.filename),
                        'type': arquivo.get('tipo', 'unknown'),
                        'size': arquivo.get('tamanho', 0)
                    })
                else:
                    return jsonify({'status': 'error', 'error': result.get('error', 'Erro no upload')}), 500
            else:
                return jsonify({'status': 'error', 'error': f'Erro no servidor: {response.status_code}'}), 500

        elif server_protocol == 'nip96':
            # NIP-96 padrão
            files = {'file': (file.filename, file.stream, file.content_type)}
            data = {'pubkey': npub}
            upload_endpoint = f'{media_server}/api/upload/nip96'

            response = requests.post(upload_endpoint, files=files, data=data, timeout=30)

            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                # NIP-96 retorna url diretamente
                file_url = result.get('url') or result.get('download_url')

                return jsonify({
                    'status': 'ok',
                    'url': file_url,
                    'filename': result.get('name', file.filename),
                    'type': result.get('type', 'unknown'),
                    'size': result.get('size', 0)
                })
            else:
                return jsonify({'status': 'error', 'error': f'Erro no servidor: {response.status_code}'}), 500

        elif server_protocol == 'blossom':
            # Protocolo Blossom - requer PUT com binary data e auth Nostr
            # Por enquanto, vamos usar o protocolo libermedia padrão como fallback
            # TODO: Implementar autenticação Blossom correta (kind 24242)
            files = {'file': (file.filename, file.stream, file.content_type)}
            data = {'npub': npub, 'pasta': 'LiberChat'}
            upload_endpoint = f'{media_server}/api/upload'

            response = requests.post(upload_endpoint, files=files, data=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'ok':
                    arquivo = result.get('arquivo', {})
                    arquivo_id = arquivo.get('id')
                    file_url = f"{media_server}/f/{arquivo_id}"

                    return jsonify({
                        'status': 'ok',
                        'url': file_url,
                        'filename': arquivo.get('nome', file.filename),
                        'type': arquivo.get('tipo', 'unknown'),
                        'size': arquivo.get('tamanho', 0)
                    })
                else:
                    return jsonify({'status': 'error', 'error': result.get('error', 'Erro no upload')}), 500
            else:
                return jsonify({'status': 'error', 'error': f'Erro no servidor: {response.status_code}'}), 500
        else:
            return jsonify({'status': 'error', 'error': 'Protocolo não suportado'}), 400

    except Exception as e:
        print(f'[ERROR] Erro ao fazer upload: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==================== HEALTH CHECK ====================

@app.route('/health')
def health():
    """Health check para monitoramento"""
    try:
        # Testar conexão com DB
        conn = get_db_connection()
        conn.close()

        # Testar conexão com Redis
        r = get_redis_connection()
        r.ping()

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'redis': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Página não encontrada"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Erro interno do servidor"""
    return render_template('500.html'), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG
    )
