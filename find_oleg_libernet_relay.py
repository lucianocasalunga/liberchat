#!/usr/bin/env python3
"""
Buscar perfil do Oleg especificamente no relay.libernet.app
"""

import asyncio
from nostr_sdk import Client, Filter, Kind, PublicKey, Nip19, RelayMetadata
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
        print("  Buscando perfil do Oleg no relay.libernet.app")
        print("=" * 70)
        print(f"\nNpub: {OLEG_NPUB}")
        print(f"Pubkey: {pubkey_hex}")
        print()

        client = Client()

        # Adicionar APENAS o relay da libernet
        relay_url = "wss://relay.libernet.app"
        print(f"Conectando ao relay: {relay_url}")
        await client.add_relay(relay_url)
        await client.connect()

        # Dar mais tempo para conexão
        print("Aguardando conexão...")
        await asyncio.sleep(3)

        print("\nBuscando perfil (kind 0)...")
        filter_obj = Filter().kind(Kind(0)).author(pubkey_obj)

        # Timeout maior
        events = await client.fetch_events([filter_obj], timeout=timedelta(seconds=20))

        if not events.is_empty():
            print(f"\n✅ Encontrado {len(events)} evento(s) de perfil!")
            print()

            # Pegar o mais recente
            event = events.first()
            content = json.loads(event.content())

            print("=" * 70)
            print("DADOS DO PERFIL DO OLEG:")
            print("=" * 70)
            print(f"Nome: {content.get('name', 'N/A')}")
            print(f"Display Name: {content.get('display_name', 'N/A')}")
            print(f"NIP-05: {content.get('nip05', 'N/A')}")
            print(f"Picture: {content.get('picture', 'N/A')}")
            print(f"About: {content.get('about', 'N/A')}")
            print(f"Banner: {content.get('banner', 'N/A')}")
            print(f"Website: {content.get('website', 'N/A')}")
            print(f"LUD16: {content.get('lud16', 'N/A')}")
            print("=" * 70)
            print()

            # Salvar no banco
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

            # Atualizar ou inserir
            cur.execute("""
                INSERT INTO users (pubkey, npub, display_name, picture_url, nip05, about, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (pubkey)
                DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    picture_url = EXCLUDED.picture_url,
                    nip05 = COALESCE(EXCLUDED.nip05, users.nip05),
                    about = EXCLUDED.about,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                pubkey_hex,
                OLEG_NPUB,
                content.get('display_name') or content.get('name'),
                content.get('picture'),
                content.get('nip05'),
                content.get('about')
            ))

            user_id = cur.fetchone()['id']
            conn.commit()

            print(f"✅ Perfil salvo no banco (User ID: {user_id})!")
            print()

            # Verificar dados salvos
            cur.execute("""
                SELECT display_name, picture_url, nip05
                FROM users
                WHERE pubkey = %s
            """, (pubkey_hex,))

            saved = cur.fetchone()
            print("Dados salvos no banco:")
            print(f"  Nome: {saved['display_name']}")
            print(f"  Foto: {saved['picture_url']}")
            print(f"  NIP-05: {saved['nip05']}")

            cur.close()
            conn.close()

            print()
            print("=" * 70)
            print("✅ SUCESSO! Agora você pode adicionar o Oleg como contato!")
            print("=" * 70)

            return True
        else:
            print("\n❌ Perfil não encontrado no relay.libernet.app!")
            print("\nPossíveis problemas:")
            print("  1. O relay pode estar offline ou inacessível")
            print("  2. O perfil não foi publicado nesse relay")
            print("  3. A pubkey pode estar incorreta")
            print()
            print("Vou tentar pingar o relay...")

            # Testar conexão WebSocket
            import websockets
            try:
                async with websockets.connect(relay_url, ping_timeout=10) as ws:
                    print("✅ Relay está acessível via WebSocket")
            except Exception as e:
                print(f"❌ Erro ao conectar no relay: {e}")

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
