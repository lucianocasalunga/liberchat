#!/usr/bin/env python3
import psycopg2

# Conversão manual bech32 -> hex
def bech32_decode(bech):
    """Decodifica bech32"""
    charset = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

    if bech.lower() != bech and bech.upper() != bech:
        return None, None

    bech = bech.lower()
    pos = bech.rfind('1')
    if pos < 1 or pos + 7 > len(bech):
        return None, None

    hrp = bech[:pos]
    data = []
    for char in bech[pos+1:]:
        if char not in charset:
            return None, None
        data.append(charset.find(char))

    return hrp, data

def convertbits(data, frombits, tobits, pad=True):
    """Converter bits"""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1

    for value in data:
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)

    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None

    return ret

# Converter npub para hex
npub = 'npub1uvksan4sr32e3tdxul7dmugc8ujz5yz0e7rwm3waj2znm27mjmqquvvsfn'

hrp, data = bech32_decode(npub)
if not hrp:
    print('[ERRO] Npub inválido')
    exit(1)

# Remover checksum (últimos 6 caracteres)
data = data[:-6]

# Converter de 5-bit para 8-bit
decoded = convertbits(data, 5, 8, False)
if not decoded:
    print('[ERRO] Erro ao converter bits')
    exit(1)

hex_key = ''.join(f'{b:02x}' for b in decoded)

print(f'[INFO] npub: {npub}')
print(f'[INFO] hex: {hex_key}')

# Conectar ao banco
try:
    conn = psycopg2.connect(
        dbname='liberchat',
        user='libernet',
        password='libernet2024',
        host='localhost',
        port='5432'
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

except Exception as e:
    print(f'[ERRO] {e}')
    exit(1)
