# -*- coding: utf-8 -*-
"""
CCBill Payment Processor

Sandbox API: https://sandbox-api.ccbill.com
Production API: https://api.ccbill.com

CCBill is the most stable payment gateway in the adult industry,
with fees ranging from 10.8% to 14.5%. Primary channel for US/CA/GB.
"""

import hashlib
import hmac
import json
import time
from typing import Dict, Any

import requests
from flask import current_app

from . import PaymentResult


class CCBillProcessor:
    """CCBill payment processor for adult industry transactions."""

    def __init__(self):
        self.account_id = current_app.config.get('CCBILL_ACCOUNT_ID', '')
        self.api_key = current_app.config.get('CCBILL_API_KEY', '')
        self.sandbox = current_app.config.get('PAYMENT_SANDBOX', True)
        self.base_url = (
            'https://sandbox-api.ccbill.com'
            if self.sandbox
            else 'https://api.ccbill.com'
        )

    def create_payment(
        self,
        amount: float,
        currency: str,
        order_id: str,
        customer_info: Dict[str, Any]
    ) -> PaymentResult:
        """
        Create a payment through CCBill.

        Args:
            amount: Payment amount
            currency: ISO 4217 currency code (e.g. 'USD')
            order_id: Internal order ID for reconciliation
            customer_info: Dict with keys: email, first_name, last_name, ip_address

        Returns:
            PaymentResult with transaction details or error
        """
        try:
            payload = {
                'account_id': self.account_id,
                'amount': str(amount),
                'currency': currency,
                'order_id': order_id,
                'customer_email': customer_info.get('email', ''),
                'customer_first_name': customer_info.get('first_name', ''),
                'customer_last_name': customer_info.get('last_name', ''),
                'ip_address': customer_info.get('ip_address', ''),
                'timestamp': str(int(time.time())),
            }

            signature = self._sign(payload)
            headers = {
                'Content-Type': 'application/json',
                'X-CCBill-Signature': signature,
                'X-CCBill-Account': self.account_id,
            }

            resp = requests.post(
                f'{self.base_url}/transaction/create',
                json=payload,
                headers=headers,
                timeout=30,
            )

            data = resp.json()

            if resp.status_code == 200 and data.get('status') == 'success':
                return PaymentResult(
                    success=True,
                    transaction_id=data.get('transaction_id', ''),
                    amount=amount,
                    currency=currency,
                    raw_response=data,
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=data.get('message', 'CCBill payment failed'),
                    raw_response=data,
                )

        except requests.RequestException as e:
            current_app.logger.error(f'CCBill request error: {e}')
            return PaymentResult(success=False, error_message=str(e))
        except Exception as e:
            current_app.logger.error(f'CCBill unexpected error: {e}')
            return PaymentResult(success=False, error_message=str(e))

    def verify_webhook(self, request_data: bytes, headers: Dict[str, str]) -> bool:
        """
        Verify CCBill webhook signature.

        Args:
            request_data: Raw request body bytes
            headers: Request headers dict

        Returns:
            True if signature is valid
        """
        received_sig = headers.get('X-CCBill-Signature', '')
        expected_sig = self._sign_raw(request_data)

        if not received_sig or not expected_sig:
            return False

        return hmac.compare_digest(received_sig, expected_sig)

    def _sign(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for the payload."""
        raw = '&'.join(f'{k}={v}' for k, v in sorted(payload.items()))
        return hmac.new(
            self.api_key.encode('utf-8'),
            raw.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def _sign_raw(self, data: bytes) -> str:
        """Generate HMAC-SHA256 signature for raw bytes."""
        return hmac.new(
            self.api_key.encode('utf-8'),
            data,
            hashlib.sha256,
        ).hexdigest()
