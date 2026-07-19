# Intima 生产环境部署文档

## 前置条件

部署前请先注册以下外部服务：

| 服务 | 用途 | 注册链接 | 免费额度 |
|------|------|---------|---------|
| MongoDB Atlas | 主数据库 | https://www.mongodb.com/atlas | 512 MB |
| Upstash Redis | 缓存 / 消息队列 / Session | https://upstash.com | 256 MB |
| Render | 托管平台（Web + Worker） | https://render.com | 750 h/mo |
| Google OAuth | Google 登录 | https://console.cloud.google.com/apis/credentials | 免费 |
| Facebook Login | Facebook 登录 | https://developers.facebook.com | 免费 |
| CCBill | US/CA/GB 支付 | https://ccbill.com | — |
| EcomCharge | EU 支付 | https://ecomcharge.com | — |
| WcPay | 全球兜底支付 | https://wcpay.io | — |
| Sentry | 错误监控 | https://sentry.io | 5K errors/mo |
| Let's Encrypt | SSL 证书 | https://letsencrypt.org | 免费 |

---

## 一、本地开发

### 1.1 克隆项目

```bash
git clone <repo-url> intima
cd intima
```

### 1.2 创建虚拟环境

```bash
python3.12 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.3 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填写 SECRET_KEY 和 MONGODB_URI
```

### 1.4 启动本地服务

需要本地运行 MongoDB 和 Redis，或连接到 Atlas/Upstash。

```bash
# Terminal 1 — Flask 应用
flask run --debug

# Terminal 2 — Celery Worker
celery -A application.cel worker --loglevel=info

# Terminal 3 — Celery Beat（定时任务）
celery -A application.cel beat --loglevel=info
```

### 1.5 生成 Sitemap

```bash
python scripts/generate_sitemap.py --base-url http://localhost:5000
```

### 1.6 运行验证脚本

```bash
python scripts/verify_project.py
```

---

## 二、Render 一键部署

### 2.1 连接 GitHub 仓库

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New +** → **Blueprint**
3. 连接 GitHub 仓库（仓库根目录需包含 `render.yaml`）
4. Render 自动识别 Blueprint，展示 Web Service 和 Worker Service
5. 点击 **Apply**

### 2.2 配置环境变量

在 Render Dashboard 中逐一手动设置所有 `sync: false` 的环境变量：

- `SECRET_KEY`
- `IDCARD_KEY`
- `MONGODB_URI`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CCBILL_ACCOUNT_ID` / `CCBILL_API_KEY`
- `ECOMCHARGE_API_KEY`
- `WCPAY_API_KEY`
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
- `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET`
- `OAUTH_REDIRECT_BASE`
- `SENTRY_DSN`（可选）

### 2.3 部署后验证

```bash
# 健康检查
curl https://YOUR_RENDER_URL.onrender.com/api/health

# 详细健康检查
curl https://YOUR_RENDER_URL.onrender.com/api/health/detailed
```

---

## 三、环境变量配置清单

### 3.1 核心配置

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEV_MODE` | 是 | `true` = 开发模式（跳过 OAuth/支付），`false` = 生产模式 |
| `FLASK_ENV` | 是 | `development` / `production` |
| `ENV` | 是 | `development` / `staging` / `production` |
| `SITE_URL` | 是 | 站点 URL，不含尾部斜杠 |
| `APP_VERSION` | 否 | 应用版本号（默认 `2.0.0`） |
| `SECRET_KEY` | 是 | Flask 密钥 |
| `IDCARD_KEY` | 是 | 身份证加密密钥 |

### 3.2 数据库

| 变量 | 必填 | 说明 |
|------|------|------|
| `MONGODB_URI` | 是 | MongoDB Atlas SRV 连接字符串 |
| `REDIS_URL` | 是 | Upstash Redis `rediss://` 连接字符串 |
| `CELERY_BROKER_URL` | 是 | Celery 消息队列（默认 = `REDIS_URL`） |
| `CELERY_RESULT_BACKEND` | 是 | Celery 结果后端（默认 = `REDIS_URL`） |

### 3.3 OAuth

| 变量 | 必填（生产） | 说明 |
|------|-------------|------|
| `GOOGLE_CLIENT_ID` | 是 | Google OAuth 客户端 ID |
| `GOOGLE_CLIENT_SECRET` | 是 | Google OAuth 客户端密钥 |
| `FACEBOOK_APP_ID` | 是 | Facebook 应用 ID |
| `FACEBOOK_APP_SECRET` | 是 | Facebook 应用密钥 |
| `OAUTH_REDIRECT_BASE` | 是 | OAuth 回调基础 URL |

### 3.4 支付

| 变量 | 必填（生产） | 说明 |
|------|-------------|------|
| `CCBILL_ACCOUNT_ID` | 按需 | CCBill 账户 ID |
| `CCBILL_API_KEY` | 按需 | CCBill API 密钥 |
| `ECOMCHARGE_API_KEY` | 按需 | EcomCharge API 密钥 |
| `WCPAY_API_KEY` | 按需 | WcPay API 密钥 |
| `PAYMENT_SANDBOX` | 是 | `true` = 沙箱模式 |

### 3.5 监控

| 变量 | 必填 | 说明 |
|------|------|------|
| `SENTRY_DSN` | 否 | Sentry DSN（留空禁用） |

---

## 四、首次部署后操作

### 4.1 域名绑定

1. 在 Render Dashboard → Web Service → Settings → Custom Domain 添加域名
2. 在域名 DNS 添加 CNAME 记录指向 Render 提供的地址
3. 等待 DNS 生效（最长 48 小时）

### 4.2 SSL 证书

Render 自动为 `*.onrender.com` 和自定义域名签发 Let's Encrypt 证书。无需手动操作。

### 4.3 Google Search Console

1. 登录 [Google Search Console](https://search.google.com/search-console)
2. 添加属性 → URL 前缀 → 输入 `https://yourdomain.com`
3. 选择 HTML 文件验证方式 → 下载验证文件
4. 将验证文件放到 `application/static/` 目录并重新部署
5. 提交 Sitemap：`https://yourdomain.com/sitemap.xml`

### 4.4 生成 Sitemap（部署后）

Render 部署后通过 Shell 进入 Web Service 执行：

```bash
python scripts/generate_sitemap.py --base-url https://yourdomain.com
```

---

## 五、备份与恢复

### 5.1 自动备份（CI）

GitHub Actions `backup` job 每周日凌晨 3:00 (UTC) 执行数据库备份并上传 S3。

需要在 GitHub Secrets 中配置：
- `MONGODB_URI`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 5.2 手动备份

```bash
# MongoDB 备份
mongodump --uri="$MONGODB_URI" --out backups/$(date +%Y-%m-%d)/

# Redis 备份（Upstash 自动每日备份，无需手动操作）
```

### 5.3 恢复

```bash
# MongoDB 恢复
mongorestore --uri="$MONGODB_URI" --drop backups/2026-07-15/bibi/
```

---

## 六、CI/CD 流水线

每次 Push 到 `main` 或 `develop` 分支自动触发：

| 阶段 | 内容 | 阻塞 |
|------|------|------|
| Lint | Ruff 代码检查 | 是 |
| Test | Pytest 单元测试 | 是 |
| Security | Safety 依赖安全扫描 | 否 |

Render 自动监听 `main` 分支变更并触发重新部署。

---

## 七、常见问题排查

### 7.1 502 Bad Gateway

```bash
# 检查 Render 日志
# Dashboard → Web Service → Logs

# 常见原因：
# - 环境变量未设置或错误
# - MongoDB/Redis 连接失败
# - Gunicorn worker 超时
```

### 7.2 MongoDB 连接失败

```bash
# 检查 MONGODB_URI 格式
# 确保 Atlas IP 白名单包含 0.0.0.0/0（Render 出口 IP 不固定）
# 测试连接：
python -c "from pymongo import MongoClient; c=MongoClient('$MONGODB_URI'); print(c.server_info())"
```

### 7.3 Redis 连接失败

```bash
# Upstash 控制台检查连接状态
# 确保使用 rediss:// 协议（TLS）
# 测试连接：
python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
```

### 7.4 Celery Worker 不执行任务

```bash
# 检查 Worker 日志（Render Dashboard → Worker Service → Logs）
# 检查 CELERY_BROKER_URL 与 REDIS_URL 一致
# 确保 Worker Service 与 Web Service 使用相同的环境变量
```

### 7.5 速率限制误触发（开发环境）

设置 `DEV_MODE=true` 即可禁用所有速率限制。生产环境误触发：检查 `RATELIMIT_STORAGE_URI` 与 `REDIS_URL` 一致。

### 7.6 安全头缺失

检查 `TALISMAN_ENABLED=true` 且 `DEV_MODE=false`。

```bash
curl -I https://yourdomain.com | grep -E "X-|Strict-|Referrer"
```

---

## 八、目录结构

```
intima/
├── application/
│   ├── controllers/   # 路由控制器
│   ├── models/        # 数据模型（MongoEngine）
│   ├── services/      # 业务逻辑 + Celery 任务
│   ├── static/        # 静态资源
│   ├── templates/     # Jinja2 模板
│   └── utils/         # 工具函数（含降级、限流、Sentry）
├── configs/
│   └── config.py      # Flask 配置
├── scripts/           # 运维脚本
├── .github/workflows/ # GitHub Actions CI
├── requirements.txt   # Python 依赖
├── render.yaml        # Render Blueprint
├── Dockerfile         # Docker 镜像
├── docker-compose.yml # 本地 Docker 编排
├── wsgi.py            # WSGI 入口
├── gunicorn.conf.py   # Gunicorn 配置
├── DEPLOY.md          # 部署文档（本文件）
└── OPS.md             # 运维速查手册
```
