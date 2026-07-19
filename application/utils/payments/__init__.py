# -*- coding: utf-8 -*-
"""
Bibi Payment Gateway — Adult Industry Three-Channel Payment Router

Channels:
  - CCBill (US/CA/GB): ~10.8-14.5%, most stable in adult industry
  - EcomCharge (DE/FR/IT/NL/ES): 3.5-5%, optimal for European markets
  - WcPay (Global fallback): USDC instant settlement

Routing logic: route_payment(country_code) → PaymentProcessor
Primary failure → automatic fallback to next available channel.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


# Country → Primary channel routing map
_COUNTRY_CHANNEL_MAP = {
    'US': 'ccbill',
    'CA': 'ccbill',
    'GB': 'ccbill',
    'DE': 'ecomcharge',
    'FR': 'ecomcharge',
    'IT': 'ecomcharge',
    'NL': 'ecomcharge',
    'ES': 'ecomcharge',
}

# Fallback order per primary channel
_FALLBACK_ORDER = {
    'ccbill': ['ecomcharge', 'wcpay'],
    'ecomcharge': ['ccbill', 'wcpay'],
    'wcpay': ['ecomcharge', 'ccbill'],
}


def route_payment(country_code: str) -> str:
    """Return the primary payment channel name for a given country code."""
    return _COUNTRY_CHANNEL_MAP.get(country_code.upper(), 'wcpay')


def get_fallback_chain(primary_channel: str):
    """Return a list of fallback channel names for the given primary channel."""
    return _FALLBACK_ORDER.get(primary_channel, ['wcpay'])


def create_payment_with_fallback(
    amount: float,
    currency: str,
    order_id: str,
    customer_info: Dict[str, Any],
    country_code: str = 'US'
) -> PaymentResult:
    """
    Attempt payment through primary channel, fall back on failure.

    Returns the first successful PaymentResult, or the last failure.
    """
    primary = route_payment(country_code)
    channels = [primary] + get_fallback_chain(primary)

    last_error = None

    for channel in channels:
        try:
            if channel == 'ccbill':
                from .ccbill import CCBillProcessor
                processor = CCBillProcessor()
            elif channel == 'ecomcharge':
                from .ecomcharge import EcomChargeProcessor
                processor = EcomChargeProcessor()
            elif channel == 'wcpay':
                from .wcpay import WcPayProcessor
                processor = WcPayProcessor()
            else:
                continue

            result = processor.create_payment(amount, currency, order_id, customer_info)
            if result.success:
                return result
            last_error = result.error_message

        except Exception as e:
            last_error = f"{channel}: {str(e)}"
            continue

    return PaymentResult(success=False, error_message=last_error or 'All channels failed')
