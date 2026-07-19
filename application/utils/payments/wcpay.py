# -*- coding: utf-8 -*-
"""
WcPay Payment Processor (Global Fallback)

WcPay supports USDC instant settlement as a global fallback channel.
Used when CCBill and EcomCharge are unavailable or for countries
not covered by the primary channels.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any

import requests
from flask import current_app

from . import PaymentResult


class WcPayProcessor:
    """WcPay payment processor with USDC settlement support."""

    def __init__(self):
        self.api_key = current_app.config.get('WCPAY_API_KEY', '')
        self.sandbox = current_app.config.get('PAYMENT_SANDBOX', True)
        self.base_url = (
            'https://sandbox-api.wcpay.io'
            if self.sandbox
            else 'https://api.wcpay.io'
        )

    def create_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any]
    ) -> PaymentResult:
        """
        Create a payment through WcPay.

        Supports USDC settlement for instant crypto payouts.

        Args:
            amount: Payment amount
            currency: ISO 4217 currency code
            order_id: Internal order ID
            customer_info: Dict with keys: email, first_name, last_name

        Returns:
            PaymentResult
        """
        try:
            payload = {
                'amount': str(amount),
                'currency': currency,
                'order_id': order_id,
                'customer_email': customer_info.get('email', ''),
                'customer_name': (
                    f"{customer_info.get('first_name', '')} "
                    f"{customer_info.get('last_name', '')}"
                ).strip(),
                'settlement_currency': 'USDC',
                'timestamp': int(time.time()),
            }

            signature = self._sign(payload)
            headers = {
                'Content-Type': 'application/json',
                'X-WcPay-Signature': signature,
                'X-WcPay-API-Key': self.api_key,
            }

            resp = requests.post(
                f'{self.base_url}/v1/payments',
                json=payload,
                headers=headers,
                timeout=30,
            )

            data = resp.json()

            if resp.status_code == 200 and data.get('success'):
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('payment_id', ''),
                    amount=amount,
                    currency=currency,
                    redirect_url=data.get('checkout_url', ''),
                    raw_response=data,
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=data.get('error', 'WcPay payment failed'),
                    raw_response=data,
                )

        except requests.RequestException as e:
            current_app.logger.error(f'WcPay request error: {e}')
            return PaymentResult(success=False, error_message=str(e))
        except Exception as e:
            current_app.logger.error(f'WcPay unexpected error: {e}')
            return PaymentResult(success=False, error_message=str(e))

    def verify_webhook(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify WcPay webhook signature.
        """
        received_sig = headers.get('X-WcPay-Signature', '')
        if not received_sig:
            return False

        expected_sig = hmac.new(
            self.api_key.encode('utf-8'),
            request_data,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(received_sig, expected_sig)
