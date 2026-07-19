# -*- coding: utf-8 -*-
"""
Bibi Phase 1: Adult Payment Controller

Routes:
  GET  /checkout             → SSR checkout page
  POST /api/payment/checkout → initiate payment through routed channel
  GET  /payment/success      → SSR success page
  GET  /payment/failed       → SSR failed page

Webhook callbacks are routed to payment_webhook.py:
  POST /api/payment/webhook/ccbill
  POST /api/payment/webhook/ecomcharge
  POST /api/payment/webhook/wcpay
"""

import datetime
import json

from flask import Blueprint, jsonify, request, redirect, render_template, current_app
from flask_login import login_required, current_user

import application.models as Models
from configs.enum import PAYMENT_TYPE, PAYMENT_TRADERS, ORDER_TYPE
from application.utils.payments import (
    route_payment,
    create_payment_with_fallback,
    PaymentResult,
)

payment = Blueprint('payment', __name__, url_prefix='')


@payment.route('/checkout', methods=['GET'])
@login_required
def checkout_page():
    """Render SSR checkout page."""
    # Retrieve pending order for current user
    # For MVP, get the most recent unpaid order
    order = Models.Order.objects(
        customer_id=current_user.id,
        status__ne='CANCELLED',
    ).order_by('-created_at').first()

    if not order:
        return redirect('/')

    return render_template('payment/checkout.html', order=order)


@payment.route('/api/payment/checkout/<order_id>', methods=['POST'])
@login_required
def create_payment(order_id):
    """
    Initiate payment for an order.

    Determines customer country from request context,
    routes to appropriate payment channel.
    """
    order = Models.Order.objects(id=order_id, customer_id=current_user.id).first()
    if not order:
        return jsonify(message='Failed', error='Order not found'), 404

    if order.is_paid:
        return jsonify(message='Failed', error='Order already paid'), 400

    # Determine country from request metadata or geolocation header
    country_code = request.headers.get('CF-IPCountry', 'US')

    # Customer info for payment gateway
    customer_info = {
        'email': current_user.account.email,
        'first_name': getattr(current_user.profile, 'first_name', ''),
        'last_name': getattr(current_user.profile, 'last_name', ''),
        'ip_address': request.remote_addr,
    }

    # Determine primary channel
    channel = route_payment(country_code)

    # Create payment record
    ptype = PAYMENT_TYPE.WITHOUT_TAX
    payment_obj = order.create_payment(ptype, channel.upper())
    payment_obj.payment_channel = channel
    payment_obj.save()

    # Attempt payment through routed channel
    result = create_payment_with_fallback(
        amount=order.final,
        currency='USD',
        order_id=str(order.id),
        customer_info=customer_info,
        country_code=country_code,
    )

    if result.success:
        # Map channel name back to PAYMENT_TRADERS
        trader_map = {
            'ccbill': PAYMENT_TRADERS.CCBILL,
            'ecomcharge': PAYMENT_TRADERS.ECOMCHARGE,
            'wcpay': PAYMENT_TRADERS.WCPAY,
        }
        payment_obj.trader = trader_map.get(channel, PAYMENT_TRADERS.WCPAY)
        payment_obj.ref_number = result.transaction_id
        payment_obj.payment_ref = result.transaction_id
        payment_obj.redirect_url = result.redirect_url or ''
        payment_obj.save()

        # Build redirect URL for SSR success page
        success_url = f'/payment/success?order_id={order.id}&ref={result.transaction_id}'
        return jsonify(message='OK', url=success_url)
    else:
        current_app.logger.error(
            f'Payment failed for order {order_id}: {result.error_message}'
        )
        return jsonify(
            message='Failed',
            error='Payment could not be processed. Please try again.',
        ), 500


@payment.route('/payment/success', methods=['GET'])
@login_required
def payment_success():
    """Render SSR payment success page."""
    order_id = request.args.get('order_id', '')
    order = Models.Order.objects(id=order_id, customer_id=current_user.id).first()
    order_short_id = order.short_id if order else 'N/A'
    return render_template('payment/success.html', order_short_id=order_short_id)


@payment.route('/payment/failed', methods=['GET'])
@login_required
def payment_failed():
    """Render SSR payment failed page."""
    return render_template('payment/failed.html')
