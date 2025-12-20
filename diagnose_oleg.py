#!/usr/bin/env python3
"""
Diagnóstico completo do perfil do Oleg
"""

import asyncio
from nostr_sdk import Client, Filter, Kind, PublicKey, Nip19
from datetime import timedelta
import json

OLEG_PUBKEY = '1961d24aadab04769a53ca74770fa0b263e73ea40f39d5d0781b0d578b11a27d'
OLEG_NPUB = 'npub1r9sayj4d4vz8dxjnef68wraqkf37w04ypuuat5rcrvx40zc35f7stwgr57'

async def diagnose():
    try:
        pubkey = PublicKey.from_hex(OLEG_PUBKEY)

        client = Client()

        # Relays do Oleg
        relays = [
            "wss://relay.libernet.app",
            "wss://relay.damus.io",
            "wss://nostr.wine"
        ]

        print("=" * 80)
        print("  DIAGNÓSTICO COMPLETO - PERFIL DO OLEG")
        print("=" * 80)
        print(f"\nNpub: {OLEG_NPUB}")
        print(f"Pubkey: {OLEG_PUBKEY}")
        print()

        for relay in relays:
            await client.add_relay(relay)
            print(f"+ {relay}")

        print("\nConectando...")
        await client.connect()
        await asyncio.sleep(3)

        print("\n" + "=" * 80)
        print("  TESTE 1: Perfil (kind 0) - Metadados")
        print("=" * 80)

        filter_profile = Filter().kind(Kind(0)).author(pubkey).limit(1)
        events_profile = await client.fetch_events([filter_profile], timeout=timedelta(seconds=10))

        if not events_profile.is_empty():
            event = events_profile.first()
            content = json.loads(event.content())
            print("✅ PERFIL ENCONTRADO!")
            print(f"   Nome: {content.get('name', 'N/A')}")
            print(f"   Display Name: {content.get('display_name', 'N/A')}")
            print(f"   NIP-05: {content.get('nip05', 'N/A')}")
            print(f"   Picture: {content.get('picture', 'N/A')}")
            print(f"   About: {content.get('about', 'N/A')}")
        else:
            print("❌ PERFIL NÃO ENCONTRADO!")
            print("   Problema: LiberMedia não publicou o kind 0 nos relays")

        print("\n" + "=" * 80)
        print("  TESTE 2: Relays (kind 10002) - NIP-65")
        print("=" * 80)

        filter_relays = Filter().kind(Kind(10002)).author(pubkey).limit(1)
        events_relays = await client.fetch_events([filter_relays], timeout=timedelta(seconds=10))

        if not events_relays.is_empty():
            event = events_relays.first()
            print("✅ LISTA DE RELAYS ENCONTRADA!")
            for tag in event.tags():
                if tag.as_vec()[0] == 'r':
                    relay_url = tag.as_vec()[1] if len(tag.as_vec()) > 1 else 'N/A'
                    relay_type = tag.as_vec()[2] if len(tag.as_vec()) > 2 else 'read/write'
                    print(f"   • {relay_url} ({relay_type})")
        else:
            print("❌ LISTA DE RELAYS NÃO ENCONTRADA!")
            print("   Problema: Jumble não publicou o kind 10002 nos relays")

        print("\n" + "=" * 80)
        print("  TESTE 3: Notas (kind 1) - Verificar se consegue publicar")
        print("=" * 80)

        filter_notes = Filter().kind(Kind(1)).author(pubkey).limit(5)
        events_notes = await client.fetch_events([filter_notes], timeout=timedelta(seconds=10))

        if not events_notes.is_empty():
            print(f"✅ ENCONTRADAS {len(events_notes)} NOTAS!")
            for event in events_notes:
                content = event.content()[:50]
                print(f"   • {content}...")
        else:
            print("⚠️  Nenhuma nota encontrada")

        print("\n" + "=" * 80)
        print("  RESUMO DO DIAGNÓSTICO")
        print("=" * 80)

        has_profile = not events_profile.is_empty()
        has_relays = not events_relays.is_empty()
        has_notes = not events_notes.is_empty()

        print(f"\n{'✅' if has_profile else '❌'} Perfil (kind 0)")
        print(f"{'✅' if has_relays else '❌'} Relays (kind 10002)")
        print(f"{'✅' if has_notes else '⚠️ '} Notas (kind 1)")

        print("\n" + "=" * 80)
        print("  SOLUÇÃO RECOMENDADA")
        print("=" * 80)

        if not has_profile and not has_relays:
            print("""
O LiberMedia NÃO publicou os metadados do Oleg nos relays.

PRECISO FAZER:
1. Publicar perfil completo (kind 0) com:
   - Nome: Oleg
   - NIP-05: oleg@libernet.app
   - Foto: [URL da imagem do LiberMedia]

2. Publicar lista de relays (kind 10002) com:
   - relay.libernet.app
   - relay.damus.io
   - nostr.wine

Para isso, PRECISO da nsec do Oleg para assinar os eventos.
            """)
        elif not has_profile:
            print("\n⚠️  Falta publicar o PERFIL (kind 0)")
            print("   Preciso da nsec do Oleg e URL da foto")
        elif not has_relays:
            print("\n⚠️  Falta publicar os RELAYS (kind 10002)")
            print("   Preciso da nsec do Oleg")

    except Exception as e:
        print(f'\n❌ Erro: {e}')
        import traceback
        traceback.print_exc()
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == '__main__':
    asyncio.run(diagnose())
