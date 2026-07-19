# -*- coding: utf-8 -*-
"""
Payment Webhook Callback Routes (Bibi Phase 1)

Each payment channel sends asynchronous webhook notifications
to confirm payment status. These endpoints verify signatures
and update order status accordingly.

Endpoints:
  POST /api/payment/webhook/ccbill
  POST /api/payment/webhook/ecomcharge
  POST /api/payment/webhook/wcpay
"""

import json
import datetime

from flask import Blueprint, request, jsonify, current_app

import application.models as Models
from application.utils.payments.ccbill import CCBillProcessor
from application.utils.payments.ecomcharge import EcomChargeProcessor
from application.utils.payments.wcpay import WcPayProcessor
from configs.enum import PAYMENT_STATUS, PAYMENT_TRADERS

payment_webhook = Blueprint('payment_webhook', __name__, url_prefix='/api/payment/webhook')


def _update_order_from_webhook(
    payment_ref: str,
    channel: str,
    paid_amount: float,
    currency: str,
    buyer_id: str = '',
) -> bool:
    """
    Find payment by ref_number and mark it as paid.

    Returns True if successful, False otherwise.
    """
    payment_obj = Models.Payment.objects(ref_number=payment_ref).first()
    if not payment_obj:
        current_app.logger.warning(
            f'Webhook: payment not found for ref {payment_ref} (channel={channel})'
        )
        return False

    if payment_obj.status == PAYMENT_STATUS.PAID:
        return True  # Already paid, idempotent

    data = {
        'paid_amount': paid_amount,
        'currency': currency,
        'buyer_id': buyer_id,
        'trade_status': 'APPROVED',
        'ref_number': payment_ref,
        'modified': datetime.datetime.utcnow(),
    }
    payment_obj.mark_paid(data)
    current_app.logger.info(
        f'Webhook: payment {payment_ref} marked paid via {channel}'
    )
    return True


@payment_webhook.route('/ccbill', methods=['POST'])
def ccbill_webhook():
    """CCBill payment notification webhook."""
    processor = CCBillProcessor()
    raw_data = request.get_data()

    if not processor.verify_webhook(raw_data, dict(request.headers)):
        current_app.logger.warning('CCBill webhook: signature verification failed')
        return jsonify(message='Failed', error='Invalid signature'), 403

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return jsonify(message='Failed', error='Invalid JSON'), 400

    payment_ref = data.get('transaction_id', '')
    amount = float(data.get('amount', 0))
    currency = data.get('currency', 'USD')
    buyer_id = data.get('customer_email', '')

    success = _update_order_from_webhook(
        payment_ref, PAYMENT_TRADERS.CCBILL, amount, currency, buyer_id
    )

    if success:
        return jsonify(message='OK'), 200
    return jsonify(message='Failed', error='Payment not found'), 404


@payment_webhook.route('/ecomcharge', methods=['POST'])
def ecomcharge_webhook():
    """EcomCharge payment notification webhook."""
    processor = EcomChargeProcessor()
    raw_data = request.get_data()

    if not processor.verify_webhook(raw_data, dict(request.headers)):
        current_app.logger.warning('EcomCharge webhook: signature verification failed')
        return jsonify(message='Failed', error='Invalid signature'), 403

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return jsonify(message='Failed', error='Invalid JSON'), 400

    transaction = data.get('transaction', {})
    payment_ref = transaction.get('id', '')
    amount = float(transaction.get('amount', 0)) / 100  # minor to major units
    currency = transaction.get('currency', 'EUR')
    buyer_id = data.get('customer', {}).get('email', '')

    success = _update_order_from_webhook(
        payment_ref, PAYMENT_TRADERS.ECOMCHARGE, amount, currency, buyer_id
    )

    if success:
        return jsonify(message='OK'), 200
    return jsonify(message='Failed', error='Payment not found'), 404


@payment_webhook.route('/wcpay', methods=['POST'])
def wcpay_webhook():
    """WcPay payment notification webhook."""
    processor = WcPayProcessor()
    raw_data = request.get_data()

    if not processor.verify_webhook(raw_data, dict(request.headers)):
        current_app.logger.warning('WcPay webhook: signature verification failed')
        return jsonify(message='Failed', error='Invalid signature'), 403

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return jsonify(message='Failed', error='Invalid JSON'), 400

    payment_ref = data.get('payment_id', '')
    amount = float(data.get('amount', 0))
    currency = data.get('currency', 'USD')
    buyer_id = data.get('customer_email', '')

    success = _update_order_from_webhook(
        payment_ref, PAYMENT_TRADERS.WCPAY, amount, currency, buyer_id
    )

    if success:
        return jsonify(message='OK'), 200
    return jsonify(message='Failed', error='Payment not found'), 404
