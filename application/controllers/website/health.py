# -*- coding: utf-8 -*-
"""
Bibi 健康检查端点。

路由：
- GET /api/health         基础健康检查（返回 200）
- GET /api/health/detailed 详细检查（MongoDB / Redis / Celery 状态）
"""

import time
import logging
from flask import Blueprint, jsonify, current_app as app

logger = logging.getLogger('bibi.health')

health = Blueprint('health', __name__, url_prefix='/api/health')


def _check_mongodb() -> dict:
    """检查 MongoDB 连接状态。"""
    start = time.perf_counter()
    try:
        from mongoengine.connection import get_db
        db = get_db()
        db.command('ping')
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {'status': 'OK', 'latency_ms': elapsed_ms}
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning('MongoDB health check failed: %s', e)
        return {'status': 'FAIL', 'error': str(e), 'latency_ms': elapsed_ms}


def _check_redis() -> dict:
    """检查 Redis 连接状态。"""
    start = time.perf_counter()
    try:
        from application.extensions import redis
        redis.ping()
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {'status': 'OK', 'latency_ms': elapsed_ms}
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning('Redis health check failed: %s', e)
        return {'status': 'FAIL', 'error': str(e), 'latency_ms': elapsed_ms}


def _check_celery() -> dict:
    """检查 Celery worker 状态。"""
    start = time.perf_counter()
    try:
        from application.ext_celery import make_celery
        celery = make_celery(app)
        inspect = celery.control.inspect()
        stats = inspect.stats()
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        if not stats:
            return {
                'status': 'WARN',
                'error': 'No Celery workers responded to ping',
                'latency_ms': elapsed_ms,
            }

        workers = list(stats.keys())
        return {
            'status': 'OK',
            'workers': len(workers),
            'worker_names': workers,
            'latency_ms': elapsed_ms,
        }
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.warning('Celery health check failed: %s', e)
        return {'status': 'FAIL', 'error': str(e), 'latency_ms': elapsed_ms}


@health.route('', methods=['GET'])
def basic_health():
    """基础健康检查 — 返回 200 表示服务存活。"""
    return jsonify(
        status='OK',
        service='bibi',
        version=app.config.get('VERSION', 'unknown'),
        timestamp=int(time.time()),
    )


@health.route('/detailed', methods=['GET'])
def detailed_health():
    """详细健康检查 — 包含 MongoDB / Redis / Celery 状态。"""
    checks = {
        'mongodb': _check_mongodb(),
        'redis': _check_redis(),
        'celery': _check_celery(),
    }

    overall = all(
        c['status'] == 'OK' for c in checks.values()
    )

    return jsonify(
        status='OK' if overall else 'DEGRADED',
        service='bibi',
        version=app.config.get('VERSION', 'unknown'),
        timestamp=int(time.time()),
        checks=checks,
    )
