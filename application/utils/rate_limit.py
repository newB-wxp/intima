# -*- coding: utf-8 -*-
"""
Flask-Limiter 速率限制集成模块。

使用 Upstash Redis 作为存储后端，DEV_MODE=True 时自动禁用。
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)


def init_limiter(app):
    """初始化 Flask-Limiter。

    DEV_MODE=True 时禁用所有速率限制（方便本地开发）。
    生产环境使用 REDIS_URL 作为存储后端。
    """
    if app.config.get('DEV_MODE'):
        app.config['RATELIMIT_ENABLED'] = False
        return

    redis_url = app.config.get('REDIS_URL', '')
    if redis_url:
        # Flask-Limiter 3.x 通过 RATELIMIT_STORAGE_URI 或直接设置
        app.config['RATELIMIT_STORAGE_URI'] = redis_url

    limiter.init_app(app)


# ============================================
# 快捷装饰器使用示例（在路由文件中使用）
# ============================================
#
# from application.utils.rate_limit import limiter
#
# @limiter.limit("5 per minute")       # 登录
# @limiter.limit("3 per hour")         # 注册 / 密码重置
# @limiter.limit("30 per minute")      # 搜索
#
# 运行时 error_message 可通过 app.config 自定义：
#   app.config['RATELIMIT_STORAGE_URI'] = "redis://..."
#   429 响应由 Flask-Limiter 自动处理
