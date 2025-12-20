#!/usr/bin/env python3
"""
Script para criar NIP-05 para o Oleg
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from nostr_sdk import PublicKey, Nip19

load_dotenv()

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'liberchat'),
    'user': os.getenv('DB_USER', 'liberchat'),
    'password': os.getenv('DB_PASSWORD', ''),
}

OLEG_NPUB = 'npub1r9sayj4d4vz8dxjnef68wraqkf37w04ypuuat5rcrvx40zc35f7stwgr57'
OLEG_USERNAME = 'oleg'

def main():
    print("=" * 60)
    print("  Criando NIP-05 para Oleg")
    print("=" * 60)
    print()

    # Converter npub para pubkey hex
    try:
        decoded = Nip19.from_bech32(OLEG_NPUB)
        pubkey_obj = decoded.as_enum().npub
        oleg_pubkey = pubkey_obj.to_hex()
        print(f"Npub: {OLEG_NPUB}")
        print(f"Pubkey: {oleg_pubkey}")
        print()
    except Exception as e:
        print(f"❌ Erro ao converter npub: {e}")
        return

    # Conectar ao banco
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cur = conn.cursor()

        # Verificar se já existe user com essa pubkey
        cur.execute("SELECT id FROM users WHERE pubkey = %s", (oleg_pubkey,))
        user = cur.fetchone()

        if user:
            user_id = user['id']
            print(f"✅ Usuário encontrado (ID: {user_id})")
        else:
            # Criar usuário
            print("Criando usuário no banco...")
            cur.execute("""
                INSERT INTO users (pubkey, npub, last_seen)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (oleg_pubkey, OLEG_NPUB))
            user_id = cur.fetchone()['id']
            print(f"✅ Usuário criado (ID: {user_id})")

        conn.commit()

        # Verificar se NIP-05 já existe
        cur.execute("SELECT id FROM nip05_verifications WHERE username = %s", (OLEG_USERNAME,))
        existing = cur.fetchone()

        if existing:
            print(f"⚠️  NIP-05 '{OLEG_USERNAME}@libernet.app' já existe!")
            print("Atualizando registro...")
            cur.execute("""
                UPDATE nip05_verifications
                SET pubkey = %s, user_id = %s, verified = TRUE, verified_at = CURRENT_TIMESTAMP
                WHERE username = %s
                RETURNING id
            """, (oleg_pubkey, user_id, OLEG_USERNAME))
        else:
            print(f"Criando NIP-05 '{OLEG_USERNAME}@libernet.app'...")
            cur.execute("""
                INSERT INTO nip05_verifications (user_id, pubkey, username, verified, verified_at)
                VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                RETURNING id
            """, (user_id, oleg_pubkey, OLEG_USERNAME))

        nip05_id = cur.fetchone()['id']
        print(f"✅ NIP-05 criado/atualizado (ID: {nip05_id})")

        # Atualizar campo nip05 na tabela users
        cur.execute("""
            UPDATE users
            SET nip05 = %s
            WHERE id = %s
        """, (f'{OLEG_USERNAME}@libernet.app', user_id))

        conn.commit()
        print(f"✅ Campo nip05 atualizado no usuário")

        # Verificar resultado
        cur.execute("""
            SELECT username, domain, pubkey, verified
            FROM nip05_verifications
            WHERE username = %s
        """, (OLEG_USERNAME,))

        result = cur.fetchone()
        print()
        print("Dados salvos:")
        print(f"   NIP-05: {result['username']}@{result['domain']}")
        print(f"   Pubkey: {result['pubkey']}")
        print(f"   Verificado: {'✅ Sim' if result['verified'] else '❌ Não'}")

        cur.close()
        conn.close()

        print()
        print("=" * 60)
        print("  ✅ NIP-05 criado com sucesso!")
        print("=" * 60)
        print()
        print(f"Teste em: https://chat.libernet.app/.well-known/nostr.json?name={OLEG_USERNAME}")

    except Exception as e:
        print(f"❌ Erro ao criar NIP-05: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
