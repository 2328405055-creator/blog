# textscripts · cli.py — 命令行入口

import sys
import os
import logging
import subprocess

from textscripts.config import BASE_DIR, POSTS_DIR, JSON_PATH
from textscripts.generators.daily_generator import generate_posts
from textscripts.utils.sitemap_generator import generate_sitemap
from textscripts.utils.file_ops import load_json, today_str

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()

    do_push = "--push" in sys.argv

    logger.info("=" * 56)
    logger.info("  每日内容生成器 v5 — 真实来源 · 有据可查")
    logger.info("=" * 56)

    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)

    try:
        generate_posts()
    except Exception as e:
        logger.error(f"内容生成失败: {e}", exc_info=True)

    try:
        generate_sitemap()
    except Exception as e:
        logger.error(f"Sitemap 生成失败: {e}", exc_info=True)

    if do_push:
        logger.info("推送至 GitHub...")
        for cmd in [
            ["git", "add", "."],
            ["git", "commit", "-m", f"每日更新 {today_str()} — 来源采集"],
            ["git", "push"],
        ]:
            r = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
            tag = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:60]}"
            logger.info(f"  {' '.join(cmd)} -> {tag}")
        logger.info("推送完成")

    total = len(load_json(JSON_PATH))
    logger.info(f"当前线上 {total} 篇文章 -> http://20020426.top")


if __name__ == "__main__":
    main()
