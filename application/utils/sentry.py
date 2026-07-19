# -*- coding: utf-8 -*-
"""
Sentry 错误监控集成模块。

生产环境通过 SENTRY_DSN 环境变量激活。无 DSN 时静默跳过。
免费额度：5,000 errors/月。
"""

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def init_sentry(app):
    """初始化 Sentry SDK。

    仅当 SENTRY_DSN 非空且非 TESTING 模式时激活。
    traces_sample_rate 设为 0.1 以控制 APM 配额消耗。
    """
    dsn = app.config.get('SENTRY_DSN', '')
    if not dsn or app.config.get('TESTING'):
        return

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.1,
        environment=app.config.get('ENV', 'production'),
        release=app.config.get('APP_VERSION', '1.0.0'),
    )
