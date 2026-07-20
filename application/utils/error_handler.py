# -*- coding: utf-8 -*-
"""
Bibi 全局异常捕获与错误处理。

功能：
- 注册 Flask errorhandler（404 / 500 / 403）
- 500 错误自动记录完整堆栈到日志
- 生产环境返回友好错误页面（不暴露堆栈）
- DEV_MODE=True 时保留 Werkzeug debugger
"""

import logging
import traceback
from flask import Flask, jsonify, render_template_string, request

logger = logging.getLogger('bibi.error')

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
{% raw %}        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
               display: flex; justify-content: center; align-items: center; min-height: 100vh;
               margin: 0; background: #f5f5f5; color: #333; }
        .card { background: #fff; padding: 48px 64px; border-radius: 12px;
                 box-shadow: 0 2px 16px rgba(0,0,0,0.08); text-align: center; max-width: 480px; }
        h1 { font-size: 72px; margin: 0; color: #e74c3c; font-weight: 200; }
        h2 { font-size: 20px; margin: 8px 0 16px; color: #555; }
        p { color: #888; font-size: 14px; line-height: 1.6; }
        a { color: #3498db; text-decoration: none; }{% endraw %}
    </style>
</head>
<body>
    <div class="card">
        <h1>{code}</h1>
        <h2>{heading}</h2>
        <p>{message}</p>
        <p><a href="/">&larr; 返回首页</a></p>
    </div>
</body>
</html>
"""

ERROR_MESSAGES = {
    400: ('Bad Request', '请求参数有误，请检查后重试。'),
    403: ('Forbidden', '您没有权限访问此页面。'),
    404: ('Not Found', '您访问的页面不存在或已被移除。'),
    500: ('Internal Server Error', '服务器内部错误，请稍后重试。'),
}


def _should_use_debugger(app: Flask) -> bool:
    """判断是否保留 Werkzeug debugger。"""
    return app.config.get('DEV_MODE', False) or app.debug


def register_error_handlers(app: Flask) -> None:
    """
    注册全局错误处理器。

    注意：404 / 403 已在 configure_error_handlers 中注册，
    此函数补充 500 处理及覆盖逻辑。
    """
    dev_mode = _should_use_debugger(app)

    @app.errorhandler(400)
    def _bad_request(error):
        if dev_mode:
            raise error
        return _error_response(400)

    @app.errorhandler(403)
    def _forbidden(error):
        if dev_mode:
            raise error
        return _error_response(403)

    @app.errorhandler(404)
    def _not_found(error):
        if dev_mode:
            raise error
        return _error_response(404)

    @app.errorhandler(500)
    def _internal_error(error):
        # 记录完整堆栈
        logger.error(
            '500 Internal Server Error | path=%s | method=%s | ip=%s\n%s',
            request.path, request.method, request.remote_addr,
            traceback.format_exc()
        )
        if dev_mode:
            raise error
        return _error_response(500)

    @app.errorhandler(Exception)
    def _unhandled_exception(error):
        logger.error(
            'Unhandled exception | path=%s | method=%s | ip=%s | type=%s\n%s',
            request.path, request.method, request.remote_addr,
            type(error).__name__, traceback.format_exc()
        )
        if dev_mode:
            raise error
        return _error_response(500)

    logger.info('Error handlers registered | DEV_MODE=%s', dev_mode)


def _error_response(status_code: int):
    """根据 Accept 头返回 JSON 或 HTML 错误页面。"""
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])

    if best == 'application/json':
        return jsonify(
            success=False,
            code=status_code,
            error=ERROR_MESSAGES.get(status_code, ('Error', ''))[1]
        ), status_code

    heading, message = ERROR_MESSAGES.get(status_code, ('Error', '未知错误。'))
    html = render_template_string(
        ERROR_TEMPLATE,
        code=status_code,
        title=f'{status_code} - {heading}',
        heading=heading,
        message=message
    )
    return html, status_code
