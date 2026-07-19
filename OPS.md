# Bibi 运维速查手册 (OPS.md)

> 快速定位常用命令与关键路径，适用于值班运维和应急响应。

---

## 一、服务管理

### 启动

```bash
# systemd（生产环境）
systemctl start bibi          # Flask (Gunicorn)
systemctl start bibi-worker   # Celery Worker
systemctl start bibi-beat     # Celery Beat
systemctl start nginx         # Nginx

# Docker Compose
cd /opt/bibi && docker-compose up -d
```

### 停止

```bash
systemctl stop bibi bibi-worker bibi-beat
docker-compose down
```

### 重启

```bash
# 平滑重启（零停机）
systemctl reload bibi

# 硬重启
systemctl restart bibi bibi-worker bibi-beat
systemctl reload nginx
```

### 查看状态

```bash
systemctl status bibi bibi-worker bibi-beat
docker-compose ps
```

---

## 二、日志位置

| 日志类型 | 路径 | 查看命令 |
|----------|------|---------|
| **应用日志** | `/opt/bibi/logs/app.log` | `tail -f /opt/bibi/logs/app.log` |
| Gunicorn 访问日志 | `/opt/bibi/logs/gunicorn-access.log` | `tail -f /opt/bibi/logs/gunicorn-access.log` |
| Gunicorn 错误日志 | `/opt/bibi/logs/gunicorn-error.log` | `tail -f /opt/bibi/logs/gunicorn-error.log` |
| systemd 日志 (bibi) | `journald` | `journalctl -u bibi -f` |
| systemd 日志 (worker) | `journald` | `journalctl -u bibi-worker -f` |
| Nginx 访问日志 | `/var/log/nginx/bibi-access.log` | `tail -f /var/log/nginx/bibi-access.log` |
| Nginx 错误日志 | `/var/log/nginx/bibi-error.log` | `tail -f /var/log/nginx/bibi-error.log` |
| Docker 日志 | `docker logs bibi-web -f` | — |

### 日志轮转

- `app.log` 按天轮转，保留 30 天（`TimedRotatingFileHandler`）。
- 不再需要手动配置 logrotate 处理 app.log。

---

## 三、备份位置

| 备份类型 | 路径 | 频率 |
|----------|------|------|
| MongoDB 全量备份 | `/opt/bibi/backups/YYYY-MM-DD/` | 每天 03:00 |
| 完整备份（含文件） | `/opt/bibi/backups/full_YYYY-MM-DD/` | 每周一 04:00 |

### 手动备份

```bash
cd /opt/bibi
source venv/bin/activate
python scripts/backup_db.py
```

### 恢复数据库

```bash
# 恢复 bibi 数据库
mongorestore --db bibi /opt/bibi/backups/2026-07-15/bibi/

# 恢复所有数据库
mongorestore --dir /opt/bibi/backups/2026-07-15/
```

### 上传到 S3

```bash
python scripts/backup_db.py --upload-s3 s3://my-bucket/bibi-backups
```

---

## 四、监控端点

| 端点 | URL | 说明 |
|------|-----|------|
| 基础健康检查 | `GET /api/health` | 返回 200 表示服务存活 |
| 详细健康检查 | `GET /api/health/detailed` | MongoDB / Redis / Celery 状态 + 延迟 |

### 健康检查示例

```bash
# 基础检查
curl -s http://localhost:5000/api/health | jq

# 详细检查
curl -s http://localhost:5000/api/health/detailed | jq

# 通过 Nginx
curl -s https://bibi.shop/api/health | jq
```

### 告警集成建议

- **Uptime 监控**：Prometheus Blackbox Exporter 轮询 `/api/health`。
- **组件监控**：Prometheus 轮询 `/api/health/detailed`，组件状态 != OK 时触发告警。
- **日志告警**：ELK/Sentry 收集 Python 异常 stack trace。

---

## 五、紧急回滚步骤

### 1. 代码回滚

```bash
cd /opt/bibi
git checkout <last-stable-tag-or-commit>
source venv/bin/activate
pip install -r requirements.txt
systemctl restart bibi bibi-worker bibi-beat
```

### 2. 数据库回滚

```bash
# 恢复最近一次备份
mongorestore --drop --dir /opt/bibi/backups/$(ls -1 /opt/bibi/backups/ | sort | tail -1)/
```

### 3. Docker 环境回滚

```bash
docker-compose down
git checkout <last-stable-tag-or-commit>
docker-compose build --no-cache
docker-compose up -d
```

---

## 六、常见问题故障排查

### 502 Bad Gateway

```bash
systemctl status bibi                    # Gunicorn 是否运行中
ss -tlnp | grep 8000                    # 端口是否监听
tail -50 /opt/bibi/logs/gunicorn-error.log
```

### MongoDB 连接失败

```bash
mongosh --eval "db.adminCommand('ping')"  # 测试连接
systemctl status mongod                   # 服务状态
curl -s localhost:5000/api/health/detailed | jq '.checks.mongodb'
```

### Redis 连接失败

```bash
redis-cli ping                           # 测试连接
systemctl status redis                   # 服务状态
curl -s localhost:5000/api/health/detailed | jq '.checks.redis'
```

### Celery 任务不执行

```bash
systemctl status bibi-worker                # Worker 状态
redis-cli LLEN celery                       # 队列积压
celery -A application.cel inspect active    # 当前活跃任务
curl -s localhost:5000/api/health/detailed | jq '.checks.celery'
```

### 磁盘空间不足

```bash
df -h /opt/bibi
du -sh /opt/bibi/logs/*
du -sh /opt/bibi/backups/*
```

---

## 七、Crontab 定时任务

```
# 每天凌晨 3 点 — MongoDB 增量备份
0 3 * * * cd /opt/bibi && venv/bin/python scripts/backup_db.py >> /var/log/bibi-backup.log 2>&1

# 每周一凌晨 4 点 — 完整备份（含文件 + 上传 S3）
0 4 * * 1 cd /opt/bibi && venv/bin/python scripts/backup_db.py --upload-s3 s3://my-bucket/bibi-backups >> /var/log/bibi-full-backup.log 2>&1
```

---

## 八、联系信息

| 角色 | 姓名 | 邮箱 | 电话 |
|------|------|------|------|
| 开发负责人 | — | season@maybi.cn | — |
| 运维负责人 | — | — | — |
| 应急联系人 | — | — | — |

> **模板说明**：请根据团队实际人员填充联系信息。
