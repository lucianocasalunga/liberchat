#!/usr/bin/env python3
import sys
import os

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from nostr_sdk import PublicKey
    import psycopg2
    from config import Config

    npub = 'npub1uvksan4sr32e3tdxul7dmugc8ujz5yz0e7rwm3waj2znm27mjmqquvvsfn'

    # Converter para hex
    pk = PublicKey.from_bech32(npub)
    hex_key = pk.to_hex()

    print(f'[INFO] npub: {npub}')
    print(f'[INFO] hex: {hex_key}')

    # Conectar ao banco
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
    cur = conn.cursor()

    # Verificar se já existe
    cur.execute("SELECT pubkey FROM blacklist WHERE pubkey = %s", (hex_key,))
    existing = cur.fetchone()

    if existing:
        print(f'[AVISO] Pubkey já está na blacklist')
    else:
        # Adicionar à blacklist
        cur.execute("""
            INSERT INTO blacklist (pubkey, reason, created_at)
            VALUES (%s, %s, NOW())
        """, (hex_key, 'Adicionado manualmente'))
        conn.commit()
        print(f'[SUCESSO] Pubkey adicionado à blacklist')

    cur.close()
    conn.close()

except ImportError as e:
    print(f'[ERRO] Módulo não encontrado: {e}')
    sys.exit(1)
except Exception as e:
    print(f'[ERRO] {e}')
    sys.exit(1)
