# -*- coding: utf-8 -*-
"""
EcomCharge Payment Processor

API endpoint: https://api.ecomcharge.com/v1

EcomCharge is the optimal gateway for European markets
with competitive rates of 3.5-5%. Primary channel for DE/FR/IT/NL/ES.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any

import requests
from flask import current_app

from . import PaymentResult


class EcomChargeProcessor:
    """EcomCharge payment processor for European markets."""

    def __init__(self):
        self.api_key = current_app.config.get('ECOMCHARGE_API_KEY', '')
        self.sandbox = current_app.config.get('PAYMENT_SANDBOX', True)
        self.base_url = (
            'https://api.ecomcharge.com/v1'
        )

    def create_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any]
    ) -> PaymentResult:
        """
        Create a payment through EcomCharge.

        Args:
            amount: Payment amount in minor currency unit (e.g., cents for USD)
            currency: ISO 4217 currency code
            order_id: Internal order ID
            customer_info: Dict with keys: email, first_name, last_name

        Returns:
            PaymentResult
        """
        try:
            payload = {
                'transaction': {
                    'amount': int(amount * 100),  # minor units
                    'currency': currency,
                    'description': f'Order #{order_id}',
                },
                'customer': {
                    'email': customer_info.get('email', ''),
                    'first_name': customer_info.get('first_name', ''),
                    'last_name': customer_info.get('last_name', ''),
                },
                'reference_id': order_id,
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            }

            if self.sandbox:
                headers['X-Sandbox'] = 'true'

            resp = requests.post(
                f'{self.base_url}/payments',
                json=payload,
                headers=headers,
                timeout=30,
            )

            data = resp.json()

            if resp.status_code in (200, 201) and data.get('status') == 'pending':
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('id', ''),
                    amount=amount,
                    currency=currency,
                    redirect_url=data.get('redirect_url', ''),
                    raw_response=data,
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=data.get('error', {}).get('message', 'EcomCharge payment failed'),
                    raw_response=data,
                )

        except requests.RequestException as e:
            current_app.logger.error(f'EcomCharge request error: {e}')
            return PaymentResult(success=False, error_message=str(e))
        except Exception as e:
            current_app.logger.error(f'EcomCharge unexpected error: {e}')
            return PaymentResult(success=False, error_message=str(e))

    def verify_webhook(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify EcomCharge webhook signature.

        EcomCharge uses a signing secret to HMAC-SHA256 sign the webhook body.
        """
        received_sig = headers.get('X-EcomCharge-Signature', '')
        if not received_sig:
            return False

        expected_sig = hmac.new(
            self.api_key.encode('utf-8'),
            request_data,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(received_sig, expected_sig)
