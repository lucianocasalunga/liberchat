#!/usr/bin/env python3
"""
Buscar perfil do Oleg em múltiplos relays
"""

import asyncio
from nostr_sdk import Client, Filter, Kind, PublicKey, Nip19
from datetime import timedelta
import json

OLEG_NPUB = 'npub1r9sayj4d4vz8dxjnef68wraqkf37w04ypuuat5rcrvx40zc35f7stwgr57'

async def find_profile():
    try:
        # Converter npub
        decoded = Nip19.from_bech32(OLEG_NPUB)
        pubkey_obj = decoded.as_enum().npub
        pubkey_hex = pubkey_obj.to_hex()

        print("=" * 70)
        print("  Buscando perfil do Oleg em múltiplos relays")
        print("=" * 70)
        print(f"\nNpub: {OLEG_NPUB}")
        print(f"Pubkey: {pubkey_hex}")
        print()

        client = Client()

        # Lista expandida de relays
        relays = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.nostr.band",
            "wss://relay.libernet.app",
            "wss://nostr.wine",
            "wss://relay.snort.social",
            "wss://relay.current.fyi",
            "wss://nostr.mom",
            "wss://relay.primal.net",
            "wss://purplepag.es",
            "wss://relay.nostr.bg",
            "wss://offchain.pub"
        ]

        print("Adicionando relays:")
        for relay in relays:
            await client.add_relay(relay)
            print(f"  + {relay}")

        print("\nConectando...")
        await client.connect()
        await asyncio.sleep(2)  # Dar tempo para conectar

        print("\nBuscando perfil (kind 0)...")
        filter_obj = Filter().kind(Kind(0)).author(pubkey_obj).limit(10)
        events = await client.fetch_events([filter_obj], timeout=timedelta(seconds=15))

        if not events.is_empty():
            print(f"\n✅ Encontrado {len(events)} evento(s) de perfil!")
            print()

            # Pegar o mais recente
            event = events.first()
            content = json.loads(event.content())

            print("Dados do perfil:")
            print(f"  Nome: {content.get('name', 'N/A')}")
            print(f"  Display Name: {content.get('display_name', 'N/A')}")
            print(f"  NIP-05: {content.get('nip05', 'N/A')}")
            print(f"  Picture: {content.get('picture', 'N/A')}")
            print(f"  About: {content.get('about', 'N/A')}")
            print(f"  Banner: {content.get('banner', 'N/A')}")
            print(f"  Website: {content.get('website', 'N/A')}")
            print(f"  LUD16: {content.get('lud16', 'N/A')}")
            print()
            print(f"Event ID: {event.id().to_hex()}")
            print(f"Created at: {event.created_at().as_secs()}")

            # Salvar no banco
            print("\n" + "=" * 70)
            print("Salvando perfil no LiberChat...")
            import psycopg2
            from psycopg2.extras import RealDictCursor
            import os
            from dotenv import load_dotenv

            load_dotenv()

            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', 5432),
                database=os.getenv('DB_NAME', 'liberchat'),
                user=os.getenv('DB_USER', 'liberchat'),
                password=os.getenv('DB_PASSWORD', ''),
                cursor_factory=RealDictCursor
            )
            cur = conn.cursor()

            cur.execute("""
                UPDATE users
                SET display_name = %s,
                    picture_url = %s,
                    nip05 = %s,
                    about = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE pubkey = %s
            """, (
                content.get('display_name') or content.get('name'),
                content.get('picture'),
                content.get('nip05'),
                content.get('about'),
                pubkey_hex
            ))

            conn.commit()
            cur.close()
            conn.close()

            print("✅ Perfil salvo no banco de dados do LiberChat!")
            print("=" * 70)

            return True
        else:
            print("\n❌ Nenhum perfil encontrado em nenhum relay!")
            print("\nVerifique se:")
            print("  1. O npub está correto")
            print("  2. O perfil foi realmente publicado")
            print("  3. Os relays estão acessíveis")
            return False

    except Exception as e:
        print(f'\n❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == '__main__':
    asyncio.run(find_profile())
