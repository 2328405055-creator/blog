@echo off
cd /d D:\games\blog
python scripts\daily_generator.py --push >> update_log.txt 2>&1
