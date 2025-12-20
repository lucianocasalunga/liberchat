#!/usr/bin/env python3
"""
LiberChat - Payment Integration
Integração com OpenNode para doações via Lightning Network
"""

import requests
import os
from typing import Optional, Dict

# OpenNode Configuration
OPENNODE_API_KEY = "76ce1b39-cdb8-4c6d-8754-c7035977eb87"
OPENNODE_API_URL = "https://api.opennode.com/v1"

class OpenNodeClient:
    def __init__(self):
        self.api_key = OPENNODE_API_KEY
        self.base_url = OPENNODE_API_URL

    def create_invoice(self, amount_sats: int, memo: str, callback_url: str = None) -> Optional[Dict]:
        """
        Cria invoice no OpenNode
        Returns: {'bolt11': str, 'payment_hash': str (charge_id), 'qr_code_url': str}
        """
        if not self.api_key:
            raise RuntimeError("OpenNode não configurado (API_KEY ausente)")

        url = f"{self.base_url}/charges"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "amount": amount_sats,
            "currency": "btc",
            "description": memo,
            "auto_settle": False  # Não converter automaticamente para fiat
        }

        if callback_url:
            payload["callback_url"] = callback_url

        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)

            if r.status_code not in [200, 201]:
                raise RuntimeError(f"OpenNode erro HTTP {r.status_code}: {r.text}")

            data = r.json()
            charge_data = data.get("data", {})

            lightning_invoice = charge_data.get("lightning_invoice", {})

            print(f"[OPENNODE] ✅ Invoice criado: {amount_sats} sats - {charge_data.get('id')}")

            return {
                "bolt11": lightning_invoice.get("payreq", ""),
                "payment_hash": charge_data.get("id"),
                "checking_id": charge_data.get("id"),
                "qr_code_url": lightning_invoice.get("qr_code_url", ""),  # URL do QR code
                "expires_at": lightning_invoice.get("expires_at", "")
            }
        except Exception as e:
            print(f"[OPENNODE] ❌ Erro ao criar invoice: {e}")
            return None

    def check_invoice(self, charge_id: str) -> Optional[Dict]:
        """
        Verifica status de pagamento no OpenNode
        Returns: {'paid': bool, 'status': str}
        """
        if not self.api_key:
            raise RuntimeError("OpenNode não configurado (API_KEY ausente)")

        url = f"{self.base_url}/charge/{charge_id}"
        headers = {
            "Authorization": self.api_key
        }

        try:
            r = requests.get(url, headers=headers, timeout=15)

            if r.status_code not in [200, 201]:
                raise RuntimeError(f"OpenNode erro HTTP {r.status_code}: {r.text}")

            data = r.json()
            charge_data = data.get("data", {})

            # OpenNode retorna status: "paid", "unpaid", "processing", etc
            status = charge_data.get("status", "unpaid")
            is_paid = (status == "paid")

            return {
                "paid": is_paid,
                "status": status,
                "amount": charge_data.get("amount", 0)
            }
        except Exception as e:
            print(f"[OPENNODE] ❌ Erro ao verificar invoice: {e}")
            return None


# Instância global OpenNode
opennode = OpenNodeClient()

# Valores pré-definidos para doações
DONATION_AMOUNTS = {
    '5k': 5000,
    '10k': 10000,
    '50k': 50000,
    '100k': 100000,
    '1m': 1000000
}

def create_donation_invoice(amount_key: str) -> Optional[Dict]:
    """
    Cria invoice para doação de valor pré-definido
    """
    if amount_key not in DONATION_AMOUNTS:
        return None

    amount = DONATION_AMOUNTS[amount_key]
    memo = f"Doação LiberChat - {amount:,} sats"

    return opennode.create_invoice(
        amount_sats=amount,
        memo=memo,
        callback_url="https://chat.libernet.app/api/webhook/opennode"
    )

def create_custom_donation_invoice(amount_sats: int) -> Optional[Dict]:
    """
    Cria invoice para doação de valor livre
    """
    if amount_sats < 1000:  # Mínimo 1k sats
        return None

    memo = f"Doação LiberChat - {amount_sats:,} sats"

    return opennode.create_invoice(
        amount_sats=amount_sats,
        memo=memo,
        callback_url="https://chat.libernet.app/api/webhook/opennode"
    )
