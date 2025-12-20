#!/usr/bin/env python3
"""
Verificar se perfil do Oleg existe nos relays
"""

import asyncio
from nostr_sdk import Client, Filter, Kind, PublicKey
from datetime import timedelta
import json

OLEG_PUBKEY = '1961d24aadab04769a53ca74770fa0b263e73ea40f39d5d0781b0d578b11a27d'

async def check_profile():
    try:
        pubkey = PublicKey.from_hex(OLEG_PUBKEY)

        client = Client()
        await client.add_relay("wss://relay.damus.io")
        await client.add_relay("wss://nos.lol")
        await client.add_relay("wss://relay.nostr.band")
        await client.add_relay("wss://relay.libernet.app")

        print("Conectando aos relays...")
        await client.connect()

        print(f"Buscando perfil (kind 0) para pubkey: {OLEG_PUBKEY}")
        filter_obj = Filter().kind(Kind(0)).author(pubkey).limit(1)
        events = await client.fetch_events([filter_obj], timeout=timedelta(seconds=10))

        if not events.is_empty():
            event = events.first()
            content = json.loads(event.content())
            print("\n✅ Perfil encontrado!")
            print(f"   Nome: {content.get('name', 'N/A')}")
            print(f"   Display Name: {content.get('display_name', 'N/A')}")
            print(f"   NIP-05: {content.get('nip05', 'N/A')}")
            print(f"   About: {content.get('about', 'N/A')}")
            return True
        else:
            print("\n❌ Nenhum perfil encontrado nos relays!")
            print("\nO Oleg precisa:")
            print("1. Fazer login em um cliente Nostr (Damus, Amethyst, Primal, etc)")
            print("2. Configurar seu perfil (nome, foto, bio)")
            print("3. O cliente vai publicar automaticamente nos relays")
            print("\nOu posso criar um perfil básico para ele agora.")
            return False

    except Exception as e:
        print(f'❌ Erro: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == '__main__':
    asyncio.run(check_profile())
