#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bibi 数据库备份脚本。

功能：
- MongoDB 导出：使用 mongodump
- 备份到 backups/ 目录（按日期命名）
- 自动清理 7 天前的备份
- 支持 --upload-s3 参数（上传到 S3，可选）
- 支持 --dry-run 参数（仅打印操作，不执行）

用法：
    python scripts/backup_db.py                          # 标准备份
    python scripts/backup_db.py --dry-run                # 模拟运行
    python scripts/backup_db.py --upload-s3 s3://my-bucket/bibi-backups  # 备份并上传
"""

import os
import sys
import shutil
import argparse
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger('bibi.backup')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# ── Configuration ──────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_ROOT = PROJECT_ROOT / 'backups'

# MongoDB 数据库列表（按项目配置）
DATABASES = ['bibi', 'order', 'inventory', 'cart', 'content']

# 保留天数
RETENTION_DAYS = 7


# ── Core Functions ─────────────────────────────────────────────

def check_mongodump() -> bool:
    """检查 mongodump 是否可用。"""
    if not shutil.which('mongodump'):
        logger.error('mongodump not found. Install MongoDB Database Tools.')
        return False
    return True


def create_backup_dir(date_str: str) -> Path:
    """创建备份目录 backups/YYYY-MM-DD/"""
    backup_dir = BACKUP_ROOT / date_str
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def mongodump_database(db_name: str, backup_dir: Path, dry_run: bool = False) -> bool:
    """使用 mongodump 导出单个数据库。"""
    cmd = ['mongodump', '--db', db_name, '--out', str(backup_dir)]

    if dry_run:
        logger.info('[DRY-RUN] Would execute: %s', ' '.join(cmd))
        return True

    try:
        logger.info('Backing up database: %s', db_name)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error('mongodump failed for %s: %s', db_name, result.stderr.strip())
            return False
        logger.info('Backup complete: %s -> %s', db_name, backup_dir / db_name)
        return True
    except subprocess.TimeoutExpired:
        logger.error('mongodump timed out for %s', db_name)
        return False
    except Exception as e:
        logger.error('mongodump error for %s: %s', db_name, e)
        return False


def cleanup_old_backups(retention_days: int = RETENTION_DAYS, dry_run: bool = False):
    """清理 retention_days 天前的备份目录。"""
    if not BACKUP_ROOT.exists():
        logger.info('No backups directory found. Skipping cleanup.')
        return

    cutoff = datetime.now() - timedelta(days=retention_days)

    for entry in sorted(BACKUP_ROOT.iterdir()):
        if not entry.is_dir():
            continue

        # 尝试解析目录名为 YYYY-MM-DD 格式
        try:
            dir_date = datetime.strptime(entry.name, '%Y-%m-%d')
        except ValueError:
            logger.debug('Skipping non-date directory: %s', entry.name)
            continue

        if dir_date < cutoff:
            if dry_run:
                logger.info('[DRY-RUN] Would remove: %s', entry)
            else:
                logger.info('Removing old backup: %s', entry)
                shutil.rmtree(entry)
        else:
            logger.debug('Keeping backup: %s', entry.name)


def upload_to_s3(s3_uri: str, backup_dir: Path, dry_run: bool = False):
    """上传备份到 S3。"""
    cmd = ['aws', 's3', 'sync', str(backup_dir), f'{s3_uri}/{backup_dir.name}/']

    if dry_run:
        logger.info('[DRY-RUN] Would execute: %s', ' '.join(cmd))
        return True

    if not shutil.which('aws'):
        logger.warning('AWS CLI not found. Skipping S3 upload.')
        return False

    try:
        logger.info('Uploading to S3: %s', s3_uri)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if result.returncode != 0:
            logger.error('S3 upload failed: %s', result.stderr.strip())
            return False
        logger.info('S3 upload complete.')
        return True
    except Exception as e:
        logger.error('S3 upload error: %s', e)
        return False


def generate_manifest(backup_dir: Path, success_count: int, total_count: int):
    """生成备份清单文件。"""
    manifest_path = backup_dir / 'MANIFEST.txt'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(f'Bibi Backup Manifest\n')
        f.write(f'=====================\n')
        f.write(f'Date:       {datetime.now().isoformat()}\n')
        f.write(f'Databases:  {success_count}/{total_count} succeeded\n')
        f.write(f'Host:       {os.uname().nodename if hasattr(os, "uname") else "unknown"}\n')
        f.write(f'Tool:       mongodump\n')
        f.write(f'\nDatabases backed up:\n')
        for db_name in DATABASES:
            db_path = backup_dir / db_name
            if db_path.exists():
                size = sum(p.stat().st_size for p in db_path.rglob('*') if p.is_file())
                f.write(f'  - {db_name} ({size:,} bytes)\n')
    logger.info('Manifest written: %s', manifest_path)


# ── Main ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Bibi Database Backup Script')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without executing')
    parser.add_argument('--upload-s3', type=str, default=None,
                        help='S3 URI to upload backup (e.g. s3://my-bucket/bibi-backups)')
    parser.add_argument('--db', type=str, nargs='+', default=DATABASES,
                        help='Databases to backup (default: all)')
    parser.add_argument('--retention', type=int, default=RETENTION_DAYS,
                        help=f'Retention days (default: {RETENTION_DAYS})')
    args = parser.parse_args()

    date_str = datetime.now().strftime('%Y-%m-%d')
    logger.info('Starting backup | date=%s | dry_run=%s', date_str, args.dry_run)

    if not args.dry_run and not check_mongodump():
        sys.exit(1)

    backup_dir = create_backup_dir(date_str)
    success_count = 0

    for db_name in args.db:
        ok = mongodump_database(db_name, backup_dir, dry_run=args.dry_run)
        if ok:
            success_count += 1

    total = len(args.db)
    if not args.dry_run and success_count > 0:
        generate_manifest(backup_dir, success_count, total)

    cleanup_old_backups(retention_days=args.retention, dry_run=args.dry_run)

    if args.upload_s3 and not args.dry_run:
        upload_to_s3(args.upload_s3, backup_dir)

    if args.dry_run:
        logger.info('[DRY-RUN] Backup simulation complete. %d/%d would be backed up.', total, total)
    else:
        logger.info('Backup complete. %d/%d databases backed up to %s', success_count, total, backup_dir)

    if success_count < total:
        sys.exit(1)


if __name__ == '__main__':
    main()
