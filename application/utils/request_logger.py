# -*- coding: utf-8 -*-
"""
Bibi 请求日志中间件。

功能：
- 记录 method, path, status_code, 耗时(ms), IP, User-Agent
- 仅在非静态资源请求时记录
- DEV_MODE=True 时启用，生产环境可选
"""

import time
import logging
from flask import Flask, request, g

logger = logging.getLogger('bibi.request')

STATIC_PREFIXES = ('/static/', '/favicon.ico', '/_debug_toolbar/')


def _is_static_request() -> bool:
    """判断是否为静态资源请求。"""
    path = request.path
    return any(path.startswith(prefix) for prefix in STATIC_PREFIXES)


def register_request_logging(app: Flask) -> None:
    """
    注册请求日志钩子到 Flask app。

    仅在 DEV_MODE=True 时启用。
    """
    dev_mode = app.config.get('DEV_MODE', False)
    if not dev_mode:
        logger.info('Request logging disabled (DEV_MODE=False)')
        return

    @app.before_request
    def _before_request():
        if _is_static_request():
            return
        g._request_start_time = time.perf_counter()

    @app.after_request
    def _after_request(response):
        if _is_static_request():
            return response

        start_time = g.pop('_request_start_time', None)
        if start_time is None:
            return response

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            'method=%-7s | status=%d | %5dms | ip=%-15s | ua=%s | %s',
            request.method,
            response.status_code,
            elapsed_ms,
            request.remote_addr or '-',
            request.headers.get('User-Agent', '-')[:120],
            request.path,
        )
        return response

    logger.info('Request logging enabled (DEV_MODE=True)')
