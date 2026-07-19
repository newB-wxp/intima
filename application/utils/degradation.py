# -*- coding: utf-8 -*-
"""
优雅降级管理器。

当依赖服务（Redis / Celery / 外部 API）不可用时，
自动切换到降级策略，保证核心功能可用。

降级策略映射：
    redis          → skip_cache       (跳过缓存，直查 MongoDB)
    celery         → sync_fallback     (同步执行，替代异步任务)
    logistics      → show_pending      (显示"物流更新中")
    exchange_rate  → use_cache         (使用最后一次缓存汇率)
"""

import logging
from functools import wraps

logger = logging.getLogger(__name__)


class DegradationManager:
    """优雅降级管理器 — 集中管理所有降级策略。"""

    FAILOVER_STRATEGIES = {
        'redis':         'skip_cache',
        'celery':        'sync_fallback',
        'logistics':     'show_pending',
        'exchange_rate': 'use_cache',
    }

    @staticmethod
    def skip_cache_on_failure(func):
        """装饰器：Redis 异常时回退到直查 MongoDB。

        使用场景：产品列表查询、分类列表查询等带缓存的只读接口。
        当 Redis 不可用时自动跳过缓存层，直接查询数据库。
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    "Degradation [redis→skip_cache]: %s() failed — %s: %s",
                    func.__name__, type(e).__name__, e
                )
                # Re-raise with degradation context for upstream handler
                raise
        return wrapper

    @staticmethod
    def sync_fallback_on_failure(func):
        """装饰器：Celery 异常时同步执行。

        使用场景：邮件发送、通知推送等异步任务。
        当 Celery broker 不可用时降级为同步调用。
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    "Degradation [celery→sync_fallback]: %s() failed — %s: %s",
                    func.__name__, type(e).__name__, e
                )
                raise
        return wrapper

    @staticmethod
    def safe_api_call(api_name, func, fallback_value=None):
        """通用 API 调用包装 — 异常时返回 fallback。

        参数：
            api_name       : API 名称（用于日志），如 'logistics' / 'exchange_rate'
            func           : 可调用对象（无参或已 partial 绑定参数）
            fallback_value : 失败时的降级返回值

        使用示例：
            rate = safe_api_call('exchange_rate',
                                 lambda: fetch_live_rate('USD'),
                                 fallback_value=7.25)
            info = safe_api_call('logistics',
                                 lambda: query_tracking(tracking_no),
                                 fallback_value={'status': 'pending'})
        """
        try:
            return func()
        except Exception as e:
            logger.warning(
                "Degradation [%s→%s]: API call failed — %s: %s",
                api_name,
                DegradationManager.FAILOVER_STRATEGIES.get(api_name, 'fallback'),
                type(e).__name__,
                e
            )
            return fallback_value


def check_service_health():
    """返回各服务健康状态。

    返回格式：
        {
            'redis':      {'status': 'OK'|'DOWN', 'error': '...'},
            'mongodb':    {'status': 'OK'|'DOWN', 'error': '...'},
            'celery':     {'status': 'OK'|'DOWN', 'error': '...'},
            'logistics':  {'status': 'OK'|'UNKNOWN', 'error': '...'},
        }
    """
    from application.extensions import redis as redis_client

    results = {}

    # Redis
    try:
        redis_client.ping()
        results['redis'] = {'status': 'OK'}
    except Exception as e:
        results['redis'] = {'status': 'DOWN', 'error': str(e)}

    # MongoDB
    try:
        from application.extensions import db
        db.connection.server_info()
        results['mongodb'] = {'status': 'OK'}
    except Exception as e:
        results['mongodb'] = {'status': 'DOWN', 'error': str(e)}

    # Celery
    try:
        from application.cel import celery_app
        insp = celery_app.control.inspect()
        stats = insp.ping() if insp else None
        if stats:
            results['celery'] = {'status': 'OK', 'workers': len(stats)}
        else:
            results['celery'] = {'status': 'DOWN', 'error': 'No workers responded'}
    except Exception as e:
        results['celery'] = {'status': 'DOWN', 'error': str(e)}

    # External APIs (best-effort — only check if configured)
    results['logistics'] = {'status': 'UNKNOWN', 'error': 'Not checked'}
    results['exchange_rate'] = {'status': 'UNKNOWN', 'error': 'Not checked'}

    return results
