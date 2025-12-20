#!/usr/bin/env python3
"""
Script para buscar e atualizar o perfil da Sofia no banco de dados
"""

import os
import sys
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from nostr_sdk import Client, Filter, Kind, PublicKey, Nip19
from datetime import timedelta
import json

load_dotenv()

# Configuração do banco
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
    'database': os.getenv('DB_NAME', 'liberchat'),
    'user': os.getenv('DB_USER', 'liberchat'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Pubkey da Sofia
SOFIA_PUBKEY = '555db8757455d25088b6dfe27aaa9f2b5d3330fec0c10fd7e8f00caf9f6b3c01'

async def buscar_perfil_nostr(npub: str):
    """Busca perfil (kind 0) de um npub nos relays"""
    try:
        decoded = Nip19.from_bech32(npub)
        pubkey = decoded.as_enum().npub

        client = Client()
        await client.add_relay("wss://relay.damus.io")
        await client.add_relay("wss://nos.lol")
        await client.add_relay("wss://relay.nostr.band")
        await client.add_relay("wss://relay.libernet.app")

        print(f"Conectando aos relays...")
        await client.connect()

        print(f"Buscando perfil no Nostr...")
        filter_obj = Filter().kind(Kind(0)).author(pubkey).limit(1)
        events = await client.fetch_events([filter_obj], timeout=timedelta(seconds=10))

        if not events.is_empty():
            event = events.first()
            content = json.loads(event.content())

            print(f"✅ Perfil encontrado!")
            print(f"   Nome: {content.get('name', 'N/A')}")
            print(f"   Display Name: {content.get('display_name', 'N/A')}")
            print(f"   NIP-05: {content.get('nip05', 'N/A')}")
            print(f"   Picture: {content.get('picture', 'N/A')}")

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

        print("❌ Perfil não encontrado")
        return None
    except Exception as e:
        print(f'❌ Erro ao buscar perfil: {e}')
        import traceback
        traceback.print_exc()
        return None
    finally:
        try:
            await client.disconnect()
        except:
            pass

async def main():
    print("=" * 60)
    print("  Atualizando perfil da Sofia no LiberChat")
    print("=" * 60)
    print()

    # Converter pubkey para npub
    try:
        sofia_pk = PublicKey.from_hex(SOFIA_PUBKEY)
        sofia_npub = sofia_pk.to_bech32()
        print(f"Pubkey: {SOFIA_PUBKEY}")
        print(f"Npub: {sofia_npub}")
        print()
    except Exception as e:
        print(f"❌ Erro ao converter pubkey: {e}")
        return

    # Buscar perfil
    perfil = await buscar_perfil_nostr(sofia_npub)

    if not perfil:
        print()
        print("❌ Não foi possível encontrar o perfil da Sofia nos relays")
        return

    # Atualizar banco de dados
    print()
    print("Atualizando banco de dados...")

    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
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
            SOFIA_PUBKEY,
            sofia_npub,
            perfil.get('display_name') or perfil.get('name'),
            perfil.get('picture'),
            perfil.get('nip05'),
            perfil.get('about')
        ))

        conn.commit()
        print("✅ Perfil atualizado no banco de dados!")

        # Verificar resultado
        cur.execute("""
            SELECT display_name, picture_url, nip05
            FROM users
            WHERE pubkey = %s
        """, (SOFIA_PUBKEY,))

        result = cur.fetchone()
        print()
        print("Dados salvos no banco:")
        print(f"   Nome: {result['display_name']}")
        print(f"   NIP-05: {result['nip05']}")
        print(f"   Foto: {result['picture_url'][:50]}..." if result['picture_url'] else "   Foto: N/A")

        cur.close()
        conn.close()

        print()
        print("=" * 60)
        print("  ✅ Processo concluído com sucesso!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
