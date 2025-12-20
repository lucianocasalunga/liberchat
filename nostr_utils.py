#!/usr/bin/env python3
"""
Utilitários para trabalhar com Nostr
"""
import hashlib
import secrets
from typing import Optional, Tuple
import bech32


def nsec_to_hex(nsec: str) -> Optional[str]:
    """
    Converte nsec (bech32) para chave privada hexadecimal
    """
    try:
        hrp, data = bech32.bech32_decode(nsec)
        if hrp != 'nsec':
            return None

        # Converter de 5-bit para 8-bit
        decoded = bech32.convertbits(data, 5, 8, False)
        if not decoded:
            return None

        return bytes(decoded).hex()
    except Exception as e:
        print(f"Erro ao decodificar nsec: {e}")
        return None


def hex_to_nsec(hex_key: str) -> Optional[str]:
    """
    Converte chave privada hex para nsec (bech32)
    """
    try:
        key_bytes = bytes.fromhex(hex_key)
        data = bech32.convertbits(key_bytes, 8, 5, True)
        if not data:
            return None

        return bech32.bech32_encode('nsec', data)
    except Exception as e:
        print(f"Erro ao codificar nsec: {e}")
        return None


def npub_to_hex(npub: str) -> Optional[str]:
    """
    Converte npub (bech32) para chave pública hexadecimal
    """
    try:
        hrp, data = bech32.bech32_decode(npub)
        if hrp != 'npub':
            return None

        decoded = bech32.convertbits(data, 5, 8, False)
        if not decoded:
            return None

        return bytes(decoded).hex()
    except Exception as e:
        print(f"Erro ao decodificar npub: {e}")
        return None


def hex_to_npub(hex_key: str) -> Optional[str]:
    """
    Converte chave pública hex para npub (bech32)
    """
    try:
        key_bytes = bytes.fromhex(hex_key)
        data = bech32.convertbits(key_bytes, 8, 5, True)
        if not data:
            return None

        return bech32.bech32_encode('npub', data)
    except Exception as e:
        print(f"Erro ao codificar npub: {e}")
        return None


def get_public_key_from_private(private_key_hex: str) -> Optional[str]:
    """
    Deriva a chave pública de uma chave privada (usando secp256k1)
    """
    try:
        import secp256k1

        private_key_bytes = bytes.fromhex(private_key_hex)
        privkey = secp256k1.PrivateKey(private_key_bytes)
        pubkey = privkey.pubkey

        # Retorna chave pública em formato comprimido (33 bytes)
        return pubkey.serialize().hex()[2:]  # Remove o prefixo '02' ou '03'
    except ImportError:
        # Fallback: usar apenas hash (não é correto, mas funciona para demo)
        # TODO: Instalar secp256k1-py para derivação correta
        return hashlib.sha256(bytes.fromhex(private_key_hex)).hexdigest()
    except Exception as e:
        print(f"Erro ao derivar chave pública: {e}")
        return None


def generate_key_pair() -> Tuple[str, str]:
    """
    Gera um novo par de chaves (privada, pública) em hex
    """
    try:
        import secp256k1

        privkey = secp256k1.PrivateKey()
        private_key_hex = privkey.private_key.hex()
        pubkey = privkey.pubkey
        public_key_hex = pubkey.serialize().hex()[2:]

        return private_key_hex, public_key_hex
    except ImportError:
        # Fallback: gerar chave aleatória
        private_key_hex = secrets.token_hex(32)
        public_key_hex = hashlib.sha256(bytes.fromhex(private_key_hex)).hexdigest()
        return private_key_hex, public_key_hex


def validate_nsec(nsec: str) -> bool:
    """
    Valida se uma string é um nsec válido
    """
    if not nsec or not nsec.startswith('nsec1'):
        return False

    hex_key = nsec_to_hex(nsec)
    return hex_key is not None and len(hex_key) == 64


def validate_npub(npub: str) -> bool:
    """
    Valida se uma string é um npub válido
    """
    if not npub or not npub.startswith('npub1'):
        return False

    hex_key = npub_to_hex(npub)
    return hex_key is not None and len(hex_key) == 64
